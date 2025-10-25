"""
Endpoints de la API para el visor de tarifarios.
"""
from fastapi import APIRouter, Query, Response
from pathlib import Path
from typing import Optional

from src.core.viewer_models import PaginatedTarifariosResponse, StatsResponse, FilterOptionsResponse
from src.services.viewer_service import ViewerService

# --- Configuración del Router ---
router = APIRouter(
    prefix="/api/v1",
    tags=["Visor de Tarifarios"],
)

# --- Instancia del Servicio ---
# Apuntar a la ruta correcta del CSV de salida
CSV_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "output" / "tarifarios_bancarios.csv"
service = ViewerService(csv_path=CSV_PATH)

# --- Endpoints ---

@router.get("/export/csv")
def export_to_csv(
    banco: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    moneda: Optional[str] = Query(None),
    producto: Optional[str] = Query(None),
    concepto: Optional[str] = Query(None),
    tasa_mn_gte: Optional[float] = Query(None),
    tasa_mn_lte: Optional[float] = Query(None),
    tasa_me_gte: Optional[float] = Query(None),
    tasa_me_lte: Optional[float] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query('asc')
):
    """Exporta los datos filtrados a un archivo CSV."""
    kwargs = locals()
    filtered_df = service._get_filtered_df(**kwargs)
    
    csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=tarifarios_filtrados.csv"
        }
    )

@router.get("/tarifarios", response_model=PaginatedTarifariosResponse)
def get_all_tarifarios(
    skip: int = 0,
    limit: int = 20,
    banco: Optional[str] = Query(None, description="Filtrar por banco"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (TASA, COMISION, etc.)"),
    moneda: Optional[str] = Query(None, description="Filtrar por moneda (MN, ME, AMBAS)"),
    producto: Optional[str] = Query(None, description="Buscar texto en el nombre del producto"),
    concepto: Optional[str] = Query(None, description="Buscar texto en el concepto"),
    tasa_mn_gte: Optional[float] = Query(None, description="Tasa MN mayor o igual que"),
    tasa_mn_lte: Optional[float] = Query(None, description="Tasa MN menor o igual que"),
    tasa_me_gte: Optional[float] = Query(None, description="Tasa ME mayor o igual que"),
    tasa_me_lte: Optional[float] = Query(None, description="Tasa ME menor o igual que"),
    sort_by: Optional[str] = Query(None, description="Columna por la cual ordenar"),
    sort_order: str = Query('asc', description="Orden de clasificación ('asc' o 'desc')")
):
    """Obtiene una lista paginada y filtrada de todos los items del tarifario."""
    data = service.get_tarifarios(
        skip=skip, 
        limit=limit, 
        banco=banco, 
        tipo=tipo, 
        moneda=moneda, 
        producto=producto, 
        concepto=concepto,
        tasa_mn_gte=tasa_mn_gte,
        tasa_mn_lte=tasa_mn_lte,
        tasa_me_gte=tasa_me_gte,
        tasa_me_lte=tasa_me_lte,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return data

@router.get("/stats", response_model=StatsResponse)
def get_statistics():
    """Obtiene estadísticas generales del conjunto de datos."""
    stats = service.get_stats()
    return stats

@router.get("/filters", response_model=FilterOptionsResponse)
def get_filter_options():
    """Obtiene los valores únicos para poblar los controles de filtro en la UI."""
    options = service.get_filter_options()
    return options
