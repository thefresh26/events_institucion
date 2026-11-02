from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg2 import IntegrityError

from app.api.deps import colegio_actual
from app.core.auditoria import ip_de
from app.models.estudiante import EstudianteEdita, EstudianteNuevo
from app.repositories.estudiante_repo import EstudianteRepository

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes (colegio)"])
repo = EstudianteRepository()


@router.get("")
def listar_estudiantes(col=Depends(colegio_actual)):
    return repo.obtener_todos(col.id)


@router.post("", status_code=201)
def crear_estudiante(estudiante: EstudianteNuevo, request: Request, col=Depends(colegio_actual)):
    if not repo.grado_valido(estudiante.id_grado):
        raise HTTPException(status_code=422, detail="Grado inválido")
    try:
        return repo.crear(col.id, estudiante, col.id_usuario, ip_de(request))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya registraste un estudiante con ese nombre, apellido y grado")


NO_ENCONTRADO = HTTPException(status_code=404, detail="Estudiante no encontrado")  # 404 y no 403: no revela si existe en otro colegio


@router.get("/{estudiante_id}")
def obtener_estudiante(estudiante_id: int, col=Depends(colegio_actual)):
    estudiante = repo.obtener_por_id(estudiante_id, col.id)
    if not estudiante:
        raise NO_ENCONTRADO
    return estudiante


@router.put("/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, estudiante: EstudianteEdita, request: Request, col=Depends(colegio_actual)):
    if not repo.grado_valido(estudiante.id_grado):
        raise HTTPException(status_code=422, detail="Grado inválido")
    try:
        actualizado = repo.actualizar(estudiante_id, col.id, estudiante, col.id_usuario, ip_de(request))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya registraste un estudiante con ese nombre, apellido y grado")
    if not actualizado:
        raise NO_ENCONTRADO
    return actualizado


@router.delete("/{estudiante_id}", status_code=204)
def eliminar_estudiante(estudiante_id: int, request: Request, col=Depends(colegio_actual)):
    """Borrado logico: se conserva el historial de eventos del estudiante."""
    if not repo.eliminar(estudiante_id, col.id, col.id_usuario, ip_de(request)):
        raise NO_ENCONTRADO
