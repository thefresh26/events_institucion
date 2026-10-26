from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import colegio_actual
from app.api.v1.comun import evento_out, id_estado_inscripcion, inscritos, no_encontrado
from app.db.session import get_db
from app.models import Colegio, Estudiante, EstadoEvento, Evento, Inscripcion, InscripcionEstudiante
from app.schemas import InscripcionIn

router = APIRouter(prefix="/colegio", tags=["colegio"])


# ---------------- Eventos e inscripciones ----------------
@router.get("/eventos")
def eventos_disponibles(col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    """Solo eventos PUBLICADOS del organizador que registro a este colegio."""
    q = (db.query(Evento).join(EstadoEvento).filter(Evento.estado.is_(True), EstadoEvento.nombre == "publicado", Evento.id_organizador == col.id_organizador)
         .order_by(Evento.fecha_inicio))
    mias = {i.id_evento: i.estado_inscripcion.nombre for i in db.query(Inscripcion).filter_by(id_colegio=col.id)}
    return [{**evento_out(db, e), "mi_inscripcion": mias.get(e.id)} for e in q.limit(500)]


@router.post("/eventos/{id_evento}/inscripcion", status_code=201)
def inscribirse(id_evento: int, datos: InscripcionIn, col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    e = (db.query(Evento).join(EstadoEvento).filter(Evento.estado.is_(True), Evento.id == id_evento, Evento.id_organizador == col.id_organizador,
                                                     EstadoEvento.nombre == "publicado").first())
    if e is None:
        raise no_encontrado()
    if e.fecha_inicio <= datetime.now(timezone.utc).replace(tzinfo=e.fecha_inicio.tzinfo):
        raise HTTPException(409, "El evento ya comenzó")
    ids = set(datos.estudiantes)
    if len(ids) != len(datos.estudiantes):
        raise HTTPException(422, "Hay estudiantes repetidos")
    if len(ids) > e.cupo_estudiantes:
        raise HTTPException(422, f"Máximo {e.cupo_estudiantes} estudiantes por colegio")
    validos = db.query(Estudiante.id).filter(Estudiante.id.in_(ids), Estudiante.id_colegio == col.id, Estudiante.estado.is_(True)).count()
    if validos != len(ids):
        raise HTTPException(422, "Algún estudiante no pertenece a tu colegio")
    if db.query(Inscripcion).filter_by(id_evento=e.id, id_colegio=col.id).first():
        raise HTTPException(409, "Tu colegio ya está inscrito en este evento")
    # ponytail: no es atomico; con mucho trafico concurrente se podria exceder el cupo por 1-2. Mejora: bloqueo de fila (SELECT ... FOR UPDATE).
    if inscritos(db, e.id) >= e.cupo_colegios:
        raise HTTPException(409, "El evento no tiene cupos disponibles")
    i = Inscripcion(id_evento=e.id, id_colegio=col.id, id_estado=id_estado_inscripcion(db, "pendiente"))
    db.add(i)
    db.flush()
    db.add_all(InscripcionEstudiante(id_inscripcion=i.id, id_estudiante=x) for x in ids)
    db.commit()
    return {"id": i.id, "estado": "pendiente", "estudiantes": len(ids)}


@router.get("/inscripciones")
def mis_inscripciones(col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    q = db.query(Inscripcion).filter_by(id_colegio=col.id).order_by(Inscripcion.creado.desc())
    return [{"id": i.id, "evento": i.evento.nombre, "fecha_inicio": i.evento.fecha_inicio, "estado": i.estado_inscripcion.nombre,
             "estudiantes": [f"{x.estudiante.nombre} {x.estudiante.apellido}" for x in i.estudiantes]} for i in q.limit(500)]
