from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos: las lee app/core/database.py (guia del profesor); aqui solo se exige que esten
    db_host: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int = 5432
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
    def origenes_permitidos(self) -> list[str]:
        return [u.strip() for u in self.frontend_url.split(",") if u.strip()]


settings = Settings()
