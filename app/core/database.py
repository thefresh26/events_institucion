import psycopg
from psycopg.rows import dict_row

from app.core.config import settings


class Database:
    def __init__(self):
        # Una sola variable DATABASE_URL (Neon / Render) en vez de DB_HOST, DB_NAME, ... de la guia.
        # config.py le agrega "+psycopg" para SQLAlchemy; psycopg puro necesita la URL original.
        self.url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    def get_connection(self):
        # dict_row = RealDictCursor de psycopg2: cada fila llega como diccionario {"columna": valor}.
        # Usada con "with": hace commit si todo sale bien, rollback si hay error, y siempre cierra.
        return psycopg.connect(self.url, row_factory=dict_row)
