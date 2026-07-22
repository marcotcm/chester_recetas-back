from sqlalchemy import Column, String, DateTime, BigInteger, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
import uuid
from db.session import Base

class UserRole(enum.IntEnum):
    usuario = 0
    admin = 1

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    nombre = Column(String, default='')
    email = Column(String, unique=True, default='', index=True)
    telefono = Column(String, nullable=True)
    ubicacion = Column(String, nullable=True)
    foto_perfil = Column(String, nullable=True)
    is_deleted = Column(DateTime, nullable=True)
    role = Column(SmallInteger, nullable=False, default=UserRole.usuario)
    
    # Nueva columna vinculada a auth.users de Supabase
    id_supabase = Column(UUID(as_uuid=True), unique=True, nullable=True)

    # Relaciones
    recetas = relationship("Receta", back_populates="usuario", lazy="selectin")
    favoritos = relationship("Favorito", back_populates="usuario", lazy="selectin")