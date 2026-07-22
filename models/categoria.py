from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.session import Base

class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    nombre = Column(String, default='')
    descripcion = Column(String, nullable=True)
    is_deleted = Column(DateTime, nullable=True)

    # Relaciones
    recetas = relationship("Receta", back_populates="categoria", lazy="selectin")