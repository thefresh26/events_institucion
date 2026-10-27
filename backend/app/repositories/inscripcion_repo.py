from app.core.auditoria import auditar
from app.core.database import Database

# Bloquea la fila del evento hasta el fin de la transaccion: si dos colegios se inscriben al mismo tiempo,
# el segundo espera a que el primero termine y cuenta su inscripcion (asi el cupo nunca se pasa).
BLOQUEAR_EVENTO = "SELECT cupo_colegios FROM evento WHERE id = %s FOR UPDATE;"
CONTAR = """
    SELECT count(*) AS n FROM inscripcion i JOIN estado_inscripcion ei ON ei.id = i.id_estado
    WHERE i.id_evento = %s AND i.estado = true AND ei.nombre {condicion};
"""


class InscripcionRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    # ---------------- Colegio ----------------
    def evento_publicado(self, evento_id: int, id_organizador: int):
        """El evento solo existe para el colegio si esta publicado y es de SU organizador."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.fecha_inicio, e.cupo_estudiantes FROM evento e JOIN estado_evento ee ON ee.id = e.id_estado
                WHERE e.id = %s AND e.id_organizador = %s AND e.estado = true AND ee.nombre = 'publicado';
            """, (evento_id, id_organizador))
            return cursor.fetchone()

    def contar_estudiantes_propios(self, ids: list[int], id_colegio: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) AS n FROM estudiante WHERE id = ANY(%s) AND id_colegio = %s AND estado = true;",
                           (ids, id_colegio))
            return cursor.fetchone()["n"]

    def ya_inscrito(self, evento_id: int, id_colegio: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM inscripcion WHERE id_evento = %s AND id_colegio = %s AND estado = true;",
                           (evento_id, id_colegio))
            return cursor.fetchone() is not None

    def crear(self, evento_id: int, id_colegio: int, ids: list[int], id_usuario: int, ip: str | None):
        """Inscripcion pendiente + sus estudiantes. Devuelve None si el evento ya no tiene cupo de colegios."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(BLOQUEAR_EVENTO, (evento_id,))
            cupo = cursor.fetchone()["cupo_colegios"]
            cursor.execute(CONTAR.format(condicion="<> 'rechazada'"), (evento_id,))
            if cursor.fetchone()["n"] >= cupo:
                return None
            cursor.execute("""
                INSERT INTO inscripcion (id_evento, id_colegio, id_estado)
                VALUES (%s, %s, (SELECT id FROM estado_inscripcion WHERE nombre = 'pendiente')) RETURNING id;
            """, (evento_id, id_colegio))
            nuevo_id = cursor.fetchone()["id"]
            cursor.executemany("INSERT INTO inscripcion_estudiante (id_inscripcion, id_estudiante, asistio) VALUES (%s, %s, false);",
                               [(nuevo_id, x) for x in ids])
            auditar(cursor, id_usuario, "crear_inscripcion", "inscripcion", nuevo_id, ip)
            return {"id": nuevo_id, "estado": "pendiente", "estudiantes": len(ids)}

    def obtener_del_colegio(self, id_colegio: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id, e.nombre AS evento, e.fecha_inicio, ei.nombre AS estado,
                       COALESCE(array_agg(es.nombre || ' ' || es.apellido ORDER BY ie.id) FILTER (WHERE ie.id IS NOT NULL), '{}') AS estudiantes
                FROM inscripcion i
                JOIN evento e ON e.id = i.id_evento
                JOIN estado_inscripcion ei ON ei.id = i.id_estado
                LEFT JOIN inscripcion_estudiante ie ON ie.id_inscripcion = i.id AND ie.estado = true
                LEFT JOIN estudiante es ON es.id = ie.id_estudiante
                WHERE i.id_colegio = %s AND i.estado = true
                GROUP BY i.id, e.nombre, e.fecha_inicio, ei.nombre
                ORDER BY i.creado DESC LIMIT 500;
            """, (id_colegio,))
            return cursor.fetchall()

    # ---------------- Organizador ----------------
    def obtener_del_organizador(self, id_organizador: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id, e.nombre AS evento, i.id_evento, c.nombre AS colegio,
                       (SELECT count(*) FROM inscripcion_estudiante ie WHERE ie.id_inscripcion = i.id AND ie.estado = true) AS estudiantes,
                       ei.nombre AS estado, i.creado AS creada_en
                FROM inscripcion i
                JOIN evento e ON e.id = i.id_evento
                JOIN colegio c ON c.id = i.id_colegio
                JOIN estado_inscripcion ei ON ei.id = i.id_estado
                WHERE e.id_organizador = %s AND i.estado = true
                ORDER BY i.creado DESC LIMIT 1000;
            """, (id_organizador,))
            return cursor.fetchall()

    def obtener_por_id(self, inscripcion_id: int, id_organizador: int):
        """Solo si la inscripcion es de un evento de ESTE organizador."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id, i.id_evento, ei.nombre AS estado FROM inscripcion i
                JOIN evento e ON e.id = i.id_evento JOIN estado_inscripcion ei ON ei.id = i.id_estado
                WHERE i.id = %s AND e.id_organizador = %s AND i.estado = true;
            """, (inscripcion_id, id_organizador))
            return cursor.fetchone()

    def decidir(self, inscripcion: dict, estado: str, id_usuario: int, ip: str | None):
        """Acepta o rechaza. Devuelve False si se quiere aceptar y ya no hay cupo de colegios aceptados."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if estado == "aceptada":
                cursor.execute(BLOQUEAR_EVENTO, (inscripcion["id_evento"],))
                cupo = cursor.fetchone()["cupo_colegios"]
                cursor.execute(CONTAR.format(condicion="= 'aceptada'"), (inscripcion["id_evento"],))
                if cursor.fetchone()["n"] >= cupo:
                    return False
            cursor.execute("""
                UPDATE inscripcion SET id_estado = (SELECT id FROM estado_inscripcion WHERE nombre = %s), actualizado = now()
                WHERE id = %s;
            """, (estado, inscripcion["id"]))
            auditar(cursor, id_usuario, f"inscripcion_{estado}", "inscripcion", inscripcion["id"], ip)
            return True

    # ---------------- Asistencia ----------------
    def obtener_asistencia(self, evento_id: int):
        """Estudiantes de las inscripciones ACEPTADAS, agrupados por colegio."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id AS id_inscripcion, c.nombre AS colegio, ie.id AS id_inscripcion_estudiante,
                       es.nombre || ' ' || es.apellido AS nombre, g.nombre AS grado, ie.asistio
                FROM inscripcion i
                JOIN estado_inscripcion ei ON ei.id = i.id_estado
                JOIN colegio c ON c.id = i.id_colegio
                JOIN inscripcion_estudiante ie ON ie.id_inscripcion = i.id AND ie.estado = true
                JOIN estudiante es ON es.id = ie.id_estudiante
                JOIN grado g ON g.id = es.id_grado
                WHERE i.id_evento = %s AND i.estado = true AND ei.nombre = 'aceptada'
                ORDER BY i.id, ie.id;
            """, (evento_id,))
            grupos = {}
            for f in cursor.fetchall():
                grupo = grupos.setdefault(f["id_inscripcion"], {"id_inscripcion": f["id_inscripcion"], "colegio": f["colegio"], "estudiantes": []})
                grupo["estudiantes"].append({k: f[k] for k in ("id_inscripcion_estudiante", "nombre", "grado", "asistio")})
            return list(grupos.values())

    def guardar_asistencia(self, evento_id: int, marcas: list, id_usuario: int, ip: str | None):
        """Todas las marcas o ninguna. Devuelve False si alguna no es de este evento."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for m in marcas:
                # El filtro por evento impide marcar asistencia de inscripciones de otros eventos.
                cursor.execute("""
                    UPDATE inscripcion_estudiante ie SET asistio = %s, actualizado = now()
                    FROM inscripcion i
                    WHERE ie.id = %s AND i.id = ie.id_inscripcion AND i.id_evento = %s AND ie.estado = true
                    RETURNING ie.id;
                """, (m.asistio, m.id_inscripcion_estudiante, evento_id))
                if cursor.fetchone() is None:
                    conn.rollback()  # deshace las marcas anteriores de esta misma peticion
                    return False
            auditar(cursor, id_usuario, "guardar_asistencia", "evento", evento_id, ip)
            return True

    # ---------------- Reportes ----------------
    def reporte_colegios(self, evento_id: int, id_usuario: int, ip: str | None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.nombre AS evento, c.nombre AS colegio, c.nit, ei.nombre AS estado,
                       (SELECT count(*) FROM inscripcion_estudiante ie WHERE ie.id_inscripcion = i.id AND ie.estado = true) AS estudiantes
                FROM inscripcion i
                JOIN evento e ON e.id = i.id_evento
                JOIN colegio c ON c.id = i.id_colegio
                JOIN estado_inscripcion ei ON ei.id = i.id_estado
                WHERE i.id_evento = %s AND i.estado = true ORDER BY i.id;
            """, (evento_id,))
            filas = cursor.fetchall()
            auditar(cursor, id_usuario, "descargar_reporte_colegios", "evento", evento_id, ip)
            return filas

    def reporte_estudiantes(self, evento_id: int, id_usuario: int, ip: str | None):
        """Sin documento: dato minimo necesario para el organizador. Son datos de menores: queda auditado."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.nombre AS evento, c.nombre AS colegio, es.nombre || ' ' || es.apellido AS estudiante, g.nombre AS grado, ie.asistio
                FROM inscripcion i
                JOIN estado_inscripcion ei ON ei.id = i.id_estado
                JOIN evento e ON e.id = i.id_evento
                JOIN colegio c ON c.id = i.id_colegio
                JOIN inscripcion_estudiante ie ON ie.id_inscripcion = i.id AND ie.estado = true
                JOIN estudiante es ON es.id = ie.id_estudiante
                JOIN grado g ON g.id = es.id_grado
                WHERE i.id_evento = %s AND i.estado = true AND ei.nombre = 'aceptada'
                ORDER BY i.id, ie.id;
            """, (evento_id,))
            filas = cursor.fetchall()
            auditar(cursor, id_usuario, "descargar_reporte_estudiantes", "evento", evento_id, ip)
            return filas
