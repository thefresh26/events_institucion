from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_usuario
from app.core import rate_limit
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Colegio, Organizador, Rol, Usuario
from app.schemas import CambioContrasena, LoginIn, RegistroOrganizador

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash de relleno: si el correo no existe igual se hace una verificacion, para que el tiempo de
# respuesta no delate si un correo esta registrado.
_FALSO = hash_password("relleno-de-tiempo-1")
PENDIENTE = "Registro recibido. Un administrador debe aprobar tu cuenta antes de que puedas entrar."


def _crear_usuario(db: Session, datos, nombre_rol: str) -> Usuario:
    rol = db.query(Rol).filter(Rol.nombre == nombre_rol).one()
    # activo=False: la cuenta queda pendiente hasta que el administrador la apruebe.
    u = Usuario(id_rol=rol.id, correo=datos.correo.lower(), contrasena=hash_password(datos.contrasena),
                nombre=datos.nombre, apellido=datos.apellido, activo=False)
    db.add(u)
    db.flush()
    return u


@router.post("/registro/organizador", status_code=201)
def registro_organizador(datos: RegistroOrganizador, db: Session = Depends(get_db)):
    try:
        u = _crear_usuario(db, datos, "organizador")
        db.add(Organizador(id_usuario=u.id, nombre=datos.organizacion_nombre, nit=datos.nit,
                           telefono=datos.telefono, descripcion=datos.descripcion))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ese correo o NIT ya está registrado")
    return {"mensaje": PENDIENTE}


def _perfil(db: Session, u: Usuario) -> dict:
    col = db.query(Colegio).filter_by(id_usuario=u.id).first()
    org = db.query(Organizador).filter_by(id_usuario=u.id).first()
    return {"id": u.id, "correo": u.correo, "nombre": u.nombre, "apellido": u.apellido, "rol": u.rol.nombre,
            "modulos": sorted(m.nombre for m in u.rol.modulos),
            "id_colegio": col.id if col else None, "id_organizador": org.id if org else None}


@router.post("/login")
def login(datos: LoginIn, response: Response, db: Session = Depends(get_db)):
    correo = datos.correo.lower()
    espera = rate_limit.segundos_de_bloqueo(correo)
    if espera:
        raise HTTPException(429, f"Demasiados intentos. Intenta de nuevo en {espera // 60 + 1} minutos")
    u = db.query(Usuario).filter(Usuario.correo == correo).first()
    ok = verify_password(datos.contrasena, u.contrasena if u else _FALSO)
    if not u or not ok:
        rate_limit.registrar_fallo(correo)
        raise HTTPException(401, "Correo o contraseña incorrectos")
    if not u.activo:
        raise HTTPException(403, "Tu cuenta está pendiente de aprobación o fue desactivada")
    rate_limit.limpiar(correo)
    response.set_cookie("token", create_access_token({"sub": str(u.id)}), httponly=True,
                        secure=settings.cookie_secure, samesite="lax",
                        max_age=settings.access_token_expire_minutes * 60, path="/")
    return _perfil(db, u)


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie("token", path="/")


@router.get("/me")
def me(u: Usuario = Depends(get_current_usuario), db: Session = Depends(get_db)):
    return _perfil(db, u)


@router.post("/cambiar-contrasena", status_code=204)
def cambiar_contrasena(datos: CambioContrasena, u: Usuario = Depends(get_current_usuario), db: Session = Depends(get_db)):
    if not verify_password(datos.actual, u.contrasena):
        raise HTTPException(400, "La contraseña actual no es correcta")
    u.contrasena = hash_password(datos.nueva)
    db.commit()
