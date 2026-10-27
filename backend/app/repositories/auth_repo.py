from app.core.auditoria import auditar
from app.core.database import Database
from app.models.auth import RegistroOrganizador


class AuthRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    def obtener_por_correo(self, correo: str):
        """Para el login: solo usuarios que existen (estado = true)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.contrasena, u.activo, r.nombre AS rol
                FROM usuario u JOIN rol r ON r.id = u.id_rol
                WHERE u.correo = %s AND u.estado = true;
            """, (correo,))
            return cursor.fetchone()

    def obtener_sesion(self, usuario_id: int):
        """Usuario del token, con su rol. None si no existe, fue eliminado o esta inactivo (no puede seguir dentro)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.correo, u.nombre, u.apellido, r.nombre AS rol
                FROM usuario u JOIN rol r ON r.id = u.id_rol
                WHERE u.id = %s AND u.estado = true AND u.activo = true;
            """, (usuario_id,))
            return cursor.fetchone()

    def obtener_perfil(self, usuario_id: int):
        """Lo que recibe el frontend: datos, rol, modulos del menu e id de su colegio u organizacion."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.correo, u.nombre, u.apellido, r.nombre AS rol,
                       COALESCE((SELECT array_agg(m.nombre ORDER BY m.nombre) FROM modulo_por_rol mr
                                  JOIN modulo m ON m.id = mr.id_modulo
                                  WHERE mr.id_rol = r.id AND mr.estado = true AND m.estado = true), '{}') AS modulos,
                       (SELECT c.id FROM colegio c WHERE c.id_usuario = u.id AND r.nombre = 'colegio') AS id_colegio,
                       (SELECT o.id FROM organizador o WHERE o.id_usuario = u.id AND r.nombre = 'organizador') AS id_organizador
                FROM usuario u JOIN rol r ON r.id = u.id_rol
                WHERE u.id = %s;
            """, (usuario_id,))
            return cursor.fetchone()

    def obtener_organizador(self, usuario_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, id_usuario FROM organizador WHERE id_usuario = %s AND estado = true;", (usuario_id,))
            return cursor.fetchone()

    def obtener_colegio(self, usuario_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, id_usuario, id_organizador FROM colegio WHERE id_usuario = %s AND estado = true;", (usuario_id,))
            return cursor.fetchone()

    def registrar_organizador(self, datos: RegistroOrganizador, contrasena_hash: str):
        """activo = false: la cuenta queda pendiente hasta que el administrador la apruebe."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuario (id_rol, correo, contrasena, nombre, apellido, activo)
                VALUES ((SELECT id FROM rol WHERE nombre = 'organizador'), %s, %s, %s, %s, false) RETURNING id;
            """, (datos.correo.lower(), contrasena_hash, datos.nombre, datos.apellido))
            nuevo_id = cursor.fetchone()["id"]
            cursor.execute("INSERT INTO organizador (id_usuario, nombre, nit, telefono, descripcion) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                           (nuevo_id, datos.organizacion_nombre, datos.nit, datos.telefono, datos.descripcion))
            auditar(cursor, nuevo_id, "registro_organizador", "organizador", cursor.fetchone()["id"], None)

    def obtener_contrasena(self, usuario_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT contrasena FROM usuario WHERE id = %s;", (usuario_id,))
            return cursor.fetchone()["contrasena"]

    def cambiar_contrasena(self, usuario_id: int, contrasena_hash: str, ip: str | None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE usuario SET contrasena = %s, actualizado = now() WHERE id = %s;", (contrasena_hash, usuario_id))
            auditar(cursor, usuario_id, "cambiar_contrasena", "usuario", usuario_id, ip)
