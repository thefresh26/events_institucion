from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import requerir_rol
from app.api.v1.comun import evento_out, id_estado_evento, no_encontrado
from app.core.auditoria import registrar
from app.db.session import get_db
from app.models import Colegio, Evento, EstadoEvento, Inscripcion, Organizador, Usuario
from app.schemas import ActivoIn, DecisionEvento

router = APIRouter(prefix="/admin", tags=["admin"])
Admin = Depends(requerir_rol("administrador"))


@router.get("/resumen")
def resumen(_: Usuario = Admin, db: Session = Depends(get_db)):
    por_estado = dict(db.query(EstadoEvento.nombre, func.count(Evento.id)).outerjoin(Evento, Evento.id_estado == EstadoEvento.id)
                      .group_by(EstadoEvento.nombre).all())
    return {"eventos_por_estado": por_estado, "colegios": db.query(func.count(Colegio.id)).scalar(),
            "organizadores": db.query(func.count(Organizador.id)).scalar(),
            "organizadores_pendientes": db.query(func.count(Organizador.id)).join(Usuario).filter(Usuario.activo.is_(False)).scalar(),
            "inscripciones": db.query(func.count(Inscripcion.id)).scalar()}


@router.get("/organizadores")
def organizadores(_: Usuario = Admin, db: Session = Depends(get_db)):
    return [{"id": o.id, "nombre": o.nombre, "nit": o.nit, "correo": o.usuario.correo, "telefono": o.telefono,
             "activo": o.usuario.activo} for o in db.query(Organizador).order_by(Organizador.nombre)]


@router.patch("/organizadores/{id_organizador}/activo")
def activar_organizador(id_organizador: int, datos: ActivoIn, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    o = db.get(Organizador, id_organizador) or (_ for _ in ()).throw(no_encontrado())
    o.usuario.activo = datos.activo
    db.commit()
    registrar(db, request, admin.id, "activar_organizador" if datos.activo else "desactivar_organizador", "organizador", o.id)
    return {"id": o.id, "activo": o.usuario.activo}


@router.get("/colegios")
def colegios(_: Usuario = Admin, db: Session = Depends(get_db)):
    return [{"id": c.id, "nombre": c.nombre, "nit": c.nit, "ciudad": c.ciudad.nombre, "organizador": db.get(Organizador, c.id_organizador).nombre,
             "activo": c.usuario.activo} for c in db.query(Colegio).order_by(Colegio.nombre)]


@router.get("/eventos")
def eventos(estado: str | None = None, _: Usuario = Admin, db: Session = Depends(get_db)):
    q = db.query(Evento).order_by(Evento.fecha_inicio)
    if estado:
        q = q.join(EstadoEvento).filter(EstadoEvento.nombre == estado)
    return [evento_out(db, e) for e in q.limit(500)]


@router.patch("/eventos/{id_evento}/decision")
def decidir(id_evento: int, datos: DecisionEvento, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    e = db.get(Evento, id_evento) or (_ for _ in ()).throw(no_encontrado())
    if e.estado.nombre != "pendiente":
        raise HTTPException(409, "Solo se pueden decidir eventos pendientes")
    e.id_estado = id_estado_evento(db, datos.decision)
    e.id_aprobador, e.fecha_aprobacion = admin.id, datetime.now(timezone.utc)
    db.commit()
    registrar(db, request, admin.id, f"evento_{datos.decision}", "evento", e.id)
    db.refresh(e)
    return evento_out(db, e)


@router.post("/eventos/{id_evento}/cerrar")
def cerrar(id_evento: int, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    e = db.get(Evento, id_evento) or (_ for _ in ()).throw(no_encontrado())
    if e.estado.nombre != "publicado":
        raise HTTPException(409, "Solo se pueden cerrar eventos publicados")
    e.id_estado = id_estado_evento(db, "cerrado")
    db.commit()
    registrar(db, request, admin.id, "evento_cerrado", "evento", e.id)
    db.refresh(e)
    return evento_out(db, e)
