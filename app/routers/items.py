from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. database import get_db
from .. import models, schemas, database

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

@router.get("/", response_model=list[schemas.ProductResponse])
def get_items(db: Session = Depends(database.get_db)):
    return db.query(models.Product).all()

@router.post("/", response_model=schemas.ProductResponse)
def create_item(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product