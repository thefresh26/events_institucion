from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = True   # cookie solo por HTTPS
    forzar_https: bool = False   # redirige http -> https (true en produccion)

    class Config:
        env_file = ".env"

    @field_validator("database_url")
    @classmethod
    def usar_psycopg3(cls, v: str) -> str:
        # Neon entrega "postgresql://..."; SQLAlchemy lo leeria como psycopg2 (no instalado).
        return v.replace("postgresql://", "postgresql+psycopg://", 1) if v.startswith("postgresql://") else v

    @property
    def origenes_permitidos(self) -> list[str]:
        return [u.strip() for u in self.frontend_url.split(",") if u.strip()]


settings = Settings()
