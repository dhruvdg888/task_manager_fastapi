from fastapi import FastAPI
from .router import auth, user, task

app = FastAPI()

# use this when not using Alembic
#models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(task.router)

@app.get("/")
async def root():
    return {"message":"Welcome to Task Manager App"}


    

