#!/usr/bin/env python3
"""
Procesamiento OCR Página por Página con Gemini Flash 2.5
Procesa imágenes PNG individuales y combina resultados por PDF
Soluciona problemas de PDFs grandes y contenido repetitivo
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
import signal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import base64
import io

# Variable global para manejo de Ctrl+C
shutdown_requested = False

def signal_handler(signum, frame):
    """Maneja Ctrl+C para detener procesamiento limpiamente"""
    global shutdown_requested
    logger.warning("\n\n⚠️  CTRL+C detectado! Deteniendo procesamiento...")
    logger.info("Esperando que terminen los trabajos en curso...")
    shutdown_requested = True

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

# Configuración
MODEL_NAME = "gemini-2.5-flash-lite"
INPUT_DIR = Path("data/images")  # Carpeta con PNGs
OUTPUT_DIR = Path("data/ocr")
PROCESSED_DIR = Path("data/images_processed")  # PNGs ya procesados
PROGRESS_FILE = Path("data/processed/progress_ocr_paginas.json")
MAX_WORKERS = 1  # 1 hilo (rate limit: 15 req/min)
DELAY_BETWEEN_PAGES = 3  # Segundos entre páginas (15 req/min = 1 cada 4s)

# Lock para operaciones thread-safe
progress_lock = threading.Lock()

PROMPT_OCR_PAGINA = """You are a professional OCR system specialized in extracting banking tariff documents with MAXIMUM precision.

CRITICAL INSTRUCTIONS:
1. Extract ALL table content with exact structure
2. Use Markdown table format: | Column1 | Column2 |
3. Preserve EXACT numerical values (rates, fees, percentages)
4. Keep ALL currency symbols exactly as shown (S/, US$, etc.)
5. Each table row must be ONE LINE ONLY
6. Cell content must be CONCISE (max 150 characters per cell)
7. **STOP IMMEDIATELY when you reach the end of the visible content**
8. **DO NOT repeat any content - each piece of text appears ONCE**

TABLE FORMAT RULES:
- Use | separators for columns
- Use | --- | for headers
- ONE row per line (no line breaks inside cells)
- If a cell has long text, SUMMARIZE to max 150 chars
- NO blank spaces longer than 2 spaces
- NO long dashes (----) inside cells

ANTI-REPETITION RULES:
- Extract content sequentially from top to bottom
- Once you finish extracting, STOP generating
- Never repeat headers, footers, or table rows
- If you see "END" or run out of content, STOP

OUTPUT FORMAT:
Clean Markdown with tables, NO explanations, NO preamble, NO repetitions.

BEGIN EXTRACTION NOW:"""


def load_progress() -> dict:
    """Carga el registro de progreso"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "processed_pdfs": [],
        "failed_pdfs": [],
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


def get_pdf_folders() -> list:
    """Obtiene lista de carpetas de PDFs (cada carpeta = un PDF con sus páginas PNG)"""
    pdf_folders = []

    for banco_dir in INPUT_DIR.iterdir():
        if not banco_dir.is_dir():
            continue

        for pdf_folder in banco_dir.iterdir():
            if not pdf_folder.is_dir():
                continue

            # Verificar que tenga imágenes PNG
            png_files = list(pdf_folder.glob("*.png"))
            if png_files:
                pdf_folders.append(pdf_folder)

    return sorted(pdf_folders)


