from fastapi import APIRouter
from api.v1.endpoints import user, receta, categoria, favorito,comentario_receta



api_router = APIRouter()
api_router.include_router(user.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(receta.router, prefix="/recetas", tags=["Recetas"])
api_router.include_router(categoria.router, prefix="/categorias", tags=["Categorías"])
api_router.include_router(favorito.router, prefix="/favoritos", tags=["Favoritos"])
api_router.include_router(comentario_receta.router, prefix="/comentarios", tags=["Comentarios de Recetas"])