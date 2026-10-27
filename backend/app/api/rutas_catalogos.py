from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg2 import IntegrityError

from app.api.deps import requerir_rol
from app.core.auditoria import ip_de
from app.models.catalogo import CatalogoEdita, CatalogoNuevo, EstadoIn
from app.repositories.catalogo_repo import TABLAS, CatalogoRepository

repo = CatalogoRepository()

# Listas publicas que usan los formularios (ciudades, grados, categorias)
router = APIRouter(prefix="/catalogos", tags=["Catálogos"])
# CRUD de las 8 tablas de catalogo: solo administrador
router_admin = APIRouter(prefix="/admin/catalogos", tags=["Catálogos (CRUD admin)"])
Admin = Depends(requerir_rol("administrador"))


@router.get("/ciudades")
def listar_ciudades():
    return repo.listar_ciudades()


@router.get("/grados")
def listar_grados():
    return repo.listar_grados()


@router.get("/categorias")
def listar_categorias():
    return repo.listar_categorias()


def validar_tabla(tabla: str):
    if tabla not in TABLAS:
        raise HTTPException(status_code=404, detail=f"Tabla desconocida. Disponibles: {', '.join(TABLAS)}")


def validar_campos(tabla: str, datos: dict, completo: bool) -> dict:
    """Cada tabla acepta solo sus columnas (ej. grados no tiene descripcion)."""
    _, permitidos, obligatorios = TABLAS[tabla]
    extra = set(datos) - permitidos
    if extra:
        raise HTTPException(status_code=422, detail=f"Campos no permitidos: {', '.join(sorted(extra))}")
    faltan = obligatorios - set(datos) if completo else set()
    if faltan:
        raise HTTPException(status_code=422, detail=f"Falta el campo {', '.join(sorted(faltan))}")
    return datos


def no_encontrado():
    return HTTPException(status_code=404, detail="No encontrado")


DUPLICADO = HTTPException(status_code=409, detail="Ya existe un registro con ese valor único, o una referencia no es válida")


@router_admin.get("/{tabla}")
def listar(tabla: str, todos: bool = False, _=Admin):
    validar_tabla(tabla)
    return repo.obtener_todos(tabla, todos)


@router_admin.get("/{tabla}/{registro_id}")
def obtener(tabla: str, registro_id: int, _=Admin):
    validar_tabla(tabla)
    fila = repo.obtener_por_id(tabla, registro_id)
    if not fila:
        raise no_encontrado()
    return fila


@router_admin.post("/{tabla}", status_code=201)
def crear(tabla: str, datos: CatalogoNuevo, request: Request, admin=Admin):
    validar_tabla(tabla)
    limpio = validar_campos(tabla, datos.model_dump(exclude_unset=True), completo=True)
    try:
        return repo.crear(tabla, limpio, admin.id, ip_de(request))
    except IntegrityError:
        raise DUPLICADO


@router_admin.put("/{tabla}/{registro_id}")
def actualizar(tabla: str, registro_id: int, datos: CatalogoEdita, request: Request, admin=Admin):
    validar_tabla(tabla)
    limpio = validar_campos(tabla, datos.model_dump(exclude_unset=True), completo=False)
    if not limpio:  # nada que cambiar: se devuelve el registro tal cual
        return obtener(tabla, registro_id)
    try:
        fila = repo.actualizar(tabla, registro_id, limpio, admin.id, ip_de(request))
    except IntegrityError:
        raise DUPLICADO
    if not fila:
        raise no_encontrado()
    return fila


def poner_estado(tabla: str, registro_id: int, estado: bool, request: Request, admin):
    validar_tabla(tabla)
    if tabla == "roles" and not estado:
        rol = repo.obtener_por_id(tabla, registro_id)
        if rol and rol["nombre"] == "administrador":
            raise HTTPException(status_code=409, detail="El rol administrador no se puede eliminar")
    if estado:
        fila = repo.cambiar_estado(tabla, registro_id, True, admin.id, ip_de(request))
    else:
        fila = repo.eliminar(tabla, registro_id, admin.id, ip_de(request))  # borrado logico
    if not fila:
        raise no_encontrado()
    return fila


@router_admin.patch("/{tabla}/{registro_id}/estado")
def cambiar_estado(tabla: str, registro_id: int, datos: EstadoIn, request: Request, admin=Admin):
    """estado=true restaura un registro eliminado."""
    return poner_estado(tabla, registro_id, datos.estado, request, admin)


@router_admin.delete("/{tabla}/{registro_id}")
def eliminar(tabla: str, registro_id: int, request: Request, admin=Admin):
    """Borrado logico: estado = false. El registro NO se borra de la tabla."""
    return poner_estado(tabla, registro_id, False, request, admin)
