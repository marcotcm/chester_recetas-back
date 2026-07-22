from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.session import get_db
from core.security import get_current_user
from schemas.comentario_receta import ComentarioRecetaCreate, ComentarioRecetaUpdate, ComentarioRecetaResponse
from models.user import Usuario
from services import comentario_receta as services_comentario

router = APIRouter()

@router.post("/", response_model=ComentarioRecetaResponse, status_code=status.HTTP_201_CREATED)
async def publicar_comentario(
    comentario_in: ComentarioRecetaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** POST /api/v1/comentarios
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Envía una crítica escrita y una puntuación en estrellas (1 a 5) en el cuerpo JSON para evaluar una receta.
    * **Resultado:** Guarda la review en la base de datos vinculándola al usuario activo. Valida que el autor no pueda comentar sus propias recetas.
    """
    return await services_comentario.post_comentario(db, comentario_in, current_user)

@router.get("/receta/{receta_id}", response_model=List[ComentarioRecetaResponse])
async def listar_comentarios_de_receta(
    receta_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    * **Ruta:** GET /api/v1/comentarios/receta/{receta_id}
    * **Token:** No requiere
    * **Nivel de permiso:** Público (Cualquier visitante)
    * **Uso:** Carga cronológicamente la sección de opiniones y reseñas públicas de una receta específica.
    * **Resultado:** Devuelve el listado de comentarios activos asociados a la receta consultada.
    """
    return await services_comentario.get_comments_by_recipe(db, receta_id)

@router.patch("/{id}", response_model=ComentarioRecetaResponse)
async def editar_comentario(
    id: int,
    comentario_in: ComentarioRecetaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** PATCH /api/v1/comentarios/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Autor del comentario o Administrador
    * **Uso:** Permite modificar el texto o la calificación en estrellas de un comentario previamente publicado.
    * **Resultado:** Actualiza parcialmente el registro en la base de datos. Lanza un error 403 si un usuario intenta modificar un comentario ajeno.
    """
    return await services_comentario.update_user_comment(db, id, comentario_in, current_user)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def eliminar_comentario(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** DELETE /api/v1/comentarios/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Autor del comentario o Administrador
    * **Uso:** Pasa el ID del comentario en la URL para retirarlo o moderarlo.
    * **Resultado:** Ejecuta un borrado lógico (Soft Delete) marcando el timestamp en `is_deleted` para ocultarlo de la plataforma sin corromper métricas históricas.
    """
    return await services_comentario.soft_delete_comment(db, id, current_user)