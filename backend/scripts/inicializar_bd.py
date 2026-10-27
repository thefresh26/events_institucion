"""Prepara una base de datos NUEVA (p. ej. un proyecto Neon vacio). Idempotente.
Uso (desde la carpeta backend/, con DB_HOST, DB_NAME, DB_USER, DB_PASSWORD y DB_PORT en el .env):
    python -m scripts.inicializar_bd
Crea las 18 tablas, el trigger de `actualizado` y los datos base (roles, modulos, catalogos).
Luego crea el administrador con:  python -m scripts.crear_admin"""
from sqlalchemy import text

from app.db.seed import asegurar_modulos_admin
from app.db.session import Base, SessionLocal, engine
from app.models import (CategoriaEvento, Ciudad, Departamento, EstadoEvento, EstadoInscripcion, Grado, Modulo,
                        ModuloPorRol, Rol)

MODULOS_POR_ROL = {
    "administrador": ["panel", "aprobar_eventos", "organizadores", "colegios"],
    "organizador": ["panel", "mis_eventos", "mis_colegios", "inscripciones", "asistencia", "reportes"],
    "colegio": ["panel", "eventos_disponibles", "mis_inscripciones", "mis_estudiantes"],
}
CIUDADES = {"Cundinamarca": ["Bogotá", "Soacha", "Zipaquirá"], "Antioquia": ["Medellín", "Envigado"],
            "Valle del Cauca": ["Cali"], "Atlántico": ["Barranquilla"], "Santander": ["Bucaramanga"]}
GRADOS = ["Preescolar", *[str(n) for n in range(1, 12)]]
CATEGORIAS = ["Ciencia", "Deporte", "Cultura", "Tecnología", "Académico"]

TRIGGER = """
CREATE OR REPLACE FUNCTION set_actualizado() RETURNS trigger AS $$
BEGIN NEW.actualizado = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;
"""


def obtener(db, modelo, **filtro):
    fila = db.query(modelo).filter_by(**filtro).first()
    if fila is None:
        fila = modelo(**filtro)
        db.add(fila)
        db.flush()
    return fila


def main() -> None:
    Base.metadata.create_all(engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as con:
            con.execute(text(TRIGGER))
            for t in Base.metadata.tables:
                con.execute(text(f'DROP TRIGGER IF EXISTS trg_actualizado ON "{t}"'))
                con.execute(text(f'CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "{t}" '
                                 "FOR EACH ROW EXECUTE FUNCTION set_actualizado()"))
    with SessionLocal() as db:
        for rol, modulos in MODULOS_POR_ROL.items():
            r = obtener(db, Rol, nombre=rol)
            for m in modulos:
                mod = obtener(db, Modulo, nombre=m)
                obtener(db, ModuloPorRol, id_rol=r.id, id_modulo=mod.id)
        for n in ("borrador", "pendiente", "publicado", "rechazado", "cerrado"):
            obtener(db, EstadoEvento, nombre=n)
        for n in ("pendiente", "aceptada", "rechazada"):
            obtener(db, EstadoInscripcion, nombre=n)
        for n in GRADOS:
            obtener(db, Grado, nombre=n)
        for n in CATEGORIAS:
            obtener(db, CategoriaEvento, nombre=n)
        for dep, ciudades in CIUDADES.items():
            d = obtener(db, Departamento, nombre=dep)
            for c in ciudades:
                obtener(db, Ciudad, id_departamento=d.id, nombre=c)
        db.commit()
        asegurar_modulos_admin(db)  # usuarios y roles para el administrador
    print("Base lista: 18 tablas, triggers y datos base. Ahora: python -m scripts.crear_admin")


if __name__ == "__main__":
    main()
