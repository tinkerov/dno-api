from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    price: int
    description: Optional[str] = None
    image_url: Optional[str] = None

class ProductResponse(ProductCreate):
    id: int
    in_stock: bool

    model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    in_stock: Optional[bool] = None

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str