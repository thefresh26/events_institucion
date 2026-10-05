import csv
import io
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import organizador_actual
from app.api.v1.comun import csv_seguro, evento_out, id_estado_evento, id_estado_inscripcion, inscritos, no_encontrado
from app.core.auditoria import registrar
from app.core.security import hash_password
from app.db.session import get_db
from app.models import (AutorizacionAcudiente, Auditoria, CategoriaEvento, Ciudad, Colegio, Estudiante, Evento, Inscripcion, InscripcionEstudiante, Organizador, Rol,
                        Usuario)
from app.schemas import ActivoIn, AsistenciaIn, ColegioNuevo, DecisionInscripcion, EventoIn

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


@router.delete("/colegios/{id_colegio}", status_code=204)
def eliminar_colegio(id_colegio: int, request: Request, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    """Borra el colegio y sus estudiantes. Solo si nunca se inscribio a un evento (si no, usar Desactivar: conserva el historial)."""
    c = db.query(Colegio).filter_by(id=id_colegio, id_organizador=org.id).first()
    if c is None:
        raise HTTPException(404, "Colegio no encontrado")
    if db.query(Inscripcion).filter_by(id_colegio=c.id).first():
        raise HTTPException(409, "El colegio tiene inscripciones en eventos; desactívalo en lugar de eliminarlo")
    ids = [i for (i,) in db.query(Estudiante.id).filter_by(id_colegio=c.id)]
    if ids:
        db.query(AutorizacionAcudiente).filter(AutorizacionAcudiente.id_estudiante.in_(ids)).delete(synchronize_session=False)
        db.query(Estudiante).filter(Estudiante.id.in_(ids)).delete(synchronize_session=False)
    id_usuario = c.id_usuario
    db.query(Auditoria).filter_by(id_usuario=id_usuario).update({"id_usuario": None})
    registrar(db, request, org.id_usuario, "eliminar_colegio", "colegio", c.id)
    db.delete(c)
    db.flush()
    db.delete(db.get(Usuario, id_usuario))
    db.commit()


# ---------------- Eventos ----------------
def _mio(db: Session, org: Organizador, id_evento: int) -> Evento:
    e = db.query(Evento).filter_by(id=id_evento, id_organizador=org.id).first()
    if e is None:
        raise no_encontrado()
    return e


def _validar_refs(db: Session, d: EventoIn):
    if db.get(CategoriaEvento, d.id_categoria) is None or db.get(Ciudad, d.id_ciudad) is None:
        raise HTTPException(422, "Categoría o ciudad inválida")


@router.post("/eventos", status_code=201)
def crear_evento(datos: EventoIn, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    _validar_refs(db, datos)
    e = Evento(id_organizador=org.id, id_estado=id_estado_evento(db, "borrador"), **datos.model_dump())
    db.add(e)
    db.commit()
    return evento_out(db, e)


@router.get("/eventos")
def mis_eventos(org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    return [evento_out(db, e) for e in db.query(Evento).filter_by(id_organizador=org.id).order_by(Evento.fecha_inicio.desc()).limit(500)]


@router.put("/eventos/{id_evento}")
def editar_evento(id_evento: int, datos: EventoIn, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    e = _mio(db, org, id_evento)
    if e.estado.nombre not in ("borrador", "rechazado"):
        raise HTTPException(409, "Solo se pueden editar eventos en borrador o rechazados")
    _validar_refs(db, datos)
    for k, v in datos.model_dump().items():
        setattr(e, k, v)
    e.id_estado = id_estado_evento(db, "borrador")  # editado: vuelve a borrador
    db.commit()
    db.refresh(e)
    return evento_out(db, e)


@router.post("/eventos/{id_evento}/enviar")
def enviar_a_aprobacion(id_evento: int, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    e = _mio(db, org, id_evento)
    if e.estado.nombre != "borrador":
        raise HTTPException(409, "Solo se pueden enviar eventos en borrador")
    e.id_estado = id_estado_evento(db, "pendiente")
    db.commit()
    db.refresh(e)
    return evento_out(db, e)


# ---------------- Inscripciones ----------------
@router.get("/inscripciones")
def inscripciones(org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    q = db.query(Inscripcion).join(Evento).filter(Evento.id_organizador == org.id).order_by(Inscripcion.creada_en.desc())
    return [{"id": i.id, "evento": i.evento.nombre, "id_evento": i.id_evento, "colegio": i.colegio.nombre,
             "estudiantes": len(i.estudiantes), "estado": i.estado.nombre, "creada_en": i.creada_en} for i in q.limit(1000)]


@router.patch("/inscripciones/{id_inscripcion}")
def decidir_inscripcion(id_inscripcion: int, datos: DecisionInscripcion, request: Request,
                        org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    i = db.query(Inscripcion).join(Evento).filter(Inscripcion.id == id_inscripcion, Evento.id_organizador == org.id).first()
    if i is None:
        raise no_encontrado()
    if i.estado.nombre != "pendiente":
        raise HTTPException(409, "Esta inscripción ya fue decidida")
    if datos.estado == "aceptada" and inscritos(db, i.id_evento, solo_aceptadas=True) >= i.evento.cupo_colegios:
        raise HTTPException(409, "El evento ya no tiene cupos de colegios")
    i.id_estado = id_estado_inscripcion(db, datos.estado)
    db.commit()
    registrar(db, request, org.id_usuario, f"inscripcion_{datos.estado}", "inscripcion", i.id)
    return {"id": i.id, "estado": datos.estado}


# ---------------- Asistencia ----------------
@router.get("/eventos/{id_evento}/asistencia")
def ver_asistencia(id_evento: int, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    _mio(db, org, id_evento)
    out = []
    for i in db.query(Inscripcion).filter_by(id_evento=id_evento).all():
        if i.estado.nombre == "aceptada":
            out.append({"id_inscripcion": i.id, "colegio": i.colegio.nombre,
                        "estudiantes": [{"id_inscripcion_estudiante": x.id, "nombre": f"{x.estudiante.nombre} {x.estudiante.apellido}",
                                         "grado": x.estudiante.grado.nombre, "asistio": x.asistio} for x in i.estudiantes]})
    return out


@router.put("/eventos/{id_evento}/asistencia", status_code=204)
def guardar_asistencia(id_evento: int, datos: AsistenciaIn, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    _mio(db, org, id_evento)
    for m in datos.marcas:
        # El filtro por evento impide marcar asistencia de inscripciones de otros eventos.
        fila = (db.query(InscripcionEstudiante).join(Inscripcion)
                .filter(InscripcionEstudiante.id == m.id_inscripcion_estudiante, Inscripcion.id_evento == id_evento).first())
        if fila is None:
            raise HTTPException(422, "Marca de asistencia inválida")
        fila.asistio = m.asistio
    db.commit()


# ---------------- Reportes (CSV) ----------------
def _csv(nombre: str, filas: list[list]) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf)
    for f in filas:
        w.writerow([csv_seguro(c) for c in f])
    return Response("\ufeff" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


@router.get("/eventos/{id_evento}/reporte/colegios.csv")
def reporte_colegios(id_evento: int, request: Request, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    e = _mio(db, org, id_evento)
    filas = [["Evento", "Colegio", "NIT", "Estado", "Estudiantes"]]
    for i in db.query(Inscripcion).filter_by(id_evento=e.id).all():
        filas.append([e.nombre, i.colegio.nombre, i.colegio.nit, i.estado.nombre, len(i.estudiantes)])
    registrar(db, request, org.id_usuario, "descargar_reporte_colegios", "evento", e.id)
    return _csv(f"colegios_evento_{e.id}.csv", filas)


@router.get("/eventos/{id_evento}/reporte/estudiantes.csv")
def reporte_estudiantes(id_evento: int, request: Request, org: Organizador = Depends(organizador_actual), db: Session = Depends(get_db)):
    e = _mio(db, org, id_evento)
    filas = [["Evento", "Colegio", "Estudiante", "Grado", "Asistio"]]
    for i in db.query(Inscripcion).filter_by(id_evento=e.id).all():
        if i.estado.nombre == "aceptada":
            for x in i.estudiantes:  # sin documento: dato minimo necesario para el organizador
                filas.append([e.nombre, i.colegio.nombre, f"{x.estudiante.nombre} {x.estudiante.apellido}", x.estudiante.grado.nombre,
                              "Si" if x.asistio else "No"])
    registrar(db, request, org.id_usuario, "descargar_reporte_estudiantes", "evento", e.id)  # datos de menores: queda auditado
    return _csv(f"estudiantes_evento_{e.id}.csv", filas)
