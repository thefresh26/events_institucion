from fastapi import Request
from sqlalchemy.orm import Session

from app.models import Auditoria


def registrar(db: Session, request: Request, id_usuario: int | None, accion: str, tabla: str | None = None, registro_id: int | None = None):
    ip = request.client.host if request.client else None
    db.add(Auditoria(id_usuario=id_usuario, accion=accion, tabla=tabla, registro_id=registro_id, ip=ip))
    db.commit()
