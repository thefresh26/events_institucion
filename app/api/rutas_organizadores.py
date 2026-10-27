from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import requerir_rol
from app.core.auditoria import ip_de
from app.models.colegio import Activo
from app.repositories.organizador_repo import OrganizadorRepository

router = APIRouter(prefix="/admin/organizadores", tags=["Organizadores (administrador)"])
repo = OrganizadorRepository()
Admin = Depends(requerir_rol("administrador"))


@router.get("")
def listar_organizadores(_=Admin):
    return repo.obtener_todos()


@router.patch("/{organizador_id}/activo")
def activar_organizador(organizador_id: int, datos: Activo, request: Request, admin=Admin):
    """Aprueba una cuenta nueva (activo=true) o la desactiva."""
    resultado = repo.activar(organizador_id, datos.activo, admin.id, ip_de(request))
    if not resultado:
        raise HTTPException(status_code=404, detail="No encontrado")
    return resultado
