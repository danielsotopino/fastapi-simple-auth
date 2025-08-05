import structlog
import logging
import sys
import os
from structlog.stdlib import add_log_level, PositionalArgumentsFormatter
from structlog.processors import JSONRenderer, TimeStamper
from typing import Any, Dict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    # Database
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # JWT
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_USE_ENV_VAR"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email
    EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS: int = 24
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configura structlog para la aplicación FastAPI
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        json_logs: Si usar formato JSON o formato legible para desarrollo
    """
    
    # Configurar el logging estándar de Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Procesadores comunes
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if json_logs:
        # Procesadores para producción (JSON)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Procesadores para desarrollo (más legible)
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # Configurar structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
