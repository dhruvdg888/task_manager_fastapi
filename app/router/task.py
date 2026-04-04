from fastapi import APIRouter, HTTPException, status, Response
from typing import List
from fastapi.params import Depends, Query
from sqlalchemy import or_
from .. import models
from ..database import get_db
from sqlalchemy.orm import Session
from .. import schemas, models, oauth2
from datetime import datetime, timezone


router = APIRouter(prefix='/tasks', tags=['Tasks'])

# Create task
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate,db:Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    owner_id = current_user.id
    new_task = models.Task(**task.model_dump(), owner_id=int(owner_id))

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

# Get all tasks for the current user 
# applied filters
@router.get("/", response_model=List[schemas.Task])
async def get_all_tasks(status:str = Query(None),priority:str = Query(None), search:str = Query(None),db: Session = Depends(get_db),current_user = Depends(oauth2.get_current_user)):
    tasks_query = db.query(models.Task).filter(models.Task.owner_id == int(current_user.id))

    if status:
        tasks_query = tasks_query.filter(models.Task.status == status)
    
    if priority:
        tasks_query = tasks_query.filter(models.Task.priority == priority)
    
    if search:
     tasks_query = tasks_query.filter(
        or_(
            models.Task.title.ilike(f"%{search}%"),
            models.Task.description.ilike(f"%{search}%")
        )
     )

    return tasks_query.all()

# Get the analytics of overall tasks
@router.get("/analytics", response_model=schemas.TaskAnalytics)
async def get_analysis(db:Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    # Fetch all tasks once (1 query instead of 7)
    tasks = db.query(models.Task).filter(models.Task.owner_id == current_user.id).all()

    now = datetime.now(timezone.utc)
    
    total_tasks_count = len(tasks)
    completed_tasks_count = sum(1 for t in tasks if t.status == 'completed')
    pending_tasks_count = sum(1 for t in tasks if t.status == 'pending')
    high_priority_count = sum(1 for t in tasks if t.priority == 'high')
    medium_priority_count = sum(1 for t in tasks if t.priority == 'medium')
    low_priority_count = sum(1 for t in tasks if t.priority == 'low')
    over_due_tasks_count = sum(1 for t in tasks if t.due_date < now and t.status != 'completed')

    return {
        "total_tasks": total_tasks_count,
        "completed_tasks": completed_tasks_count,
        "pending_tasks": pending_tasks_count,
        "priority_counts": {
            "high": high_priority_count,
            "medium": medium_priority_count,
            "low": low_priority_count
        },
        "overdue_tasks": over_due_tasks_count
    }

# Get single task based on task id
@router.get("/{id}", response_model=schemas.Task)
async def get_task(id:int, db:Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == int(id), models.Task.owner_id == current_user.id).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"task with id {id} doesn't not exist")
    return task


# Update task (only owner can update the task)
@router.put("/{id}", response_model=schemas.Task)
async def update_task(task: schemas.TaskUpdate, id:int, db:Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
     task_query = db.query(models.Task).filter(models.Task.id == int(id))

     existing_task = task_query.first()

     if existing_task == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {id} doesn't exist")

     if current_user.id != task.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'You can not delete task with id {id}')
     
     task_query.update(task.model_dump(), synchronize_session=False)

     db.commit()

     return task_query.first()

# Delete a task (only owner can delete)
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id:int, db:Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    
    task_query = db.query(models.Task).filter(models.Task.id == id)
    task = task_query.first()

    if task == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {id} does not exist")
    
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You are not the owner of this task")
    
    task_query.delete(synchronize_session=False)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

    
# Mark task complete
@router.patch("/{id}", response_model=schemas.TaskBase)
async def mark_as_complete(id: int, db:Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == id).first()

    if task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You are not the owner of this task")
    
    task.status = "completed"

    db.commit()
    db.refresh(task)

    return task
