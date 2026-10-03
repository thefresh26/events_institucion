"""Modelos que reflejan EXACTAMENTE las 18 tablas creadas en Neon (esquema_eventos_neon.sql)."""
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

ahora = dict(server_default=func.now())


# ---- Las 4 tablas base del profesor ----
class Rol(Base):
    __tablename__ = "rol"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    modulos: Mapped[list["Modulo"]] = relationship(secondary="modulo_por_rol", viewonly=True)


class Modulo(Base):
    __tablename__ = "modulo"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))


class ModuloPorRol(Base):
    __tablename__ = "modulo_por_rol"
    __table_args__ = (UniqueConstraint("id_rol", "id_modulo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    id_modulo: Mapped[int] = mapped_column(ForeignKey("modulo.id"))


class Usuario(Base):
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    correo: Mapped[str] = mapped_column(String(255), unique=True)
    contrasena: Mapped[str] = mapped_column(String(255))  # hash bcrypt
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), **ahora)
    rol: Mapped[Rol] = relationship()


# ---- Ubicacion ----
class Departamento(Base):
    __tablename__ = "departamento"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)


class Ciudad(Base):
    __tablename__ = "ciudad"
    __table_args__ = (UniqueConstraint("id_departamento", "nombre"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_departamento: Mapped[int] = mapped_column(ForeignKey("departamento.id"))
    nombre: Mapped[str] = mapped_column(String(100))
    departamento: Mapped[Departamento] = relationship()


# ---- Actores ----
class Colegio(Base):
    __tablename__ = "colegio"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    id_ciudad: Mapped[int] = mapped_column(ForeignKey("ciudad.id"))
    nombre: Mapped[str] = mapped_column(String(150))
    nit: Mapped[str] = mapped_column(String(20), unique=True)
    direccion: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(20))
    usuario: Mapped[Usuario] = relationship()
    ciudad: Mapped[Ciudad] = relationship()


class Organizador(Base):
    __tablename__ = "organizador"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    nit: Mapped[str] = mapped_column(String(20), unique=True)
    telefono: Mapped[str | None] = mapped_column(String(20))
    descripcion: Mapped[str | None] = mapped_column(String(255))
    usuario: Mapped[Usuario] = relationship()


# ---- Estudiantes ----
class Grado(Base):
    __tablename__ = "grado"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(20), unique=True)


class Estudiante(Base):
    __tablename__ = "estudiante"
    __table_args__ = (UniqueConstraint("id_colegio", "documento"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_colegio: Mapped[int] = mapped_column(ForeignKey("colegio.id"))
    id_grado: Mapped[int] = mapped_column(ForeignKey("grado.id"))
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str] = mapped_column(String(100))
    documento: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    grado: Mapped[Grado] = relationship()


class AutorizacionAcudiente(Base):
    __tablename__ = "autorizacion_acudiente"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_estudiante: Mapped[int] = mapped_column(ForeignKey("estudiante.id"))
    nombre_acudiente: Mapped[str] = mapped_column(String(150))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), **ahora)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)


# ---- Eventos ----
class CategoriaEvento(Base):
    __tablename__ = "categoria_evento"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))


class EstadoEvento(Base):
    __tablename__ = "estado_evento"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)


class Evento(Base):
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
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), **ahora)
    estado: Mapped[EstadoEvento] = relationship()
    categoria: Mapped[CategoriaEvento] = relationship()
    organizador: Mapped[Organizador] = relationship()


# ---- Inscripciones ----
class EstadoInscripcion(Base):
    __tablename__ = "estado_inscripcion"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)


class Inscripcion(Base):
    __tablename__ = "inscripcion"
    __table_args__ = (UniqueConstraint("id_evento", "id_colegio"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_evento: Mapped[int] = mapped_column(ForeignKey("evento.id"))
    id_colegio: Mapped[int] = mapped_column(ForeignKey("colegio.id"))
    id_estado: Mapped[int] = mapped_column(ForeignKey("estado_inscripcion.id"))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), **ahora)
    estado: Mapped[EstadoInscripcion] = relationship()
    evento: Mapped[Evento] = relationship()
    colegio: Mapped[Colegio] = relationship()
    estudiantes: Mapped[list["InscripcionEstudiante"]] = relationship()


class InscripcionEstudiante(Base):
    __tablename__ = "inscripcion_estudiante"
    __table_args__ = (UniqueConstraint("id_inscripcion", "id_estudiante"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_inscripcion: Mapped[int] = mapped_column(ForeignKey("inscripcion.id"))
    id_estudiante: Mapped[int] = mapped_column(ForeignKey("estudiante.id"))
    asistio: Mapped[bool] = mapped_column(Boolean, default=False)
    estudiante: Mapped[Estudiante] = relationship()


# ---- Auditoria ----
class Auditoria(Base):
    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    accion: Mapped[str] = mapped_column(String(100))
    tabla: Mapped[str | None] = mapped_column(String(60))
    registro_id: Mapped[int | None] = mapped_column(Integer)
    ip: Mapped[str | None] = mapped_column(String(45))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), **ahora)
