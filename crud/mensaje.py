from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.mensaje import Mensaje
from schemas.mensaje import MensajeCreate
from datetime import datetime, timezone

async def create_mensaje(db: AsyncSession, obj_in: MensajeCreate) -> Mensaje:
    mensaje_data = obj_in.model_dump()
    db_obj = Mensaje(**mensaje_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_mensajes(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Mensaje]:
    result = await db.execute(
        select(Mensaje).where(Mensaje.is_deleted == None).offset(skip).limit(limit)
    )
    return list(result.scalars().all())

async def delete_mensaje(db: AsyncSession, db_obj: Mensaje) -> Mensaje:
    db_obj.is_deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj