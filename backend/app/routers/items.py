from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, database
from app.services import items as items_service

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

@router.get("/", response_model=list[schemas.ProductResponse])
async def get_items(db: AsyncSession = Depends(database.get_db)):
    return await items_service.get_items_service(db)

@router.post("/", response_model=schemas.ProductResponse)
async def create_item(product: schemas.ProductCreate, db: AsyncSession = Depends(database.get_db)):
    return await items_service.create_item_service(db, product)