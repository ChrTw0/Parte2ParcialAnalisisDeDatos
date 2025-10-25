#!/usr/bin/env python3
"""
Procesamiento OCR por Banco Específico
Permite procesar solo un banco para distribuir trabajo entre dispositivos
"""
import os
import sys
from pathlib import Path
import argparse

# Importar todo del script principal
sys.path.insert(0, str(Path(__file__).parent))
from procesar_ocr_por_pagina import *

def get_available_banks(input_dir: Path) -> list:
    """Lista los bancos disponibles"""
    banks = []
    if input_dir.exists():
        for item in input_dir.iterdir():
            if item.is_dir():
                banks.append(item.name)
    return sorted(banks)


def main_por_banco():
    # Parsear argumentos
    parser = argparse.ArgumentParser(description='Procesar OCR de un banco específico')
    parser.add_argument('banco',
                       nargs='?',
                       help='Nombre del banco a procesar (ej: BBVA_Continental, BCP, etc.)')
    parser.add_argument('--list',
                       action='store_true',
                       help='Listar bancos disponibles')

    args = parser.parse_args()

    # Listar bancos si se solicita
    if args.list:
        banks = get_available_banks(INPUT_DIR)
        print("=" * 70)
        print("📊 BANCOS DISPONIBLES:")
        print("=" * 70)
        for i, bank in enumerate(banks, 1):
            # Contar PDFs por banco
            bank_dir = INPUT_DIR / bank
            pdf_count = len(list(bank_dir.iterdir())) if bank_dir.exists() else 0
            print(f"{i}. {bank:30} ({pdf_count} PDFs)")
        print("=" * 70)
        print("\nUso: python scripts/procesar_ocr_por_banco.py <nombre_banco>")
        print("Ejemplo: python scripts/procesar_ocr_por_banco.py BBVA_Continental")
        return

    # Verificar que se especificó un banco
    if not args.banco:
        print("❌ Error: Debes especificar un banco")
        print("\nUsa --list para ver bancos disponibles")
        print("Ejemplo: python scripts/procesar_ocr_por_banco.py BBVA_Continental")
        return

    banco_seleccionado = args.banco

    # Verificar que el banco existe
    banco_dir = INPUT_DIR / banco_seleccionado
    if not banco_dir.exists():
        print(f"❌ Error: Banco '{banco_seleccionado}' no encontrado")
        print("\nBancos disponibles:")
        for bank in get_available_banks(INPUT_DIR):
            print(f"  - {bank}")
        return

    # Configurar manejo de Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("=" * 70)
    logger.info(f"🚀 PROCESAMIENTO OCR - BANCO: {banco_seleccionado} [API 2]")
    logger.info("=" * 70)
    logger.info("💡 Presiona Ctrl+C para detener limpiamente")
    logger.info(f"⚙️  Workers: {MAX_WORKERS} | Delay: {DELAY_BETWEEN_PAGES}s | API: #2")

    # Verificar API key (Segunda API)
    api_key = os.getenv("GOOGLE_API_KEY_2")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY_2 no configurada")
        logger.info(f"   Configura GOOGLE_API_KEY_2 en: {env_path}")
        return

    logger.success(f"✅ API Key 2 encontrada")

    # Verificar directorios
    if not INPUT_DIR.exists():
        logger.error(f"❌ Directorio {INPUT_DIR} no existe")
        logger.info(f"   Ejecuta primero: python scripts/convertir_pdfs_a_png.py")
        return

    # Crear directorios de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar progreso previo
    progress = load_progress()
    logger.info(f"📊 PDFs ya procesados (todos los bancos): {len(progress['processed_pdfs'])}")

    # Obtener lista de PDFs SOLO del banco seleccionado
    pdf_folders = []
    for pdf_folder in banco_dir.iterdir():
        if not pdf_folder.is_dir():
            continue

        # Verificar que tenga imágenes PNG
        png_files = list(pdf_folder.glob("*.png"))
        if png_files:
            pdf_folders.append(pdf_folder)

    pdf_folders = sorted(pdf_folders)
    logger.info(f"📄 PDFs de {banco_seleccionado}: {len(pdf_folders)}")

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

    logger.info(f"📄 PDFs pendientes de {banco_seleccionado}: {len(pdfs_pendientes)}")

    if not pdfs_pendientes:
        logger.success(f"\n✅ Todos los PDFs de {banco_seleccionado} ya fueron procesados")
        logger.info(f"   Revisa resultados en: {OUTPUT_DIR}/{banco_seleccionado}/")
        return

    # Configurar Gemini con LangChain (importado desde procesar_ocr_por_pagina)
    logger.info("\n🔄 Configurando LangChain + Gemini API...")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

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

    # Procesar PDFs (con 1 worker por el rate limit)
    logger.info("\n" + "=" * 70)
    logger.info(f"🔄 PROCESANDO {banco_seleccionado}")
    logger.info("=" * 70)

    resultados = []
    tiempo_inicio = time.time()

    # Procesar secuencialmente (MAX_WORKERS=1)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_pdf_folder, folder, model, progress): folder
                   for folder in pdfs_pendientes}

        with tqdm(total=len(pdfs_pendientes), desc=f"Procesando {banco_seleccionado}", unit="pdf") as pbar:
            for future in as_completed(futures):
                if shutdown_requested:
                    logger.warning("⏸️  Deteniendo nuevos trabajos...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                pdf_folder = futures[future]

                try:
                    resultado = future.result()
                    resultados.append(resultado)

                    pdf_relative = f"{pdf_folder.parent.name}/{pdf_folder.name}"

                    with progress_lock:
                        if resultado["exito"]:
                            progress["processed_pdfs"].append(pdf_relative)
                        else:
                            progress["failed_pdfs"].append({
                                "pdf": pdf_relative,
                                "error": resultado["error"]
                            })

                        pbar.set_postfix({
                            "✅": len([r for r in resultados if r["exito"]]),
                            "❌": len([r for r in resultados if not r["exito"]])
                        })

                    if len(resultados) % 5 == 0:
                        save_progress(progress)

                except Exception as e:
                    logger.error(f"Error procesando {pdf_folder.name}: {e}")

                pbar.update(1)

    if shutdown_requested:
        logger.warning("⏸️  Procesamiento interrumpido por usuario")
        logger.info("💾 Guardando progreso actual...")

    tiempo_total = time.time() - tiempo_inicio
    progress["total_time"] += tiempo_total
    save_progress(progress)

    # Estadísticas
    exitosos = [r for r in resultados if r["exito"]]
    fallidos = [r for r in resultados if not r["exito"]]
    total_paginas = sum(r["paginas_procesadas"] for r in exitosos)

    logger.info("\n" + "=" * 70)
    logger.info(f"📊 RESUMEN - {banco_seleccionado}")
    logger.info("=" * 70)
    logger.info(f"PDFs procesados:              {len(resultados)}")
    logger.info(f"  - Exitosos:                 {len(exitosos)} ✅")
    logger.info(f"  - Fallidos:                 {len(fallidos)} ❌")
    logger.info(f"Páginas procesadas:           {total_paginas}")
    logger.info(f"Tiempo total:                 {tiempo_total/60:.2f} min ({tiempo_total/3600:.2f} h)")
    if resultados:
        logger.info(f"Promedio por PDF:             {tiempo_total/len(resultados):.2f}s")
    if total_paginas:
        logger.info(f"Promedio por página:          {tiempo_total/total_paginas:.2f}s")

    if fallidos:
        logger.warning(f"\n⚠️  PDFs con errores:")
        for r in fallidos[:5]:
            logger.warning(f"  - {r['pdf']}: {r['error'][:60]}")

    logger.info("\n" + "=" * 70)
    logger.info("📁 UBICACIÓN DE ARCHIVOS:")
    logger.info("=" * 70)
    logger.info(f"  - Resultados:  {OUTPUT_DIR}/{banco_seleccionado}/")
    logger.info(f"  - Registro:    {PROGRESS_FILE}")

    logger.success(f"\n✅ Procesamiento de {banco_seleccionado} completado")


if __name__ == "__main__":
    main_por_banco()
