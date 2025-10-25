"""
Punto de entrada para ejecutar el servicio del visor de datos.
"""
import uvicorn
import os

# Añadir el directorio raíz al sys.path para permitir importaciones como 'from src.api...'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.data_viewer_api import app

if __name__ == "__main__":
    # Obtener el puerto desde una variable de entorno o usar 8000 por defecto
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "src.api.data_viewer_api:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )
