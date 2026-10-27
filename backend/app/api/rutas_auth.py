from fastapi import APIRouter, Depends, HTTPException, Request, Response
from psycopg2 import IntegrityError

from app.api.deps import get_current_usuario
from app.core import rate_limit
from app.core.auditoria import ip_de
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.auth import CambioContrasena, Login, RegistroOrganizador
from app.repositories.auth_repo import AuthRepository

router = APIRouter(prefix="/auth", tags=["Autenticación"])
repo = AuthRepository()

# Hash de relleno: si el correo no existe igual se hace una verificacion, para que el tiempo de
# respuesta no delate si un correo esta registrado.
_FALSO = hash_password("relleno-de-tiempo-1")
PENDIENTE = "Registro recibido. Un administrador debe aprobar tu cuenta antes de que puedas entrar."


@router.post("/registro/organizador", status_code=201)
def registro_organizador(datos: RegistroOrganizador):
    try:
        repo.registrar_organizador(datos, hash_password(datos.contrasena))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ese correo o NIT ya está registrado")
    return {"mensaje": PENDIENTE}


@router.post("/login")
def login(datos: Login, response: Response):
    correo = datos.correo.lower()
    espera = rate_limit.segundos_de_bloqueo(correo)
    if espera:
        raise HTTPException(status_code=429, detail=f"Demasiados intentos. Intenta de nuevo en {espera // 60 + 1} minutos")
    usuario = repo.obtener_por_correo(correo)
    ok = verify_password(datos.contrasena, usuario["contrasena"] if usuario else _FALSO)
    if not usuario or not ok:
        rate_limit.registrar_fallo(correo)
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    if not usuario["activo"]:
        raise HTTPException(status_code=403, detail="Tu cuenta está pendiente de aprobación o fue desactivada")
    rate_limit.limpiar(correo)
    token = create_access_token({"sub": str(usuario["id"]), "rol": usuario["rol"]})  # sub = id de usuario, rol = para la API auxiliar
    response.set_cookie("token", token, httponly=True, secure=settings.cookie_secure, samesite="lax",
                        max_age=settings.access_token_expire_minutes * 60, path="/")
    return {**repo.obtener_perfil(usuario["id"]), "access_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie("token", path="/")


@router.get("/me")
def me(usuario=Depends(get_current_usuario)):
    return repo.obtener_perfil(usuario.id)


@router.post("/cambiar-contrasena", status_code=204)
def cambiar_contrasena(datos: CambioContrasena, request: Request, usuario=Depends(get_current_usuario)):
    if not verify_password(datos.actual, repo.obtener_contrasena(usuario.id)):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    repo.cambiar_contrasena(usuario.id, hash_password(datos.nueva), ip_de(request))
