"""
Configuración global del proyecto
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # Project
    PROJECT_NAME: str = "Tarifarios Scraper API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"  # PDFs originales por banco
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"  # CSV/Excel procesados
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Legacy path (deprecado, usar RAW_DATA_DIR)
    TARIFARIOS_DIR: Path = RAW_DATA_DIR

    # Scraping
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30
    RETRY_ATTEMPTS: int = 3
    DELAY_BETWEEN_REQUESTS: float = 1.0

    # OCR
    TESSERACT_CMD: Optional[str] = None
    TESSDATA_PREFIX: Optional[str] = None
    OCR_LANG: str = "spa"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/tarifarios.db"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()

# Crear directorios si no existen
settings.DATA_DIR.mkdir(exist_ok=True)
settings.RAW_DATA_DIR.mkdir(exist_ok=True, parents=True)
settings.PROCESSED_DATA_DIR.mkdir(exist_ok=True, parents=True)
settings.LOGS_DIR.mkdir(exist_ok=True)
