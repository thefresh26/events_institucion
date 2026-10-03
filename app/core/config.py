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

    @property
    def origenes_permitidos(self) -> list[str]:
        return [u.strip() for u in self.frontend_url.split(",") if u.strip()]


settings = Settings()
