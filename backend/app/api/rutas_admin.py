from fastapi import APIRouter, Depends

from app.api.deps import requerir_rol
from app.repositories.admin_repo import AdminRepository

router = APIRouter(prefix="/admin", tags=["Administrador"])
repo = AdminRepository()


@router.get("/resumen")
def resumen(_=Depends(requerir_rol("administrador"))):
    """Numeros del panel: eventos por estado, colegios, organizadores (y pendientes) e inscripciones."""
    return repo.resumen()
