from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .. import models, schemas, database
import httpx
from fastapi.responses import Response
import json
from app.services.cache import get_cache, set_cache, delete_cache

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

# Переводим на асинхрон
@router.get("/", response_model=list[schemas.ProductResponse])
async def get_items(db: AsyncSession = Depends(database.get_db)):
    cached = await get_cache("all_items")
    if cached:
        return json.loads(cached)
    
    result = await db.execute(select(models.Product))
    items = result.scalars().all()

    await set_cache("all_items", json.dumps([schemas.ProductResponse.model_validate(i).model_dump() for i in items]), expire=300)

    return items

# Так же переводим на асинхрон
@router.post("/", response_model=schemas.ProductResponse)
async def create_item(product: schemas.ProductCreate, db: AsyncSession = Depends(database.get_db)):
    new_product = models.Product(**product.model_dump())

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    await delete_cache("all_items")

    return new_product