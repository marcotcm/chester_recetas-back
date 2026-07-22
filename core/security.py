import jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from core.config import settings
from db.session import get_db
from crud.user import get_usuario_by_supabase_id
from models.user import UserRole, Usuario

security = HTTPBearer()

def verify_supabase_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    try:
        # Ajustado para procesar tokens ES256 de Supabase
        payload = jwt.decode(
            credentials.credentials, 
            options={"verify_signature": False},  # Cambiar a True en prod usando JWKS
            algorithms=["ES256"],
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="El token ha expirado."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token inválido o mal formado."
        )

async def get_current_user(
    token_payload: dict = Depends(verify_supabase_token),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    """
    Dependencia para obtener el usuario actual mapeado en nuestra base de datos
    a partir del UUID de Supabase Auth ('sub' en el JWT).
    """
    # El campo 'sub' en los tokens de Supabase contiene el UUID del usuario
    supabase_uuid_str = token_payload.get("sub")
    if not supabase_uuid_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token no contiene un identificador de usuario válido."
        )
    
    try:
        supabase_uuid = uuid.UUID(supabase_uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de ID de Supabase inválido."
        )
        
    usuario = await get_usuario_by_supabase_id(db, supabase_uuid=supabase_uuid)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no está registrado en la base de datos local."
        )
        
    return usuario


class RoleChecker:
    """
    Permite restringir endpoints según el rol numérico guardado en la base de datos local.
    Uso: Depends(RoleChecker([UserRole.admin]))
    """
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción."
            )
        return current_user