import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from crud import mensaje as crud_mensaje
from schemas.mensaje import MensajeCreate
from fastapi import HTTPException, status
from models.user import Usuario, UserRole

async def submit_contact_form(db: AsyncSession, msg_in: MensajeCreate):
    """Procesa y almacena las peticiones del formulario de soporte y contacto público (Sin autenticación)."""
    # Validación básica preventiva para evitar payloads vacíos o abusos de spam
    if not msg_in.mensaje or len(msg_in.mensaje.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cuerpo del mensaje es demasiado corto."
        )
    try:
        return await crud_mensaje.create_mensaje(db, obj_in=msg_in)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def review_inbox(db: AsyncSession, current_user: Usuario):
    """Permite auditar los mensajes entrantes en el buzón. Acción restringida para Administradores."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso no autorizado.")
    return await crud_mensaje.get_mensajes(db)
