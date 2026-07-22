from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import EmailStr
from supabase import Client

from db.session import get_db
from core.security import get_current_user
from schemas.user import (
    UsuarioCreate, 
    UsuarioUpdate, 
    UsuarioResponse, 
    UserLogin, 
    TokenRefreshRequest, 
    TokenResponse, 
    ForgotPasswordRequest
)
from models.user import Usuario
from services import user as services_usuario
from db.supabaseR import get_supabase_admin

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    user_in: UsuarioCreate, 
    db: AsyncSession = Depends(get_db),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    * **Ruta:** POST /api/v1/usuarios/registro
    * **Token:** No requiere
    * **Nivel de permiso:** Público (Cualquier visitante)
    * **Uso:** Recibe el formulario de registro con la contraseña del nuevo usuario.
    * **Resultado:** Registra de forma segura las credenciales en Supabase Auth y crea el perfil en la base de datos local de PostgreSQL de manera atómica.
    """
    return await services_usuario.register_usuario(db=db, user_in=user_in, supabase_admin=supabase_admin)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
    supabase_client: Client = Depends(get_supabase_admin)
):
    """
    * **Ruta:** POST /api/v1/usuarios/login
    * **Token:** No requiere
    * **Nivel de permiso:** Público
    * **Uso:** Recibe las credenciales básicas (email y password) del usuario para iniciar sesión.
    * **Resultado:** Autentica contra Supabase Auth y, tras validar que no posea un borrado lógico local, retorna un par de tokens válidos (`access_token` y `refresh_token`) acoplados al perfil completo del usuario.
    """
    return await services_usuario.login_usuario(db=db, credentials=credentials, supabase_client=supabase_client)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    supabase_client: Client = Depends(get_supabase_admin)
):
    """
    * **Ruta:** POST /api/v1/usuarios/refresh
    * **Token:** No requiere (Se transfiere en el cuerpo JSON de la petición)
    * **Nivel de permiso:** Público
    * **Uso:** Envía el `refresh_token` provisto en el login una vez que el JWT de acceso haya expirado.
    * **Resultado:** Evalúa el estado en Supabase y la base de datos local, generando un juego de tokens renovados sin interrumpir la experiencia del usuario. Lanza error si la cuenta fue dada de baja.
    """
    return await services_usuario.refresh_session(db=db, refresh_token=payload.refresh_token, supabase_client=supabase_client)


@router.post("/recuperar-contrasena", status_code=status.HTTP_200_OK)
async def recuperar_contrasena(
    payload: ForgotPasswordRequest,
    supabase_client: Client = Depends(get_supabase_admin)
):
    """
    * **Ruta:** POST /api/v1/usuarios/recuperar-contrasena
    * **Token:** No requiere
    * **Nivel de permiso:** Público
    * **Uso:** Recibe el correo electrónico de la cuenta que solicita el restablecimiento.
    * **Resultado:** Solicita al proveedor Supabase Auth el disparo automatizado de un correo electrónico seguro con el link de redirección para actualizar la contraseña.
    """
    return await services_usuario.request_password_reset(email=payload.email, supabase_client=supabase_client)


@router.get("/", response_model=List[UsuarioResponse], status_code=status.HTTP_200_OK)
async def obtener_usuarios_activos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros a traer"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** GET /api/v1/usuarios/
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Trae la lista completa y paginada de todos los usuarios del sistema que NO tengan un soft-delete (`is_deleted`).
    * **Resultado:** Retorna un arreglo JSON con los perfiles públicos activos del sistema aplicando los parámetros opcionales de paginación (`skip` y `limit`).
    """
    return await services_usuario.get_all_usuarios_active(db=db, skip=skip, limit=limit)


@router.get("/me", response_model=UsuarioResponse)
async def obtener_mi_perfil(current_user: Usuario = Depends(get_current_user)):
    """
    * **Ruta:** GET /api/v1/usuarios/me
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Permite al cliente obtener los datos del perfil del usuario logueado en la sesión activa.
    * **Resultado:** Retorna la información privada del perfil que corresponde al token validado.
    """
    return current_user


@router.get("/buscar", response_model=List[UsuarioResponse])
async def buscar_usuarios(
    nombre: str = Query(..., min_length=3, description="Texto parcial del nombre a buscar"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** GET /api/v1/usuarios/buscar?nombre={valor_a_buscar}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Se añade el parámetro '?nombre=' al final de la ruta para filtrar usuarios del sistema.
    * **Resultado:** Retorna una lista con los usuarios activos cuyos nombres contengan la coincidencia parcial dada.
    """
    return await services_usuario.search_usuarios_by_name(db, nombre)


@router.get("/buscar-email", response_model=UsuarioResponse)
async def buscar_usuario_por_email(
    email: EmailStr = Query(..., description="Correo electrónico exacto a buscar"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** GET /api/v1/usuarios/buscar-email?email={correo_a_buscar}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Se añade el parámetro '?email=' al final de la ruta pasando la dirección de correo exacta.
    * **Resultado:** Devuelve los datos públicos del usuario que coincida exactamente con el email proporcionado. Lanza un error 404 si no se encuentra activo en el sistema.
    """
    return await services_usuario.get_usuario_by_email_or_404(db, email)


@router.get("/{id}", response_model=UsuarioResponse)
async def obtener_usuario_por_id(
    id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** GET /api/v1/usuarios/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Usuario Común o Administrador
    * **Uso:** Pasa el ID numérico directo en la URL (ej: /api/v1/usuarios/5) para inspeccionar una cuenta específica.
    * **Resultado:** Muestra el perfil del usuario solicitado. Responde con un error 404 si la cuenta no existe o fue eliminada lógicamente.
    """
    return await services_usuario.get_usuario_or_404(db, id)


@router.patch("/{id}", response_model=UsuarioResponse)
async def actualizar_perfil(
    id: int, 
    user_in: UsuarioUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    * **Ruta:** PATCH /api/v1/usuarios/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Propietario de la cuenta o Administrador
    * **Uso:** Pasa el ID en la URL y envía en el cuerpo JSON únicamente los campos del perfil que se desean modificar.
    * **Resultado:** Aplica los cambios en la base de datos local y retorna el perfil actualizado. Bloquea de forma preventiva que usuarios comunes cambien su propio rol a Admin.
    """
    return await services_usuario.update_profile(db, id, user_in, current_user)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def dar_de_baja_usuario(
    id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    * **Ruta:** DELETE /api/v1/usuarios/{id}
    * **Token:** Requiere (Bearer JWT)
    * **Nivel de permiso:** Propietario de la cuenta o Administrador
    * **Uso:** Pasa el ID en la URL para solicitar la eliminación de la cuenta.
    * **Resultado:** Ejecuta una baja lógica local registrando el timestamp en `is_deleted` y remueve de forma definitiva el registro en Supabase Auth.
    """
    return await services_usuario.disable_usuario(db, id, current_user, supabase_admin)