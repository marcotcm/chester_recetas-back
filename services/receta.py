import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from crud import receta as crud_receta
from crud import categoria as crud_categoria
from crud import ingrediente as crud_ingrediente
from schemas.receta import RecetaCreate, RecetaUpdate
from schemas.ingrediente import IngredienteCreate, IngredienteUpdate, IngredienteBulkUpdate
from models.ingrediente import Ingrediente
from fastapi import HTTPException, status
from models.user import Usuario, UserRole
from models.receta import Receta

async def get_receta_or_404(db: AsyncSession, receta_id: int) -> Receta:
    """Obtiene una receta específica por su clave primaria. Lanza 404 si fue eliminada lógicamente."""
    receta = await crud_receta.get_receta_by_id(db, receta_id)
    if not receta or receta.is_deleted is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La receta no existe o fue dada de baja.")
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
    if receta_in.id_categoria:
        cat = await crud_categoria.get_categoria_by_id(db, receta_in.id_categoria)
        if not cat:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoría no válida.")
            
    receta_in.id_user = current_user.id
    try:
        nueva_receta = await crud_receta.create_receta(db, obj_in=receta_in)
        
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
        await crud_receta.delete_receta(db, db_obj=receta)
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

# =========================================================================
# LÓGICA DE NEGOCIO NUEVA PARA INGREDIENTES
# =========================================================================

async def get_ingredients_by_recipe_id(db: AsyncSession, receta_id: int) -> list[Ingrediente]:
    """Valida la existencia de la receta y extrae la lista de sus ingredientes activos."""
    await get_receta_or_404(db, receta_id)
    return await crud_ingrediente.get_ingredientes_by_receta(db, receta_id)

async def update_single_ingredient(
    db: AsyncSession, ingrediente_id: int, ing_in: IngredienteUpdate, current_user: Usuario
) -> Ingrediente:
    """Modifica un ingrediente específico directo por su clave primaria, comprobando la autoría."""
    # Buscar el ingrediente en base de datos
    result = await db.execute(
        select(Ingrediente).where(Ingrediente.id == ingrediente_id, Ingrediente.is_deleted == None)
    )
    db_ing = result.scalars().first()
    if not db_ing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El ingrediente especificado no existe.")
        
    # Validar permisos sobre la receta dueña
    receta = await get_receta_or_404(db, db_ing.id_receta)
    if receta.id_user != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para modificar este componente.")
        
    try:
        return await crud_ingrediente.update_ingrediente(db, db_obj=db_ing, obj_in=ing_in)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def update_recipe_ingredients_bulk(
    db: AsyncSession, receta_id: int, bulk_in: IngredienteBulkUpdate, current_user: Usuario
) -> list[Ingrediente]:
    """Actualiza o reemplaza la lista completa de ingredientes de una receta."""
    receta = await get_receta_or_404(db, receta_id)
    if receta.id_user != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción denegada por falta de permisos.")
        
    try:
        # Obtener los ingredientes actuales
        ingredientes_actuales = await crud_ingrediente.get_ingredientes_by_receta(db, receta_id)
        ids_actuales = {i.id for i in ingredientes_actuales}
        
        # Procesar entradas
        ids_a_mantener = set()
        
        for item in bulk_in.ingredientes:
            if item.id and item.id in ids_actuales:
                # Actualizar ingrediente existente
                result = await db.execute(select(Ingrediente).where(Ingrediente.id == item.id))
                db_obj = result.scalars().first()
                obj_update = IngredienteUpdate(ingrediente=item.ingrediente, cantidad=item.cantidad, unidad=item.unidad)
                await crud_ingrediente.update_ingrediente(db, db_obj=db_obj, obj_in=obj_update)
                ids_a_mantener.add(item.id)
            else:
                # Es un ingrediente nuevo, se inserta
                obj_create = IngredienteCreate(id_receta=receta_id, ingrediente=item.ingrediente, cantidad=item.cantidad, unidad=item.unidad)
                await crud_ingrediente.create_ingrediente(db, obj_in=obj_create)
                
        # Hacer soft-delete de los ingredientes viejos que no vinieron en la petición
        for viejo in ingredientes_actuales:
            if viejo.id not in ids_a_mantener:
                await crud_ingrediente.delete_ingrediente(db, db_obj=viejo)
                
        # Retornar el estado final del set de ingredientes
        return await crud_ingrediente.get_ingredientes_by_receta(db, receta_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))