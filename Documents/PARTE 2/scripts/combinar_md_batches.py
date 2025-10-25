#!/usr/bin/env python3
"""
Script para combinar archivos .md en batches de 10
Prepara archivos para normalización con Gemini
"""
import random
from pathlib import Path
from loguru import logger
import sys

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Directorios
PROJECT_ROOT = Path(__file__).parent.parent
OCR_DIR = PROJECT_ROOT / "data" / "ocr"
BATCHES_DIR = PROJECT_ROOT / "data" / "batches_combinados"

# Configuración
ARCHIVOS_POR_BATCH = 10


def get_md_files_by_banco() -> dict[str, list[Path]]:
    """Obtiene archivos .md agrupados por banco"""
    files_by_banco = {}

    for banco_dir in OCR_DIR.iterdir():
        if not banco_dir.is_dir():
            continue

        banco_name = banco_dir.name
        md_files = list(banco_dir.glob("*.md"))

        if md_files:
            files_by_banco[banco_name] = md_files

    return files_by_banco


def create_batch_file(batch_files: list[Path], batch_number: int, banco_name: str, batch_number_banco: int) -> Path:
    """
    Combina múltiples .md en un solo archivo batch

    Formato del batch:
    ---DOCUMENT_START---
    FILE_NUMBER: 1/10
    BANCO: BBVA_Continental
    PRODUCTO: adelanto-ppjj
    FILENAME: adelanto-ppjj.md
    FILEPATH: BBVA_Continental/adelanto-ppjj.md
    ---CONTENT_START---
    [contenido del .md]
    ---CONTENT_END---
    """
    # Crear carpeta del banco
    banco_dir = BATCHES_DIR / banco_name
    banco_dir.mkdir(parents=True, exist_ok=True)

    batch_filename = f"batch_{batch_number_banco:03d}.txt"
    batch_path = banco_dir / batch_filename

    with open(batch_path, 'w', encoding='utf-8') as f:
        for i, md_file in enumerate(batch_files, 1):
            banco = md_file.parent.name
            producto = md_file.stem
            filepath_relativo = f"{banco}/{md_file.name}"

            # Leer contenido del .md
            try:
                content = md_file.read_text(encoding='utf-8')
            except Exception as e:
                logger.warning(f"Error leyendo {md_file.name}: {e}")
                content = f"[ERROR: No se pudo leer el archivo - {e}]"

            # Escribir con delimitadores
            f.write(f"---DOCUMENT_START---\n")
            f.write(f"FILE_NUMBER: {i}/{len(batch_files)}\n")
            f.write(f"BANCO: {banco}\n")
            f.write(f"PRODUCTO: {producto}\n")
            f.write(f"FILENAME: {md_file.name}\n")
            f.write(f"FILEPATH: {filepath_relativo}\n")
            f.write(f"---CONTENT_START---\n")
            f.write(content)
            f.write(f"\n---CONTENT_END---\n\n")

    return batch_path


def create_batch_manifest(batches_info: list[dict]) -> Path:
    """Crea archivo manifest.txt con información de todos los batches"""
    manifest_path = BATCHES_DIR / "manifest.txt"

    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("MANIFEST DE BATCHES COMBINADOS POR BANCO\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total de archivos .md procesados: {sum(b['total_archivos'] for b in batches_info)}\n")
        f.write(f"Total de batches creados: {len(batches_info)}\n")
        f.write(f"Archivos por batch: {ARCHIVOS_POR_BATCH}\n\n")

        # Resumen por banco
        bancos = {}
        for batch_info in batches_info:
            banco = batch_info['banco']
            if banco not in bancos:
                bancos[banco] = {"batches": 0, "archivos": 0}
            bancos[banco]["batches"] += 1
            bancos[banco]["archivos"] += batch_info['total_archivos']

        f.write("=" * 70 + "\n")
        f.write("RESUMEN POR BANCO:\n")
        f.write("=" * 70 + "\n\n")
        for banco, info in sorted(bancos.items()):
            f.write(f"{banco}:\n")
            f.write(f"  Batches: {info['batches']}\n")
            f.write(f"  Archivos: {info['archivos']}\n\n")

        f.write("=" * 70 + "\n")
        f.write("DETALLE POR BATCH:\n")
        f.write("=" * 70 + "\n\n")

        for batch_info in batches_info:
            f.write(f"Batch {batch_info['numero']:03d} [{batch_info['banco']}]:\n")
            f.write(f"  Archivo: {batch_info['archivo']}\n")
            f.write(f"  Archivos incluidos: {batch_info['total_archivos']}\n")
            f.write(f"  Tamaño: {batch_info['tamaño_kb']:.2f} KB\n")
            f.write(f"  Tokens estimados: {batch_info['tokens_estimados']:,}\n")
            f.write(f"  Archivos:\n")
            for archivo in batch_info['archivos']:
                f.write(f"    - {archivo}\n")
            f.write("\n")

    return manifest_path


