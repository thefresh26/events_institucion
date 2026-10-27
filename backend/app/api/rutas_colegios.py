import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg2 import IntegrityError

from app.api.deps import organizador_actual, requerir_rol
from app.core.auditoria import ip_de
from app.core.security import hash_password
from app.models.colegio import Activo, ColegioNuevo
from app.repositories.colegio_repo import ColegioRepository

repo = ColegioRepository()
router = APIRouter(prefix="/organizador/colegios", tags=["Colegios (organizador)"])
router_admin = APIRouter(prefix="/admin/colegios", tags=["Colegios (administrador)"])


def colegio_del_organizador(colegio_id: int, org):
    colegio = repo.obtener_por_id(colegio_id, org.id)
    if not colegio:
        raise HTTPException(status_code=404, detail="Colegio no encontrado")  # 404 y no 403: no revela si existe
    return colegio


@router.post("", status_code=201)
def crear_colegio(datos: ColegioNuevo, request: Request, org=Depends(organizador_actual)):
    """El organizador registra al colegio. El servidor genera una contraseña temporal que se muestra UNA vez."""
    if not repo.ciudad_valida(datos.id_ciudad):
        raise HTTPException(status_code=422, detail="Ciudad inválida")
    temporal = secrets.token_urlsafe(9)
    try:
        colegio = repo.crear(datos, hash_password(temporal), org.id, org.id_usuario, ip_de(request))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ese correo o NIT ya está registrado")
    return {"colegio": colegio, "contrasena_temporal": temporal,
            "aviso": "Entrega esta contraseña al colegio; no se volverá a mostrar y debe cambiarla al entrar."}


@router.get("")
def listar_colegios(org=Depends(organizador_actual)):
    return repo.obtener_todos(org.id)


@router.patch("/{colegio_id}/activo")
def activar_colegio(colegio_id: int, datos: Activo, request: Request, org=Depends(organizador_actual)):
    colegio_del_organizador(colegio_id, org)
    repo.activar(colegio_id, datos.activo, org.id_usuario, ip_de(request))
    return colegio_del_organizador(colegio_id, org)


@router.delete("/{colegio_id}", status_code=204)
def eliminar_colegio(colegio_id: int, request: Request, org=Depends(organizador_actual)):
    """Borrado logico: el colegio y su usuario quedan con estado=false. Se conserva el historial."""
    colegio_del_organizador(colegio_id, org)
    repo.eliminar(colegio_id, org.id_usuario, ip_de(request))


# ---------------- Administrador ----------------
@router_admin.get("")
def listar_todos(_=Depends(requerir_rol("administrador"))):
    return repo.obtener_todos_admin()
