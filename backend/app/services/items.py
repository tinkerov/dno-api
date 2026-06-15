import json
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas
from app.crud import items as crud_items
from app.services.cache import get_cache, set_cache, delete_cache

async def get_items_service(db: AsyncSession):
    cached = await get_cache("all_items")
    if cached:
        return json.loads(cached)
    
    items = await crud_items.get_all_products(db)

    items_data = [schemas.ProductResponse.model_validate(i).model_dump() for i in items]
    await set_cache("all_items", json.dumps(items_data), expire=300)
    return items

async def create_item_service(db: AsyncSession, product_data: schemas.ProductCreate):
    new_product = await crud_items.create_product(db, product_data)
    await delete_cache("all_items")
    return new_product