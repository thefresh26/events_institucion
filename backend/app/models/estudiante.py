from pydantic import BaseModel, Field, field_validator


class EstudianteNuevo(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "forbid"}  # extra=forbid: rechaza campos como "id_colegio"
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


class EstudianteEdita(BaseModel):
    """Cuerpo de PUT: reemplaza los datos del estudiante (la autorizacion del acudiente no cambia)."""
    model_config = {"str_strip_whitespace": True, "extra": "forbid"}
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    documento: str = Field(pattern=r"^\d{5,15}$")
    id_grado: int = Field(gt=0)
