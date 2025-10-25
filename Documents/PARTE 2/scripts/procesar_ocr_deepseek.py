#!/usr/bin/env python3
"""
Script para procesar imágenes con DeepSeek-OCR
Optimizado para CPU Intel i9-13900H
"""
import sys
from pathlib import Path
import torch
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm
from loguru import logger
import time
import json

# Configuración
MODEL_NAME = 'deepseek-ai/DeepSeek-OCR'
BATCH_SIZE = 4  # Procesar 4 imágenes por vez (ajustar según RAM)
PROMPT = "<image>\n<|grounding|>Convert the document to markdown. "
OUTPUT_DIR = Path("data/ocr")

# Configuración DeepSeek para CPU
BASE_SIZE = 1024
IMAGE_SIZE = 640
CROP_MODE = True

def inicializar_modelo():
    """Inicializa el modelo DeepSeek-OCR en CPU"""
    logger.info("🔄 Descargando/cargando modelo DeepSeek-OCR...")
    logger.info(f"   Modelo: {MODEL_NAME}")
    logger.info(f"   Device: CPU (torch.float32)")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True
        )

        model = AutoModel.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=torch.float32  # CPU usa float32
        )

        # Mover a CPU y modo evaluación
        model = model.eval().to('cpu')

        logger.success("✅ Modelo cargado exitosamente en CPU")
        return tokenizer, model

    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        raise


def procesar_imagen(tokenizer, model, image_path: Path, output_path: Path) -> dict:
    """
    Procesa una imagen con DeepSeek-OCR

    Returns:
        dict con resultado y estadísticas
    """
    resultado = {
        "imagen": image_path.name,
        "exito": False,
        "markdown": "",
        "error": None,
        "tiempo": 0
    }

    start_time = time.time()

    try:
        # Procesar con DeepSeek
        res = model.infer(
            tokenizer,
            prompt=PROMPT,
            image_file=str(image_path),
            output_path=str(output_path.parent),
            base_size=BASE_SIZE,
            image_size=IMAGE_SIZE,
            crop_mode=CROP_MODE,
            save_results=True,
            test_compress=False
        )

        resultado["markdown"] = res
        resultado["exito"] = True
        resultado["tiempo"] = time.time() - start_time

        logger.debug(f"✅ {image_path.name} procesado ({resultado['tiempo']:.2f}s)")

    except Exception as e:
        resultado["error"] = str(e)
        resultado["tiempo"] = time.time() - start_time
        logger.error(f"❌ {image_path.name}: {e}")

    return resultado


def main():
    """Procesa todas las imágenes PNG generadas"""

    logger.info("=" * 70)
    logger.info("🤖 OCR CON DEEPSEEK-OCR")
    logger.info("=" * 70)
    logger.info(f"Configuración:")
    logger.info(f"  - Device: CPU")
    logger.info(f"  - Batch size: {BATCH_SIZE}")
    logger.info(f"  - Base size: {BASE_SIZE}")
    logger.info(f"  - Image size: {IMAGE_SIZE}")
    logger.info("=" * 70)

    # Verificar directorio de imágenes
    images_dir = Path("data/images")
    if not images_dir.exists():
        logger.error(f"❌ Directorio {images_dir} no existe")
        logger.info("   Ejecuta primero: python convertir_pdfs_a_png.py")
        return

    # Obtener todas las imágenes
    imagenes = list(images_dir.rglob("*.png"))

    if not imagenes:
        logger.error(f"❌ No se encontraron imágenes en {images_dir}")
        return

    logger.info(f"📸 Total de imágenes encontradas: {len(imagenes)}")

    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Inicializar modelo
    try:
        tokenizer, model = inicializar_modelo()
    except Exception as e:
        logger.error(f"❌ No se pudo cargar el modelo: {e}")
        logger.info("\nAsegúrate de tener instaladas las dependencias:")
        logger.info("  pip install -r requirements_fase2.txt")
        return

    # Procesar imágenes
    resultados = []

    logger.info("\n🔄 Iniciando procesamiento OCR...")

    with tqdm(total=len(imagenes), desc="Procesando OCR", unit="img") as pbar:
        for imagen_path in imagenes:
            # Determinar estructura de salida
            # data/images/BBVA/archivo/pagina_001.png
            # → data/ocr/BBVA/archivo/pagina_001.md

            relpath = imagen_path.relative_to(images_dir)
            output_path = OUTPUT_DIR / relpath.with_suffix('.md')
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Procesar
            resultado = procesar_imagen(tokenizer, model, imagen_path, output_path)
            resultados.append(resultado)

            # Guardar markdown
            if resultado["exito"]:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(resultado["markdown"])

            pbar.update(1)

    # Estadísticas finales
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN DE OCR")
    logger.info("=" * 70)

    exitosos = [r for r in resultados if r["exito"]]
    fallidos = [r for r in resultados if not r["exito"]]
    tiempo_total = sum(r["tiempo"] for r in resultados)

    logger.info(f"Imágenes procesadas:   {len(imagenes)}")
    logger.info(f"OCR exitoso:           {len(exitosos)} ✅")
    logger.info(f"OCR fallido:           {len(fallidos)} ❌")
    logger.info(f"Tiempo total:          {tiempo_total:.2f}s ({tiempo_total/60:.2f} min)")
    logger.info(f"Promedio por imagen:   {tiempo_total/len(imagenes):.2f}s")

    if fallidos:
        logger.warning("\n⚠️ Imágenes con errores:")
        for r in fallidos[:10]:  # Mostrar solo primeros 10
            logger.warning(f"  - {r['imagen']}: {r['error']}")
        if len(fallidos) > 10:
            logger.warning(f"  ... y {len(fallidos) - 10} más")

    logger.info("=" * 70)
    logger.info(f"✅ Archivos Markdown guardados en: {OUTPUT_DIR}/")
    logger.info("=" * 70)

    # Guardar reporte
    reporte = {
        "total_imagenes": len(imagenes),
        "exitosos": len(exitosos),
        "fallidos": len(fallidos),
        "tiempo_total_segundos": tiempo_total,
        "configuracion": {
            "batch_size": BATCH_SIZE,
            "base_size": BASE_SIZE,
            "image_size": IMAGE_SIZE,
            "device": "cpu"
        },
        "resultados": resultados
    }

    reporte_path = Path("data/processed/reporte_ocr_deepseek.json")

    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Reporte guardado en: {reporte_path}")


if __name__ == "__main__":
    main()
