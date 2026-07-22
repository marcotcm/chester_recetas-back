from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.session import get_db
from core.security import RoleChecker
from schemas.categoria import CategoriaCreate, CategoriaResponse
from models.user import Usuario, UserRole
from services import categoria as services_categoria

router = APIRouter()

@router.get("/", response_model=List[CategoriaResponse])
async def listar_todas_las_categorias(db: AsyncSession = Depends(get_db)):
    """
    * **Ruta:** GET /api/v1/categorias
    * **Token:** No requiere
    * **Nivel de permiso:** Público (Cualquier visitante)
    * **Uso:** Permite a la aplicación móvil o web consultar la lista de agrupaciones de cocina válidas.
    * **Resultado:** Retorna el catálogo completo de categorías activas para poblar selectores y listados en el frontend.
    """
    return await services_categoria.list_categorias(db)

@router.post("/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
async def crear_categoria(
    cat_in: CategoriaCreate, 
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(RoleChecker([UserRole.admin])) 
):
    """
    * **Ruta:** POST /api/v1/categorias
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Exclusivo Administrador (role: 1)
    * **Uso:** Envía el nombre y descripción para dar de alta una nueva agrupación (ej: "Saludable", "Bebidas").
    * **Resultado:** Inserta la nueva categoría en la base de datos. Si el usuario no tiene rol administrativo, responde con un error 403.
    """
    return await services_categoria.create_new_categoria(db, cat_in, admin_user)

@router.delete("/{id}")
async def eliminar_categoria(
    id: int, 
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(RoleChecker([UserRole.admin]))
):
    """
    * **Ruta:** DELETE /api/v1/categorias/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Exclusivo Administrador (role: 1)
    * **Uso:** `DELETE /categorias/3` para remover una clasificación del catálogo general.
    * **Resultado:** Ejecuta una desactivación lógica (Soft Delete) del registro maestro, protegiendo la integridad de recetas pasadas.
    """
    return await services_categoria.remove_categoria(db, id, admin_user)