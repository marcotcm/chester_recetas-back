from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import comentario_receta as crud_comentario
from crud import receta as crud_receta
from models.user import Usuario, UserRole
from models.comentario_receta import ComentarioReceta
from schemas.comentario_receta import ComentarioRecetaCreate, ComentarioRecetaUpdate

async def post_comentario(
    db: AsyncSession, comentario_in: ComentarioRecetaCreate, current_user: Usuario
) -> ComentarioReceta:
    """Publica un comentario validando permisos y propiedad de la receta."""
    receta = await crud_receta.get_receta_by_id(db, comentario_in.id_receta)

    # Validar que el autor no comente su propia receta
    if receta.id_user == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes publicar un comentario o calificación en tu propia receta."
        )

    return await crud_comentario.create_comentario(
        db, obj_in=comentario_in, id_user=current_user.id
    )

async def get_comments_by_recipe(
    db: AsyncSession, id_receta: int
) -> List[ComentarioReceta]:
    """Obtiene el listado de comentarios de una receta existente."""
    await crud_receta.get_receta_by_id(db, id_receta)
    return await crud_comentario.get_comentarios_by_receta(db, id_receta)

async def update_user_comment(
    db: AsyncSession, comentario_id: int, comentario_in: ComentarioRecetaUpdate, current_user: Usuario
) -> ComentarioReceta:
    """Actualiza un comentario verificando que el solicitante sea el dueño o admin."""
    comentario = await crud_comentario.get_comentario_by_id(db, comentario_id)
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El comentario solicitado no existe o fue eliminado."
        )

    # Solo el autor del comentario o un Admin pueden editarlo
    if comentario.id_user != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este comentario."
        )

    return await crud_comentario.update_comentario(db, db_obj=comentario, obj_in=comentario_in)

async def soft_delete_comment(
    db: AsyncSession, comentario_id: int, current_user: Usuario
) -> dict:
    """Aplica soft delete al comentario comprobando la autoría."""
    comentario = await crud_comentario.get_comentario_by_id(db, comentario_id)
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El comentario solicitado no existe o ya fue borrado."
        )

    if comentario.id_user != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este comentario."
        )

    await crud_comentario.soft_delete_comentario(db, comentario)
    return {"status": "success", "message": "Comentario eliminado correctamente."}