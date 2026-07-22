from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class IngredienteBase(BaseModel):
    id_receta: Optional[int] = None
    ingrediente: Optional[str] = None
    cantidad: Optional[int] = None
    unidad: Optional[str] = None

class IngredienteCreate(IngredienteBase):
    pass

class IngredienteUpdate(BaseModel):
    ingrediente: Optional[str] = None
    cantidad: Optional[int] = None
    unidad: Optional[str] = None

class IngredienteResponse(IngredienteBase):
    id: int
    created_at: datetime
    is_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==========================================
# Esquemas Nuevos para Edición en Lote
# ==========================================

class IngredienteBulkItem(BaseModel):
    """Estructura de un ingrediente individual para actualización masiva."""
    id: Optional[int] = None  # Si viene con ID, se edita. Si no, se crea uno nuevo.
    ingrediente: str
    cantidad: int
    unidad: str

class IngredienteBulkUpdate(BaseModel):
    """Contenedor de lista para reemplazar o actualizar los ingredientes de una receta."""
    ingredientes: List[IngredienteBulkItem]