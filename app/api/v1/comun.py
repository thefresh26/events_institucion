"""Funciones compartidas por los endpoints de eventos e inscripciones."""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import EstadoInscripcion, Inscripcion


def id_estado_inscripcion(db: Session, nombre: str) -> int:
    return db.query(EstadoInscripcion.id).filter_by(nombre=nombre).scalar()


def inscritos(db: Session, id_evento: int, solo_aceptadas: bool = False) -> int:
    q = db.query(func.count(Inscripcion.id)).join(EstadoInscripcion).filter(Inscripcion.id_evento == id_evento)
    q = q.filter(EstadoInscripcion.nombre == "aceptada") if solo_aceptadas else q.filter(EstadoInscripcion.nombre != "rechazada")
    return q.scalar()


def csv_seguro(valor) -> str:
    """Evita 'inyeccion de formulas' al abrir el CSV en Excel: celdas que empiezan con = + - @ se neutralizan."""
    t = "" if valor is None else str(valor)
    return "'" + t if t[:1] in ("=", "+", "-", "@") else t


def no_encontrado():
    return HTTPException(404, "No encontrado")  # 404 y no 403: no revela si el recurso existe
