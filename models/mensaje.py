from sqlalchemy import Column, String, DateTime, BigInteger
from datetime import datetime, timezone
from db.session import Base

class Mensaje(Base):
    __tablename__ = "mensajes"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    nombre = Column(String, nullable=True)
    apellido = Column(String, nullable=True)
    correo = Column(String, nullable=True)
    motivo = Column(String, nullable=True)
    mensaje = Column(String, nullable=True)
    is_deleted = Column(DateTime, nullable=True)