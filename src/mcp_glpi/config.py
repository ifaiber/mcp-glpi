"""Configuración del servidor MCP GLPI usando variables de entorno."""

import os
from pathlib import Path
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Cargar archivo .env si existe
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

class GLPIConfig(BaseSettings):
    """Configuración de GLPI usando variables de entorno."""
    
    # Configuración GLPI
    url: str = "http://localhost"
    app_token: str = ""
    user_token: str = ""
    
    # Configuración del servidor MCP
    server_name: str = "mcp-glpi"
    server_version: str = "0.1.0"
    debug_mode: bool = False
    
    # Timeout para requests
    request_timeout: int = 30
    
    model_config = SettingsConfigDict(
        env_prefix="GLPI_",
        case_sensitive=False
    )
    
    @field_validator('app_token', 'user_token')
    @classmethod
    def tokens_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError('Token no puede estar vacío')
        return v
    
    @field_validator('url')
    @classmethod
    def url_must_be_valid(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL debe comenzar con http:// o https://')
        return v.rstrip('/')

# Instancia global de configuración
config = GLPIConfig()

def get_config() -> GLPIConfig:
    """Obtiene la configuración actual."""
    return config

def validate_config() -> bool:
    """Valida que la configuración sea correcta."""
    try:
        config_test = GLPIConfig()
        return True
    except Exception as e:
        print(f"Error de configuración: {e}")
        return False