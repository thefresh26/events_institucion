"""CRUD de las tablas de catalogo (rol, modulo, departamento, ciudad, grado, categoria y los dos estados).
Solo administrador. DELETE = baja logica (estado=False); PATCH .../estado lo cambia a mano (True restaura)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import requerir_rol
from app.api.v1.comun import no_encontrado
from app.core.auditoria import registrar
from app.db.session import get_db
from app.models import CategoriaEvento, Ciudad, Departamento, EstadoEvento, EstadoInscripcion, Grado, Modulo, Rol, Usuario
from app.schemas import EstadoIn

router = APIRouter(prefix="/admin/catalogos", tags=["catalogos-crud"])
Admin = Depends(requerir_rol("administrador"))

# tabla -> (modelo, {campo editable: (tipo, obligatorio)})
TABLAS = {
    "roles": (Rol, {"nombre": (str, True), "descripcion": (str, False)}),
    "modulos": (Modulo, {"nombre": (str, True), "descripcion": (str, False)}),
    "departamentos": (Departamento, {"nombre": (str, True)}),
    "ciudades": (Ciudad, {"id_departamento": (int, True), "nombre": (str, True)}),
    "grados": (Grado, {"nombre": (str, True)}),
    "categorias": (CategoriaEvento, {"nombre": (str, True), "descripcion": (str, False)}),
    "estados-evento": (EstadoEvento, {"nombre": (str, True)}),
    "estados-inscripcion": (EstadoInscripcion, {"nombre": (str, True)}),
}


def _tabla(nombre: str):
    if nombre not in TABLAS:
        raise HTTPException(404, f"Tabla desconocida. Disponibles: {', '.join(TABLAS)}")
    return TABLAS[nombre]


def _validar(campos: dict, datos: dict, completo: bool) -> dict:
    extra = set(datos) - set(campos)
    if extra:
        raise HTTPException(422, f"Campos no permitidos: {', '.join(sorted(extra))}")
    limpio = {}
    for k, (tipo, obligatorio) in campos.items():
        if k not in datos:
            if completo and obligatorio:
                raise HTTPException(422, f"Falta el campo {k}")
            continue
        v = datos[k]
        if tipo is str:
            if not isinstance(v, str) or (obligatorio and not v.strip()) or len(v) > 255:
                raise HTTPException(422, f"{k} inválido")
            v = v.strip() or None
        elif not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise HTTPException(422, f"{k} inválido")
        limpio[k] = v
    return limpio


def _out(f) -> dict:
    return {c.name: getattr(f, c.name) for c in f.__table__.columns}


def _guardar(db: Session, f):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe un registro con ese valor único, o una referencia no es válida")
    db.refresh(f)
    return _out(f)


def _fila(db: Session, modelo, id_: int):
    return db.get(modelo, id_) or (_ for _ in ()).throw(no_encontrado())


@router.get("/{tabla}")
def listar(tabla: str, todos: bool = False, _: Usuario = Admin, db: Session = Depends(get_db)):
    """Por defecto solo los registros con estado=True; con ?todos=true tambien los eliminados."""
    modelo, _c = _tabla(tabla)
    q = db.query(modelo)
    if not todos:
        q = q.filter(modelo.estado.is_(True))
    return [_out(f) for f in q.order_by(modelo.id).limit(2000)]


@router.get("/{tabla}/{id_}")
def uno(tabla: str, id_: int, _: Usuario = Admin, db: Session = Depends(get_db)):
    return _out(_fila(db, _tabla(tabla)[0], id_))


@router.post("/{tabla}", status_code=201)
def crear(tabla: str, request: Request, datos: dict = Body(...), admin: Usuario = Admin, db: Session = Depends(get_db)):
    modelo, campos = _tabla(tabla)
    f = modelo(**_validar(campos, datos, completo=True))
    db.add(f)
    salida = _guardar(db, f)
    registrar(db, request, admin.id, f"crear_{tabla}", modelo.__tablename__, f.id)
    return salida


@router.put("/{tabla}/{id_}")
def editar(tabla: str, id_: int, request: Request, datos: dict = Body(...), admin: Usuario = Admin, db: Session = Depends(get_db)):
    modelo, campos = _tabla(tabla)
    f = _fila(db, modelo, id_)
    for k, v in _validar(campos, datos, completo=False).items():
        setattr(f, k, v)
    salida = _guardar(db, f)
    registrar(db, request, admin.id, f"editar_{tabla}", modelo.__tablename__, f.id)
    return salida


def _poner_estado(db: Session, request: Request, admin: Usuario, tabla: str, id_: int, estado: bool):
    modelo, _c = _tabla(tabla)
    f = _fila(db, modelo, id_)
    if modelo is Rol and f.nombre == "administrador" and not estado:
        raise HTTPException(409, "El rol administrador no se puede eliminar")
    f.estado = estado
    salida = _guardar(db, f)
    registrar(db, request, admin.id, f"estado_{tabla}", modelo.__tablename__, f.id)
    return salida


@router.patch("/{tabla}/{id_}/estado")
def cambiar_estado(tabla: str, id_: int, datos: EstadoIn, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    return _poner_estado(db, request, admin, tabla, id_, datos.estado)


@router.delete("/{tabla}/{id_}")
def eliminar(tabla: str, id_: int, request: Request, admin: Usuario = Admin, db: Session = Depends(get_db)):
    """Baja logica: estado=False. El registro NO se borra de la tabla."""
    return _poner_estado(db, request, admin, tabla, id_, False)
