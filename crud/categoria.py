from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.categoria import Categoria
from schemas.categoria import CategoriaCreate, CategoriaUpdate
from datetime import datetime, timezone

async def create_categoria(db: AsyncSession, obj_in: CategoriaCreate) -> Categoria:
    categoria_data = obj_in.model_dump()
    db_obj = Categoria(**categoria_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_categoria_by_id(db: AsyncSession, categoria_id: int) -> Categoria | None:
    result = await db.execute(
        select(Categoria).where(Categoria.id == categoria_id, Categoria.is_deleted == None)
    )
    return result.scalars().first()

async def get_categorias(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Categoria]:
    result = await db.execute(
        select(Categoria).where(Categoria.is_deleted == None).offset(skip).limit(limit)
    )
    return list(result.scalars().all())

async def update_categoria(db: AsyncSession, db_obj: Categoria, obj_in: CategoriaUpdate) -> Categoria:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def delete_categoria(db: AsyncSession, db_obj: Categoria) -> Categoria:
    db_obj.is_deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj