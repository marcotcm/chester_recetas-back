from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid
from models.user import UserRole

class UsuarioBase(BaseModel):
    nombre: Optional[str] = ""
    email: Optional[EmailStr] = ""
    telefono: Optional[str] = None
    ubicacion: Optional[str] = None
    foto_perfil: Optional[str] = None
    role: UserRole = UserRole.usuario

class UsuarioCreate(UsuarioBase):
    password: str  # Para el Auth Service externo de Supabase

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    ubicacion: Optional[str] = None
    foto_perfil: Optional[str] = None
    role: Optional[UserRole] = None
    # id_supabase normalmente no cambia tras el registro, pero lo dejamos por consistencia
    id_supabase: Optional[uuid.UUID] = None 

class UsuarioResponse(UsuarioBase):
    id: int
    id_supabase: Optional[uuid.UUID] = None
    created_at: datetime
    is_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True