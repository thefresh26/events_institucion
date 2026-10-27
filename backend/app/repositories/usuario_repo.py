from app.core.auditoria import auditar
from app.core.database import Database
from app.models.usuario import UsuarioNuevo

# Usuario con su rol y el nombre de su perfil (organizacion o colegio), como lo muestra el panel de administracion
SELECT_USUARIO = """
    SELECT u.id, u.correo, u.nombre, u.apellido, r.nombre AS rol, u.activo, u.creado AS creado_en,
           COALESCE(o.nombre, c.nombre) AS perfil
    FROM usuario u
    JOIN rol r ON r.id = u.id_rol
    LEFT JOIN organizador o ON o.id_usuario = u.id
    LEFT JOIN colegio c ON c.id_usuario = u.id
"""


class UsuarioRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    def obtener_todos(self, q: str | None = None, rol: str | None = None, estado: str | None = None):
        filtros, valores = ["u.estado = true"], []
        if q:
            filtros.append("(u.correo ILIKE %s OR u.nombre ILIKE %s OR u.apellido ILIKE %s)")
            valores += [f"%{q.strip()[:60]}%"] * 3
        if rol:
            filtros.append("r.nombre = %s")
            valores.append(rol)
        if estado in ("activo", "inactivo"):
            filtros.append("u.activo = %s")
            valores.append(estado == "activo")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{SELECT_USUARIO} WHERE {' AND '.join(filtros)} ORDER BY u.creado DESC, u.id DESC LIMIT 500;", valores)
            return cursor.fetchall()

    def obtener_por_id(self, usuario_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{SELECT_USUARIO} WHERE u.id = %s AND u.estado = true;", (usuario_id,))
            return cursor.fetchone()

    def crear(self, datos: UsuarioNuevo, contrasena_hash: str, id_admin: int, ip: str | None):
        """Cuenta ya activa; si es organizador, tambien su perfil. Todo en una transaccion."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuario (id_rol, correo, contrasena, nombre, apellido, activo)
                VALUES ((SELECT id FROM rol WHERE nombre = %s), %s, %s, %s, %s, true) RETURNING id;
            """, (datos.rol, datos.correo.lower(), contrasena_hash, datos.nombre, datos.apellido))
            nuevo_id = cursor.fetchone()["id"]
            if datos.rol == "organizador":
                cursor.execute("INSERT INTO organizador (id_usuario, nombre, nit, telefono) VALUES (%s, %s, %s, %s);",
                               (nuevo_id, datos.organizacion_nombre, datos.nit, datos.telefono))
            auditar(cursor, id_admin, f"crear_usuario_{datos.rol}", "usuario", nuevo_id, ip)
        return self.obtener_por_id(nuevo_id)

    def tiene_perfil(self, usuario_id: int, rol: str):
        """organizador y colegio necesitan su fila de perfil; administrador no."""
        if rol == "administrador":
            return True
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # el nombre de tabla sale de esta lista fija, nunca del usuario
            cursor.execute(f"SELECT 1 FROM {'organizador' if rol == 'organizador' else 'colegio'} WHERE id_usuario = %s;", (usuario_id,))
            return cursor.fetchone() is not None

    def actualizar(self, usuario_id: int, cambios: dict, id_admin: int, ip: str | None):
        """cambios: nombre, apellido, activo y/o rol (por nombre). Solo se toca lo que llega."""
        sets, valores = [], []
        for campo in ("nombre", "apellido", "activo"):
            if cambios.get(campo) is not None:
                sets.append(f"{campo} = %s")
                valores.append(cambios[campo])
        if cambios.get("rol"):
            sets.append("id_rol = (SELECT id FROM rol WHERE nombre = %s)")
            valores.append(cambios["rol"])
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE usuario SET {''.join(s + ', ' for s in sets)}actualizado = now() WHERE id = %s AND estado = true;",
                           [*valores, usuario_id])
            auditar(cursor, id_admin, "editar_usuario", "usuario", usuario_id, ip)
        return self.obtener_por_id(usuario_id)

    def cambiar_contrasena(self, usuario_id: int, contrasena_hash: str, id_admin: int, ip: str | None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE usuario SET contrasena = %s, actualizado = now() WHERE id = %s;", (contrasena_hash, usuario_id))
            auditar(cursor, id_admin, "restablecer_contrasena", "usuario", usuario_id, ip)

    def cambiar_estado(self, usuario_id: int, estado: bool, id_admin: int, ip: str | None, accion: str):
        """Borrado logico (estado=false, y ya no puede entrar) o restauracion (estado=true). Su perfil sigue la misma suerte."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            extra = "" if estado else ", activo = false"
            cursor.execute(f"UPDATE usuario SET estado = %s{extra}, actualizado = now() WHERE id = %s RETURNING id, estado;",
                           (estado, usuario_id))
            fila = cursor.fetchone()
            if fila:
                for tabla in ("organizador", "colegio"):
                    cursor.execute(f"UPDATE {tabla} SET estado = %s, actualizado = now() WHERE id_usuario = %s;", (estado, usuario_id))
                auditar(cursor, id_admin, accion, "usuario", usuario_id, ip)
            return fila

    def existe(self, usuario_id: int):
        """Tambien encuentra usuarios eliminados (para poder restaurarlos)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuario WHERE id = %s;", (usuario_id,))
            return cursor.fetchone() is not None

    # ---------------- Roles y modulos ----------------
    def obtener_roles(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # usuarios: solo los que existen (estado = true); los eliminados ya no cuentan
            cursor.execute("""
                SELECT r.id, r.nombre, r.descripcion,
                       (SELECT count(*) FROM usuario u WHERE u.id_rol = r.id AND u.estado = true) AS usuarios,
                       COALESCE((SELECT array_agg(mr.id_modulo ORDER BY mr.id_modulo) FROM modulo_por_rol mr
                                  WHERE mr.id_rol = r.id AND mr.estado = true), '{}') AS modulos,
                       r.nombre = 'administrador' AS bloqueado
                FROM rol r WHERE r.estado = true ORDER BY r.id;
            """)
            roles = cursor.fetchall()
            cursor.execute("SELECT id, nombre, descripcion FROM modulo WHERE estado = true ORDER BY id;")
            return {"roles": roles, "modulos": cursor.fetchall()}

    def obtener_rol(self, rol_id: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM rol WHERE id = %s AND estado = true;", (rol_id,))
            return cursor.fetchone()

    def contar_modulos(self, ids: list[int]):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) AS n FROM modulo WHERE id = ANY(%s) AND estado = true;", (ids,))
            return cursor.fetchone()["n"]

    def asignar_modulos(self, rol_id: int, ids: list[int], id_admin: int, ip: str | None):
        """Borrado logico en la tabla intermedia: se apagan las filas que sobran y se reactivan o crean las nuevas."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE modulo_por_rol SET estado = (id_modulo = ANY(%s)), actualizado = now() WHERE id_rol = %s;", (ids, rol_id))
            cursor.execute("""
                INSERT INTO modulo_por_rol (id_rol, id_modulo)
                SELECT %s, m FROM unnest(%s::int[]) AS m
                WHERE NOT EXISTS (SELECT 1 FROM modulo_por_rol WHERE id_rol = %s AND id_modulo = m);
            """, (rol_id, ids, rol_id))
            auditar(cursor, id_admin, "asignar_modulos", "rol", rol_id, ip)
