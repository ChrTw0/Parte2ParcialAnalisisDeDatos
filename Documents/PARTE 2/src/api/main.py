"""
FastAPI Application - API principal
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from loguru import logger

from ..config import settings
from ..models import BancoEnum, TarifarioURL, ScrapingResult
from ..scrapers import (
    BBVAScraper,
    BCPScraper,
    InterbankScraper,
    ScotiabankScraper,
    BancoNacionScraper
)
from ..utils import PDFDownloader, setup_logger

# Configurar logger
setup_logger()

# Crear app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para scraping y descarga de tarifarios bancarios del Perú"
)


@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    logger.info("Cerrando aplicación")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "proyecto": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "estado": "activo"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.get("/bancos", response_model=List[str])
async def listar_bancos():
    """Lista todos los bancos disponibles"""
    return [banco.value for banco in BancoEnum]


@app.post("/scrape/{banco}", response_model=ScrapingResult)
async def scrape_banco(banco: BancoEnum):
    """
    Scrapea las URLs de PDFs de un banco específico
    """
    try:
        logger.info(f"Iniciando scraping de {banco.value}")

        # Seleccionar scraper según banco
        scrapers = {
            BancoEnum.BBVA: BBVAScraper,
            BancoEnum.BCP: BCPScraper,
            BancoEnum.INTERBANK: InterbankScraper,
            BancoEnum.SCOTIABANK: ScotiabankScraper,
            BancoEnum.BANCO_NACION: BancoNacionScraper
        }

        scraper_class = scrapers.get(banco)
        if not scraper_class:
            raise HTTPException(status_code=400, detail=f"Banco no soportado: {banco}")

        # Ejecutar scraping
        import time
        inicio = time.time()

        with scraper_class() as scraper:
            urls = scraper.obtener_urls()

        duracion = time.time() - inicio

        resultado = ScrapingResult(
            banco=banco,
            urls_encontradas=urls,
            total_urls=len(urls),
            duracion_segundos=duracion,
            exito=True
        )

        logger.success(f"Scraping completado: {len(urls)} URLs encontradas en {duracion:.2f}s")
        return resultado

    except Exception as e:
        logger.error(f"Error en scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download/{banco}")
async def descargar_pdfs_banco(banco: BancoEnum):
    """
    Scrapea y descarga todos los PDFs de un banco
    """
    try:
        logger.info(f"Iniciando descarga de tarifarios de {banco.value}")

        # Scraping
        scrapers = {
            BancoEnum.BBVA: BBVAScraper,
            BancoEnum.BCP: BCPScraper,
            BancoEnum.INTERBANK: InterbankScraper,
            BancoEnum.SCOTIABANK: ScotiabankScraper,
            BancoEnum.BANCO_NACION: BancoNacionScraper
        }

        scraper_class = scrapers.get(banco)
        if not scraper_class:
            raise HTTPException(status_code=400, detail=f"Banco no soportado: {banco}")

        with scraper_class() as scraper:
            urls = scraper.obtener_urls()

        if not urls:
            return {
                "banco": banco.value,
                "total_urls": 0,
                "descargados": 0,
                "errores": [],
                "mensaje": "No se encontraron PDFs para descargar"
            }

        # Descargar
        downloader = PDFDownloader()
        resultados_exitosos = []
        errores = []

        for url in urls:
            resultado = downloader.descargar(url)
            if resultado.exito:
                resultados_exitosos.append(resultado.metadata)
            else:
                errores.append(f"{url.texto}: {resultado.error}")

        return {
            "banco": banco.value,
            "total_urls": len(urls),
            "descargados": len(resultados_exitosos),
            "errores": errores,
            "metadata": [meta.dict() for meta in resultados_exitosos]
        }

    except Exception as e:
        logger.error(f"Error en descarga: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download/all")
async def descargar_todos():
    """
    Descarga todos los tarifarios de todos los bancos
    """
    resultados = {}

    for banco in BancoEnum:
        try:
            resultado = await descargar_pdfs_banco(banco)
            resultados[banco.value] = resultado
        except Exception as e:
            logger.error(f"Error descargando {banco.value}: {e}")
            resultados[banco.value] = {
                "error": str(e),
                "descargados": 0
            }

    return {
        "resultados": resultados,
        "total_bancos": len(BancoEnum),
        "total_descargados": sum(r.get("descargados", 0) for r in resultados.values())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
