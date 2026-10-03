from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import colegio_actual
from app.api.v1.comun import evento_out, id_estado_inscripcion, inscritos, no_encontrado
from app.db.session import get_db
from app.models import AutorizacionAcudiente, Colegio, Estudiante, EstadoEvento, Evento, Grado, Inscripcion, InscripcionEstudiante
from app.schemas import EstudianteNuevo, InscripcionIn

router = APIRouter(prefix="/colegio", tags=["colegio"])


def _est_out(e: Estudiante) -> dict:
    doc = e.documento
    return {"id": e.id, "nombre": e.nombre, "apellido": e.apellido, "grado": e.grado.nombre,
            "documento": doc[:3] + "*" * (len(doc) - 5) + doc[-2:]}  # documento enmascarado


@router.get("/estudiantes")
def listar(col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    q = db.query(Estudiante).filter_by(id_colegio=col.id, activo=True).order_by(Estudiante.apellido, Estudiante.nombre)
    return [_est_out(e) for e in q.limit(1000)]


@router.post("/estudiantes", status_code=201)
def registrar(datos: EstudianteNuevo, col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    if db.get(Grado, datos.id_grado) is None:
        raise HTTPException(422, "Grado inválido")
    try:
        e = Estudiante(id_colegio=col.id, id_grado=datos.id_grado, nombre=datos.nombre, apellido=datos.apellido,
                       documento=datos.documento)
        db.add(e)
        db.flush()
        db.add(AutorizacionAcudiente(id_estudiante=e.id, nombre_acudiente=datos.nombre_acudiente))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya registraste un estudiante con ese documento")
    return _est_out(e)


@router.delete("/estudiantes/{id_estudiante}", status_code=204)
def retirar(id_estudiante: int, col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    # Filtra por id_colegio: un colegio no puede tocar estudiantes de otro (evita IDOR).
    e = db.query(Estudiante).filter_by(id=id_estudiante, id_colegio=col.id).first()
    if e is None:
        raise HTTPException(404, "Estudiante no encontrado")
    e.activo = False  # baja logica: se conserva el historial de eventos
    db.commit()


# ---------------- Eventos e inscripciones ----------------
@router.get("/eventos")
def eventos_disponibles(col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    """Solo eventos PUBLICADOS del organizador que registro a este colegio."""
    q = (db.query(Evento).join(EstadoEvento).filter(EstadoEvento.nombre == "publicado", Evento.id_organizador == col.id_organizador)
         .order_by(Evento.fecha_inicio))
    mias = {i.id_evento: i.estado.nombre for i in db.query(Inscripcion).filter_by(id_colegio=col.id)}
    return [{**evento_out(db, e), "mi_inscripcion": mias.get(e.id)} for e in q.limit(500)]


@router.post("/eventos/{id_evento}/inscripcion", status_code=201)
def inscribirse(id_evento: int, datos: InscripcionIn, col: Colegio = Depends(colegio_actual), db: Session = Depends(get_db)):
    e = (db.query(Evento).join(EstadoEvento).filter(Evento.id == id_evento, Evento.id_organizador == col.id_organizador,
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
    validos = db.query(Estudiante.id).filter(Estudiante.id.in_(ids), Estudiante.id_colegio == col.id, Estudiante.activo.is_(True)).count()
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
    q = db.query(Inscripcion).filter_by(id_colegio=col.id).order_by(Inscripcion.creada_en.desc())
    return [{"id": i.id, "evento": i.evento.nombre, "fecha_inicio": i.evento.fecha_inicio, "estado": i.estado.nombre,
             "estudiantes": [f"{x.estudiante.nombre} {x.estudiante.apellido}" for x in i.estudiantes]} for i in q.limit(500)]
