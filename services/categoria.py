import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.categoria import Categoria
from crud import categoria as crud_categoria
from schemas.categoria import CategoriaCreate, CategoriaUpdate
from fastapi import HTTPException, status
from models.user import Usuario, UserRole

async def create_new_categoria(db: AsyncSession, cat_in: CategoriaCreate, current_user: Usuario):
    """Crea una nueva clasificación de recetas. Exclusivo para cuentas Admin."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso exclusivo para administradores.")
    try:
        return await crud_categoria.create_categoria(db, obj_in=cat_in)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def search_categorias_by_name(db: AsyncSession, query_name: str) -> list[Categoria]:
    """Filtra y extrae las categorías del sistema por término textual de nombre."""
    result = await db.execute(
        select(Categoria).where(
            Categoria.nombre.ilike(f"%{query_name}%"),
            Categoria.is_deleted == None
        )
    )
    return list(result.scalars().all())

async def list_categorias(db: AsyncSession):
    """Retorna el catálogo global de categorías activas para los dropdowns del frontend."""
    return await crud_categoria.get_categorias(db)

async def remove_categoria(db: AsyncSession, categoria_id: int, current_user: Usuario):
    """Aplica baja lógica a una categoría del sistema (Restringido a administradores)."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
        
    cat = await crud_categoria.get_categoria_by_id(db, categoria_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada.")
        
    try:
        await crud_categoria.delete_categoria(db, db_obj=cat)
        return {"detail": "Categoría eliminada."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))