from sqlalchemy import select
from app import models
from sqlalchemy.ext.asyncio import AsyncSession

async def delete_refresh_token(db: AsyncSession, token: str) -> bool:
    query = select(models.User).where(models.User.refresh_token == token)
    result = await db.execute(query)

    user = result.scalars().first()

    # Если нашли сессию - сносим ее из бд
    if user:
        user.refresh_token = None
        await db.commit()
        return True
    
    # Токен не найден в базе
    return False