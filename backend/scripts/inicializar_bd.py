"""Prepara una base de datos NUEVA (p. ej. un proyecto Neon vacio). Idempotente.
Uso (desde la carpeta backend/, con DB_HOST, DB_NAME, DB_USER, DB_PASSWORD y DB_PORT en el .env):
    python -m scripts.inicializar_bd
Crea las 18 tablas y el trigger de `actualizado` (scripts/schema.sql) y los datos base (roles, modulos, catalogos).
Luego crea el administrador con:  python -m scripts.crear_admin"""
from pathlib import Path

from app.core.database import Database
from app.repositories.admin_repo import AdminRepository

ESQUEMA = Path(__file__).resolve().parent / "schema.sql"
MODULOS_POR_ROL = {
    "administrador": ["panel", "aprobar_eventos", "organizadores", "colegios"],
    "organizador": ["panel", "mis_eventos", "mis_colegios", "inscripciones", "asistencia", "reportes"],
    "colegio": ["panel", "eventos_disponibles", "mis_inscripciones", "mis_estudiantes"],
}
CIUDADES = {"Cundinamarca": ["Bogotá", "Soacha", "Zipaquirá"], "Antioquia": ["Medellín", "Envigado"],
            "Valle del Cauca": ["Cali"], "Atlántico": ["Barranquilla"], "Santander": ["Bucaramanga"]}
GRADOS = ["Preescolar", *[str(n) for n in range(1, 12)]]
CATEGORIAS = ["Ciencia", "Deporte", "Cultura", "Tecnología", "Académico"]


def main() -> None:
    with Database().get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ESQUEMA.read_text(encoding="utf-8"))
        # ON CONFLICT DO NOTHING: si el dato ya existe no se duplica (se puede correr varias veces)
        for rol, modulos in MODULOS_POR_ROL.items():
            cursor.execute("INSERT INTO rol (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING;", (rol,))
            for m in modulos:
                cursor.execute("INSERT INTO modulo (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING;", (m,))
                cursor.execute("""
                    INSERT INTO modulo_por_rol (id_rol, id_modulo)
                    SELECT r.id, m.id FROM rol r, modulo m WHERE r.nombre = %s AND m.nombre = %s
                    ON CONFLICT (id_rol, id_modulo) DO NOTHING;
                """, (rol, m))
        for tabla, nombres in (("estado_evento", ["borrador", "pendiente", "publicado", "rechazado", "cerrado"]),
                               ("estado_inscripcion", ["pendiente", "aceptada", "rechazada"]),
                               ("grado", GRADOS), ("categoria_evento", CATEGORIAS)):
            for n in nombres:  # el nombre de la tabla sale de esta lista fija
                cursor.execute(f"INSERT INTO {tabla} (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING;", (n,))
        for dep, ciudades in CIUDADES.items():
            cursor.execute("INSERT INTO departamento (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING;", (dep,))
            for c in ciudades:
                cursor.execute("""
                    INSERT INTO ciudad (id_departamento, nombre) SELECT id, %s FROM departamento WHERE nombre = %s
                    ON CONFLICT (id_departamento, nombre) DO NOTHING;
                """, (c, dep))
    AdminRepository().asegurar_modulos_admin()  # usuarios y roles para el administrador
    print("Base lista: 18 tablas, triggers y datos base. Ahora: python -m scripts.crear_admin")


if __name__ == "__main__":
    main()
