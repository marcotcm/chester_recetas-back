import traceback
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from crud import user as crud_usuario
from schemas.user import UsuarioCreate, UsuarioUpdate, UserLogin
from fastapi import HTTPException, status
from models.user import Usuario, UserRole
from supabase import Client
from supabase_auth.errors import AuthApiError
from pydantic import EmailStr

async def register_usuario(db: AsyncSession, user_in: UsuarioCreate, supabase_admin: Client) -> Usuario:
    """
    Registra un usuario de forma atómica. 
    Primero valida la unicidad local, luego crea el usuario en Supabase Auth y, 
    si todo sale bien, persiste el perfil en PostgreSQL. 
    Aplica rollback en Supabase si falla la inserción en la base de datos local.
    """
    if await crud_usuario.get_usuario_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El correo electrónico ya está registrado."
        )
    
    try:
        auth_response = supabase_admin.auth.admin.create_user({
            "email": user_in.email,
            "password": user_in.password,
            "email_confirm": True
        })
        supabase_uuid_str = auth_response.user.id
        supabase_uuid = uuid.UUID(supabase_uuid_str)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el proveedor de autenticación: {str(e)}"
        )

    try:
        return await crud_usuario.create_usuario(db, obj_in=user_in, supabase_uuid=supabase_uuid)
    except Exception as e:
        traceback.print_exc()
        try:
            supabase_admin.auth.admin.delete_user(supabase_uuid_str)
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el perfil local. Registro revertido: {str(e)}"
        )

async def login_usuario(db: AsyncSession, credentials: UserLogin, supabase_client: Client) -> dict:
    """
    Autentica al usuario en Supabase. Si tiene éxito, valida su estado en la base de
    datos local. Si está eliminado lógicamente, deniega el acceso de inmediato.
    """
    try:
        # 1. Autenticar en Supabase utilizando el cliente estándar
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        # 2. Buscar el perfil local mapeado por el email
        usuario_local = await crud_usuario.get_usuario_by_email(db, credentials.email)
        
        if not usuario_local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuario autenticado en el proveedor pero no encontrado localmente (ha sido eliminado)."
            )
        
        # 3. Validación de borrado lógico
        if usuario_local.is_deleted is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta cuenta ha sido eliminada o desactivada del sistema."
            )
            
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer",
            "user": usuario_local
        }
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El correo electrónico o la contraseña son incorrectos."
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

async def refresh_session(db: AsyncSession, refresh_token: str, supabase_client: Client) -> dict:
    """Refresca una sesión activa utilizando el refresh_token provisto por Supabase."""
    try:
        # 1. Refrescar sesión en Supabase
        auth_response = supabase_client.auth.refresh_session(refresh_token)
        
        # 2. Obtener datos del usuario desde la nueva sesión generada
        email = auth_response.user.email
        usuario_local = await crud_usuario.get_usuario_by_email(db, email)
        
        if not usuario_local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Usuario no encontrado localmente."
            )
            
        if usuario_local.is_deleted is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Esta cuenta ha sido eliminada o desactivada del sistema."
            )
            
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer",
            "user": usuario_local
        }
    except AuthApiError:
        # Evita la traza en consola cuando el token enviado expira o es incorrecto
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de refresco provisto no es válido o ya ha sido utilizado."
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al procesar el refresco: {str(e)}"
        )

async def request_password_reset(email: EmailStr, supabase_client: Client):
    """Solicita a Supabase el envío de un correo seguro para restablecer la contraseña."""
    try:
        supabase_client.auth.reset_password_for_email(email)
        return {"detail": "Si el correo electrónico existe en el sistema, se ha enviado un enlace de recuperación."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar la solicitud de recuperación."
        )

async def get_usuario_or_404(db: AsyncSession, usuario_id: int) -> Usuario:
    """Obtiene un usuario por su ID interno. Lanza 404 si no existe o está eliminado."""
    usuario = await crud_usuario.get_usuario_by_id(db, usuario_id)
    if not usuario or usuario.is_deleted is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado o dado de baja.")
    return usuario

async def get_usuario_by_email_or_404(db: AsyncSession, email: str) -> Usuario:
    """Obtiene un usuario por su Email. Lanza 404 si no existe o está eliminado."""
    usuario = await crud_usuario.get_usuario_by_email(db, email)
    if not usuario or usuario.is_deleted is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado o dado de baja.")
    return usuario

async def search_usuarios_by_name(db: AsyncSession, query_name: str) -> list[Usuario]:
    """Busca y filtra usuarios cuyo nombre coincida parcialmente (Case-Insensitive)."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.nombre.ilike(f"%{query_name}%"),
            Usuario.is_deleted == None
        )
    )
    return list(result.scalars().all())

async def get_all_usuarios_active(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Usuario]:
    """Retorna la lista paginada de todos los usuarios que no han sido borrados lógicamente."""
    result = await db.execute(
        select(Usuario).where(Usuario.is_deleted == None).offset(skip).limit(limit)
    )
    return list(result.scalars().all())

async def update_profile(db: AsyncSession, usuario_id: int, user_in: UsuarioUpdate, current_user: Usuario) -> Usuario:
    """Actualiza los datos del perfil. Valida que el solicitante sea dueño de la cuenta o administrador."""
    if current_user.id != usuario_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para actualizar este perfil.")
    
    usuario_to_update = await get_usuario_or_404(db, usuario_id)
    
    if user_in.role is not None and current_user.role != UserRole.admin:
        user_in.role = None
        
    try:
        return await crud_usuario.update_usuario(db, db_obj=usuario_to_update, obj_in=user_in)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar: {str(e)}")

async def disable_usuario(db: AsyncSession, usuario_id: int, current_user: Usuario, supabase_admin: Client):
    """Aplica soft-delete local al perfil y elimina de forma definitiva el acceso en Supabase Auth."""
    if current_user.id != usuario_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos.")
        
    usuario = await get_usuario_or_404(db, usuario_id)
    try:
        await crud_usuario.delete_usuario(db, db_obj=usuario)
        if usuario.id_supabase:
            supabase_admin.auth.admin.delete_user(str(usuario.id_supabase))
        return {"detail": "Usuario eliminado y accesos revocados correctamente."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))