#!/usr/bin/env python3
"""
Script para convertir PDFs a imágenes PNG en paralelo
Optimizado para Intel i9-13900H (20 threads)
"""
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdf2image import convert_from_path
from PIL import Image
from tqdm import tqdm
from loguru import logger
import time

# Configuración
MAX_WORKERS = 16  # Usar 16 hilos (dejar 4 threads libres)
DPI = 300  # Calidad de imagen (300 DPI = buena calidad)
OUTPUT_DIR = Path("data/images")

def convertir_pdf_a_png(pdf_path: Path) -> dict:
    """
    Convierte un PDF a imágenes PNG (una por página)

    Returns:
        dict con estadísticas de conversión
    """
    resultado = {
        "pdf": pdf_path.name,
        "paginas": 0,
        "exito": False,
        "error": None,
        "tiempo": 0
    }

    start_time = time.time()

    try:
        # Determinar banco desde la ruta
        banco = pdf_path.parent.name

        # Crear carpeta de salida: data/images/{banco}/{nombre_pdf}/
        pdf_name = pdf_path.stem  # Nombre sin extensión
        output_folder = OUTPUT_DIR / banco / pdf_name
        output_folder.mkdir(parents=True, exist_ok=True)

        # Convertir PDF a imágenes
        # poppler_path: Descomentar y ajustar si poppler no está en PATH
        imagenes = convert_from_path(
            pdf_path,
            dpi=DPI,
            # poppler_path=r"C:\path\to\poppler\bin"  # Ajustar si es necesario
        )

        # Guardar cada página como PNG
        for i, imagen in enumerate(imagenes, start=1):
            output_path = output_folder / f"pagina_{i:03d}.png"
            imagen.save(output_path, "PNG", optimize=True)

        resultado["paginas"] = len(imagenes)
        resultado["exito"] = True
        resultado["tiempo"] = time.time() - start_time

        logger.info(f"✅ {pdf_path.name}: {len(imagenes)} páginas ({resultado['tiempo']:.2f}s)")

    except Exception as e:
        resultado["error"] = str(e)
        resultado["tiempo"] = time.time() - start_time
        logger.error(f"❌ {pdf_path.name}: {e}")

    return resultado


def main():
    """Procesa todos los PDFs en data/raw/ en paralelo"""

    logger.info("=" * 70)
    logger.info("🔄 CONVERSIÓN DE PDFs A IMÁGENES PNG")
    logger.info("=" * 70)
    logger.info(f"Configuración:")
    logger.info(f"  - Hilos paralelos: {MAX_WORKERS}")
    logger.info(f"  - DPI: {DPI}")
    logger.info(f"  - Directorio salida: {OUTPUT_DIR}")
    logger.info("=" * 70)

    # Buscar todos los PDFs en data/raw/
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        logger.error(f"❌ Directorio {raw_dir} no existe")
        return

    # Obtener lista de PDFs
    pdfs = list(raw_dir.rglob("*.pdf"))

    if not pdfs:
        logger.error("❌ No se encontraron PDFs en data/raw/")
        return

    logger.info(f"📄 Total de PDFs encontrados: {len(pdfs)}")

    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Procesar PDFs en paralelo con ThreadPoolExecutor
    resultados = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Enviar trabajos
        futures = {executor.submit(convertir_pdf_a_png, pdf): pdf for pdf in pdfs}

        # Procesar resultados con barra de progreso
        with tqdm(total=len(pdfs), desc="Convirtiendo PDFs", unit="pdf") as pbar:
            for future in as_completed(futures):
                resultado = future.result()
                resultados.append(resultado)
                pbar.update(1)

    # Estadísticas finales
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN DE CONVERSIÓN")
    logger.info("=" * 70)

    exitosos = [r for r in resultados if r["exito"]]
    fallidos = [r for r in resultados if not r["exito"]]
    total_paginas = sum(r["paginas"] for r in exitosos)
    tiempo_total = sum(r["tiempo"] for r in resultados)

    logger.info(f"PDFs procesados:     {len(pdfs)}")
    logger.info(f"Conversiones exitosas: {len(exitosos)} ✅")
    logger.info(f"Conversiones fallidas: {len(fallidos)} ❌")
    logger.info(f"Total de páginas:    {total_paginas}")
    logger.info(f"Tiempo total:        {tiempo_total:.2f}s")
    logger.info(f"Promedio por PDF:    {tiempo_total/len(pdfs):.2f}s")

    if fallidos:
        logger.warning("\n⚠️ PDFs con errores:")
        for r in fallidos:
            logger.warning(f"  - {r['pdf']}: {r['error']}")

    logger.info("=" * 70)
    logger.info(f"✅ Imágenes guardadas en: {OUTPUT_DIR}/")
    logger.info("=" * 70)

    # Guardar reporte
    import json
    reporte = {
        "total_pdfs": len(pdfs),
        "exitosos": len(exitosos),
        "fallidos": len(fallidos),
        "total_paginas": total_paginas,
        "tiempo_total_segundos": tiempo_total,
        "configuracion": {
            "max_workers": MAX_WORKERS,
            "dpi": DPI
        },
        "resultados": resultados
    }

    reporte_path = Path("data/processed/reporte_conversion_png.json")
    reporte_path.parent.mkdir(parents=True, exist_ok=True)

    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Reporte guardado en: {reporte_path}")


if __name__ == "__main__":
    main()
