#!/usr/bin/env python3
"""
Extractor de JSONs a CSV según especificaciones del EXAMEN PARCIAL
Columnas requeridas: Banco, Producto, Tasa, Moneda, Fecha de registro, Observaciones
"""
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
import sys
import pandas as pd

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Directorios
PROJECT_ROOT = Path(__file__).parent.parent
JSON_DIR = PROJECT_ROOT / "data" / "normalized_json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"

# Configuración
OUTPUT_CSV = OUTPUT_DIR / "EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.csv"
OUTPUT_EXCEL = OUTPUT_DIR / "EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.xlsx"


def extract_items_from_json(json_file: Path, banco_name: str) -> List[Dict[str, Any]]:
    """
    Extrae items de un JSON normalizado según formato del EXAMEN PARCIAL

    Columnas requeridas:
    - Banco
    - Producto
    - Tasa (puede ser tasa porcentual o monto fijo)
    - Moneda (MN | ME | AMBAS)
    - Fecha de registro (vigencia)
    - Observaciones
    """
    items_extraidos = []

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Procesar cada documento del batch
        for documento in data.get('documentos', []):
            metadata = documento.get('metadata', {})
            producto_nombre = metadata.get('producto_nombre', metadata.get('producto_codigo', 'N/A'))
            fecha_extraccion = metadata.get('fecha_extraccion', '')
            tipo_cliente = metadata.get('tipo_cliente', '')
            segmento = metadata.get('segmento', '')

            # Procesar cada item del documento
            for item in documento.get('items', []):
                # Saltar encabezados
                jerarquia = item.get('jerarquia', {})
                if jerarquia and jerarquia.get('es_encabezado', False):
                    continue

                clasificacion = item.get('clasificacion', {})
                concepto = item.get('concepto', {})
                valores = item.get('valores', {})
                aplicacion = item.get('aplicacion', {})
                metadata_item = item.get('metadata_item', {})

                # Extraer valores
                tipo = clasificacion.get('tipo', 'N/A')
                nombre_concepto = concepto.get('nombre', 'N/A')
                descripcion_breve = concepto.get('descripcion_breve', '')

                moneda = valores.get('moneda', '') if valores else ''

                # Construir campo TASA (puede ser porcentaje o monto)
                tasa_info = []

                # Tasas porcentuales MN
                if valores and valores.get('mn'):
                    mn = valores['mn']
                    if mn.get('tasa_porcentaje') is not None:
                        tasa_info.append(f"MN: {mn['tasa_porcentaje']}%")
                    elif mn.get('monto_fijo') is not None:
                        tasa_info.append(f"MN: S/ {mn['monto_fijo']}")
                    elif mn.get('monto_minimo') is not None or mn.get('monto_maximo') is not None:
                        if mn.get('monto_minimo') and mn.get('monto_maximo'):
                            tasa_info.append(f"MN: S/ {mn['monto_minimo']} - S/ {mn['monto_maximo']}")
                        elif mn.get('monto_minimo'):
                            tasa_info.append(f"MN: Mín S/ {mn['monto_minimo']}")
                        elif mn.get('monto_maximo'):
                            tasa_info.append(f"MN: Máx S/ {mn['monto_maximo']}")

                # Tasas porcentuales ME
                if valores and valores.get('me'):
                    me = valores['me']
                    if me.get('tasa_porcentaje') is not None:
                        tasa_info.append(f"ME: {me['tasa_porcentaje']}%")
                    elif me.get('monto_fijo') is not None:
                        tasa_info.append(f"ME: $ {me['monto_fijo']}")
                    elif me.get('monto_minimo') is not None or me.get('monto_maximo') is not None:
                        if me.get('monto_minimo') and me.get('monto_maximo'):
                            tasa_info.append(f"ME: $ {me['monto_minimo']} - $ {me['monto_maximo']}")
                        elif me.get('monto_minimo'):
                            tasa_info.append(f"ME: Mín $ {me['monto_minimo']}")
                        elif me.get('monto_maximo'):
                            tasa_info.append(f"ME: Máx $ {me['monto_maximo']}")

                tasa_str = " | ".join(tasa_info) if tasa_info else "N/A"

                # Fecha de registro (vigencia)
                fecha_registro = aplicacion.get('vigencia', '') if aplicacion else ''
                if not fecha_registro:
                    fecha_registro = fecha_extraccion

                # Observaciones (concatenar información relevante)
                observaciones_partes = []

                # Tipo de item
                observaciones_partes.append(f"Tipo: {tipo}")

                # Descripción breve
                if descripcion_breve:
                    observaciones_partes.append(descripcion_breve)

                # Descripción detallada
                if concepto.get('descripcion_detallada'):
                    observaciones_partes.append(concepto['descripcion_detallada'])

                # Periodicidad
                if aplicacion and aplicacion.get('periodicidad'):
                    observaciones_partes.append(f"Periodicidad: {aplicacion['periodicidad']}")

                # Oportunidad de cobro
                if aplicacion and aplicacion.get('oportunidad_cobro'):
                    observaciones_partes.append(f"Cobro: {aplicacion['oportunidad_cobro']}")

                # Condiciones
                if aplicacion and aplicacion.get('condiciones'):
                    observaciones_partes.append(f"Condiciones: {aplicacion['condiciones']}")

                # Cliente
                if tipo_cliente:
                    observaciones_partes.append(f"Cliente: {tipo_cliente}")

                # Segmento
                if segmento:
                    observaciones_partes.append(f"Segmento: {segmento}")

                # Categoría
                if clasificacion.get('categoria'):
                    observaciones_partes.append(f"Categoría: {clasificacion['categoria']}")

                observaciones = " | ".join(observaciones_partes)

                # Crear fila según formato del EXAMEN
                row = {
                    'Banco': banco_name,
                    'Producto': producto_nombre,
                    'Tasa': tasa_str,
                    'Moneda': moneda,
                    'Fecha de registro': fecha_registro,
                    'Observaciones': observaciones
                }

                items_extraidos.append(row)

        logger.debug(f"  Extraídos {len(items_extraidos)} items de {json_file.name}")

    except Exception as e:
        logger.error(f"  Error procesando {json_file}: {e}")

    return items_extraidos