def process_image_page(image_path: Path, model, max_retries=3) -> str:
    """Procesa una página PNG con LangChain + Gemini OCR usando base64 con retry automático"""
    from PIL import Image

    for attempt in range(max_retries):
        try:
            # Cargar imagen con PIL y convertir a base64
            img = Image.open(image_path)

            # Convertir a base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Crear data URI
            image_data_uri = f"data:image/png;base64,{img_base64}"

            # Crear mensaje con imagen en base64
            message = HumanMessage(
                content=[
                    {"type": "text", "text": PROMPT_OCR_PAGINA},
                    {"type": "image_url", "image_url": image_data_uri},
                ]
            )

            # Invocar modelo
            response = model.invoke([message])
            return response.content

        except Exception as e:
            error_msg = str(e)

            # Si es error 429 (rate limit), esperar y reintentar
            if "429" in error_msg or "quota" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s
                    logger.warning(f"⚠️  Rate limit - esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                    continue

            # Otro error o último intento
            logger.error(f"Error procesando {image_path.name}: {e}")
            return f"\n\n<!-- Error en página {image_path.name}: {error_msg} -->\n\n"

    return f"\n\n<!-- Error en página {image_path.name}: Max retries exceeded -->\n\n"


def move_folder_to_processed(pdf_folder: Path):
    """Mueve la carpeta de PNGs procesados a images_processed"""
    banco = pdf_folder.parent.name
    pdf_name = pdf_folder.name

    # Ruta destino
    processed_path = PROCESSED_DIR / banco / pdf_name

    # Crear directorio padre
    processed_path.parent.mkdir(parents=True, exist_ok=True)

    # Mover carpeta completa
    import shutil
    shutil.move(str(pdf_folder), str(processed_path))
    logger.debug(f"Movido a: {processed_path}")


def process_pdf_folder(pdf_folder: Path, model, progress: dict) -> dict:
    """
    Procesa todas las páginas PNG de un PDF y combina resultados
    Con checkpoint por página para poder continuar desde donde falló

    Returns:
        dict con resultado del procesamiento
    """
    banco = pdf_folder.parent.name
    pdf_name = pdf_folder.name
    pdf_relative = f"{banco}/{pdf_name}"

    resultado = {
        "pdf": pdf_relative,
        "exito": False,
        "tiempo": 0,
        "error": None,
        "output_path": None,
        "paginas_procesadas": 0,
        "paginas_con_error": 0,
        "caracteres": 0
    }

    start_time = time.time()

    try:
        # Obtener lista de imágenes ordenadas
        png_files = sorted(pdf_folder.glob("*.png"))

        if not png_files:
            resultado["error"] = "No PNG files found"
            return resultado

        # Crear carpeta temporal para páginas procesadas
        temp_dir = OUTPUT_DIR / ".temp" / banco / pdf_name
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📄 Procesando {pdf_relative} ({len(png_files)} páginas)...")

        # Procesar cada página (con checkpoint)
        errores = 0
        paginas_procesadas = 0

        for i, png_file in enumerate(png_files, 1):
            page_num = f"{i:04d}"  # 0001, 0002, etc.
            temp_page_file = temp_dir / f"page_{page_num}.md"

            # Verificar si esta página ya fue procesada
            if temp_page_file.exists():
                logger.debug(f"  ✅ Página {i}/{len(png_files)} ya procesada: {png_file.name}")
                paginas_procesadas += 1
                continue

            # Procesar página
            logger.debug(f"  🔄 Página {i}/{len(png_files)}: {png_file.name}")
            contenido = process_image_page(png_file, model)

            # Detectar si hubo error
            if "<!-- Error en página" in contenido:
                errores += 1
                logger.warning(f"  ❌ Error en página {i}")
            else:
                paginas_procesadas += 1

            # Guardar página procesada en archivo temporal
            with open(temp_page_file, 'w', encoding='utf-8') as f:
                f.write(contenido)

            # NO mover PNG aquí - se moverá al final si todo está OK

            # Delay para respetar rate limit (15 req/min)
            if i < len(png_files):  # No esperar después de la última página
                time.sleep(DELAY_BETWEEN_PAGES)

        # Combinar todas las páginas procesadas
        contenidos_paginas = []
        for i in range(1, len(png_files) + 1):
            page_num = f"{i:04d}"
            temp_page_file = temp_dir / f"page_{page_num}.md"

            if temp_page_file.exists():
                with open(temp_page_file, 'r', encoding='utf-8') as f:
                    contenidos_paginas.append(f.read())
            else:
                contenidos_paginas.append(f"\n\n<!-- PÁGINA {i} NO PROCESADA -->\n\n")
                errores += 1

        # Verificar si está completo
        if errores > 0:
            resultado["error"] = f"{errores} páginas con error de {len(png_files)} total"
            resultado["paginas_procesadas"] = paginas_procesadas
            resultado["paginas_con_error"] = errores
            logger.warning(f"⚠️  {pdf_relative}: {errores} páginas fallaron o faltan")

            # Guardar .md incompleto con marca de error
            markdown_result = f"<!-- ADVERTENCIA: {errores} páginas fallaron - PDF INCOMPLETO -->\n\n"
            markdown_result += "\n\n".join(contenidos_paginas)
        else:
            # Todo bien, procesar normalmente
            markdown_result = "\n\n".join(contenidos_paginas)

            # Post-procesamiento: eliminar líneas repetitivas obvias
            markdown_result = limpiar_contenido_repetitivo(markdown_result)

            resultado["exito"] = True
            resultado["paginas_procesadas"] = len(png_files)

        # Guardar resultado final
        output_path = OUTPUT_DIR / banco / f"{pdf_name}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_result)

        resultado["output_path"] = str(output_path)
        resultado["caracteres"] = len(markdown_result)

        # Si TODO está completo, mover TODOS los PNGs a procesados
        if resultado["exito"]:
            # Mover todos los PNGs a images_processed
            for png_file in png_files:
                if png_file.exists():
                    move_png_to_processed(png_file, pdf_folder)

            # Verificar que la carpeta quedó vacía
            remaining_pngs = list(pdf_folder.glob("*.png"))
            if not remaining_pngs:
                # Carpeta vacía, moverla a procesados
                move_folder_to_processed(pdf_folder)

                # Limpiar archivos temporales
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"✅ Limpieza completa de {pdf_relative}")
            else:
                logger.warning(f"⚠️  Quedan {len(remaining_pngs)} PNGs en carpeta original")
        else:
            logger.warning(f"⚠️  {pdf_relative} incompleto - PNGs NO movidos, ejecuta de nuevo para continuar")

    except Exception as e:
        resultado["error"] = str(e)
        logger.error(f"Error procesando {pdf_relative}: {e}")

    resultado["tiempo"] = time.time() - start_time
    return resultado


