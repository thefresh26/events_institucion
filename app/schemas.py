import re

from pydantic import BaseModel, EmailStr, Field, field_validator

TEL = re.compile(r"^[0-9+\s\-]{7,20}$")
NIT = re.compile(r"^[0-9\-]{5,20}$")


def _limpio(v: str) -> str:
    return " ".join(v.split())


class _Base(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "forbid"}  # extra=forbid: rechaza campos como "rol" o "activo"


def clave_fuerte(v: str) -> str:
    if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
        raise ValueError("La contraseña debe tener letras y números")
    return v


class ContactoBase(_Base):
    correo: EmailStr
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    nit: str
    telefono: str | None = None

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


class ColegioNuevo(ContactoBase):
    """Lo envia el ORGANIZADOR. No lleva contrasena: el servidor genera una temporal."""
    colegio_nombre: str = Field(min_length=3, max_length=150)
    id_ciudad: int = Field(gt=0)
    direccion: str | None = Field(default=None, max_length=200)


class RegistroOrganizador(ContactoBase):
    contrasena: str = Field(min_length=8, max_length=72)  # 72 = limite de bcrypt
    _clave = field_validator("contrasena")(lambda cls, v: clave_fuerte(v))
    organizacion_nombre: str = Field(min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=255)


class LoginIn(_Base):
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=72)


class CambioContrasena(_Base):
    actual: str = Field(min_length=1, max_length=72)
    nueva: str = Field(min_length=8, max_length=72)
    _clave = field_validator("nueva")(lambda cls, v: clave_fuerte(v))


class EstudianteNuevo(_Base):
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    documento: str = Field(pattern=r"^\d{5,15}$")
    id_grado: int = Field(gt=0)
    nombre_acudiente: str = Field(min_length=3, max_length=150)
    acudiente_autoriza: bool  # el colegio confirma que tiene la autorizacion (Ley 1581 de 2012)

    @field_validator("acudiente_autoriza")
    @classmethod
    def debe_autorizar(cls, v):
        if not v:
            raise ValueError("Debes confirmar la autorización del acudiente")
        return v


class ActivoIn(_Base):
    activo: bool