def main():
    logger.info("=" * 80)
    logger.info("📊 EXTRACCIÓN PARA EXAMEN PARCIAL - GRUPO 2")
    logger.info("=" * 80)
    logger.info("Formato: Banco | Producto | Tasa | Moneda | Fecha de registro | Observaciones")
    logger.info(f"📂 Directorio JSONs: {JSON_DIR}")
    logger.info(f"📁 Directorio output: {OUTPUT_DIR}")

    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Recopilar todos los items
    logger.info("\n🔍 Procesando archivos JSON...")

    all_items = []
    bancos_stats = {}

    for banco_dir in sorted(JSON_DIR.iterdir()):
        if not banco_dir.is_dir():
            continue

        banco_name = banco_dir.name
        json_files = sorted(banco_dir.glob("*.json"))

        logger.info(f"\n🏦 {banco_name}: {len(json_files)} batches")

        banco_items = 0
        for json_file in json_files:
            items = extract_items_from_json(json_file, banco_name)
            all_items.extend(items)
            banco_items += len(items)

        bancos_stats[banco_name] = banco_items
        logger.success(f"  ✅ Extraídos {banco_items} items de {banco_name}")

    # Verificar datos
    if not all_items:
        logger.error("❌ No se extrajeron items")
        return

    logger.info(f"\n📊 Total items extraídos: {len(all_items)}")

    # Guardar CSV
    logger.info(f"\n💾 Guardando CSV: {OUTPUT_CSV}")

    fieldnames = ['Banco', 'Producto', 'Tasa', 'Moneda', 'Fecha de registro', 'Observaciones']

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)

    logger.success(f"✅ CSV guardado: {OUTPUT_CSV}")
    logger.info(f"   Tamaño: {OUTPUT_CSV.stat().st_size / 1024:.2f} KB")
    logger.info(f"   Filas: {len(all_items) + 1} (incluye header)")

    # Guardar Excel
    logger.info(f"\n💾 Guardando Excel: {OUTPUT_EXCEL}")

    df = pd.DataFrame(all_items)

    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # Hoja principal
        df.to_excel(writer, sheet_name='Tarifarios Bancarios', index=False)

        # Hoja de resumen
        resumen_df = pd.DataFrame([
            {'Banco': banco, 'Total_Items': count}
            for banco, count in sorted(bancos_stats.items())
        ])
        resumen_df.to_excel(writer, sheet_name='Resumen por Banco', index=False)

        # Estadísticas
        stats_data = {
            'Métrica': [
                'Total de registros',
                'Total de bancos',
                'Fecha de extracción',
                'Grupo',
                'Curso'
            ],
            'Valor': [
                len(all_items),
                len(bancos_stats),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Grupo 2',
                'Analítica de Datos - UNI FIIS'
            ]
        }
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='Metadatos', index=False)

        # Ajustar anchos de columna
        worksheet = writer.sheets['Tarifarios Bancarios']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 60)

    logger.success(f"✅ Excel guardado: {OUTPUT_EXCEL}")
    logger.info(f"   Tamaño: {OUTPUT_EXCEL.stat().st_size / 1024:.2f} KB")

    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.info("📊 RESUMEN FINAL - EXAMEN PARCIAL")
    logger.info("=" * 80)
    logger.info(f"Total registros extraídos:  {len(all_items)}")
    logger.info(f"Total bancos procesados:    {len(bancos_stats)}")
    logger.info("")
    logger.info("Distribución por banco:")
    for banco, count in sorted(bancos_stats.items()):
        porcentaje = (count / len(all_items)) * 100
        logger.info(f"  {banco:30} {count:4} items ({porcentaje:5.2f}%)")
    logger.info("=" * 80)

    logger.success("\n✅ Dataset para EXAMEN PARCIAL generado exitosamente")
    logger.info(f"📄 CSV:   {OUTPUT_CSV}")
    logger.info(f"📊 Excel: {OUTPUT_EXCEL}")
    logger.info("\nColumnas generadas:")
    logger.info("  1. Banco              - Nombre de la institución bancaria")
    logger.info("  2. Producto           - Nombre del producto financiero")
    logger.info("  3. Tasa               - Tasa/monto (MN y/o ME)")
    logger.info("  4. Moneda             - MN | ME | AMBAS")
    logger.info("  5. Fecha de registro  - Fecha de vigencia")
    logger.info("  6. Observaciones      - Tipo, descripción, condiciones, etc.")


if __name__ == "__main__":
    main()
