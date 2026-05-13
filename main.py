from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DNO")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {
        "status": "working",
        "message": "privet",
        "tech_stack": ["FastAPI", "PostgreSQL", "Docker"]
    }

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return products

@app.post("/items")
def create_item(name: str, price: int, description: str = None, db: Session = Depends(get_db)):
    new_product = models.Product(name=name, price=price, description=description)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return(new_product)