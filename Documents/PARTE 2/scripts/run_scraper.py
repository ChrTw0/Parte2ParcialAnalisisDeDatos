#!/usr/bin/env python3
"""
Script para ejecutar el scraping desde CLI
"""
import sys
import json
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import BancoEnum
from src.scrapers import (
    BBVAScraper,
    BCPScraper,
    InterbankScraper,
    ScotiabankScraper,
    BancoNacionScraper
)
from src.utils import PDFDownloader, setup_logger
from loguru import logger

# Configurar logger
setup_logger("scraper_cli.log")


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("SCRAPER DE TARIFARIOS BANCARIOS - Modo CLI")
    logger.info("=" * 60)

    scrapers = {
        BancoEnum.BBVA: BBVAScraper,
        BancoEnum.BCP: BCPScraper,
        BancoEnum.INTERBANK: InterbankScraper,
        BancoEnum.SCOTIABANK: ScotiabankScraper,
        BancoEnum.BANCO_NACION: BancoNacionScraper
    }

    todas_urls = []
    downloader = PDFDownloader()

    for banco, scraper_class in scrapers.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Procesando: {banco.value}")
        logger.info(f"{'='*60}")

        try:
            # Scraping
            with scraper_class() as scraper:
                urls = scraper.obtener_urls()

            logger.info(f"URLs encontradas: {len(urls)}")

            if urls:
                # Descargar
                exitosos = 0
                for url in urls:
                    resultado = downloader.descargar(url)
                    if resultado.exito:
                        exitosos += 1
                        todas_urls.append(url.dict())

                logger.success(f"Descargados: {exitosos}/{len(urls)}")
            else:
                logger.warning(f"No se encontraron PDFs para {banco.value}")

        except Exception as e:
            logger.error(f"Error procesando {banco.value}: {e}")
            continue

    # Guardar resumen
    resumen_path = Path("data") / "urls_scrapeadas.json"
    resumen_path.parent.mkdir(exist_ok=True)

    with open(resumen_path, 'w', encoding='utf-8') as f:
        json.dump(todas_urls, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*60}")
    logger.success(f"✅ Proceso completado")
    logger.info(f"Total URLs procesadas: {len(todas_urls)}")
    logger.info(f"Resumen guardado en: {resumen_path}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
