from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import favorito as crud_favorito
from crud import receta as crud_receta
from models.user import Usuario
from models.receta import Receta
from schemas.favorito import FavoritoCreate

async def get_user_favoritos(db: AsyncSession, id_user: int) -> List[Receta]:
    """Retorna las recetas favoritas del usuario autenticado."""
    return await crud_favorito.get_favoritos_by_usuario(db, id_user)

async def toggle_recipe_favorito(
    db: AsyncSession, receta_id: int, current_user: Usuario
) -> dict:
    """
    Alterna el estado de favorito de una receta para el usuario activo:
    - Si no existe: lo crea.
    - Si existe activo: le aplica soft delete.
    - Si existía pero estaba eliminado: lo reactiva.
    """
    # Validar que la receta exista y no esté eliminada
    receta = await crud_receta.get_receta_by_id(db, receta_id)

    fav = await crud_favorito.get_favorito_by_user_and_receta(
        db, id_user=current_user.id, id_receta=receta.id
    )

    if not fav:
        new_fav = FavoritoCreate(id_user=current_user.id, id_receta=receta.id)
        await crud_favorito.create_favorito(db, new_fav)
        return {"status": "added", "message": "Receta añadida a favoritos."}
    
    if fav.is_deleted is None:
        await crud_favorito.soft_delete_favorito(db, fav)
        return {"status": "removed", "message": "Receta removida de favoritos."}
    else:
        await crud_favorito.restore_favorito(db, fav)
        return {"status": "restored", "message": "Receta restaurada en favoritos."}

async def remove_from_favoritos(
    db: AsyncSession, receta_id: int, current_user: Usuario
) -> dict:
    """Elimina explícitamente una receta de la lista de favoritos."""
    fav = await crud_favorito.get_favorito_by_user_and_receta(
        db, id_user=current_user.id, id_receta=receta_id
    )

    if not fav or fav.is_deleted is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La receta no se encuentra en tus favoritos activos."
        )

    await crud_favorito.soft_delete_favorito(db, fav)
    return {"status": "success", "message": "Receta eliminada de tus favoritos."}