from sqlalchemy import Column, DateTime, BigInteger, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.session import Base

class ComentarioReceta(Base):
    __tablename__ = "comentarios_recetas"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    id_receta = Column(BigInteger, ForeignKey("public.recetas.id"), nullable=True)
    comentario = Column(String(255), nullable=True)
    rating = Column(BigInteger, nullable=True)
    is_deleted = Column(DateTime, nullable=True)

    # Relaciones
    receta = relationship("Receta", back_populates="comentarios", lazy="selectin")