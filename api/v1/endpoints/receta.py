from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.session import get_db
from core.security import get_current_user
from schemas.receta import RecetaCreate, RecetaUpdate, RecetaResponse, PayloadCrearReceta
from models.user import Usuario
from services import receta as services_receta

router = APIRouter(prefix="/recetas", tags=["Recetas"])

@router.post("/", response_model=RecetaResponse, status_code=status.HTTP_201_CREATED)
async def publicar_receta(
    payload: PayloadCrearReceta,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** POST /api/v1/recetas
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Envía en el cuerpo JSON un objeto estructurado con los datos de la receta y una lista de sus ingredientes asociados.
    * **Resultado:** Registra la receta vinculando al autor autenticado e inserta todos sus ingredientes de forma relacional dentro de una transacción.
    """
    return await services_receta.create_recipe_with_ingredients(
        db=db, 
        receta_in=payload.receta, 
        ingredientes_in=payload.ingredientes, 
        current_user=current_user
    )

@router.get("/", response_model=List[RecetaResponse])
async def obtener_todas_las_recetas(
    skip: int = Query(0, ge=0, description="Número de registros a omitir para la paginación"),
    limit: int = Query(100, ge=1, le=100, description="Límite máximo de registros a retornar"),
    db: AsyncSession = Depends(get_db)
):
    """
    * **Ruta:** GET /api/v1/recetas?skip={offset}&limit={max_cantidad}
    * **Token:** No requiere
    * **Nivel de permiso:** Público (Cualquier visitante)
    * **Uso:** Llama a la ruta base usando parámetros de consulta para paginar los catálogos generales de la aplicación.
    * **Resultado:** Devuelve una lista con todas las recetas culinarias que se encuentren activas en la plataforma.
    """
    return await services_receta.get_all_active_recipes(db, skip=skip, limit=limit)

@router.get("/buscar", response_model=List[RecetaResponse])
async def buscar_recetas(
    nombre: str = Query(..., min_length=2, description="Nombre o palabra clave de la receta"),
    db: AsyncSession = Depends(get_db)
):
    """
    * **Ruta:** GET /api/v1/recetas/buscar?nombre={valor_a_buscar}
    * **Token:** No requiere
    * **Nivel de permiso:** Público (Cualquier visitante)
    * **Uso:** Añade el parámetro '?nombre=' al final de la ruta para buscar recetas en la plataforma.
    * **Resultado:** Retorna una lista con las recetas culinarias activas que coincidan textualmente con el término buscado.
    """
    return await services_receta.search_recetas_by_name(db, nombre)

@router.get("/{id}", response_model=RecetaResponse)
async def ver_detalle_receta(id: int, db: AsyncSession = Depends(get_db)):
    """
    * **Ruta:** GET /api/v1/recetas/{id}
    * **Token:** No requiere
    * **Nivel de permiso:** Público (Cualquier visitante)
    * **Uso:** Pasa el ID numérico de la receta en la URL para consultar su preparación completa.
    * **Resultado:** Devuelve la receta junto con su listado de ingredientes precargados mediante joins asíncronos en memoria. Lanza 404 si fue eliminada.
    """
    return await services_receta.get_receta_or_404(db, id)

@router.patch("/{id}", response_model=RecetaResponse)
async def editar_receta(
    id: int, 
    receta_in: RecetaUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** PATCH /api/v1/recetas/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Autor de la receta o Administrador
    * **Uso:** Envía los campos descriptivos o los bloques JSON de preparación/nutrición que se deseen cambiar de una receta propia.
    * **Resultado:** Modifica la receta en base de datos. Si el solicitante intenta editar una receta ajena, deniega la acción con un error 403.
    """
    return await services_receta.update_recipe_details(db, id, receta_in, current_user)

@router.delete("/{id}")
async def eliminar_receta(
    id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** DELETE /api/v1/recetas/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Autor de la receta o Administrador
    * **Uso:** Permite archivar o remover una publicación de recetas de la vista de la plataforma.
    * **Resultado:** Aplica Soft Delete marcando el campo de borrado lógico en el registro de la receta y lo propaga automáticamente hacia todos sus ingredientes.
    """
    return await services_receta.soft_delete_recipe(db, id, current_user)