def move_png_to_processed(png_file: Path, pdf_folder: Path):
    """Mueve un PNG individual a la carpeta de procesados"""
    banco = pdf_folder.parent.name
    pdf_name = pdf_folder.name

    # Ruta destino
    processed_png_dir = PROCESSED_DIR / banco / pdf_name
    processed_png_dir.mkdir(parents=True, exist_ok=True)

    # Mover PNG
    dest_path = processed_png_dir / png_file.name
    import shutil
    shutil.move(str(png_file), str(dest_path))


def limpiar_contenido_repetitivo(texto: str) -> str:
    """
    Post-procesamiento para eliminar contenido repetitivo obvio
    """
    lineas = texto.split('\n')
    lineas_limpias = []
    lineas_contador = {}  # Cambio: usar dict para contar

    for linea in lineas:
        # Normalizar para detectar duplicados
        linea_normalizada = linea.strip().lower()

        # Si es una línea genérica repetitiva, skip
        if linea_normalizada in ["", "vigencia", "observación", "bbva", "banco"]:
            continue

        # Contar cuántas veces hemos visto esta línea
        if linea_normalizada:
            count = lineas_contador.get(linea_normalizada, 0)

            # Si ya vimos esta línea más de 2 veces, skip
            if count > 2:
                continue

            lineas_contador[linea_normalizada] = count + 1

        lineas_limpias.append(linea)

    return '\n'.join(lineas_limpias)


def main():
    # Configurar manejo de Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("=" * 70)
    logger.info("🚀 PROCESAMIENTO OCR PÁGINA POR PÁGINA")
    logger.info("=" * 70)
    logger.info("💡 Presiona Ctrl+C para detener limpiamente")

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
        logger.info(f"   Ejecuta primero: python scripts/convertir_pdfs_a_png.py")
        return

    # Crear directorios de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar progreso previo
    progress = load_progress()
    logger.info(f"📊 PDFs ya procesados: {len(progress['processed_pdfs'])}")

    # Obtener lista de PDFs (carpetas con PNGs)
    pdf_folders = get_pdf_folders()
    logger.info(f"📄 Total PDFs encontrados: {len(pdf_folders)}")

    # Filtrar ya procesados
    pdfs_pendientes = []
    for folder in pdf_folders:
        pdf_relative = f"{folder.parent.name}/{folder.name}"

        # Verificar si ya está en el registro de progreso
        if pdf_relative in progress["processed_pdfs"]:
            continue

        # Verificar si ya existe el archivo .md
        output_path = OUTPUT_DIR / folder.parent.name / f"{folder.name}.md"
        if output_path.exists():
            continue

        # Verificar si la carpeta ya está en images_processed
        processed_path = PROCESSED_DIR / folder.parent.name / folder.name
        if processed_path.exists():
            continue

        pdfs_pendientes.append(folder)

    logger.info(f"📄 PDFs pendientes: {len(pdfs_pendientes)}")

    if not pdfs_pendientes:
        logger.success("\n✅ Todos los PDFs ya fueron procesados")
        logger.info(f"   Revisa resultados en: {OUTPUT_DIR}/")
        return

    # Configurar Gemini con LangChain
    logger.info("\n🔄 Configurando LangChain + Gemini API...")
    try:
        model = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            temperature=0,  # Determinístico para OCR consistente
            max_output_tokens=8192,  # Duplicado para mayor robustez (previene loops infinitos)
            top_p=0.95,  # Muestreo nucleus
            top_k=40,  # Limitar tokens candidatos
            google_api_key=api_key,
        )

        logger.success("✅ Modelo LangChain configurado (temp=0, max_tokens=8192, top_p=0.95, top_k=40)")

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
        futures = {executor.submit(process_pdf_folder, folder, model, progress): folder
                   for folder in pdfs_pendientes}

        # Procesar resultados con barra de progreso
        with tqdm(total=len(pdfs_pendientes), desc="Procesando PDFs", unit="pdf") as pbar:
            for future in as_completed(futures):
                # Verificar si se solicitó shutdown
                if shutdown_requested:
                    logger.warning("⏸️  Deteniendo nuevos trabajos...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                pdf_folder = futures[future]

                try:
                    resultado = future.result()
                    resultados.append(resultado)

                    # Actualizar progreso (thread-safe)
                    pdf_relative = f"{pdf_folder.parent.name}/{pdf_folder.name}"

                    with progress_lock:
                        if resultado["exito"]:
                            progress["processed_pdfs"].append(pdf_relative)
                        else:
                            progress["failed_pdfs"].append({
                                "pdf": pdf_relative,
                                "error": resultado["error"]
                            })

                        # Actualizar barra
                        pbar.set_postfix({
                            "✅": len(progress["processed_pdfs"]),
                            "❌": len(progress["failed_pdfs"])
                        })

                    # Guardar progreso cada 10 PDFs
                    if len(resultados) % 10 == 0:
                        save_progress(progress)

                except Exception as e:
                    logger.error(f"Error procesando {pdf_folder.name}: {e}")

                pbar.update(1)

    # Si se detuvo por Ctrl+C, guardar progreso
    if shutdown_requested:
        logger.warning("⏸️  Procesamiento interrumpido por usuario")
        logger.info("💾 Guardando progreso actual...")

    # Guardar progreso final
    tiempo_total = time.time() - tiempo_inicio
    progress["total_time"] += tiempo_total
    save_progress(progress)

    # Estadísticas finales
    exitosos = [r for r in resultados if r["exito"]]
    fallidos = [r for r in resultados if not r["exito"]]
    total_paginas = sum(r["paginas_procesadas"] for r in exitosos)

    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN DE PROCESAMIENTO")
    logger.info("=" * 70)
    logger.info(f"PDFs procesados (esta sesión): {len(resultados)}")
    logger.info(f"  - Exitosos:                  {len(exitosos)} ✅")
    logger.info(f"  - Fallidos:                  {len(fallidos)} ❌")
    logger.info(f"Total páginas procesadas:      {total_paginas}")
    logger.info(f"Tiempo total:                  {tiempo_total/60:.2f} min ({tiempo_total/3600:.2f} h)")
    logger.info(f"Promedio por PDF:              {tiempo_total/len(resultados):.2f}s")
    logger.info(f"Promedio por página:           {tiempo_total/total_paginas:.2f}s")

    logger.info("\n📊 TOTALES ACUMULADOS:")
    logger.info(f"Total procesados exitosos:     {len(progress['processed_pdfs'])} ✅")
    logger.info(f"Total con error:               {len(progress['failed_pdfs'])} ❌")

    if fallidos:
        logger.warning("\n⚠️  PDFs con errores en esta sesión:")
        for r in fallidos[:10]:
            logger.warning(f"  - {r['pdf']}: {r['error'][:80]}")

    logger.info("\n" + "=" * 70)
    logger.info("📁 UBICACIÓN DE ARCHIVOS:")
    logger.info("=" * 70)
    logger.info(f"  - Resultados OCR:  {OUTPUT_DIR}/")
    logger.info(f"  - Registro:        {PROGRESS_FILE}")

    # Guardar reporte detallado
    reporte_path = Path("data/processed/reporte_ocr_paginas.json")
    reporte = {
        "fecha_ejecucion": datetime.now().isoformat(),
        "pdfs_procesados_sesion": len(resultados),
        "exitosos_sesion": len(exitosos),
        "fallidos_sesion": len(fallidos),
        "total_paginas": total_paginas,
        "tiempo_sesion_segundos": tiempo_total,
        "resultados_sesion": resultados
    }

    with open(reporte_path, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    logger.success(f"\n💾 Reporte guardado: {reporte_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
