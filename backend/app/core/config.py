from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos: las mismas 5 variables que usa app/core/database.py (guia del profesor)
    db_host: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int = 5432
    db_sslmode: str = ""  # opcional, igual que en database.py
    secret_key: str
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = True   # cookie solo por HTTPS
    forzar_https: bool = False   # redirige http -> https (true en produccion)
    docs_habilitada: bool = True  # Swagger en /docs (necesario para demostrar los endpoints)

    class Config:
        env_file = ".env"
        extra = "ignore"  # el .env puede traer variables de otras partes

    @property
    def database_url(self) -> str:
        # TEMPORAL: solo para el codigo viejo con SQLAlchemy (se borra en la limpieza del backend).
        return (f"postgresql+psycopg2://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}" + (f"?sslmode={self.db_sslmode}" if self.db_sslmode else ""))

    @property
    def origenes_permitidos(self) -> list[str]:
        return [u.strip() for u in self.frontend_url.split(",") if u.strip()]


settings = Settings()
