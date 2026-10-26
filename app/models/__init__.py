"""Modelos de las 18 tablas de Neon. TODAS llevan estado (borrado logico), creado y actualizado (ver Auditable)."""
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

ahora = dict(server_default=func.now())


class Auditable:
    """Los 3 campos que el taller exige en TODAS las tablas.
    estado: True = existe, False = eliminado (el registro NO se borra, solo cambia el estado; se maneja desde la API).
    creado: fecha de creacion, no cambia. actualizado: se refresca en cada UPDATE (ORM + trigger de PostgreSQL)."""
    estado: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    creado: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---- Las 4 tablas base del profesor ----
class Rol(Auditable, Base):
    __tablename__ = "rol"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    modulos: Mapped[list["Modulo"]] = relationship(
        secondary="modulo_por_rol", viewonly=True,
        primaryjoin="and_(Rol.id == ModuloPorRol.id_rol, ModuloPorRol.estado.is_(True))",
        secondaryjoin="and_(Modulo.id == ModuloPorRol.id_modulo, Modulo.estado.is_(True))")


class Modulo(Auditable, Base):
    __tablename__ = "modulo"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))


class ModuloPorRol(Auditable, Base):
    __tablename__ = "modulo_por_rol"
    __table_args__ = (UniqueConstraint("id_rol", "id_modulo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    id_modulo: Mapped[int] = mapped_column(ForeignKey("modulo.id"))


class Usuario(Auditable, Base):
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    correo: Mapped[str] = mapped_column(String(255), unique=True)
    contrasena: Mapped[str] = mapped_column(String(255))  # hash bcrypt
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    rol: Mapped[Rol] = relationship()


# ---- Ubicacion ----
class Departamento(Auditable, Base):
    __tablename__ = "departamento"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)


class Ciudad(Auditable, Base):
    __tablename__ = "ciudad"
    __table_args__ = (UniqueConstraint("id_departamento", "nombre"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_departamento: Mapped[int] = mapped_column(ForeignKey("departamento.id"))
    nombre: Mapped[str] = mapped_column(String(100))
    departamento: Mapped[Departamento] = relationship()


# ---- Actores ----
class Colegio(Auditable, Base):
    __tablename__ = "colegio"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    id_ciudad: Mapped[int] = mapped_column(ForeignKey("ciudad.id"))
    id_organizador: Mapped[int] = mapped_column(ForeignKey("organizador.id"))  # quien registro al colegio
    nombre: Mapped[str] = mapped_column(String(150))
    nit: Mapped[str] = mapped_column(String(20), unique=True)
    direccion: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(20))
    usuario: Mapped[Usuario] = relationship()
    ciudad: Mapped[Ciudad] = relationship()


class Organizador(Auditable, Base):
    __tablename__ = "organizador"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    nit: Mapped[str] = mapped_column(String(20), unique=True)
    telefono: Mapped[str | None] = mapped_column(String(20))
    descripcion: Mapped[str | None] = mapped_column(String(255))
    usuario: Mapped[Usuario] = relationship()


# ---- Estudiantes ----
class Grado(Auditable, Base):
    __tablename__ = "grado"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(20), unique=True)


class Estudiante(Auditable, Base):
    __tablename__ = "estudiante"
    __table_args__ = (UniqueConstraint("id_colegio", "documento"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_colegio: Mapped[int] = mapped_column(ForeignKey("colegio.id"))
    id_grado: Mapped[int] = mapped_column(ForeignKey("grado.id"))
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str] = mapped_column(String(100))
    documento: Mapped[str] = mapped_column(String(20))
    grado: Mapped[Grado] = relationship()


class AutorizacionAcudiente(Auditable, Base):
    __tablename__ = "autorizacion_acudiente"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_estudiante: Mapped[int] = mapped_column(ForeignKey("estudiante.id"), unique=True)
    nombre_acudiente: Mapped[str] = mapped_column(String(150))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), **ahora)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)


# ---- Eventos ----
class CategoriaEvento(Auditable, Base):
    __tablename__ = "categoria_evento"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))


class EstadoEvento(Auditable, Base):
    __tablename__ = "estado_evento"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)


class Evento(Auditable, Base):
    __tablename__ = "evento"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_organizador: Mapped[int] = mapped_column(ForeignKey("organizador.id"))
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categoria_evento.id"))
    id_ciudad: Mapped[int] = mapped_column(ForeignKey("ciudad.id"))
    id_estado: Mapped[int] = mapped_column(ForeignKey("estado_evento.id"))
    id_aprobador: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    lugar: Mapped[str] = mapped_column(String(150))
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cupo_colegios: Mapped[int] = mapped_column(Integer, CheckConstraint("cupo_colegios > 0"))
    cupo_estudiantes: Mapped[int] = mapped_column(Integer, CheckConstraint("cupo_estudiantes > 0"))
    fecha_aprobacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estado_evento: Mapped[EstadoEvento] = relationship()
    categoria: Mapped[CategoriaEvento] = relationship()
    organizador: Mapped[Organizador] = relationship()


# ---- Inscripciones ----
class EstadoInscripcion(Auditable, Base):
    __tablename__ = "estado_inscripcion"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)


class Inscripcion(Auditable, Base):
    __tablename__ = "inscripcion"
    __table_args__ = (UniqueConstraint("id_evento", "id_colegio"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_evento: Mapped[int] = mapped_column(ForeignKey("evento.id"))
    id_colegio: Mapped[int] = mapped_column(ForeignKey("colegio.id"))
    id_estado: Mapped[int] = mapped_column(ForeignKey("estado_inscripcion.id"))
    estado_inscripcion: Mapped[EstadoInscripcion] = relationship()
    evento: Mapped[Evento] = relationship()
    colegio: Mapped[Colegio] = relationship()
    estudiantes: Mapped[list["InscripcionEstudiante"]] = relationship()


class InscripcionEstudiante(Auditable, Base):
    __tablename__ = "inscripcion_estudiante"
    __table_args__ = (UniqueConstraint("id_inscripcion", "id_estudiante"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_inscripcion: Mapped[int] = mapped_column(ForeignKey("inscripcion.id"))
    id_estudiante: Mapped[int] = mapped_column(ForeignKey("estudiante.id"))
    asistio: Mapped[bool] = mapped_column(Boolean, default=False)
    estudiante: Mapped[Estudiante] = relationship()


# ---- Auditoria ----
class Auditoria(Auditable, Base):
    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    accion: Mapped[str] = mapped_column(String(100))
    tabla: Mapped[str | None] = mapped_column(String(60))
    registro_id: Mapped[int | None] = mapped_column(Integer)
    ip: Mapped[str | None] = mapped_column(String(45))
