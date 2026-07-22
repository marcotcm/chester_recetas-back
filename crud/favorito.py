from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from models.favorito import Favorito
from models.receta import Receta
from schemas.favorito import FavoritoCreate

async def get_favorito_by_user_and_receta(
    db: AsyncSession, id_user: int, id_receta: int
) -> Optional[Favorito]:
    """Obtiene el registro de favorito de un usuario para una receta específica (incluyendo borrados)."""
    result = await db.execute(
        select(Favorito).where(
            Favorito.id_user == id_user,
            Favorito.id_receta == id_receta
        )
    )
    return result.scalars().first()

async def get_favoritos_by_usuario(
    db: AsyncSession, id_user: int
) -> List[Receta]:
    """Obtiene el listado de recetas marcadas como favoritas (no eliminadas) por un usuario."""
    result = await db.execute(
        select(Receta)
        .join(Favorito, Favorito.id_receta == Receta.id)
        .where(
            Favorito.id_user == id_user,
            Favorito.is_deleted == None,
            Receta.is_deleted == None
        )
        .options(joinedload(Receta.ingredientes))
    )
    return list(result.scalars().unique().all())

async def create_favorito(db: AsyncSession, obj_in: FavoritoCreate) -> Favorito:
    """Crea un nuevo registro de favorito."""
    favorito_data = obj_in.model_dump()
    db_obj = Favorito(**favorito_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def soft_delete_favorito(db: AsyncSession, db_obj: Favorito) -> Favorito:
    """Aplica baja lógica marcando el timestamp en is_deleted."""
    db_obj.is_deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def restore_favorito(db: AsyncSession, db_obj: Favorito) -> Favorito:
    """Restaura un favorito previamente eliminado de forma lógica."""
    db_obj.is_deleted = None
    await db.commit()
    await db.refresh(db_obj)
    return db_obj