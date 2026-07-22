import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.exc import SQLAlchemyError

from models.user import Usuario
from models.receta import Receta
from models.categoria import Categoria
from models.ingrediente import Ingrediente
from models.favorito import Favorito
from models.comentario_receta import ComentarioReceta
from models.mensaje import Mensaje

from api.v1.api import api_router
from core.config import settings

# 1. Configuración de Logging del Sistema
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("chester_recetas_backend")

# 2. Inicialización de la Aplicación FastAPI
app = FastAPI(
    title="Chester Recetas API",
    description="Backend de alto rendimiento para la gestión de recetas, ingredientes, categorías e interacciones de usuarios.",
    version="1.0.0",
    docs_url="/docs",      # URL para la documentación interactiva Swagger
    redoc_url="/redoc"     # URL para ReDoc
)

# 3. Configuración de Middleware CORS (Esencial para conectar con React/Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar por tus dominios específicos en producción si es necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Manejadores Globales de Excepciones Profesionales

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Manejador especializado para capturar errores asíncronos de Base de Datos."""
    logger.error(f"Fallo crítico en Base de Datos: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "DatabaseError",
            "message": "El servicio de almacenamiento no está disponible temporalmente."
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de fallos imprevistos para no exponer trazas en producción."""
    logger.error(f"Error interno no controlado en {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "Ha ocurrido un error inesperado en el servidor."
        }
    )

# 5. Inclusión del Enrutador Principal unificado
app.include_router(api_router, prefix="/api/v1")

# 6. Endpoint de Monitoreo / Control de Salud
@app.get("/", tags=["Monitoreo"], status_code=status.HTTP_200_OK)
async def health_check():
    """
    **Health Check**
    Verifica que la instancia del servidor web de recetas responda correctamente y esté en línea.
    """
    return {
        "status": "online",
        "message": "API Chester Recetas operativa",
        "version": app.version
    }

# 7. Personalización de OpenAPI para Soporte Completo de Tokens Bearer en Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Añadir el esquema de seguridad Bearer Token a nivel global en la documentación interactiva
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Ingresa tu token JWT generado por Supabase Auth."
        }
    }
    
    # Aplicar la seguridad visual a los endpoints
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "responses" in operation:
                operation["security"] = [{"BearerAuth": []}]
                
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi