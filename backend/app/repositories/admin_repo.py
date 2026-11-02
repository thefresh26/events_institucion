from app.core.database import Database

# Modulos del panel de administracion que el rol administrador siempre debe tener
MODULOS_ADMIN = {"usuarios": "Gestión de usuarios", "roles": "Roles y módulos"}
# Pantallas de la API auxiliar (Express): las ven los 3 roles; el administrador puede quitarlas desde "Roles y módulos"
MODULOS_AUX = {"pqrs": "Peticiones, quejas, reclamos y sugerencias", "comunicados": "Comunicados de la plataforma",
               "valoraciones": "Valoraciones de los eventos"}
ROLES = ("administrador", "organizador", "colegio")


class AdminRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    def resumen(self):
        """Numeros del panel del administrador. Solo cuenta lo que existe (estado = true)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ee.nombre, count(e.id) AS n
                FROM estado_evento ee LEFT JOIN evento e ON e.id_estado = ee.id AND e.estado = true
                WHERE ee.estado = true GROUP BY ee.nombre;
            """)
            por_estado = {f["nombre"]: f["n"] for f in cursor.fetchall()}
            cursor.execute("""
                SELECT (SELECT count(*) FROM colegio WHERE estado = true) AS colegios,
                       (SELECT count(*) FROM organizador WHERE estado = true) AS organizadores,
                       (SELECT count(*) FROM organizador o JOIN usuario u ON u.id = o.id_usuario
                         WHERE o.estado = true AND u.activo = false) AS organizadores_pendientes,
                       (SELECT count(*) FROM inscripcion WHERE estado = true) AS inscripciones;
            """)
            return {"eventos_por_estado": por_estado, **cursor.fetchone()}

    def asegurar_modulos_admin(self):
        """Idempotente (se puede correr en cada arranque): crea los modulos si faltan y se los asigna al administrador."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM rol WHERE nombre = 'administrador';")
            rol = cursor.fetchone()
            if rol is None:
                return
            for nombre, descripcion in MODULOS_ADMIN.items():
                cursor.execute("INSERT INTO modulo (nombre, descripcion) VALUES (%s, %s) ON CONFLICT (nombre) DO NOTHING;",
                               (nombre, descripcion))
                cursor.execute("""
                    INSERT INTO modulo_por_rol (id_rol, id_modulo) SELECT %s, id FROM modulo WHERE nombre = %s
                    ON CONFLICT (id_rol, id_modulo) DO UPDATE SET estado = true, actualizado = now()
                    WHERE modulo_por_rol.estado = false;
                """, (rol["id"], nombre))
            for nombre, descripcion in MODULOS_AUX.items():  # DO NOTHING: si el administrador lo desactiva, no se vuelve a activar solo
                cursor.execute("INSERT INTO modulo (nombre, descripcion) VALUES (%s, %s) ON CONFLICT (nombre) DO NOTHING;",
                               (nombre, descripcion))
                cursor.execute("""
                    INSERT INTO modulo_por_rol (id_rol, id_modulo)
                    SELECT r.id, m.id FROM rol r, modulo m WHERE r.nombre = ANY(%s) AND m.nombre = %s
                    ON CONFLICT (id_rol, id_modulo) DO NOTHING;
                """, (list(ROLES), nombre))
