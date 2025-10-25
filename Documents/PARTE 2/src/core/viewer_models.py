"""
Modelos Pydantic para la API del visor de datos.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict

class TarifarioItem(BaseModel):
    """Modelo para un único item del tarifario en la respuesta de la API."""
    Banco: str
    Producto_Codigo: Optional[str]
    Producto_Nombre: Optional[str]
    Concepto: Optional[str]
    Descripcion_Breve: Optional[str]
    Tipo: Optional[str]
    Tasa_Porcentaje_MN: Optional[float] = None
    Tasa_Porcentaje_ME: Optional[float] = None
    Monto_Fijo_MN: Optional[float] = None
    Monto_Fijo_ME: Optional[float] = None
    Monto_Minimo_MN: Optional[float] = None
    Monto_Maximo_MN: Optional[float] = None
    Monto_Minimo_ME: Optional[float] = None
    Monto_Maximo_ME: Optional[float] = None
    Moneda: Optional[str]
    Fecha_Vigencia: Optional[str]
    Fecha_Extraccion: Optional[str]
    Periodicidad: Optional[str]
    Oportunidad_Cobro: Optional[str]
    Observaciones: Optional[str]

class PaginatedTarifariosResponse(BaseModel):
    """Modelo para la respuesta paginada de tarifarios."""
    total_items: int
    items: List[TarifarioItem]
    total_pages: int
    current_page: int

class StatsResponse(BaseModel):
    """Modelo para las estadísticas generales."""
    total_registros: int
    bancos_count: int
    tipos_count: Dict[str, int]
    tasa_promedio_mn: Optional[float]
    tasa_promedio_me: Optional[float]

class FilterOptionsResponse(BaseModel):
    """Modelo para las opciones de los filtros."""
    bancos: List[str]
    tipos: List[str]
    monedas: List[str]
