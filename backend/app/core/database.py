import os
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carga las variables del archivo .env al entorno de Python
load_dotenv()


class ConexionQueSeCierra(connection):
    """Igual a la conexion normal de psycopg2, pero al salir de un "with" ademas la CIERRA.
    (psycopg2 solo hace commit/rollback al salir del with; sin esto quedarian conexiones abiertas en Neon.)
    Uso en los repositorios:  with self.db.get_connection() as conn:  -> commit si todo sale bien,
    rollback si hay error, y siempre close()."""

    def __exit__(self, tipo, valor, traza):
        try:
            return super().__exit__(tipo, valor, traza)
        finally:
            self.close()


class Database:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT")
        self.sslmode = os.getenv("DB_SSLMODE")  # opcional (ej. "require" para Neon); si no esta, no se envia

    def get_connection(self):
        extra = {"sslmode": self.sslmode} if self.sslmode else {}
        try:
            return psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port,
                cursor_factory=RealDictCursor,
                connection_factory=ConexionQueSeCierra,
                **extra,
            )
        except Exception as e:
            print(f"Error de conexión a la BD: {e}")
            return None
