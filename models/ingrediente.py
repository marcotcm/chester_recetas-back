from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.session import Base

class Ingrediente(Base):
    __tablename__ = "ingredientes"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    id_receta = Column(BigInteger, ForeignKey("public.recetas.id"), nullable=True)
    ingrediente = Column(String, nullable=True)
    cantidad = Column(BigInteger, nullable=True)
    unidad = Column(String, nullable=True)
    is_deleted = Column(DateTime, nullable=True)

    # Relaciones
    receta = relationship("Receta", back_populates="ingredientes", lazy="selectin")