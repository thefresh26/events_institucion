from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import colegio_actual
from app.db.session import get_db
from app.models import AutorizacionAcudiente, Colegio, Estudiante, Grado
from app.schemas import EstudianteNuevo

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
