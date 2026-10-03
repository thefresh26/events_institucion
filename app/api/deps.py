from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Rol, Usuario

NO_AUTH = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudo validar la sesión")


def get_current_usuario(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """La sesion viaja en una cookie HttpOnly (el JavaScript de la pagina no puede leerla)."""
    token = request.cookies.get("token")
    if not token:
        raise NO_AUTH
    try:
        id_usuario = int(decode_access_token(token)["sub"])
    except Exception:
        raise NO_AUTH
    # Una sola consulta trae usuario + rol + modulos (antes eran 3 viajes a Neon).
    usuario = db.query(Usuario).options(joinedload(Usuario.rol).joinedload(Rol.modulos)).filter(Usuario.id == id_usuario).first()
    if usuario is None or not usuario.activo:
        raise NO_AUTH
    return usuario


def requerir_rol(*roles: str):
    """Autorizacion en el SERVIDOR: el rol sale de la base de datos, nunca del cliente."""
    def dependencia(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
        if usuario.rol.nombre not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")
        return usuario
    return dependencia


def organizador_actual(u: Usuario = Depends(requerir_rol("organizador")), db: Session = Depends(get_db)):
    from app.models import Organizador
    return db.query(Organizador).filter_by(id_usuario=u.id).one()


def colegio_actual(u: Usuario = Depends(requerir_rol("colegio")), db: Session = Depends(get_db)):
    from app.models import Colegio
    return db.query(Colegio).filter_by(id_usuario=u.id).one()
