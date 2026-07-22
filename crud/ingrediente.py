from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.ingrediente import Ingrediente
from schemas.ingrediente import IngredienteCreate, IngredienteUpdate
from datetime import datetime, timezone

async def create_ingrediente(db: AsyncSession, obj_in: IngredienteCreate) -> Ingrediente:
    ingrediente_data = obj_in.model_dump()
    db_obj = Ingrediente(**ingrediente_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_ingredientes_by_receta(db: AsyncSession, receta_id: int) -> list[Ingrediente]:
    result = await db.execute(
        select(Ingrediente).where(Ingrediente.id_receta == receta_id, Ingrediente.is_deleted == None)
    )
    return list(result.scalars().all())

async def update_ingrediente(db: AsyncSession, db_obj: Ingrediente, obj_in: IngredienteUpdate) -> Ingrediente:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def delete_ingrediente(db: AsyncSession, db_obj: Ingrediente) -> Ingrediente:
    db_obj.is_deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj