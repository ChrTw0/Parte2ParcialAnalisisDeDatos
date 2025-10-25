#!/usr/bin/env python3
"""
Procesamiento OCR Batch con Gemini Flash 2.0
Procesa todos los PDFs y guarda resultados en data/ocr/
Implementa checkpoint/resume para evitar reprocesar
"""
import os
import sys
from pathlib import Path
import time
from datetime import datetime
import json
from loguru import logger
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import google.generativeai as genai

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

# Configuración
MODEL_NAME = "gemini-2.5-flash"
INPUT_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/ocr")
PROCESSED_DIR = Path("data/raw_processed")  # PDFs ya procesados
PROGRESS_FILE = Path("data/processed/progress_ocr.json")
MAX_WORKERS = 3  # Hilos paralelos para procesamiento

# Lock para operaciones thread-safe
progress_lock = threading.Lock()

PROMPT_OCR = """You are a professional OCR system specialized in extracting banking tariff documents. Your task is to extract text, numbers, and tables from this multi-page PDF with MAXIMUM precision and cleanliness.

CRITICAL REQUIREMENTS:
1. Extract 100% of the UNIQUE content - DO NOT repeat page headers/footers
2. Preserve EXACT numerical values (rates, fees, percentages)
3. Maintain EXACT table structure with all rows and columns
4. Keep ALL currency symbols exactly as shown (S/, US$, UF, etc.)
5. Include footnotes and conditions (but only ONCE, not per page)
6. Preserve document structure (headers, sections, subsections)
7. DO NOT add explanations or interpretations
8. DO NOT repeat the same content multiple times

PAGE HANDLING:
- Extract headers/footers ONLY ONCE (first occurrence)
- DO NOT repeat "Vigencia", "Observación", or legal text on every page
- Merge content from multiple pages into a single coherent document
- Skip page numbers, "Página X de Y", etc.

OUTPUT FORMAT:
- Use markdown tables for tabular data
- Use headers (##, ###) for document sections
- Use bullet points for lists
- Use **bold** for important terms
- Preserve line breaks between sections
- NO extra spacing between elements
- NO repetitive content

TABLES - CRITICAL:
- Extract EVERY row and column from tables
- Align columns properly with | separators
- Include table headers
- **DO NOT put multi-page content inside table cells**
- **If a cell contains more than 200 characters, you are doing it WRONG**
- Keep cells concise - only the actual cell content
- Split large tables across rows, NOT by stuffing content into one cell

NUMBERS:
- Copy percentages EXACTLY as shown (15.50%, not "approximately 15%")
- Copy monetary amounts EXACTLY (S/ 25.00, not "around 25 soles")
- Preserve decimal precision

WHAT TO AVOID:
- ❌ Repeating the same footer text 50 times
- ❌ Putting entire pages of text inside a single table cell
- ❌ Including page numbers in output
- ❌ Duplicating "Vigencia desde..." on every page

Begin extraction NOW. Output ONLY the markdown content, no preamble or conclusions."""


