from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.comentario_receta import ComentarioReceta
from schemas.comentario_receta import ComentarioRecetaCreate, ComentarioRecetaUpdate

async def get_comentario_by_id(
    db: AsyncSession, comentario_id: int
) -> Optional[ComentarioReceta]:
    """Obtiene un comentario específico por su ID numérico (solo activos)."""
    result = await db.execute(
        select(ComentarioReceta).where(
            ComentarioReceta.id == comentario_id,
            ComentarioReceta.is_deleted == None
        )
    )
    return result.scalars().first()

async def get_comentario_by_user_and_receta(
    db: AsyncSession, id_user: int, id_receta: int
) -> Optional[ComentarioReceta]:
    """Obtiene el comentario activo que un usuario haya hecho en una receta determinada."""
    result = await db.execute(
        select(ComentarioReceta).where(
            ComentarioReceta.id_user == id_user,
            ComentarioReceta.id_receta == id_receta,
            ComentarioReceta.is_deleted == None
        )
    )
    return result.scalars().first()

async def get_comentarios_by_receta(
    db: AsyncSession, id_receta: int
) -> List[ComentarioReceta]:
    """Obtiene todos los comentarios activos pertenecientes a una receta."""
    result = await db.execute(
        select(ComentarioReceta)
        .where(
            ComentarioReceta.id_receta == id_receta,
            ComentarioReceta.is_deleted == None
        )
        .order_by(ComentarioReceta.created_at.desc())
    )
    return list(result.scalars().all())

async def create_comentario(
    db: AsyncSession, obj_in: ComentarioRecetaCreate, id_user: int
) -> ComentarioReceta:
    """Crea un nuevo comentario en la base de datos."""
    comentario_data = obj_in.model_dump()
    db_obj = ComentarioReceta(**comentario_data, id_user=id_user)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_comentario(
    db: AsyncSession, db_obj: ComentarioReceta, obj_in: ComentarioRecetaUpdate
) -> ComentarioReceta:
    """Actualiza parcialmente el texto o la calificación del comentario."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def soft_delete_comentario(
    db: AsyncSession, db_obj: ComentarioReceta
) -> ComentarioReceta:
    """Aplica baja lógica registrando el timestamp en is_deleted."""
    db_obj.is_deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj