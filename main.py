from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
import schemas

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

@app.post("/items", response_model=schemas.ProductResponse)
def create_item(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return(new_product)

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):

    product = db.query(models.Product).filter(models.Product.id == item_id).first()

    if product is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not Found")
    
    db.delete(product)
    db.commit()
    return {"message": f"Product with id {item_id} deleted"}

@app.patch("/items/{item_id}", response_model=schemas.ProductResponse)
def update_item(item_id: int, product_data: schemas.ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == item_id_).first()
    if db_product is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(db_product, key, value)

        db.commit()
        db.refresh(db_product)
        return db_product