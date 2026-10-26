from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

CONFIG = {"str_strip_whitespace": True, "extra": "forbid"}  # extra=forbid: rechaza campos como "id_estado"


class Evento(BaseModel):
    """Lo que envia el organizador al crear o editar un evento."""
    model_config = CONFIG
    nombre: str = Field(min_length=3, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=500)
    lugar: str = Field(min_length=3, max_length=150)
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    id_categoria: int = Field(gt=0)
    id_ciudad: int = Field(gt=0)
    cupo_colegios: int = Field(gt=0, le=1000)
    cupo_estudiantes: int = Field(gt=0, le=500)  # por colegio

    @model_validator(mode="after")
    def fechas_ok(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        return self


class DecisionEvento(BaseModel):
    """El administrador publica o rechaza un evento pendiente."""
    model_config = CONFIG
    decision: Literal["publicado", "rechazado"]
