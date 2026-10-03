import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import organizador_actual
from app.core.auditoria import registrar
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Ciudad, Colegio, Organizador, Rol, Usuario
from app.schemas import ActivoIn, ColegioNuevo

router = APIRouter(prefix="/organizador", tags=["organizador"])


def _colegio_out(c: Colegio) -> dict:
    return {"id": c.id, "nombre": c.nombre, "nit": c.nit, "ciudad": c.ciudad.nombre, "correo": c.usuario.correo,
            "contacto": f"{c.usuario.nombre} {c.usuario.apellido}", "telefono": c.telefono, "activo": c.usuario.activo}


@router.post("/colegios", status_code=201)
def registrar_colegio(datos: ColegioNuevo, request: Request, org: Organizador = Depends(organizador_actual),
                      db: Session = Depends(get_db)):
    """El organizador registra al colegio. El servidor genera una contrasena temporal que se muestra UNA vez."""
    if db.get(Ciudad, datos.id_ciudad) is None:
        raise HTTPException(422, "Ciudad inválida")
    temporal = secrets.token_urlsafe(9)
    try:
        rol = db.query(Rol).filter_by(nombre="colegio").one()
        u = Usuario(id_rol=rol.id, correo=datos.correo.lower(), contrasena=hash_password(temporal),
                    nombre=datos.nombre, apellido=datos.apellido, activo=True)
        db.add(u)
        db.flush()
        col = Colegio(id_usuario=u.id, id_ciudad=datos.id_ciudad, id_organizador=org.id, nombre=datos.colegio_nombre,
                      nit=datos.nit, direccion=datos.direccion, telefono=datos.telefono)
        db.add(col)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ese correo o NIT ya está registrado")
    registrar(db, request, org.id_usuario, "registrar_colegio", "colegio", col.id)
    return {"colegio": _colegio_out(col), "contrasena_temporal": temporal,
            "aviso": "Entrega esta contraseña al colegio; no se volverá a mostrar y debe cambiarla al entrar."}


@router.get("/colegios")
def listar_colegios(org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    # Solo los colegios que ESTE organizador registro (evita ver datos de otros organizadores).
    return [_colegio_out(c) for c in db.query(Colegio).filter_by(id_organizador=org.id).order_by(Colegio.nombre)]


@router.patch("/colegios/{id_colegio}/activo")
def activar_colegio(id_colegio: int, datos: ActivoIn, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    c = db.query(Colegio).filter_by(id=id_colegio, id_organizador=org.id).first()
    if c is None:
        raise HTTPException(404, "Colegio no encontrado")  # 404 y no 403: no revela si existe
    c.usuario.activo = datos.activo
    db.commit()
    return _colegio_out(c)
