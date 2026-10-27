from app.core.auditoria import auditar
from app.core.database import Database


class OrganizadorRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    def obtener_todos(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.id, o.nombre, o.nit, u.correo, o.telefono, u.activo
                FROM organizador o JOIN usuario u ON u.id = o.id_usuario
                WHERE o.estado = true ORDER BY o.nombre;
            """)
            return cursor.fetchall()

    def activar(self, organizador_id: int, activo: bool, id_admin: int, ip: str | None):
        """Aprueba (activo=true) o desactiva al organizador. Devuelve None si no existe."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuario SET activo = %s, actualizado = now()
                WHERE id = (SELECT id_usuario FROM organizador WHERE id = %s AND estado = true)
                RETURNING activo;
            """, (activo, organizador_id))
            fila = cursor.fetchone()
            if fila:
                auditar(cursor, id_admin, "activar_organizador" if activo else "desactivar_organizador", "organizador", organizador_id, ip)
                return {"id": organizador_id, "activo": fila["activo"]}
            return None
