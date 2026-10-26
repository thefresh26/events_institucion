import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from psycopg.errors import IntegrityError

from app.api.deps import colegio_actual, organizador_actual
from app.api.rutas_eventos import evento_del_organizador, no_encontrado
from app.core.auditoria import ip_de
from app.models.inscripcion import Asistencia, DecisionInscripcion, Inscripcion
from app.repositories.inscripcion_repo import InscripcionRepository

repo = InscripcionRepository()

router_colegio = APIRouter(prefix="/colegio", tags=["Inscripciones (colegio)"])
router = APIRouter(prefix="/organizador", tags=["Inscripciones (organizador)"])

YA_INSCRITO = HTTPException(status_code=409, detail="Tu colegio ya está inscrito en este evento")


# ---------------- Colegio ----------------
@router_colegio.post("/eventos/{evento_id}/inscripcion", status_code=201)
def inscribirse(evento_id: int, datos: Inscripcion, request: Request, col=Depends(colegio_actual)):
    evento = repo.evento_publicado(evento_id, col.id_organizador)
    if not evento:
        raise no_encontrado()
    if evento["fecha_inicio"] <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="El evento ya comenzó")
    ids = set(datos.estudiantes)
    if len(ids) != len(datos.estudiantes):
        raise HTTPException(status_code=422, detail="Hay estudiantes repetidos")
    if len(ids) > evento["cupo_estudiantes"]:
        raise HTTPException(status_code=422, detail=f"Máximo {evento['cupo_estudiantes']} estudiantes por colegio")
    if repo.contar_estudiantes_propios(list(ids), col.id) != len(ids):
        raise HTTPException(status_code=422, detail="Algún estudiante no pertenece a tu colegio")
    if repo.ya_inscrito(evento_id, col.id):
        raise YA_INSCRITO
    try:
        nueva = repo.crear(evento_id, col.id, sorted(ids), col.id_usuario, ip_de(request))
    except IntegrityError:  # dos peticiones del mismo colegio al mismo tiempo: la base lo impide
        raise YA_INSCRITO
    if not nueva:
        raise HTTPException(status_code=409, detail="El evento no tiene cupos disponibles")
    return nueva


@router_colegio.get("/inscripciones")
def mis_inscripciones(col=Depends(colegio_actual)):
    return repo.obtener_del_colegio(col.id)


# ---------------- Organizador ----------------
@router.get("/inscripciones")
def listar_inscripciones(org=Depends(organizador_actual)):
    return repo.obtener_del_organizador(org.id)


@router.patch("/inscripciones/{inscripcion_id}")
def decidir_inscripcion(inscripcion_id: int, datos: DecisionInscripcion, request: Request, org=Depends(organizador_actual)):
    inscripcion = repo.obtener_por_id(inscripcion_id, org.id)
    if not inscripcion:
        raise no_encontrado()
    if inscripcion["estado"] != "pendiente":
        raise HTTPException(status_code=409, detail="Esta inscripción ya fue decidida")
    if not repo.decidir(inscripcion, datos.estado, org.id_usuario, ip_de(request)):
        raise HTTPException(status_code=409, detail="El evento ya no tiene cupos de colegios")
    return {"id": inscripcion_id, "estado": datos.estado}


@router.get("/eventos/{evento_id}/asistencia")
def ver_asistencia(evento_id: int, org=Depends(organizador_actual)):
    evento_del_organizador(evento_id, org)
    return repo.obtener_asistencia(evento_id)


@router.put("/eventos/{evento_id}/asistencia", status_code=204)
def guardar_asistencia(evento_id: int, datos: Asistencia, request: Request, org=Depends(organizador_actual)):
    evento_del_organizador(evento_id, org)
    if not repo.guardar_asistencia(evento_id, datos.marcas, org.id_usuario, ip_de(request)):
        raise HTTPException(status_code=422, detail="Marca de asistencia inválida")


# ---------------- Reportes (CSV) ----------------
def csv_seguro(valor) -> str:
    """Evita 'inyeccion de formulas' al abrir el CSV en Excel: celdas que empiezan con = + - @ se neutralizan."""
    t = "" if valor is None else str(valor)
    return "'" + t if t[:1] in ("=", "+", "-", "@") else t


def respuesta_csv(nombre: str, filas: list[list]) -> Response:
    buf = io.StringIO()
    escritor = csv.writer(buf)
    for f in filas:
        escritor.writerow([csv_seguro(c) for c in f])
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",  # ﻿: Excel reconoce las tildes
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


@router.get("/eventos/{evento_id}/reporte/colegios.csv")
def reporte_colegios(evento_id: int, request: Request, org=Depends(organizador_actual)):
    evento_del_organizador(evento_id, org)
    filas = [["Evento", "Colegio", "NIT", "Estado", "Estudiantes"]]
    filas += [[f["evento"], f["colegio"], f["nit"], f["estado"], f["estudiantes"]]
              for f in repo.reporte_colegios(evento_id, org.id_usuario, ip_de(request))]
    return respuesta_csv(f"colegios_evento_{evento_id}.csv", filas)


@router.get("/eventos/{evento_id}/reporte/estudiantes.csv")
def reporte_estudiantes(evento_id: int, request: Request, org=Depends(organizador_actual)):
    evento_del_organizador(evento_id, org)
    filas = [["Evento", "Colegio", "Estudiante", "Grado", "Asistio"]]
    filas += [[f["evento"], f["colegio"], f["estudiante"], f["grado"], "Si" if f["asistio"] else "No"]
              for f in repo.reporte_estudiantes(evento_id, org.id_usuario, ip_de(request))]
    return respuesta_csv(f"estudiantes_evento_{evento_id}.csv", filas)
