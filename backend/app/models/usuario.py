import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

CONFIG = {"str_strip_whitespace": True, "extra": "forbid"}  # extra=forbid: rechaza campos como "id_rol" o "estado"
NIT = re.compile(r"^[0-9\-]{5,20}$")
TEL = re.compile(r"^[0-9+\s\-]{7,20}$")


def validar_nit(v):
    if v and not NIT.match(v):
        raise ValueError("NIT inválido (solo números y guion)")
    return v


def validar_telefono(v):
    if v and not TEL.match(v):
        raise ValueError("Teléfono inválido")
    return v


class UsuarioNuevo(BaseModel):
    """El administrador crea cuentas ya activas (administrador u organizador)."""
    model_config = CONFIG
    correo: EmailStr
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    rol: Literal["administrador", "organizador"]
    organizacion_nombre: Optional[str] = Field(None, min_length=3, max_length=150)
    nit: Optional[str] = None
    telefono: Optional[str] = None

    _nit = field_validator("nit")(validar_nit)
    _telefono = field_validator("telefono")(validar_telefono)


class UsuarioEdita(BaseModel):
    """Solo se cambia lo que se envia."""
    model_config = CONFIG
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    rol: Optional[Literal["administrador", "organizador", "colegio"]] = None
    activo: Optional[bool] = None


class Modulos(BaseModel):
    """Ids de los modulos que vera un rol."""
    model_config = CONFIG
    modulos: list[int] = Field(max_length=100)
