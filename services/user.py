import traceback
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from crud import user as crud_usuario
from schemas.user import UsuarioCreate, UsuarioUpdate
from fastapi import HTTPException, status
from models.user import Usuario, UserRole
from supabase import Client

async def register_usuario(db: AsyncSession, user_in: UsuarioCreate, supabase_admin: Client) -> Usuario:
    """
    Registra un usuario de forma atómica. 
    Primero valida la unicidad local, luego crea el usuario en Supabase Auth y, 
    si todo sale bien, persiste el perfil en PostgreSQL. 
    Aplica rollback en Supabase si falla la inserción en la base de datos local.
    """
    # 1. Validar si el correo ya existe en nuestra base de datos local
    if await crud_usuario.get_usuario_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El correo electrónico ya está registrado."
        )
    
    # 2. Intentar el registro en el módulo de Autenticación de Supabase
    try:
        auth_response = supabase_admin.auth.admin.create_user({
            "email": user_in.email,
            "password": user_in.password,
            "email_confirm": True
        })
        supabase_uuid_str = auth_response.user.id
        supabase_uuid = uuid.UUID(supabase_uuid_str)
    except Exception as e:
        traceback.print_exc()  # Imprime la traza exacta del fallo de Supabase en consola
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el proveedor de autenticación: {str(e)}"
        )

    # 3. Intentar persistir el perfil del usuario en la base de datos local
    try:
        return await crud_usuario.create_usuario(db, obj_in=user_in, supabase_uuid=supabase_uuid)
    except Exception as e:
        traceback.print_exc()  # Imprime el fallo de integridad o conexión local
        # OPERACIÓN DE ROLLBACK: Si la DB local falla, eliminamos la credencial en Supabase
        try:
            supabase_admin.auth.admin.delete_user(supabase_uuid_str)
        except:
            pass  # Evita que un fallo al borrar oculte el error principal de la DB
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el perfil local. Registro revertido: {str(e)}"
        )

async def get_usuario_or_404(db: AsyncSession, usuario_id: int) -> Usuario:
    """Obtiene un usuario por su ID interno. Lanza 404 si no existe o está eliminado."""
    usuario = await crud_usuario.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return usuario

async def get_usuario_by_email_or_404(db: AsyncSession, email: str) -> Usuario:
    """Obtiene un usuario por su Email corporativo/personal. Lanza 404 si no existe."""
    usuario = await crud_usuario.get_usuario_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
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
    return await crud_usuario.get_usuarios(db, skip=skip, limit=limit)

async def update_profile(db: AsyncSession, usuario_id: int, user_in: UsuarioUpdate, current_user: Usuario) -> Usuario:
    """Actualiza los datos del perfil. Valida que el solicitante sea dueño de la cuenta o administrador."""
    # Control de accesos de seguridad
    if current_user.id != usuario_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para actualizar este perfil.")
    
    usuario_to_update = await get_usuario_or_404(db, usuario_id)
    
    # Restricción de negocio: Un usuario estándar no puede escalarse el rol a Administrador
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
        # 1. Soft-delete local
        await crud_usuario.delete_usuario(db, db_obj=usuario)
        # 2. Revocación de credenciales en Supabase Auth
        if usuario.id_supabase:
            supabase_admin.auth.admin.delete_user(str(usuario.id_supabase))
        return {"detail": "Usuario eliminado y accesos revocados correctamente."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))