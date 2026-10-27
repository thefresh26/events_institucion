import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.usuario import CONFIG, NIT, validar_telefono


def clave_fuerte(v: str) -> str:
    if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
        raise ValueError("La contraseña debe tener letras y números")
    return v


class Login(BaseModel):
    model_config = CONFIG
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=72)  # 72 = limite de bcrypt


class CambioContrasena(BaseModel):
    model_config = CONFIG
    actual: str = Field(min_length=1, max_length=72)
    nueva: str = Field(min_length=8, max_length=72)

    _clave = field_validator("nueva")(lambda cls, v: clave_fuerte(v))


class RegistroOrganizador(BaseModel):
    """Registro publico: la cuenta queda pendiente hasta que el administrador la apruebe."""
    model_config = CONFIG
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=72)
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    nit: str
    telefono: Optional[str] = None
    organizacion_nombre: str = Field(min_length=3, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=255)

    _clave = field_validator("contrasena")(lambda cls, v: clave_fuerte(v))
    _telefono = field_validator("telefono")(validar_telefono)

    @field_validator("nit")
    @classmethod
    def nit_obligatorio(cls, v):
        if not NIT.match(v):
            raise ValueError("NIT inválido (solo números y guion)")
        return v
