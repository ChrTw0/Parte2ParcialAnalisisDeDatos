#!/usr/bin/env python3
"""
Regenera PNGs desde PDFs originales y reprocesa con OCR mejorado
"""
import os
import sys
from pathlib import Path
from loguru import logger
from pdf2image import convert_from_path

# Importar funciones del script principal
sys.path.insert(0, str(Path(__file__).parent))
from procesar_ocr_por_pagina import *

# Lista de PDFs corruptos a reprocesar
PDFS_A_REPROCESAR = [
    "BBVA_Continental/asesoria-juridica-ppjj",
    "BBVA_Continental/BANCA_ELECTRONICA_PJ.1_SWIFT",
    "BBVA_Continental/BANCA_ELECTRONICA_PJ.3_HOST_TO_HOST",
    "BBVA_Continental/BANCA-ELECTRONICA-NET-CASH-PN",
    "BBVA_Continental/cajas-de-seguridad-persona-juridica",
    "BBVA_Continental/cartas-fianza-pn",
    "BBVA_Continental/cobranza-libre-cobranza-garantia-personas-juridicas",
]


def limpiar_todo(banco: str, pdf_name: str):
    """Limpia TODOS los archivos previos (.md, .temp, PNGs)"""
    import shutil

    # Eliminar .md corrupto
    md_path = OUTPUT_DIR / banco / f"{pdf_name}.md"
    if md_path.exists():
        md_path.unlink()
        logger.debug(f"  🗑️  Eliminado .md corrupto")

    # Eliminar archivos temporales
    temp_dir = OUTPUT_DIR / ".temp" / banco / pdf_name
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.debug(f"  🗑️  Limpiado .temp")

    # Limpiar PNGs en images
    png_folder_images = INPUT_DIR / banco / pdf_name
    if png_folder_images.exists():
        shutil.rmtree(png_folder_images, ignore_errors=True)
        logger.debug(f"  🗑️  Limpiado PNGs en images")

    # Limpiar PNGs en images_processed
    png_folder_processed = PROCESSED_DIR / banco / pdf_name
    if png_folder_processed.exists():
        shutil.rmtree(png_folder_processed, ignore_errors=True)
        logger.debug(f"  🗑️  Limpiado PNGs en images_processed")


def regenerar_pngs(banco: str, pdf_name: str) -> Path:
    """Regenera PNGs desde el PDF original en data/raw"""

    # Buscar PDF original
    raw_dir = Path("data/raw") / banco
    pdf_path = raw_dir / f"{pdf_name}.pdf"

    if not pdf_path.exists():
        logger.error(f"  ❌ PDF original no encontrado: {pdf_path}")
        return None

    logger.info(f"  📄 PDF encontrado: {pdf_path.name}")

    # Crear carpeta destino
    output_folder = INPUT_DIR / banco / pdf_name
    output_folder.mkdir(parents=True, exist_ok=True)

    logger.info(f"  🔄 Convirtiendo PDF a PNG (300 DPI)...")

    try:
        # Convertir PDF a PNG
        images = convert_from_path(str(pdf_path), dpi=300)

        for i, image in enumerate(images, 1):
            png_path = output_folder / f"pagina_{i:03d}.png"
            image.save(str(png_path), "PNG")

        logger.success(f"  ✅ Generados {len(images)} PNGs en: {output_folder}")
        return output_folder

    except Exception as e:
        logger.error(f"  ❌ Error convirtiendo PDF: {e}")
        return None


def main():
    logger.info("=" * 70)
    logger.info("🔄 REGENERAR PNGs Y REPROCESAR PDFs CORRUPTOS")
    logger.info("=" * 70)
    logger.info(f"📄 PDFs a procesar: {len(PDFS_A_REPROCESAR)}")

    # Verificar API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY no configurada")
        return

    logger.success("✅ API Key encontrada")

    # Listar PDFs
    logger.info("\n" + "=" * 70)
    logger.info("📋 LISTA DE PDFs:")
    logger.info("=" * 70)
    for i, pdf_relative in enumerate(PDFS_A_REPROCESAR, 1):
        logger.info(f"{i}. {pdf_relative}")

    # Configurar modelo
    logger.info("\n🔄 Configurando LangChain + Gemini...")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            temperature=0,
            max_output_tokens=8192,
            top_p=0.95,
            top_k=40,
            google_api_key=api_key,
        )

        logger.success("✅ Modelo configurado")
    except Exception as e:
        logger.error(f"❌ Error configurando modelo: {e}")
        return

    # Cargar progreso
    progress = load_progress()

    # Procesar cada uno
    logger.info("\n" + "=" * 70)
    logger.info("🔄 PROCESANDO")
    logger.info("=" * 70)

    resultados = []
    tiempo_inicio = time.time()

    for i, pdf_relative in enumerate(PDFS_A_REPROCESAR, 1):
        parts = pdf_relative.split('/')
        banco = parts[0]
        pdf_name = parts[1]

        logger.info(f"\n[{i}/{len(PDFS_A_REPROCESAR)}] {banco}/{pdf_name}")

        try:
            # Limpiar todo previo
            limpiar_todo(banco, pdf_name)

            # Regenerar PNGs desde PDF original
            png_folder = regenerar_pngs(banco, pdf_name)

            if not png_folder:
                logger.error(f"  ❌ No se pudieron regenerar PNGs")
                resultados.append({
                    "exito": False,
                    "error": "No se pudo regenerar PNGs",
                    "pdf": f"{banco}/{pdf_name}"
                })
                continue

            # Procesar con OCR
            logger.info(f"  🔄 Procesando con OCR mejorado...")
            resultado = process_pdf_folder(png_folder, model, progress)
            resultados.append(resultado)

            if resultado["exito"]:
                logger.success(f"  ✅ Procesado ({resultado['paginas_procesadas']} páginas, {resultado['caracteres']:,} chars)")

                # Actualizar progreso
                pdf_relative_key = f"{banco}/{pdf_name}"
                if pdf_relative_key not in progress["processed_pdfs"]:
                    progress["processed_pdfs"].append(pdf_relative_key)
            else:
                logger.error(f"  ❌ Error: {resultado.get('error', 'Desconocido')}")

        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            resultados.append({
                "exito": False,
                "error": str(e),
                "pdf": f"{banco}/{pdf_name}"
            })

    # Guardar progreso
    tiempo_total = time.time() - tiempo_inicio
    progress["total_time"] += tiempo_total
    save_progress(progress)

    # Resumen
    exitosos = [r for r in resultados if r.get("exito", False)]
    fallidos = [r for r in resultados if not r.get("exito", False)]
    total_paginas = sum(r.get("paginas_procesadas", 0) for r in exitosos)

    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN")
    logger.info("=" * 70)
    logger.info(f"Total procesados:     {len(resultados)}")
    logger.info(f"  - Exitosos:         {len(exitosos)} ✅")
    logger.info(f"  - Fallidos:         {len(fallidos)} ❌")
    logger.info(f"Páginas procesadas:   {total_paginas}")
    logger.info(f"Tiempo total:         {tiempo_total/60:.2f} min")
    if resultados:
        logger.info(f"Promedio por PDF:     {tiempo_total/len(resultados):.2f}s")

    if fallidos:
        logger.warning("\n⚠️  PDFs con error:")
        for r in fallidos:
            logger.warning(f"  - {r.get('pdf', 'N/A')}: {r.get('error', 'N/A')[:60]}")

    logger.info("=" * 70)

    if exitosos:
        logger.success(f"\n✅ {len(exitosos)}/{len(PDFS_A_REPROCESAR)} PDFs procesados exitosamente")


if __name__ == "__main__":
    main()
