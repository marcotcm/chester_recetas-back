from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FavoritoBase(BaseModel):
    id_receta: Optional[int] = None
    id_user: Optional[int] = None

class FavoritoCreate(FavoritoBase):
    pass

class FavoritoUpdate(BaseModel):
    id_receta: Optional[int] = None
    id_user: Optional[int] = None

class FavoritoResponse(FavoritoBase):
    id: int
    created_at: datetime
    is_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True