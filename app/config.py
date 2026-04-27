import base64
import os
import re
from pathlib import Path
from typing import Optional
from pydantic import AliasChoices, Field, field_validator
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
    mysql_url: str = Field(
        "mysql+pymysql://user:pass@host/db",
        validation_alias=AliasChoices("MYSQL_URL", "DATABASE_URL", "mysql_url", "database_url"),
    )
    
    # Localización de logs
    logs_path: str = Field("./project.log", validation_alias=AliasChoices("LOGS_PATH", "logs_path"))

    # Configuración de App
    debug: bool = Field(True, validation_alias=AliasChoices("DEBUG", "debug"))
    environment: str = Field("production", validation_alias=AliasChoices("ENVIRONMENT", "environment"))
    init_db_on_startup: bool = Field(
        False,
        validation_alias=AliasChoices("INIT_DB_ON_STARTUP", "init_db_on_startup"),
    )
    root_path: str = Field("/api", validation_alias=AliasChoices("ROOT_PATH", "root_path"))
    logging_level: Optional[str] = Field("DEBUG", validation_alias=AliasChoices("LOGGING_LEVEL", "logging_level"))
    allowed_origins: str = Field(
        "*",
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "allowed_origins"),
    ) # Cambiar a una lista de URLs permitidas en producción, separadas por comas

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
