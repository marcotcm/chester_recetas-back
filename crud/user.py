from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from models.user import Usuario
from schemas.user import UsuarioCreate, UsuarioUpdate
from datetime import datetime, timezone

async def create_usuario(db: AsyncSession, obj_in: UsuarioCreate, supabase_uuid: uuid.UUID) -> Usuario:
    # 1. Convertimos el modelo Pydantic a diccionario
    user_data = obj_in.model_dump()
    
    # 2. Eliminamos 'password' para no causar conflictos con la tabla SQL
    user_data.pop("password", None)
    
    # 3. Asignamos el UUID al campo correspondiente
    user_data["id_supabase"] = supabase_uuid
    
    # 4. Instanciamos (el campo 'id' se autogenera en la DB por el IDENTITY)
    db_obj = Usuario(**user_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_usuario_by_id(db: AsyncSession, usuario_id: int) -> Usuario | None:
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id, Usuario.is_deleted == None)
    )
    return result.scalars().first()

async def get_usuario_by_supabase_id(db: AsyncSession, supabase_uuid: uuid.UUID) -> Usuario | None:
    result = await db.execute(
        select(Usuario).where(Usuario.id_supabase == supabase_uuid, Usuario.is_deleted == None)
    )
    return result.scalars().first()

async def get_usuario_by_email(db: AsyncSession, email: str) -> Usuario | None:
    result = await db.execute(
        select(Usuario).where(Usuario.email == email, Usuario.is_deleted == None)
    )
    return result.scalars().first()

async def get_usuarios(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Usuario]:
    result = await db.execute(
        select(Usuario).where(Usuario.is_deleted == None).offset(skip).limit(limit)
    )
    return list(result.scalars().all())

async def update_usuario(db: AsyncSession, db_obj: Usuario, obj_in: UsuarioUpdate) -> Usuario:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def delete_usuario(db: AsyncSession, db_obj: Usuario) -> Usuario:
    db_obj.is_deleted = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj