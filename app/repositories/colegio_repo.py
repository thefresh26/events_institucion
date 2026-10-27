from app.core.auditoria import auditar
from app.core.database import Database
from app.models.colegio import ColegioNuevo

# Colegio como lo ve su organizador: con ciudad, contacto y si su usuario puede entrar
SELECT_COLEGIO = """
    SELECT c.id, c.nombre, c.nit, ci.nombre AS ciudad, u.correo, u.nombre || ' ' || u.apellido AS contacto,
           c.telefono, u.activo
    FROM colegio c
    JOIN usuario u ON u.id = c.id_usuario
    JOIN ciudad ci ON ci.id = c.id_ciudad
"""


class ColegioRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    # ---------------- Organizador: sus colegios ----------------
    def obtener_todos(self, id_organizador: int):
        """Solo los colegios que ESTE organizador registro (evita ver datos de otros organizadores)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{SELECT_COLEGIO} WHERE c.id_organizador = %s AND c.estado = true ORDER BY c.nombre;", (id_organizador,))
            return cursor.fetchall()

    def obtener_por_id(self, colegio_id: int, id_organizador: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{SELECT_COLEGIO} WHERE c.id = %s AND c.id_organizador = %s AND c.estado = true;", (colegio_id, id_organizador))
            return cursor.fetchone()

    def ciudad_valida(self, id_ciudad: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM ciudad WHERE id = %s AND estado = true;", (id_ciudad,))
            return cursor.fetchone() is not None

    def crear(self, datos: ColegioNuevo, contrasena_hash: str, id_organizador: int, id_usuario: int, ip: str | None):
        """Usuario del colegio (ya activo) + colegio + auditoria, en una sola transaccion."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuario (id_rol, correo, contrasena, nombre, apellido, activo)
                VALUES ((SELECT id FROM rol WHERE nombre = 'colegio'), %s, %s, %s, %s, true) RETURNING id;
            """, (datos.correo.lower(), contrasena_hash, datos.nombre, datos.apellido))
            id_usuario_colegio = cursor.fetchone()["id"]
            cursor.execute("""
                INSERT INTO colegio (id_usuario, id_ciudad, id_organizador, nombre, nit, direccion, telefono)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """, (id_usuario_colegio, datos.id_ciudad, id_organizador, datos.colegio_nombre, datos.nit, datos.direccion, datos.telefono))
            nuevo_id = cursor.fetchone()["id"]
            auditar(cursor, id_usuario, "registrar_colegio", "colegio", nuevo_id, ip)
        return self.obtener_por_id(nuevo_id, id_organizador)

    def activar(self, colegio_id: int, activo: bool, id_usuario: int, ip: str | None):
        """Activa o desactiva el acceso del usuario del colegio (no lo borra)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuario SET activo = %s, actualizado = now()
                WHERE id = (SELECT id_usuario FROM colegio WHERE id = %s);
            """, (activo, colegio_id))
            auditar(cursor, id_usuario, "activar_colegio" if activo else "desactivar_colegio", "colegio", colegio_id, ip)

    def eliminar(self, colegio_id: int, id_usuario: int, ip: str | None):
        """Borrado logico: colegio y su usuario quedan con estado=false (no se borran) y ya no puede entrar. Se conserva el historial."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE colegio SET estado = false, actualizado = now() WHERE id = %s RETURNING id_usuario;", (colegio_id,))
            id_usuario_colegio = cursor.fetchone()["id_usuario"]
            cursor.execute("UPDATE usuario SET estado = false, activo = false, actualizado = now() WHERE id = %s;", (id_usuario_colegio,))
            auditar(cursor, id_usuario, "eliminar_colegio", "colegio", colegio_id, ip)

    # ---------------- Administrador: todos los colegios ----------------
    def obtener_todos_admin(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.nombre, c.nit, ci.nombre AS ciudad, o.nombre AS organizador, u.activo
                FROM colegio c
                JOIN usuario u ON u.id = c.id_usuario
                JOIN ciudad ci ON ci.id = c.id_ciudad
                JOIN organizador o ON o.id = c.id_organizador
                WHERE c.estado = true ORDER BY c.nombre;
            """)
            return cursor.fetchall()
