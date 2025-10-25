#!/usr/bin/env python3
"""
Script para descargar todos los PDFs de tarifarios bancarios
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Agregar el directorio padre al path para poder importar src
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers import (
    BBVAScraper,
    BCPScraper,
    InterbankScraper,
    BancoNacionScraper,
    ScotiabankScraper
)
from src.utils.downloader import PDFDownloader
from src.models import BancoEnum
from loguru import logger


def descargar_banco(banco_enum, scraper_class, downloader):
    """Descarga PDFs de un banco específico"""
    print(f"\n{'='*70}")
    print(f"🏦 DESCARGANDO: {banco_enum.value}")
    print(f"{'='*70}")

    resultados = {
        "banco": banco_enum.value,
        "urls_encontradas": 0,
        "descargas_exitosas": 0,
        "descargas_fallidas": 0,
        "urls": []
    }

    try:
        # Scrapear URLs
        with scraper_class() as scraper:
            logger.info(f"Scrapeando URLs de {banco_enum.value}...")
            urls = scraper.obtener_urls()
            resultados["urls_encontradas"] = len(urls)

            print(f"✅ URLs encontradas: {len(urls)}")

            if not urls:
                print("⚠️  No hay URLs para descargar\n")
                return resultados

            # Descargar cada PDF
            print(f"\n📥 Iniciando descarga de {len(urls)} PDFs...")

            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] Descargando: {url.texto[:60]}...")

                resultado = downloader.descargar(url)

                if resultado.exito:
                    resultados["descargas_exitosas"] += 1
                    print(f"  ✅ Guardado en: {resultado.ruta_archivo}")
                else:
                    resultados["descargas_fallidas"] += 1
                    print(f"  ❌ Error: {resultado.error}")

                # Guardar info de la URL
                resultados["urls"].append({
                    "url": url.url,
                    "texto": url.texto,
                    "tipo_producto": url.tipo_producto,
                    "descargado": resultado.exito,
                    "archivo": resultado.ruta_archivo if resultado.exito else None,
                    "error": resultado.error if not resultado.exito else None
                })

            print(f"\n{'='*70}")
            print(f"📊 RESUMEN {banco_enum.value}")
            print(f"{'='*70}")
            print(f"  URLs encontradas:      {resultados['urls_encontradas']}")
            print(f"  Descargas exitosas:    {resultados['descargas_exitosas']} ✅")
            print(f"  Descargas fallidas:    {resultados['descargas_fallidas']} ❌")
            print(f"{'='*70}\n")

    except Exception as e:
        logger.error(f"Error procesando {banco_enum.value}: {e}")
        print(f"❌ Error: {e}\n")

    return resultados


def main():
    print("\n" + "="*70)
    print("📥 DESCARGA DE TARIFARIOS BANCARIOS")
    print("="*70)

    # Inicializar downloader
    downloader = PDFDownloader()

    # Resumen global
    resumen_global = {
        "fecha": datetime.now().isoformat(),
        "bancos": []
    }

    # Descargar cada banco
    bancos = [
        (BancoEnum.BBVA, BBVAScraper),
        (BancoEnum.BCP, BCPScraper),
        (BancoEnum.INTERBANK, InterbankScraper),
        (BancoEnum.BANCO_NACION, BancoNacionScraper),
        (BancoEnum.SCOTIABANK, ScotiabankScraper),
    ]

    for banco_enum, scraper_class in bancos:
        resultado = descargar_banco(banco_enum, scraper_class, downloader)
        resumen_global["bancos"].append(resultado)

    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN FINAL GLOBAL")
    print("="*70)

    total_urls = 0
    total_exitosas = 0
    total_fallidas = 0

    for banco in resumen_global["bancos"]:
        total_urls += banco["urls_encontradas"]
        total_exitosas += banco["descargas_exitosas"]
        total_fallidas += banco["descargas_fallidas"]

        print(f"  {banco['banco']:20s}: {banco['descargas_exitosas']:3d}/{banco['urls_encontradas']:3d} ✅")

    print(f"  {'─'*50}")
    print(f"  {'TOTAL':20s}: {total_exitosas:3d}/{total_urls:3d} PDFs descargados")
    print(f"  {'Fallidos':20s}: {total_fallidas:3d}")
    print("="*70)

    # Guardar reporte JSON
    reporte_path = PROJECT_ROOT / "data" / "processed" / "reporte_descarga.json"
    reporte_path.parent.mkdir(parents=True, exist_ok=True)

    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(resumen_global, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Reporte guardado en: {reporte_path}")
    print("\n✅ Descarga completada!\n")

    # Cerrar downloader
    downloader.cerrar()


if __name__ == "__main__":
    main()
