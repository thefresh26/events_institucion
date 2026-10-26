from app.core.auditoria import auditar
from app.core.database import Database

# nombre en la URL -> (tabla en PostgreSQL, campos que se pueden escribir, campos obligatorios)
# Los nombres de tabla/columna salen SOLO de esta lista (nunca del usuario), por eso se pueden poner en el SQL;
# los valores siempre van con %s.
TABLAS = {
    "roles": ("rol", {"nombre", "descripcion"}, {"nombre"}),
    "modulos": ("modulo", {"nombre", "descripcion"}, {"nombre"}),
    "departamentos": ("departamento", {"nombre"}, {"nombre"}),
    "ciudades": ("ciudad", {"id_departamento", "nombre"}, {"id_departamento", "nombre"}),
    "grados": ("grado", {"nombre"}, {"nombre"}),
    "categorias": ("categoria_evento", {"nombre", "descripcion"}, {"nombre"}),
    "estados-evento": ("estado_evento", {"nombre"}, {"nombre"}),
    "estados-inscripcion": ("estado_inscripcion", {"nombre"}, {"nombre"}),
}


class CatalogoRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    # ---- Listas publicas (formularios del frontend): solo registros con estado = true ----
    def listar_ciudades(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.nombre, d.nombre AS departamento
                FROM ciudad c JOIN departamento d ON d.id = c.id_departamento
                WHERE c.estado = true ORDER BY c.nombre LIMIT 2000;
            """)
            return cursor.fetchall()

    def listar_grados(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM grado WHERE estado = true ORDER BY id;")
            return cursor.fetchall()

    def listar_categorias(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM categoria_evento WHERE estado = true ORDER BY nombre;")
            return cursor.fetchall()

    # ---- CRUD del administrador ----
    def obtener_todos(self, tabla: str, todos: bool = False):
        """Por defecto solo estado = true; con todos=True tambien los eliminados (borrado logico)."""
        filtro = "" if todos else "WHERE estado = true"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLAS[tabla][0]} {filtro} ORDER BY id LIMIT 2000;")
            return cursor.fetchall()

    def obtener_por_id(self, tabla: str, registro_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TABLAS[tabla][0]} WHERE id = %s;", (registro_id,))
            return cursor.fetchone()

    def crear(self, tabla: str, datos: dict, id_usuario: int, ip: str | None):
        nombre_tabla = TABLAS[tabla][0]
        columnas = ", ".join(datos)
        marcas = ", ".join(["%s"] * len(datos))
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {nombre_tabla} ({columnas}) VALUES ({marcas}) RETURNING *;", list(datos.values()))
            nuevo = cursor.fetchone()
            auditar(cursor, id_usuario, f"crear_{tabla}", nombre_tabla, nuevo["id"], ip)
            return nuevo

    def actualizar(self, tabla: str, registro_id: int, datos: dict, id_usuario: int, ip: str | None):
        nombre_tabla = TABLAS[tabla][0]
        cambios = "".join(f"{c} = %s, " for c in datos)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # actualizado = now(): no depende de que exista el trigger en la base
            cursor.execute(f"UPDATE {nombre_tabla} SET {cambios}actualizado = now() WHERE id = %s RETURNING *;",
                           [*datos.values(), registro_id])
            actualizado = cursor.fetchone()
            if actualizado:
                auditar(cursor, id_usuario, f"editar_{tabla}", nombre_tabla, registro_id, ip)
            return actualizado

    def cambiar_estado(self, tabla: str, registro_id: int, estado: bool, id_usuario: int, ip: str | None):
        """estado=False es el borrado logico (la fila NO se borra); estado=True la restaura."""
        nombre_tabla = TABLAS[tabla][0]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE {nombre_tabla} SET estado = %s, actualizado = now() WHERE id = %s RETURNING *;",
                           (estado, registro_id))
            fila = cursor.fetchone()
            if fila:
                auditar(cursor, id_usuario, f"estado_{tabla}", nombre_tabla, registro_id, ip)
            return fila

    def eliminar(self, tabla: str, registro_id: int, id_usuario: int, ip: str | None):
        return self.cambiar_estado(tabla, registro_id, False, id_usuario, ip)
