from app.core.auditoria import auditar
from app.core.database import Database
from app.models.evento import Evento

# Reemplaza evento_out() + inscritos() de comun.py: el evento con sus nombres y los colegios inscritos (sin contar rechazados).
SELECT_EVENTO = """
    SELECT e.id, e.nombre, e.descripcion, e.lugar, ee.nombre AS estado, c.nombre AS categoria, o.nombre AS organizador,
           e.id_ciudad, e.fecha_inicio, e.fecha_fin, e.cupo_colegios, e.cupo_estudiantes,
           (SELECT count(*) FROM inscripcion i JOIN estado_inscripcion ei ON ei.id = i.id_estado
             WHERE i.id_evento = e.id AND i.estado = true AND ei.nombre <> 'rechazada') AS colegios_inscritos
    FROM evento e
    JOIN estado_evento ee ON ee.id = e.id_estado
    JOIN categoria_evento c ON c.id = e.id_categoria
    JOIN organizador o ON o.id = e.id_organizador
"""
# Columnas que el organizador puede escribir (salen del modelo Pydantic, nunca del usuario)
CAMPOS = list(Evento.model_fields)


class EventoRepository:
    def __init__(self):
        # Composición: El repositorio instancia su propia conexión
        self.db = Database()

    def obtener_todos(self, id_organizador: int | None = None, estado_evento: str | None = None):
        """Sin filtros: todos (administrador). Con id_organizador: solo los de ese organizador."""
        filtros, valores = ["e.estado = true"], []
        if id_organizador is not None:
            filtros.append("e.id_organizador = %s")
            valores.append(id_organizador)
        if estado_evento:
            filtros.append("ee.nombre = %s")
            valores.append(estado_evento)
        orden = "e.fecha_inicio DESC" if id_organizador is not None else "e.fecha_inicio"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{SELECT_EVENTO} WHERE {' AND '.join(filtros)} ORDER BY {orden} LIMIT 500;", valores)
            return cursor.fetchall()

    def obtener_disponibles(self, id_colegio: int, id_organizador: int):
        """Para el colegio: eventos PUBLICADOS del organizador que lo registro, con el estado de su inscripcion."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT ev.*,
                       (SELECT ei.nombre FROM inscripcion i JOIN estado_inscripcion ei ON ei.id = i.id_estado
                         WHERE i.id_evento = ev.id AND i.id_colegio = %s AND i.estado = true) AS mi_inscripcion
                FROM ({SELECT_EVENTO} WHERE e.estado = true AND ee.nombre = 'publicado' AND e.id_organizador = %s) ev
                ORDER BY ev.fecha_inicio LIMIT 500;
            """, (id_colegio, id_organizador))
            return cursor.fetchall()

    def obtener_por_id(self, evento_id: int, id_organizador: int | None = None):
        """Con id_organizador: solo si el evento es suyo (evita que un organizador toque eventos de otro)."""
        filtro, valores = "", [evento_id]
        if id_organizador is not None:
            filtro, valores = "AND e.id_organizador = %s", [evento_id, id_organizador]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"{SELECT_EVENTO} WHERE e.id = %s AND e.estado = true {filtro};", valores)
            return cursor.fetchone()

    def referencias_validas(self, id_categoria: int, id_ciudad: int):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (SELECT 1 FROM categoria_evento WHERE id = %s AND estado = true)
                   AND EXISTS (SELECT 1 FROM ciudad WHERE id = %s AND estado = true) AS ok;
            """, (id_categoria, id_ciudad))
            return cursor.fetchone()["ok"]

    def crear(self, id_organizador: int, evento: Evento, id_usuario: int, ip: str | None):
        """Todo evento nace en borrador."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO evento (id_organizador, id_estado, {', '.join(CAMPOS)})
                VALUES (%s, (SELECT id FROM estado_evento WHERE nombre = 'borrador'), {', '.join(['%s'] * len(CAMPOS))})
                RETURNING id;
            """, [id_organizador, *evento.model_dump().values()])
            nuevo_id = cursor.fetchone()["id"]
            auditar(cursor, id_usuario, "crear_evento", "evento", nuevo_id, ip)
        return self.obtener_por_id(nuevo_id)

    def actualizar(self, evento_id: int, evento: Evento, id_usuario: int, ip: str | None):
        """Editar devuelve el evento a borrador (hay que enviarlo de nuevo a aprobacion)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE evento SET {''.join(f'{c} = %s, ' for c in CAMPOS)}
                       id_estado = (SELECT id FROM estado_evento WHERE nombre = 'borrador'), actualizado = now()
                WHERE id = %s AND estado = true;
            """, [*evento.model_dump().values(), evento_id])
            auditar(cursor, id_usuario, "editar_evento", "evento", evento_id, ip)
        return self.obtener_por_id(evento_id)

    def cambiar_estado_evento(self, evento_id: int, nuevo: str, id_usuario: int, accion: str, ip: str | None,
                              aprobador: bool = False):
        """Mueve el evento a otro estado (pendiente, publicado, rechazado, cerrado).
        aprobador=True: guarda quien lo decidio y cuando (decision del administrador)."""
        extra = ", id_aprobador = %s, fecha_aprobacion = now()" if aprobador else ""
        valores = [nuevo, id_usuario, evento_id] if aprobador else [nuevo, evento_id]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE evento SET id_estado = (SELECT id FROM estado_evento WHERE nombre = %s){extra}, actualizado = now()
                WHERE id = %s AND estado = true;
            """, valores)
            auditar(cursor, id_usuario, accion, "evento", evento_id, ip)
        return self.obtener_por_id(evento_id)

    def eliminar(self, evento_id: int, id_usuario: int, ip: str | None):
        """Borrado logico: estado = false (la fila NO se borra)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE evento SET estado = false, actualizado = now() WHERE id = %s AND estado = true;", (evento_id,))
            auditar(cursor, id_usuario, "eliminar_evento", "evento", evento_id, ip)
