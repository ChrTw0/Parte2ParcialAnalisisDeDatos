"""
Configuración de logging con loguru
"""
import sys
from pathlib import Path
from loguru import logger
from ..config import settings


def setup_logger(log_file: str = "tarifarios_scraper.log"):
    """
    Configura el logger de la aplicación
    """
    # Remover handler por defecto
    logger.remove()

    # Console handler con colores
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO"
    )

    # File handler
    log_path = settings.LOGS_DIR / log_file
    logger.add(
        log_path,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

    logger.info("Logger configurado correctamente")
    return logger
