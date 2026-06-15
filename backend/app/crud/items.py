from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models, schemas

async def get_all_products(db: AsyncSession):
    result = await db.execute(select(models.Product))
    return result.scalars().all()

async def create_product(db: AsyncSession, product_data: schemas.ProductCreate):
    new_product = models.Product(**product_data.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product