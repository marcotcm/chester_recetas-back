from pydantic import BaseModel
from typing import Optional
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