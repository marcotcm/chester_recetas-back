from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid
from models.user import UserRole

# ==========================================
# Esquemas Base y Perfil de Usuario
# ==========================================

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
    id_supabase: Optional[uuid.UUID] = None 

class UsuarioResponse(UsuarioBase):
    id: int
    id_supabase: Optional[uuid.UUID] = None
    created_at: datetime
    is_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==========================================
# Esquemas Nuevos para Autenticación y Flujos
# ==========================================

class UserLogin(BaseModel):
    """Esquema para recibir las credenciales de inicio de sesión."""
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    """Esquema para solicitar un nuevo access token usando el refresh token."""
    refresh_token: str

class TokenResponse(BaseModel):
    """Esquema de respuesta estándar para tokens junto con el perfil local."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UsuarioResponse

class ForgotPasswordRequest(BaseModel):
    """Esquema para solicitar el enlace de restauración al correo electrónico."""
    email: EmailStr