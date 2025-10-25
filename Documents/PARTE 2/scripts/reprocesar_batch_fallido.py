#!/usr/bin/env python3
"""
Reprocesar el batch que falló por rate limit
"""
import os
import sys
import json
import time
from pathlib import Path
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Cargar variables de entorno
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / "config" / ".env")

# Directorios
BATCHES_DIR = PROJECT_ROOT / "data" / "batches_combinados"
OUTPUT_DIR = PROJECT_ROOT / "data" / "normalized_json"

# Configuración
MODEL_NAME = "gemini-2.5-flash-lite"

# Importar esquema (simplificado para JsonOutputParser)
class BatchOutput(BaseModel):
    batch_metadata: dict
    documentos: List[dict]
    resumen_batch: Optional[dict] = None


# Importar prompt del script principal
from normalizar_batches_a_json import PROMPT_NORMALIZACION


def process_batch_with_gemini(batch_content: str, batch_path: Path, model, parser) -> dict:
    """Procesa un batch con Gemini"""
    logger.info(f"  🤖 Enviando a Gemini ({len(batch_content):,} chars)...")

    # Crear prompt completo
    full_prompt = PROMPT_NORMALIZACION + "\n\n" + parser.get_format_instructions() + f"\n\nBATCH CONTENT:\n{batch_content}"

    try:
        # Invocar modelo
        response = model.invoke(full_prompt)

        # Parsear JSON
        json_data = parser.parse(response.content)

        # Validación básica
        if not isinstance(json_data, dict):
            raise ValueError("La respuesta no es un diccionario válido")

        if "documentos" not in json_data:
            raise ValueError("El JSON no contiene el campo 'documentos'")

        total_docs = len(json_data.get('documentos', []))
        logger.success(f"  ✅ Batch procesado: {total_docs} documentos")

        return json_data

    except Exception as e:
        logger.error(f"  ❌ Error procesando batch: {e}")
        if 'response' in locals():
            logger.debug(f"  Raw output: {response.content[:1000]}")
        raise


def main():
    logger.info("=" * 70)
    logger.info("🔄 REPROCESANDO BATCH FALLIDO: BCP/batch_002.txt")
    logger.info("=" * 70)

    # Verificar API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY no configurada")
        return

    logger.success("✅ API Key encontrada")

    # Configurar modelo
    logger.info("🔧 Configurando Gemini...")
    model = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0,
        max_output_tokens=16384,
        google_api_key=api_key,
    )

    # Configurar parser
    parser = JsonOutputParser(pydantic_object=BatchOutput)
    logger.success("✅ Modelo configurado")

    # Leer batch
    batch_path = BATCHES_DIR / "BCP" / "batch_002.txt"
    logger.info(f"\n📂 Leyendo: {batch_path}")

    if not batch_path.exists():
        logger.error(f"❌ Archivo no encontrado: {batch_path}")
        return

    batch_content = batch_path.read_text(encoding='utf-8')
    logger.success(f"✅ Leído: {len(batch_content):,} caracteres")

    # Procesar
    logger.info("\n🚀 Procesando batch...")
    start_time = time.time()

    try:
        json_data = process_batch_with_gemini(batch_content, batch_path, model, parser)
        elapsed = time.time() - start_time

        # Guardar JSON
        output_dir = OUTPUT_DIR / "BCP"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "batch_002.json"

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.success(f"💾 JSON guardado: {json_path}")

        # Estadísticas
        total_docs = len(json_data.get('documentos', []))
        total_items = sum(
            d.get('control_calidad', {}).get('total_items_extraidos', 0)
            for d in json_data.get('documentos', [])
        )

        logger.info(f"\n📊 Estadísticas:")
        logger.info(f"  Documentos: {total_docs}")
        logger.info(f"  Items: {total_items}")
        logger.info(f"  Tiempo: {elapsed:.1f}s")

        logger.success("\n✅ Reprocesamiento completado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return


if __name__ == "__main__":
    main()
