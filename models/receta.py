from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.session import Base

class Receta(Base):
    __tablename__ = "recetas"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    nombre = Column(String, nullable=True)
    descripcion = Column(String, nullable=False)
    info_nutri = Column(JSON, nullable=True)
    instrucciones = Column(JSON, nullable=True)
    consejos = Column(JSON, nullable=False)  
    
    id_user = Column(BigInteger, ForeignKey("public.usuarios.id"), nullable=True)
    id_categoria = Column(BigInteger, ForeignKey("public.categorias.id"), nullable=True)
    is_deleted = Column(DateTime, nullable=True)
    foto= Column(String, nullable=True)

    # Relaciones
    usuario = relationship("Usuario", back_populates="recetas", lazy="selectin")
    categoria = relationship("Categoria", back_populates="recetas", lazy="selectin")
    ingredientes = relationship("Ingrediente", back_populates="receta", cascade="all, delete-orphan", lazy="selectin")
    favoritos = relationship("Favorito", back_populates="receta", cascade="all, delete-orphan", lazy="selectin")
    comentarios = relationship("ComentarioReceta", back_populates="receta", cascade="all, delete-orphan", lazy="selectin")
