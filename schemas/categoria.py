from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoriaBase(BaseModel):
    nombre: Optional[str] = ""
    descripcion: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class CategoriaResponse(CategoriaBase):
    id: int
    created_at: datetime
    is_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True