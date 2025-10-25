#!/usr/bin/env python3
"""
Script para reprocesar una lista específica de PDFs corruptos
"""
import os
import sys
from pathlib import Path
from loguru import logger

# Importar funciones del script principal
sys.path.insert(0, str(Path(__file__).parent))
from procesar_ocr_por_pagina import *

# Lista de PDFs corruptos a reprocesar (3 PDFs con repetición masiva)
PDFS_A_REPROCESAR = [
    "BBVA_Continental/CTS-COMISIONES-TRANSVERSALES",
    "BBVA_Continental/constancias-duplicados",
    "BBVA_Continental/Comisiones-Adquirencia-por-Giro-MCC",
]


def limpiar_archivos_previos(banco: str, pdf_name: str):
    """Limpia archivos .md y .temp previos"""
    # Eliminar .md corrupto
    md_path = OUTPUT_DIR / banco / f"{pdf_name}.md"
    if md_path.exists():
        md_path.unlink()
        logger.debug(f"  🗑️  Eliminado .md: {md_path}")

    # Eliminar archivos temporales
    temp_dir = OUTPUT_DIR / ".temp" / banco / pdf_name
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.debug(f"  🗑️  Limpiado .temp: {temp_dir}")


def mover_pngs_de_vuelta(banco: str, pdf_name: str) -> Path:
    """Mueve PNGs de images_processed de vuelta a images para reprocesar"""
    import shutil

    processed_folder = PROCESSED_DIR / banco / pdf_name
    images_folder = INPUT_DIR / banco / pdf_name

    # Si ya está en images, no hacer nada
    if images_folder.exists() and list(images_folder.glob("*.png")):
        logger.debug(f"  📁 PNGs ya están en images/")
        return images_folder

    # Si está en processed, mover de vuelta
    if processed_folder.exists() and list(processed_folder.glob("*.png")):
        logger.debug(f"  📁 Moviendo PNGs de images_processed/ a images/")

        # Crear carpeta destino
        images_folder.parent.mkdir(parents=True, exist_ok=True)

        # Mover carpeta completa
        shutil.move(str(processed_folder), str(images_folder))
        logger.debug(f"  ✅ PNGs movidos a images/")
        return images_folder

    logger.warning(f"  ⚠️  No se encontraron PNGs en ninguna ubicación")
    return None


def main():
    logger.info("=" * 70)
    logger.info("🔄 REPROCESAMIENTO DE LISTA ESPECÍFICA")
    logger.info("=" * 70)
    logger.info(f"📄 PDFs a reprocesar: {len(PDFS_A_REPROCESAR)}")

    # Verificar API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY no configurada")
        return

    logger.success("✅ API Key encontrada")

    # Verificar carpetas
    carpetas_a_procesar = []

    for pdf_relative in PDFS_A_REPROCESAR:
        parts = pdf_relative.split('/')
        banco = parts[0]
        pdf_name = parts[1]

        # Buscar carpeta con PNGs
        png_folder_processed = PROCESSED_DIR / banco / pdf_name
        png_folder_images = INPUT_DIR / banco / pdf_name

        if png_folder_processed.exists():
            carpetas_a_procesar.append({
                "banco": banco,
                "pdf_name": pdf_name,
                "png_folder": png_folder_processed,
                "ubicacion": "images_processed"
            })
        elif png_folder_images.exists():
            carpetas_a_procesar.append({
                "banco": banco,
                "pdf_name": pdf_name,
                "png_folder": png_folder_images,
                "ubicacion": "images"
            })
        else:
            logger.warning(f"⚠️  No encontrado: {pdf_relative}")

    logger.info(f"📂 Carpetas encontradas: {len(carpetas_a_procesar)}")

    if not carpetas_a_procesar:
        logger.error("❌ No se encontraron carpetas para procesar")
        return

    # Listar carpetas
    logger.info("\n" + "=" * 70)
    logger.info("📋 CARPETAS A REPROCESAR:")
    logger.info("=" * 70)
    for i, c in enumerate(carpetas_a_procesar, 1):
        png_count = len(list(c["png_folder"].glob("*.png")))
        logger.info(f"{i}. {c['banco']}/{c['pdf_name']} ({png_count} PNGs) - {c['ubicacion']}")

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

    for i, carpeta in enumerate(carpetas_a_procesar, 1):
        banco = carpeta["banco"]
        pdf_name = carpeta["pdf_name"]

        logger.info(f"\n[{i}/{len(carpetas_a_procesar)}] Procesando {banco}/{pdf_name}")

        try:
            # Limpiar archivos previos
            limpiar_archivos_previos(banco, pdf_name)

            # Mover PNGs de vuelta si están en processed
            png_folder = mover_pngs_de_vuelta(banco, pdf_name)

            if not png_folder:
                logger.error(f"  ❌ No se encontraron PNGs para {banco}/{pdf_name}")
                resultados.append({"exito": False, "error": "No PNG files found", "pdf": f"{banco}/{pdf_name}"})
                continue

            # Procesar
            resultado = process_pdf_folder(png_folder, model, progress)
            resultados.append(resultado)

            if resultado["exito"]:
                logger.success(f"  ✅ Procesado exitosamente ({resultado['paginas_procesadas']} páginas)")

                # Actualizar progreso
                pdf_relative = f"{banco}/{pdf_name}"
                if pdf_relative not in progress["processed_pdfs"]:
                    progress["processed_pdfs"].append(pdf_relative)
            else:
                logger.error(f"  ❌ Error: {resultado.get('error', 'Desconocido')}")

        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            resultados.append({"exito": False, "error": str(e)})

    # Guardar progreso
    tiempo_total = time.time() - tiempo_inicio
    progress["total_time"] += tiempo_total
    save_progress(progress)

    # Resumen
    exitosos = [r for r in resultados if r.get("exito", False)]
    fallidos = [r for r in resultados if not r.get("exito", False)]
    total_paginas = sum(r.get("paginas_procesadas", 0) for r in exitosos)

    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN DE REPROCESAMIENTO")
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
        logger.success(f"\n✅ {len(exitosos)} PDFs reprocesados exitosamente")


if __name__ == "__main__":
    main()
