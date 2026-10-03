import re

from pydantic import BaseModel, EmailStr, Field, field_validator

TEL = re.compile(r"^[0-9+\s\-]{7,20}$")
NIT = re.compile(r"^[0-9\-]{5,20}$")


def _limpio(v: str) -> str:
    return " ".join(v.split())


class _Base(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "forbid"}  # extra=forbid: rechaza campos como "rol" o "activo"


class RegistroBase(_Base):
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=72)  # 72 = limite de bcrypt
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    nit: str
    telefono: str | None = None

    @field_validator("contrasena")
    @classmethod
    def clave_fuerte(cls, v):
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("La contraseña debe tener letras y números")
        return v

    @field_validator("nit")
    @classmethod
    def nit_ok(cls, v):
        if not NIT.match(v):
            raise ValueError("NIT inválido (solo números y guion)")
        return v

    @field_validator("telefono")
    @classmethod
    def tel_ok(cls, v):
        if v and not TEL.match(v):
            raise ValueError("Teléfono inválido")
        return v


class RegistroColegio(RegistroBase):
    colegio_nombre: str = Field(min_length=3, max_length=150)
    id_ciudad: int = Field(gt=0)
    direccion: str | None = Field(default=None, max_length=200)


class RegistroOrganizador(RegistroBase):
    organizacion_nombre: str = Field(min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=255)


class LoginIn(_Base):
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=72)