def main():
    logger.info("=" * 70)
    logger.info("🔄 COMBINADOR DE ARCHIVOS .md EN BATCHES POR BANCO")
    logger.info("=" * 70)
    logger.info(f"📁 Directorio OCR: {OCR_DIR}")
    logger.info(f"📦 Directorio batches: {BATCHES_DIR}")
    logger.info(f"📊 Archivos por batch: {ARCHIVOS_POR_BATCH}")

    # Crear directorio de batches
    BATCHES_DIR.mkdir(parents=True, exist_ok=True)

    # Obtener archivos agrupados por banco
    logger.info("\n🔍 Buscando archivos .md por banco...")
    files_by_banco = get_md_files_by_banco()

    total_archivos = sum(len(files) for files in files_by_banco.values())
    logger.success(f"✅ Encontrados {total_archivos} archivos en {len(files_by_banco)} bancos")

    # Mostrar resumen por banco
    logger.info("\n📊 Archivos por banco:")
    for banco, files in sorted(files_by_banco.items()):
        logger.info(f"  {banco:30} {len(files):3} archivos")

    # Crear batches por banco
    logger.info(f"\n📦 Creando batches de {ARCHIVOS_POR_BATCH} archivos por banco...")

    batches_info = []
    batch_number = 1

    for banco_name, md_files in sorted(files_by_banco.items()):
        logger.info(f"\n🏦 Procesando {banco_name} ({len(md_files)} archivos)...")

        # Mezclar aleatoriamente archivos del banco
        random.shuffle(md_files)

        # Crear batches para este banco
        batch_number_banco = 1
        for i in range(0, len(md_files), ARCHIVOS_POR_BATCH):
            batch_files = md_files[i:i + ARCHIVOS_POR_BATCH]

            logger.info(f"\n  Batch {batch_number_banco} de {banco_name}: {len(batch_files)} archivos")

            # Crear archivo batch
            batch_path = create_batch_file(batch_files, batch_number, banco_name, batch_number_banco)

            # Calcular estadísticas
            batch_size_bytes = batch_path.stat().st_size
            batch_size_kb = batch_size_bytes / 1024
            tokens_estimados = batch_size_bytes // 4  # 1 token ≈ 4 chars

            # Guardar info del batch
            batches_info.append({
                "numero": batch_number,
                "banco": banco_name,
                "archivo": f"{banco_name}/{batch_path.name}",
                "total_archivos": len(batch_files),
                "tamaño_kb": batch_size_kb,
                "tokens_estimados": tokens_estimados,
                "archivos": [f"{f.parent.name}/{f.name}" for f in batch_files]
            })

            logger.success(f"    ✅ Creado: {banco_name}/{batch_path.name} ({batch_size_kb:.2f} KB, ~{tokens_estimados:,} tokens)")

            # Mostrar primeros 3 archivos
            for j, md_file in enumerate(batch_files[:3], 1):
                logger.info(f"       {j}. {md_file.name}")

            if len(batch_files) > 3:
                logger.info(f"       ... y {len(batch_files) - 3} más")

            batch_number += 1
            batch_number_banco += 1

    # Crear manifest
    logger.info("\n📋 Creando archivo manifest...")
    manifest_path = create_batch_manifest(batches_info)
    logger.success(f"✅ Manifest creado: {manifest_path}")

    # Resumen final
    total_archivos = sum(b['total_archivos'] for b in batches_info)
    total_batches = len(batches_info)
    total_tokens = sum(b['tokens_estimados'] for b in batches_info)

    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN:")
    logger.info("=" * 70)
    logger.info(f"Total archivos .md:        {total_archivos}")
    logger.info(f"Total batches creados:     {total_batches}")
    logger.info(f"Archivos por batch:        {ARCHIVOS_POR_BATCH}")
    logger.info(f"Tokens totales estimados:  {total_tokens:,}")
    logger.info(f"Promedio tokens por batch: {total_tokens // total_batches:,}")
    logger.info("=" * 70)

    logger.success(f"\n✅ Proceso completado")
    logger.info(f"📁 Revisa los batches en: {BATCHES_DIR}")
    logger.info(f"📋 Revisa el manifest en: {manifest_path}")


if __name__ == "__main__":
    main()
