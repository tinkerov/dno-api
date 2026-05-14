from fastapi import FastAPI
from . import models
from .database import engine
from .routers import items

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DNO")

app.include_router(items.router)

@app.get("/")
def root():
    return {"message": "DNO API is working!"}