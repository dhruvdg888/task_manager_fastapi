from fastapi import FastAPI
from . import models
from .database import engine

app = FastAPI()

# use this when not using Alembic
#models.Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message":"Welcome to Task Manager App"}

