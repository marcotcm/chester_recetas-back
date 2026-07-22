import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from crud import receta as crud_receta
from crud import categoria as crud_categoria
from crud import ingrediente as crud_ingrediente
from schemas.receta import RecetaCreate, RecetaUpdate
from schemas.ingrediente import IngredienteCreate
from fastapi import HTTPException, status
from models.user import Usuario, UserRole
from models.receta import Receta

async def get_receta_or_404(db: AsyncSession, receta_id: int) -> Receta:
    """Obtiene una receta específica por su clave primaria. Lanza 404 si fue eliminada lógicamente."""
    receta = await crud_receta.get_receta_by_id(db, receta_id)
    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La receta no existe.")
    return receta

async def search_recetas_by_name(db: AsyncSession, query_name: str) -> list[Receta]:
    """Busca recetas de cocina activas filtrando coincidencias en el título."""
    result = await db.execute(
        select(Receta).where(
            Receta.nombre.ilike(f"%{query_name}%"),
            Receta.is_deleted == None
        )
    )
    return list(result.scalars().all())

async def create_recipe_with_ingredients(
    db: AsyncSession, receta_in: RecetaCreate, ingredientes_in: list[IngredienteCreate], current_user: Usuario
) -> Receta:
    """Registra una receta inyectando el ID del autor y sus respectivos ingredientes en lote."""
    # Verificar la existencia previa de la categoría asociada
    if receta_in.id_categoria:
        cat = await crud_categoria.get_categoria_by_id(db, receta_in.id_categoria)
        if not cat:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoría no válida.")
            
    # Forzar el ID del autor basado en el token del usuario activo
    receta_in.id_user = current_user.id
    try:
        # Crear la cabecera de la receta
        nueva_receta = await crud_receta.create_receta(db, obj_in=receta_in)
        
        # Iterar e insertar de forma síncrona/asíncrona cada ingrediente enlazado
        for ing in ingredientes_in:
            ing.id_receta = nueva_receta.id
            await crud_ingrediente.create_ingrediente(db, obj_in=ing)
        return nueva_receta
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def update_recipe_details(db: AsyncSession, receta_id: int, receta_in: RecetaUpdate, current_user: Usuario) -> Receta:
    """Modifica metadatos estructurales de la receta si el solicitante es dueño o administrador."""
    receta = await get_receta_or_404(db, receta_id)
    if receta.id_user != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos.")
        
    try:
        return await crud_receta.update_receta(db, db_obj=receta, obj_in=receta_in)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def soft_delete_recipe(db: AsyncSession, receta_id: int, current_user: Usuario):
    """Archiva de manera lógica una receta y desactiva en cascada todos sus ingredientes mapeados."""
    receta = await get_receta_or_404(db, receta_id)
    if receta.id_user != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operación denegada.")
        
    try:
        # 1. Soft-delete de la entidad padre
        await crud_receta.delete_receta(db, db_obj=receta)
        
        # 2. Desactivación de las entidades hijos (ingredientes)
        ingredientes = await crud_ingrediente.get_ingredientes_by_receta(db, receta_id)
        for ing in ingredientes:
            await crud_ingrediente.delete_ingrediente(db, db_obj=ing)
        return {"detail": "Receta y componentes archivados exitosamente."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def get_all_active_recipes(db: AsyncSession, skip: int, limit: int) -> list[Receta]:
    """Obtiene el catálogo completo de recetas culinarias activas del sistema."""
    return await crud_receta.get_recetas(db, skip=skip, limit=limit)