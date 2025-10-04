"""
Configuración centralizada de la aplicación.
Lee variables de entorno del archivo .env compartido con docker-compose.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class ApplicationConfig(BaseSettings):
    """Configuración principal de la aplicación usando Pydantic Settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Telegram
    telegram_bot_token: str = Field(..., min_length=40)
    
    # Database
    database_url: str = Field(...)
    postgres_user: str = Field(default="telegram_user")
    postgres_password: str = Field(..., min_length=8)
    postgres_db: str = Field(default="telegram_db")
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    
    # App
    log_level: str = Field(default="INFO")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    default_category: str = Field(default="sin_categoria")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        value_upper = value.upper()
        if value_upper not in valid_levels:
            raise ValueError(f"log_level inválido. Debe ser: {', '.join(valid_levels)}")
        return value_upper
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("database_url debe comenzar con 'postgresql://' o 'postgresql+asyncpg://'")
        return value


# Instancia global de configuración
config = ApplicationConfig()