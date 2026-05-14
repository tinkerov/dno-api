from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    price: int
    description: Optional[str] = None

class ProductResponse(ProductCreate):
    id: int
    in_stock: bool

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    in_stock: Optional[bool] = None