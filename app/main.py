from fastapi import FastAPI
from . import models
from .database import engine
from .routers import items
from .routers import auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DNO")

app.include_router(items.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "DNO API is working!"}