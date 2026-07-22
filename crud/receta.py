from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.receta import Receta
from schemas.receta import RecetaCreate, RecetaUpdate
from datetime import datetime, timezone

async def create_receta(db: AsyncSession, obj_in: RecetaCreate) -> Receta:
    receta_data = obj_in.model_dump()
    db_obj = Receta(**receta_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_receta_by_id(db: AsyncSession, receta_id: int) -> Receta | None:
    result = await db.execute(
        select(Receta).where(Receta.id == receta_id, Receta.is_deleted == None)
    )
    return result.scalars().first()

async def get_recetas(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Receta]:
    result = await db.execute(
        select(Receta).where(Receta.is_deleted == None).offset(skip).limit(limit)
    )
    return list(result.scalars().all())

async def update_receta(db: AsyncSession, db_obj: Receta, obj_in: RecetaUpdate) -> Receta:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def delete_receta(db: AsyncSession, db_obj: Receta) -> Receta:
    db_obj.is_deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj