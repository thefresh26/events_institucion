import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg2 import IntegrityError

from app.api.deps import requerir_rol
from app.core.auditoria import ip_de
from app.core.security import hash_password
from app.models.catalogo import EstadoIn
from app.models.usuario import Modulos, UsuarioEdita, UsuarioNuevo
from app.repositories.usuario_repo import UsuarioRepository

router = APIRouter(prefix="/admin", tags=["Usuarios y roles (administrador)"])
repo = UsuarioRepository()
Admin = Depends(requerir_rol("administrador"))


def no_encontrado():
    return HTTPException(status_code=404, detail="No encontrado")


def usuario_vivo(usuario_id: int):
    usuario = repo.obtener_por_id(usuario_id)
    if not usuario:
        raise no_encontrado()
    return usuario


@router.get("/usuarios")
def listar_usuarios(q: str | None = None, rol: str | None = None, estado: str | None = None, _=Admin):
    return repo.obtener_todos(q, rol, estado)


@router.post("/usuarios", status_code=201)
def crear_usuario(datos: UsuarioNuevo, request: Request, admin=Admin):
    """Crea un administrador u organizador ya activo. La contraseña temporal se muestra UNA vez."""
    if datos.rol == "organizador" and not (datos.organizacion_nombre and datos.nit):
        raise HTTPException(status_code=422, detail="Para un organizador indica el nombre de la organización y el NIT")
    temporal = secrets.token_urlsafe(9)
    try:
        usuario = repo.crear(datos, hash_password(temporal), admin.id, ip_de(request))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ese correo o NIT ya está registrado")
    return {"usuario": usuario, "contrasena_temporal": temporal}


@router.patch("/usuarios/{usuario_id}")
def actualizar_usuario(usuario_id: int, datos: UsuarioEdita, request: Request, admin=Admin):
    usuario = usuario_vivo(usuario_id)
    cambia_rol = datos.rol and datos.rol != usuario["rol"]
    if usuario_id == admin.id and (cambia_rol or datos.activo is False):
        # Siempre queda al menos un administrador activo: el que hace el cambio.
        raise HTTPException(status_code=409, detail="No puedes cambiar tu propio rol ni desactivar tu propia cuenta")
    if cambia_rol and not repo.tiene_perfil(usuario_id, datos.rol):
        raise HTTPException(status_code=409, detail=f"Este usuario no tiene perfil de {datos.rol}; solo puede pasar a administrador")
    return repo.actualizar(usuario_id, datos.model_dump(exclude_unset=True), admin.id, ip_de(request))


@router.post("/usuarios/{usuario_id}/restablecer")
def restablecer_contrasena(usuario_id: int, request: Request, admin=Admin):
    usuario_vivo(usuario_id)
    if usuario_id == admin.id:
        raise HTTPException(status_code=409, detail="Cambia tu propia contraseña desde Mi cuenta")
    temporal = secrets.token_urlsafe(9)
    repo.cambiar_contrasena(usuario_id, hash_password(temporal), admin.id, ip_de(request))
    return {"contrasena_temporal": temporal}


@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, request: Request, admin=Admin):
    """Borrado logico: estado = false. La fila (y su historial) se conserva; el usuario ya no aparece ni puede entrar."""
    usuario_vivo(usuario_id)
    if usuario_id == admin.id:
        raise HTTPException(status_code=409, detail="No puedes eliminar tu propia cuenta")
    repo.cambiar_estado(usuario_id, False, admin.id, ip_de(request), "eliminar_usuario")
    return {"ok": True}


@router.patch("/usuarios/{usuario_id}/estado")
def cambiar_estado_usuario(usuario_id: int, datos: EstadoIn, request: Request, admin=Admin):
    """Maneja el campo estado: false = eliminar, true = restaurar un usuario eliminado."""
    if not repo.existe(usuario_id):
        raise no_encontrado()
    if usuario_id == admin.id and not datos.estado:
        raise HTTPException(status_code=409, detail="No puedes eliminar tu propia cuenta")
    return repo.cambiar_estado(usuario_id, datos.estado, admin.id, ip_de(request), "estado_usuario")


# ---------------- Roles y modulos ----------------
@router.get("/roles")
def listar_roles(_=Admin):
    return repo.obtener_roles()


@router.put("/roles/{rol_id}/modulos")
def asignar_modulos(rol_id: int, datos: Modulos, request: Request, admin=Admin):
    rol = repo.obtener_rol(rol_id)
    if not rol:
        raise no_encontrado()
    if rol["nombre"] == "administrador":
        raise HTTPException(status_code=409, detail="Los módulos del administrador no se pueden quitar (te quedarías sin acceso)")
    ids = sorted(set(datos.modulos))
    if repo.contar_modulos(ids) != len(ids):
        raise HTTPException(status_code=422, detail="Algún módulo no existe")
    repo.asignar_modulos(rol_id, ids, admin.id, ip_de(request))
    return {"id": rol_id, "modulos": ids}
