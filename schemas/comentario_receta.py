from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ComentarioRecetaBase(BaseModel):
    id_receta: Optional[int] = None
    comentario: Optional[str] = None
    rating: Optional[int] = None

class ComentarioRecetaCreate(ComentarioRecetaBase):
    pass

class ComentarioRecetaUpdate(BaseModel):
    comentario: Optional[str] = None
    rating: Optional[int] = None

class ComentarioRecetaResponse(ComentarioRecetaBase):
    id: int
    created_at: datetime
    is_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True