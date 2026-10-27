from typing import Optional

from pydantic import BaseModel, Field

CONFIG = {"str_strip_whitespace": True, "extra": "forbid"}  # extra=forbid: rechaza campos como "estado" o "id"


class CatalogoNuevo(BaseModel):
    """Cuerpo de POST /admin/catalogos/{tabla}. Cada tabla usa solo algunos campos (ver TABLAS en catalogo_repo)."""
    model_config = CONFIG
    nombre: str = Field(min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=255)
    id_departamento: Optional[int] = Field(None, gt=0)  # solo ciudades


class CatalogoEdita(CatalogoNuevo):
    """Cuerpo de PUT: igual, pero todo opcional (solo se cambia lo que se envia)."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)


class EstadoIn(BaseModel):
    model_config = CONFIG
    estado: bool
