from fastapi import Request


def ip_de(request: Request) -> str | None:
    return request.client.host if request.client else None


def auditar(cursor, id_usuario: int | None, accion: str, tabla: str, registro_id: int, ip: str | None):
    """Registra una accion en la tabla auditoria. Usa el cursor del cambio: misma transaccion, o se guardan los dos o ninguno."""
    cursor.execute("INSERT INTO auditoria (id_usuario, accion, tabla, registro_id, ip) VALUES (%s, %s, %s, %s, %s);",
                   (id_usuario, accion, tabla, registro_id, ip))
