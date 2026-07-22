from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class MensajeBase(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    correo: Optional[EmailStr] = None
    motivo: Optional[str] = None
    mensaje: Optional[str] = None

class MensajeCreate(MensajeBase):
    pass

class MensajeUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    correo: Optional[EmailStr] = None
    motivo: Optional[str] = None
    mensaje: Optional[str] = None

class MensajeResponse(MensajeBase):
    id: int
    created_at: datetime
    is_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True