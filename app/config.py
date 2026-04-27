import base64
import os
import re
from pathlib import Path
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def _expand_env_vars(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        env_value = os.environ.get(key)
        if env_value is None:
            raise ValueError(f"Falta la variable de entorno '{key}' para construir mysql_url")
        return env_value

    return _ENV_VAR_PATTERN.sub(replace, value)

class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent

    # Configuración de la base de datos
    mysql_url: str = "mysql+pymysql://user:pass@host/db"
    
    # Localización de logs
    logs_path: str = "./project.log"

    # Configuración de App
    debug: bool = True
    environment: str = "development"
    init_db_on_startup: bool = False
    root_path: str = "/api"
    logging_level: Optional[str] = 'DEBUG'
    allowed_origins: str = "*" # Cambiar a una lista de URLs permitidas en producción, separadas por comas

    ENCRYPTION_KEY: bytes = base64.b64encode(b"your-new-encryption-key-00000000")
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-it-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("mysql_url", mode="before")
    @classmethod
    def _normalize_mysql_url(cls, value):
        if isinstance(value, str) and "${" in value:
            return _expand_env_vars(value)
        return value

settings = Settings()
