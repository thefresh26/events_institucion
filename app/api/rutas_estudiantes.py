from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg.errors import IntegrityError

from app.api.deps import colegio_actual
from app.core.auditoria import ip_de
from app.models.estudiante import EstudianteNuevo
from app.repositories.estudiante_repo import EstudianteRepository

router = APIRouter(prefix="/colegio/estudiantes", tags=["Estudiantes (colegio)"])
repo = EstudianteRepository()


def enmascarar(estudiante: dict) -> dict:
    doc = estudiante["documento"]
    return {**estudiante, "documento": doc[:3] + "*" * (len(doc) - 5) + doc[-2:]}  # el documento nunca sale completo


@router.get("")
def listar_estudiantes(col=Depends(colegio_actual)):
    return [enmascarar(e) for e in repo.obtener_todos(col.id)]


@router.post("", status_code=201)
def crear_estudiante(estudiante: EstudianteNuevo, request: Request, col=Depends(colegio_actual)):
    if not repo.grado_valido(estudiante.id_grado):
        raise HTTPException(status_code=422, detail="Grado inválido")
    try:
        return enmascarar(repo.crear(col.id, estudiante, col.id_usuario, ip_de(request)))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya registraste un estudiante con ese documento")


@router.delete("/{estudiante_id}", status_code=204)
def eliminar_estudiante(estudiante_id: int, request: Request, col=Depends(colegio_actual)):
    """Borrado logico: se conserva el historial de eventos del estudiante."""
    if not repo.eliminar(estudiante_id, col.id, col.id_usuario, ip_de(request)):
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
