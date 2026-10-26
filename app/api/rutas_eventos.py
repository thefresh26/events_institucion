from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import colegio_actual, organizador_actual, requerir_rol
from app.core.auditoria import ip_de
from app.models.evento import DecisionEvento, Evento
from app.repositories.evento_repo import EventoRepository

repo = EventoRepository()

router = APIRouter(prefix="/organizador/eventos", tags=["Eventos (organizador)"])
router_colegio = APIRouter(prefix="/colegio/eventos", tags=["Eventos (colegio)"])
router_admin = APIRouter(prefix="/admin/eventos", tags=["Eventos (administrador)"])
Admin = Depends(requerir_rol("administrador"))
EDITABLES = ("borrador", "rechazado")


def no_encontrado():
    return HTTPException(status_code=404, detail="No encontrado")  # 404 y no 403: no revela si el evento existe


def evento_del_organizador(evento_id: int, org):
    evento = repo.obtener_por_id(evento_id, org.id)
    if not evento:
        raise no_encontrado()
    return evento


def validar_referencias(evento: Evento):
    if not repo.referencias_validas(evento.id_categoria, evento.id_ciudad):
        raise HTTPException(status_code=422, detail="Categoría o ciudad inválida")


# ---------------- Organizador ----------------
@router.get("")
def listar_eventos(org=Depends(organizador_actual)):
    return repo.obtener_todos(id_organizador=org.id)


@router.post("", status_code=201)
def crear_evento(evento: Evento, request: Request, org=Depends(organizador_actual)):
    validar_referencias(evento)
    return repo.crear(org.id, evento, org.id_usuario, ip_de(request))


@router.put("/{evento_id}")
def actualizar_evento(evento_id: int, evento: Evento, request: Request, org=Depends(organizador_actual)):
    if evento_del_organizador(evento_id, org)["estado"] not in EDITABLES:
        raise HTTPException(status_code=409, detail="Solo se pueden editar eventos en borrador o rechazados")
    validar_referencias(evento)
    return repo.actualizar(evento_id, evento, org.id_usuario, ip_de(request))


@router.delete("/{evento_id}", status_code=204)
def eliminar_evento(evento_id: int, request: Request, org=Depends(organizador_actual)):
    """Borrado logico (estado = false). Solo eventos en borrador o rechazados."""
    if evento_del_organizador(evento_id, org)["estado"] not in EDITABLES:
        raise HTTPException(status_code=409, detail="Solo se pueden eliminar eventos en borrador o rechazados")
    repo.eliminar(evento_id, org.id_usuario, ip_de(request))


@router.post("/{evento_id}/enviar")
def enviar_a_aprobacion(evento_id: int, request: Request, org=Depends(organizador_actual)):
    if evento_del_organizador(evento_id, org)["estado"] != "borrador":
        raise HTTPException(status_code=409, detail="Solo se pueden enviar eventos en borrador")
    return repo.cambiar_estado_evento(evento_id, "pendiente", org.id_usuario, "enviar_evento", ip_de(request))


# ---------------- Colegio ----------------
@router_colegio.get("")
def eventos_disponibles(col=Depends(colegio_actual)):
    """Solo eventos PUBLICADOS del organizador que registro a este colegio."""
    return repo.obtener_disponibles(col.id, col.id_organizador)


# ---------------- Administrador ----------------
@router_admin.get("")
def listar_todos(estado: str | None = None, _=Admin):
    return repo.obtener_todos(estado_evento=estado)


def evento_en_estado(evento_id: int, estado: str, mensaje: str):
    evento = repo.obtener_por_id(evento_id)
    if not evento:
        raise no_encontrado()
    if evento["estado"] != estado:
        raise HTTPException(status_code=409, detail=mensaje)


@router_admin.patch("/{evento_id}/decision")
def decidir_evento(evento_id: int, datos: DecisionEvento, request: Request, admin=Admin):
    evento_en_estado(evento_id, "pendiente", "Solo se pueden decidir eventos pendientes")
    return repo.cambiar_estado_evento(evento_id, datos.decision, admin.id, f"evento_{datos.decision}", ip_de(request), aprobador=True)


@router_admin.post("/{evento_id}/cerrar")
def cerrar_evento(evento_id: int, request: Request, admin=Admin):
    evento_en_estado(evento_id, "publicado", "Solo se pueden cerrar eventos publicados")
    return repo.cambiar_estado_evento(evento_id, "cerrado", admin.id, "evento_cerrado", ip_de(request))
