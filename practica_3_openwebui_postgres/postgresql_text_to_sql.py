"""
title: PostgreSQL Text-to-SQL
description: Ejecuta consultas SELECT de solo lectura contra PostgreSQL (base de datos "prueba")
"""

import psycopg2
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        host: str = Field(default="localhost", description="Host de Postgres")
        port: int = Field(default=5432)
        dbname: str = Field(default="biblioteca_db2")
        user: str = Field(default="postgres")
        password: str = Field(
            default="",
            description="Configura esto en el panel de Valves, no aquí",
        )
        max_rows: int = Field(default=50, description="Filas máximas devueltas")

    def __init__(self):
        self.valves = self.Valves()

    def get_schema(self) -> str:
        """
        Devuelve las tablas, columnas y tipos de datos de la base de datos.
        Úsala SIEMPRE antes de generar una consulta SQL para conocer los nombres reales de tablas y columnas.
        """
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        rows = self._run(query)
        if not rows:
            return "No se encontraron tablas en el esquema public."
        out = {}
        for t, c, d in rows:
            out.setdefault(t, []).append(f"{c} ({d})")
        return "\n".join(f"{t}: {', '.join(cols)}" for t, cols in out.items())

    def run_sql_query(self, sql_query: str) -> str:
        """
        Ejecuta una consulta SQL de tipo SELECT contra la base de datos PostgreSQL y devuelve el resultado.
        SOLO se permiten sentencias SELECT. No uses INSERT, UPDATE, DELETE, DROP ni ALTER.
        :param sql_query: La consulta SQL en formato SELECT a ejecutar.
        """
        cleaned = sql_query.strip().rstrip(";")
        if not cleaned.lower().startswith("select"):
            return "Error: solo se permiten consultas SELECT."
        try:
            rows = self._run(cleaned)
        except Exception as e:
            return f"Error ejecutando la consulta: {e}"
        if not rows:
            return "La consulta no devolvió resultados."
        rows = rows[: self.valves.max_rows]
        return "\n".join(str(r) for r in rows)

    def _run(self, query: str):
        conn = psycopg2.connect(
            host=self.valves.host,
            port=self.valves.port,
            dbname=self.valves.dbname,
            user=self.valves.user,
            password=self.valves.password,
            options="-c statement_timeout=5000",
        )
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        finally:
            conn.close()
