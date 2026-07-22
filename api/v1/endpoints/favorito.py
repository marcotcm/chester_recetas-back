from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.session import get_db
from core.security import get_current_user
from schemas.receta import RecetaResponse
from models.user import Usuario
from services import favorito as services_favorito

router = APIRouter()

@router.get("/", response_model=List[RecetaResponse])
async def listar_mis_favoritos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** GET /api/v1/favoritos
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Carga la lista de todas las recetas que el usuario autenticado ha guardado en su colección personal.
    * **Resultado:** Devuelve un arreglo con los datos completos de las recetas favoritas activas del usuario.
    """
    return await services_favorito.get_user_favoritos(db, current_user.id)

@router.post("/toggle/{receta_id}", status_code=status.HTTP_200_OK)
async def alternar_favorito(
    receta_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** POST /api/v1/favoritos/toggle/{receta_id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Se ejecuta al presionar el botón de guardar/corazón en una receta desde la interfaz web o móvil.
    * **Resultado:** Actúa como interruptor (Toggle). Registra la relación si no existía, le aplica soft delete si ya estaba guardada, o la reactiva si había sido removida previamente.
    """
    return await services_favorito.toggle_recipe_favorito(db, receta_id, current_user)

@router.delete("/{receta_id}", status_code=status.HTTP_200_OK)
async def eliminar_de_favoritos(
    receta_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** DELETE /api/v1/favoritos/{receta_id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Pasa el ID de la receta en la URL para quitarla definitivamente de la lista de favoritos/me gusta del usuario.
    * **Resultado:** Aplica un borrado lógico (Soft Delete) sobre el registro de la relación, asegurando que la receta ya no aparezca en la colección del perfil activo.
    """
    return await services_favorito.remove_from_favoritos(db, receta_id, current_user)