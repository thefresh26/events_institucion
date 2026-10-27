from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.usuario import CONFIG, NIT, validar_telefono


class ColegioNuevo(BaseModel):
    """Lo envia el ORGANIZADOR. No lleva contraseña: el servidor genera una temporal."""
    model_config = CONFIG
    correo: EmailStr
    nombre: str = Field(min_length=2, max_length=100)    # contacto (rector o coordinador)
    apellido: str = Field(min_length=2, max_length=100)
    nit: str
    telefono: Optional[str] = None
    colegio_nombre: str = Field(min_length=3, max_length=150)
    id_ciudad: int = Field(gt=0)
    direccion: Optional[str] = Field(None, max_length=200)

    @field_validator("nit")
    @classmethod
    def nit_obligatorio(cls, v):
        if not NIT.match(v):
            raise ValueError("NIT inválido (solo números y guion)")
        return v

    _telefono = field_validator("telefono")(validar_telefono)


class Activo(BaseModel):
    """Activa o desactiva el acceso de una cuenta (sin borrarla)."""
    model_config = CONFIG
    activo: bool
