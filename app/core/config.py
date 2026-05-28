from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/mon_compagnon"

    # JWT
    SECRET_KEY: str = "changez-moi-minimum-32-caracteres-aleatoires"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 jours

    # Application
    APP_NAME: str = "Mon Compagnon API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Cloudinary — stockage images
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Bail
    BAIL_ALERTE_JOURS: int = 30

    # Serveur
    PORT: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
