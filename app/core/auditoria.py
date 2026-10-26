from fastapi import Request
from sqlalchemy.orm import Session

from app.models import Auditoria


def registrar(db: Session, request: Request, id_usuario: int | None, accion: str, tabla: str | None = None, registro_id: int | None = None):
    ip = request.client.host if request.client else None
    db.add(Auditoria(id_usuario=id_usuario, accion=accion, tabla=tabla, registro_id=registro_id, ip=ip))
    db.commit()


def ip_de(request: Request) -> str | None:
    return request.client.host if request.client else None


def auditar(cursor, id_usuario: int | None, accion: str, tabla: str, registro_id: int, ip: str | None):
    """Version SQL puro (repositorios). Usa el cursor del cambio: misma transaccion, o se guardan los dos o ninguno."""
    cursor.execute("INSERT INTO auditoria (id_usuario, accion, tabla, registro_id, ip) VALUES (%s, %s, %s, %s, %s);",
                   (id_usuario, accion, tabla, registro_id, ip))
