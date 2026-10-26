from typing import Literal

from pydantic import BaseModel, Field

CONFIG = {"str_strip_whitespace": True, "extra": "forbid"}  # extra=forbid: rechaza campos que no se piden


class Inscripcion(BaseModel):
    """El colegio inscribe a sus estudiantes en un evento (ids de estudiante)."""
    model_config = CONFIG
    estudiantes: list[int] = Field(min_length=1, max_length=500)


class DecisionInscripcion(BaseModel):
    """El organizador acepta o rechaza una inscripcion pendiente."""
    model_config = CONFIG
    estado: Literal["aceptada", "rechazada"]


class MarcaAsistencia(BaseModel):
    model_config = CONFIG
    id_inscripcion_estudiante: int
    asistio: bool


class Asistencia(BaseModel):
    model_config = CONFIG
    marcas: list[MarcaAsistencia] = Field(max_length=2000)
