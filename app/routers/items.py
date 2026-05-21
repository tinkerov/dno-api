from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .. import models, schemas, database
import httpx
from fastapi.responses import Response

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

# Переводим на асинхрон
@router.get("/", response_model=list[schemas.ProductResponse])
async def get_items(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Product))
    items = result.scalars().all()
    return items

# Так же переводим на асинхрон
@router.post("/", response_model=schemas.ProductResponse)
async def create_item(product: schemas.ProductCreate, db: AsyncSession = Depends(database.get_db)):
    new_product = models.Product(**product.dict())

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product