def load_progress() -> dict:
    """Carga el registro de progreso"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "processed": [],
        "failed": [],
        "total_time": 0,
        "last_updated": None
    }


def save_progress(progress: dict):
    """Guarda el registro de progreso (thread-safe)"""
    with progress_lock:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        progress["last_updated"] = datetime.now().isoformat()
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)


def is_already_processed(pdf_path: Path, progress: dict) -> bool:
    """Verifica si un PDF ya fue procesado"""
    pdf_relative = str(pdf_path.relative_to(INPUT_DIR))

    # Verificar en registro de progreso
    if pdf_relative in progress["processed"]:
        return True

    # Verificar si existe el archivo Markdown de salida
    output_path = get_output_path(pdf_path)
    if output_path.exists():
        return True

    # Verificar si el PDF está en la carpeta de procesados
    processed_path = PROCESSED_DIR / pdf_path.relative_to(INPUT_DIR)
    if processed_path.exists():
        return True

    return False


def get_output_path(pdf_path: Path) -> Path:
    """Genera la ruta del archivo Markdown de salida"""
    relative_path = pdf_path.relative_to(INPUT_DIR)
    output_path = OUTPUT_DIR / relative_path.parent / f"{relative_path.stem}.md"
    return output_path


def move_to_processed(pdf_path: Path):
    """Mueve el PDF a la carpeta de procesados"""
    relative_path = pdf_path.relative_to(INPUT_DIR)
    processed_path = PROCESSED_DIR / relative_path

    # Crear directorio destino
    processed_path.parent.mkdir(parents=True, exist_ok=True)

    # Mover archivo
    pdf_path.rename(processed_path)
    logger.debug(f"Movido a: {processed_path}")


def process_pdf(pdf_path: Path, model, progress: dict) -> dict:
    """
    Procesa un PDF con Gemini OCR

    Returns:
        dict con resultado del procesamiento
    """
    resultado = {
        "pdf": str(pdf_path.relative_to(INPUT_DIR)),
        "exito": False,
        "tiempo": 0,
        "error": None,
        "output_path": None,
        "caracteres": 0
    }

    start_time = time.time()

    try:
        # Leer PDF
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        # Crear parte del PDF
        pdf_part = {
            'mime_type': 'application/pdf',
            'data': pdf_data
        }

        # Generar contenido
        response = model.generate_content([PROMPT_OCR, pdf_part])
        markdown_result = response.text

        # Guardar resultado (solo el contenido extraído, sin headers)
        output_path = get_output_path(pdf_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_result)

        # Mover PDF a carpeta de procesados
        move_to_processed(pdf_path)

        resultado["exito"] = True
        resultado["output_path"] = str(output_path)
        resultado["caracteres"] = len(markdown_result)

    except Exception as e:
        resultado["error"] = str(e)
        logger.error(f"Error procesando {pdf_path.name}: {e}")

    resultado["tiempo"] = time.time() - start_time
    return resultado


def main():
    logger.info("=" * 70)
    logger.info("🚀 PROCESAMIENTO BATCH OCR CON GEMINI FLASH 2.0")
    logger.info("=" * 70)

    # Verificar API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY no configurada")
        logger.info(f"   Configura en: {env_path}")
        return

    logger.success(f"✅ API Key encontrada")

    # Verificar directorios
    if not INPUT_DIR.exists():
        logger.error(f"❌ Directorio {INPUT_DIR} no existe")
        return

    # Crear directorios de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar progreso previo
    progress = load_progress()
    logger.info(f"📊 PDFs ya procesados: {len(progress['processed'])}")
    logger.info(f"📊 PDFs con error previo: {len(progress['failed'])}")

    # Obtener lista de PDFs
    all_pdfs = list(INPUT_DIR.rglob("*.pdf"))
    logger.info(f"📄 Total PDFs encontrados: {len(all_pdfs)}")

    # Filtrar PDFs ya procesados
    pdfs_pendientes = [pdf for pdf in all_pdfs if not is_already_processed(pdf, progress)]
    logger.info(f"📄 PDFs pendientes: {len(pdfs_pendientes)}")

    if not pdfs_pendientes:
        logger.success("\n✅ Todos los PDFs ya fueron procesados")
        logger.info(f"   Revisa resultados en: {OUTPUT_DIR}/")
        return

    # Configurar Gemini
    logger.info("\n🔄 Configurando Gemini API...")
    try:
        genai.configure(api_key=api_key)

        generation_config = {
            "temperature": 0,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config
        )

        logger.success("✅ Modelo configurado")

    except Exception as e:
        logger.error(f"❌ Error configurando modelo: {e}")
        return

    # Procesar PDFs en paralelo
    logger.info("\n" + "=" * 70)
    logger.info("🔄 INICIANDO PROCESAMIENTO PARALELO")
    logger.info("=" * 70)
    logger.info(f"⚡ Hilos paralelos: {MAX_WORKERS}")

    resultados = []
    tiempo_inicio = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Enviar trabajos
        futures = {executor.submit(process_pdf, pdf, model, progress): pdf
                   for pdf in pdfs_pendientes}

        # Procesar resultados con barra de progreso
        with tqdm(total=len(pdfs_pendientes), desc="Procesando PDFs", unit="pdf") as pbar:
            for future in as_completed(futures):
                pdf_path = futures[future]

                try:
                    resultado = future.result()
                    resultados.append(resultado)

                    # Actualizar progreso (thread-safe)
                    pdf_relative = str(pdf_path.relative_to(INPUT_DIR))

                    with progress_lock:
                        if resultado["exito"]:
                            progress["processed"].append(pdf_relative)
                        else:
                            progress["failed"].append({
                                "pdf": pdf_relative,
                                "error": resultado["error"]
                            })

                        # Actualizar barra
                        pbar.set_postfix({
                            "✅": len(progress["processed"]),
                            "❌": len(progress["failed"])
                        })

                    # Guardar progreso cada 10 PDFs
                    if len(resultados) % 10 == 0:
                        save_progress(progress)

                except Exception as e:
                    logger.error(f"Error procesando {pdf_path.name}: {e}")

                pbar.update(1)

    # Guardar progreso final
    tiempo_total = time.time() - tiempo_inicio
    progress["total_time"] += tiempo_total
    save_progress(progress)

    # Estadísticas finales
    exitosos = [r for r in resultados if r["exito"]]
    fallidos = [r for r in resultados if not r["exito"]]

    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN DE PROCESAMIENTO")
    logger.info("=" * 70)
    logger.info(f"PDFs procesados (esta sesión): {len(resultados)}")
    logger.info(f"  - Exitosos:                  {len(exitosos)} ✅")
    logger.info(f"  - Fallidos:                  {len(fallidos)} ❌")
    logger.info(f"Tiempo total:                  {tiempo_total/60:.2f} min ({tiempo_total/3600:.2f} h)")
    logger.info(f"Promedio por PDF:              {tiempo_total/len(resultados):.2f}s")

    logger.info("\n📊 TOTALES ACUMULADOS:")
    logger.info(f"Total procesados exitosos:     {len(progress['processed'])} ✅")
    logger.info(f"Total con error:               {len(progress['failed'])} ❌")
    logger.info(f"Tiempo acumulado:              {progress['total_time']/3600:.2f} horas")

    if fallidos:
        logger.warning("\n⚠️  PDFs con errores en esta sesión:")
        for r in fallidos[:10]:
            logger.warning(f"  - {r['pdf']}: {r['error'][:80]}")
        if len(fallidos) > 10:
            logger.warning(f"  ... y {len(fallidos) - 10} más")

    logger.info("\n" + "=" * 70)
    logger.info("📁 UBICACIÓN DE ARCHIVOS:")
    logger.info("=" * 70)
    logger.info(f"  - Resultados OCR:  {OUTPUT_DIR}/")
    logger.info(f"  - PDFs procesados: {PROCESSED_DIR}/")
    logger.info(f"  - Registro:        {PROGRESS_FILE}")

    # Guardar reporte detallado
    reporte_path = Path("data/processed/reporte_ocr_gemini.json")
    reporte = {
        "fecha_ejecucion": datetime.now().isoformat(),
        "pdfs_procesados_sesion": len(resultados),
        "exitosos_sesion": len(exitosos),
        "fallidos_sesion": len(fallidos),
        "tiempo_sesion_segundos": tiempo_total,
        "total_acumulado_exitosos": len(progress["processed"]),
        "total_acumulado_fallidos": len(progress["failed"]),
        "tiempo_acumulado_horas": progress["total_time"] / 3600,
        "resultados_sesion": resultados
    }

    with open(reporte_path, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    logger.success(f"\n💾 Reporte guardado: {reporte_path}")
    logger.info("=" * 70)

    if len(progress["processed"]) >= len(all_pdfs):
        logger.success("\n🎉 ¡PROCESAMIENTO COMPLETO!")
        logger.info("   Todos los PDFs han sido procesados exitosamente")
    else:
        logger.info(f"\n⏸️  Progreso: {len(progress['processed'])}/{len(all_pdfs)} PDFs")
        logger.info("   Ejecuta de nuevo para continuar")


if __name__ == "__main__":
    main()
