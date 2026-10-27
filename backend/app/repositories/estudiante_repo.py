from app.core.auditoria import auditar
from app.core.database import Database
from app.models.estudiante import EstudianteEdita, EstudianteNuevo

# Columnas que se devuelven al frontend (grado por nombre, no por id)
COLUMNAS = "id, nombre, apellido, documento, (SELECT nombre FROM grado WHERE grado.id = id_grado) AS grado"


class EstudianteRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    def obtener_todos(self, id_colegio: int):
        """Solo los estudiantes del colegio que pregunta (nunca los de otro colegio)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {COLUMNAS} FROM estudiante
                WHERE id_colegio = %s AND estado = true
                ORDER BY apellido, nombre LIMIT 1000;
            """, (id_colegio,))
            return cursor.fetchall()

    def obtener_por_id(self, estudiante_id: int, id_colegio: int):
        """Solo si es de ESTE colegio y existe (estado = true)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {COLUMNAS} FROM estudiante WHERE id = %s AND id_colegio = %s AND estado = true;",
                           (estudiante_id, id_colegio))
            return cursor.fetchone()

    def grado_valido(self, id_grado: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM grado WHERE id = %s AND estado = true;", (id_grado,))
            return cursor.fetchone() is not None

    def crear(self, id_colegio: int, estudiante: EstudianteNuevo, id_usuario: int, ip: str | None):
        """Estudiante + autorizacion del acudiente en la misma transaccion (o se guardan los dos, o ninguno)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO estudiante (id_colegio, id_grado, nombre, apellido, documento)
                VALUES (%s, %s, %s, %s, %s) RETURNING {COLUMNAS};
            """, (id_colegio, estudiante.id_grado, estudiante.nombre, estudiante.apellido, estudiante.documento))
            nuevo = cursor.fetchone()
            cursor.execute("INSERT INTO autorizacion_acudiente (id_estudiante, nombre_acudiente, vigente) VALUES (%s, %s, true);",
                           (nuevo["id"], estudiante.nombre_acudiente))
            auditar(cursor, id_usuario, "crear_estudiante", "estudiante", nuevo["id"], ip)
            return nuevo

    def actualizar(self, estudiante_id: int, id_colegio: int, estudiante: EstudianteEdita, id_usuario: int, ip: str | None):
        """Devuelve None si no es de este colegio (o no existe): nunca se edita un estudiante ajeno."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE estudiante SET nombre = %s, apellido = %s, documento = COALESCE(%s, documento), id_grado = %s, actualizado = now()
                WHERE id = %s AND id_colegio = %s AND estado = true RETURNING {COLUMNAS};
            """, (estudiante.nombre, estudiante.apellido, estudiante.documento, estudiante.id_grado, estudiante_id, id_colegio))
            actualizado = cursor.fetchone()
            if actualizado:
                auditar(cursor, id_usuario, "editar_estudiante", "estudiante", estudiante_id, ip)
            return actualizado

    def eliminar(self, estudiante_id: int, id_colegio: int, id_usuario: int, ip: str | None):
        """Borrado logico. Filtra por id_colegio: un colegio no puede tocar estudiantes de otro (evita IDOR)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE estudiante SET estado = false, actualizado = now()
                WHERE id = %s AND id_colegio = %s AND estado = true RETURNING id;
            """, (estudiante_id, id_colegio))
            if cursor.fetchone() is None:
                return False
            auditar(cursor, id_usuario, "retirar_estudiante", "estudiante", estudiante_id, ip)
            return True
