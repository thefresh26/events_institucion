from types import SimpleNamespace

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.repositories.auth_repo import AuthRepository

repo = AuthRepository()
# auto_error=False: el token puede llegar por cabecera "Authorization: Bearer <jwt>" (Swagger, Postman, otras APIs) o por cookie (el frontend).
bearer = HTTPBearer(auto_error=False, description="Pega el access_token que devuelve POST /auth/login")
NO_AUTH = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudo validar la sesión")


def get_current_usuario(request: Request, cred: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """Valida el JWT (firma y expiracion). Viaja en la cabecera Bearer o en una cookie HttpOnly.
    Devuelve el usuario con atributos (usuario.id, usuario.rol, ...)."""
    token = cred.credentials if cred else request.cookies.get("token")
    if not token:
        raise NO_AUTH
    try:
        id_usuario = int(decode_access_token(token)["sub"])
    except Exception:  # firma invalida, token vencido o mal formado
        raise NO_AUTH
    usuario = repo.obtener_sesion(id_usuario)  # None si fue eliminado o desactivado despues de entrar
    if usuario is None:
        raise NO_AUTH
    return SimpleNamespace(**usuario)


def requerir_rol(*roles: str):
    """Autorizacion en el SERVIDOR: el rol sale de la base de datos, nunca del cliente."""
    def dependencia(usuario=Depends(get_current_usuario)):
        if usuario.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")
        return usuario
    return dependencia


def organizador_actual(u=Depends(requerir_rol("organizador"))):
    """El perfil de organizador del usuario que inicio sesion (org.id, org.id_usuario)."""
    org = repo.obtener_organizador(u.id)
    if org is None:
        raise NO_AUTH
    return SimpleNamespace(**org)


def colegio_actual(u=Depends(requerir_rol("colegio"))):
    """El perfil de colegio del usuario que inicio sesion (col.id, col.id_usuario, col.id_organizador)."""
    col = repo.obtener_colegio(u.id)
    if col is None:
        raise NO_AUTH
    return SimpleNamespace(**col)
