"""
Modelos de datos para tarifarios
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field


class BancoEnum(str, Enum):
    """Bancos soportados"""
    BBVA = "BBVA Continental"
    BCP = "BCP"
    INTERBANK = "Interbank"
    SCOTIABANK = "Scotiabank"
    BANCO_NACION = "Banco de la Nación"


class TarifarioURL(BaseModel):
    """URL de un tarifario"""
    url: str
    texto: str = Field(description="Texto descriptivo del enlace")
    tipo_producto: Optional[str] = Field(None, description="Tipo de producto (tarjeta, préstamo, etc.)")
    banco: BancoEnum


class TarifarioMetadata(BaseModel):
    """Metadata de un tarifario descargado"""
    banco: BancoEnum
    nombre_archivo: str
    url_origen: str
    fecha_descarga: datetime = Field(default_factory=datetime.now)
    tamaño_bytes: int
    hash_md5: Optional[str] = None
    tipo_producto: Optional[str] = None
    valido: bool = True
    error: Optional[str] = None


class ScrapingResult(BaseModel):
    """Resultado de un proceso de scraping"""
    banco: BancoEnum
    urls_encontradas: List[TarifarioURL]
    total_urls: int
    fecha_scraping: datetime = Field(default_factory=datetime.now)
    duracion_segundos: float
    exito: bool
    errores: List[str] = Field(default_factory=list)


class DownloadResult(BaseModel):
    """Resultado de una descarga de PDF"""
    metadata: TarifarioMetadata
    ruta_archivo: str
    exito: bool
    error: Optional[str] = None
