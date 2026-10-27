from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import requerir_rol
from app.db.session import get_db
from app.models import Colegio, Evento, EstadoEvento, Inscripcion, Organizador, Usuario

router = APIRouter(prefix="/admin", tags=["admin"])
Admin = Depends(requerir_rol("administrador"))


@router.get("/resumen")
def resumen(_: Usuario = Admin, db: Session = Depends(get_db)):
    por_estado = dict(db.query(EstadoEvento.nombre, func.count(Evento.id)).outerjoin(Evento, Evento.id_estado == EstadoEvento.id)
                      .group_by(EstadoEvento.nombre).all())
    return {"eventos_por_estado": por_estado, "colegios": db.query(func.count(Colegio.id)).filter(Colegio.estado.is_(True)).scalar(),
            "organizadores": db.query(func.count(Organizador.id)).filter(Organizador.estado.is_(True)).scalar(),
            "organizadores_pendientes": db.query(func.count(Organizador.id)).join(Usuario).filter(Usuario.activo.is_(False)).scalar(),
            "inscripciones": db.query(func.count(Inscripcion.id)).scalar()}
