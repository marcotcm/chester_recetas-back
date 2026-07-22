from sqlalchemy import Column, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.session import Base

class Favorito(Base):
    __tablename__ = "favoritos"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    id_receta = Column(BigInteger, ForeignKey("public.recetas.id"), nullable=True)
    id_user = Column(BigInteger, ForeignKey("public.usuarios.id"), nullable=True)
    is_deleted = Column(DateTime, nullable=True)

    # Relaciones
    receta = relationship("Receta", back_populates="favoritos", lazy="selectin")
    usuario = relationship("Usuario", back_populates="favoritos", lazy="selectin")