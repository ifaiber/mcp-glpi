"""Configuration for the MCP GLPI server."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


env_path = Path(__file__).resolve().parents[3] / ".env"
if env_path.exists():
    load_dotenv(env_path)


class GLPIConfig(BaseSettings):
    """GLPI configuration loaded from environment variables."""

    url: str = "http://localhost"
    app_token: str = ""
    user_token: str = ""
    request_timeout: int = 30

    model_config = SettingsConfigDict(env_prefix="GLPI_", case_sensitive=False)

    @field_validator("app_token", "user_token")
    @classmethod
    def tokens_must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Token no puede estar vacio")
        return value

    @field_validator("url")
    @classmethod
    def url_must_be_valid(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("URL debe comenzar con http:// o https://")
        return value.rstrip("/")


@lru_cache(maxsize=1)
def get_config() -> GLPIConfig:
    """Return the cached GLPI configuration."""

    return GLPIConfig()


def validate_config() -> bool:
    """Validate that the current environment can build a GLPI config."""

    try:
        get_config.cache_clear()
        get_config()
        return True
    except Exception as exc:
        print(f"Error de configuracion: {exc}")
        return False
