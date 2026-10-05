"""Administracion de usuarios y de los modulos de cada rol (solo administrador)."""
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import requerir_rol
from app.api.v1.comun import no_encontrado
from app.core.auditoria import registrar
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Colegio, Modulo, ModuloPorRol, Organizador, Rol, Usuario
from app.schemas import ModulosIn, UsuarioEdita, UsuarioNuevo

router = APIRouter(prefix="/admin", tags=["admin-usuarios"])
Admin = Depends(requerir_rol("administrador"))


def _out(u: Usuario, organizacion: str | None, colegio: str | None) -> dict:
    return {"id": u.id, "correo": u.correo, "nombre": u.nombre, "apellido": u.apellido, "rol": u.rol.nombre,
            "activo": u.activo, "creado_en": u.creado_en, "perfil": organizacion or colegio}


def _una(db: Session, id_usuario: int) -> dict:
    fila = (db.query(Usuario, Organizador.nombre, Colegio.nombre)
            .outerjoin(Organizador, Organizador.id_usuario == Usuario.id).outerjoin(Colegio, Colegio.id_usuario == Usuario.id)
            .options(joinedload(Usuario.rol)).filter(Usuario.id == id_usuario).first())
    if fila is None:
        raise no_encontrado()
    return _out(*fila)


@router.get("/usuarios")
def listar(q: str | None = None, rol: str | None = None, estado: str | None = None, _: Usuario = Admin, db: Session = Depends(get_db)):
    consulta = (db.query(Usuario, Organizador.nombre, Colegio.nombre)
                .outerjoin(Organizador, Organizador.id_usuario == Usuario.id).outerjoin(Colegio, Colegio.id_usuario == Usuario.id)
                .options(joinedload(Usuario.rol)))
    if q:
        patron = f"%{q.strip()[:60]}%"
        consulta = consulta.filter(or_(Usuario.correo.ilike(patron), Usuario.nombre.ilike(patron), Usuario.apellido.ilike(patron)))
    if rol:
        consulta = consulta.join(Rol, Rol.id == Usuario.id_rol).filter(Rol.nombre == rol)
    if estado in ("activo", "inactivo"):
        consulta = consulta.filter(Usuario.activo.is_(estado == "activo"))
    return [_out(*f) for f in consulta.order_by(Usuario.creado_en.desc(), Usuario.id.desc()).limit(500)]


@router.post("/usuarios", status_code=201)
def crear(datos: UsuarioNuevo, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    """Crea un administrador u organizador ya activo. La contrasena temporal se muestra UNA vez."""
    if datos.rol == "organizador" and not (datos.organizacion_nombre and datos.nit):
        raise HTTPException(422, "Para un organizador indica el nombre de la organización y el NIT")
    temporal = secrets.token_urlsafe(9)
    rol = db.query(Rol).filter_by(nombre=datos.rol).one()
    try:
        u = Usuario(id_rol=rol.id, correo=datos.correo.lower(), contrasena=hash_password(temporal),
                    nombre=datos.nombre, apellido=datos.apellido, activo=True)
        db.add(u)
        db.flush()
        if datos.rol == "organizador":
            db.add(Organizador(id_usuario=u.id, nombre=datos.organizacion_nombre, nit=datos.nit, telefono=datos.telefono))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ese correo o NIT ya está registrado")
    registrar(db, request, admin.id, f"crear_usuario_{datos.rol}", "usuario", u.id)
    return {"usuario": _una(db, u.id), "contrasena_temporal": temporal}


@router.patch("/usuarios/{id_usuario}")
def editar(id_usuario: int, datos: UsuarioEdita, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    u = db.get(Usuario, id_usuario) or (_ for _ in ()).throw(no_encontrado())
    if u.id == admin.id and ((datos.rol and datos.rol != u.rol.nombre) or datos.activo is False):
        # Siempre queda al menos un administrador activo: el que hace el cambio.
        raise HTTPException(409, "No puedes cambiar tu propio rol ni desactivar tu propia cuenta")
    if datos.rol and datos.rol != u.rol.nombre:
        # administrador no necesita perfil; organizador y colegio solo si el usuario ya tiene ese perfil.
        perfil = {"organizador": Organizador, "colegio": Colegio}.get(datos.rol)
        if perfil is not None and not db.query(perfil).filter_by(id_usuario=u.id).first():
            raise HTTPException(409, f"Este usuario no tiene perfil de {datos.rol}; solo puede pasar a administrador")
        u.id_rol = db.query(Rol.id).filter_by(nombre=datos.rol).scalar()
    for campo in ("nombre", "apellido", "activo"):
        if getattr(datos, campo) is not None:
            setattr(u, campo, getattr(datos, campo))
    db.commit()
    registrar(db, request, admin.id, "editar_usuario", "usuario", u.id)
    return _una(db, u.id)


@router.post("/usuarios/{id_usuario}/restablecer")
def restablecer(id_usuario: int, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    u = db.get(Usuario, id_usuario) or (_ for _ in ()).throw(no_encontrado())
    if u.id == admin.id:
        raise HTTPException(409, "Cambia tu propia contraseña desde Mi cuenta")
    temporal = secrets.token_urlsafe(9)
    u.contrasena = hash_password(temporal)
    db.commit()
    registrar(db, request, admin.id, "restablecer_contrasena", "usuario", u.id)
    return {"contrasena_temporal": temporal}


@router.get("/roles")
def roles(_: Usuario = Admin, db: Session = Depends(get_db)):
    usuarios = dict(db.query(Usuario.id_rol, func.count(Usuario.id)).group_by(Usuario.id_rol).all())
    asignados: dict[int, list[int]] = {}
    for id_rol, id_modulo in db.query(ModuloPorRol.id_rol, ModuloPorRol.id_modulo):
        asignados.setdefault(id_rol, []).append(id_modulo)
    return {"roles": [{"id": r.id, "nombre": r.nombre, "descripcion": r.descripcion, "usuarios": usuarios.get(r.id, 0),
                       "modulos": sorted(asignados.get(r.id, [])), "bloqueado": r.nombre == "administrador"}
                      for r in db.query(Rol).order_by(Rol.id)],
            "modulos": [{"id": m.id, "nombre": m.nombre, "descripcion": m.descripcion} for m in db.query(Modulo).order_by(Modulo.id)]}


@router.put("/roles/{id_rol}/modulos")
def asignar_modulos(id_rol: int, datos: ModulosIn, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    rol = db.get(Rol, id_rol) or (_ for _ in ()).throw(no_encontrado())
    if rol.nombre == "administrador":
        raise HTTPException(409, "Los módulos del administrador no se pueden quitar (te quedarías sin acceso)")
    ids = set(datos.modulos)
    if db.query(func.count(Modulo.id)).filter(Modulo.id.in_(ids)).scalar() != len(ids):
        raise HTTPException(422, "Algún módulo no existe")
    db.query(ModuloPorRol).filter(ModuloPorRol.id_rol == rol.id).delete()
    db.add_all(ModuloPorRol(id_rol=rol.id, id_modulo=i) for i in ids)
    db.commit()
    registrar(db, request, admin.id, "asignar_modulos", "rol", rol.id)
    return {"id": rol.id, "modulos": sorted(ids)}
