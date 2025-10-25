"""
Archivo principal de la aplicación FastAPI para el visor de datos.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.api.endpoints import viewer_endpoints

# --- Creación de la App ---
app = FastAPI(
    title="Visor de Tarifarios Bancarios",
    version="1.0.0",
    description="Una interfaz para explorar los datos de tarifarios extraídos."
)

# --- Rutas de la API ---
# Incluir los endpoints definidos en el router
app.include_router(viewer_endpoints.router)

# --- Configuración de Archivos Estáticos y Plantillas ---

# Obtener la ruta base del proyecto de forma robusta
BASE_DIR = Path(__file__).resolve().parent

# Montar el directorio 'static' para servir CSS y JS
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Configurar el motor de plantillas Jinja2 para servir el index.html
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# --- Endpoint para servir el Frontend ---

@app.get("/", include_in_schema=False)
async def serve_frontend(request: Request):
    """Sirve el archivo index.html como la interfaz principal."""
    return templates.TemplateResponse("index.html", {"request": request})
