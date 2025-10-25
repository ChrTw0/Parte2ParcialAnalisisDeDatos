#!/usr/bin/env python3
"""
Extractor de JSONs normalizados a CSV/Excel
Genera dataset final con: Banco, Producto, Tasa, Moneda, Fecha de registro, Observaciones
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
OUTPUT_CSV = OUTPUT_DIR / "tarifarios_bancarios.csv"
OUTPUT_EXCEL = OUTPUT_DIR / "tarifarios_bancarios.xlsx"


def extract_items_from_json(json_file: Path, banco_name: str) -> List[Dict[str, Any]]:
    """
    Extrae items de un JSON normalizado y los convierte al formato CSV requerido

    Formato de salida:
    - Banco: Nombre del banco
    - Producto: Nombre del producto bancario
    - Concepto: Nombre del concepto/item
    - Tipo: TASA | COMISION | GASTO | SEGURO | OTRO
    - Tasa_Porcentaje_MN: % en moneda nacional
    - Tasa_Porcentaje_ME: % en moneda extranjera
    - Monto_Fijo_MN: Monto fijo en soles
    - Monto_Fijo_ME: Monto fijo en dólares
    - Monto_Minimo_MN: Monto mínimo en soles
    - Monto_Maximo_MN: Monto máximo en soles
    - Monto_Minimo_ME: Monto mínimo en dólares
    - Monto_Maximo_ME: Monto máximo en dólares
    - Moneda: MN | ME | AMBAS
    - Fecha_Vigencia: DD/MM/YYYY
    - Fecha_Extraccion: YYYY-MM-DD
    - Periodicidad: Mensual | Anual | Por operación
    - Observaciones: Condiciones y notas
    """
    items_extraidos = []

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Procesar cada documento del batch
        for documento in data.get('documentos', []):
            metadata = documento.get('metadata', {})
            producto_codigo = metadata.get('producto_codigo', 'N/A')
            producto_nombre = metadata.get('producto_nombre', producto_codigo)
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

                # Inicializar valores
                tasa_pct_mn = None
                tasa_pct_me = None
                monto_fijo_mn = None
                monto_fijo_me = None
                monto_min_mn = None
                monto_max_mn = None
                monto_min_me = None
                monto_max_me = None
                moneda = valores.get('moneda', '') if valores else ''

                # Extraer valores MN
                if valores and valores.get('mn'):
                    mn = valores['mn']
                    tasa_pct_mn = mn.get('tasa_porcentaje')
                    monto_fijo_mn = mn.get('monto_fijo')
                    monto_min_mn = mn.get('monto_minimo')
                    monto_max_mn = mn.get('monto_maximo')

                # Extraer valores ME
                if valores and valores.get('me'):
                    me = valores['me']
                    tasa_pct_me = me.get('tasa_porcentaje')
                    monto_fijo_me = me.get('monto_fijo')
                    monto_min_me = me.get('monto_minimo')
                    monto_max_me = me.get('monto_maximo')

                # Fechas y periodicidad
                fecha_vigencia = aplicacion.get('vigencia', '') if aplicacion else ''
                periodicidad = aplicacion.get('periodicidad', '') if aplicacion else ''
                oportunidad_cobro = aplicacion.get('oportunidad_cobro', '') if aplicacion else ''

                # Observaciones (concatenar varias fuentes)
                observaciones_partes = []

                if concepto.get('descripcion_detallada'):
                    observaciones_partes.append(concepto['descripcion_detallada'])

                if aplicacion and aplicacion.get('condiciones'):
                    observaciones_partes.append(f"Condiciones: {aplicacion['condiciones']}")

                if metadata_item and metadata_item.get('observaciones_adicionales'):
                    observaciones_partes.extend(metadata_item['observaciones_adicionales'])

                if tipo_cliente:
                    observaciones_partes.append(f"Cliente: {tipo_cliente}")

                if segmento:
                    observaciones_partes.append(f"Segmento: {segmento}")

                observaciones = " | ".join(observaciones_partes) if observaciones_partes else ''

                # Crear fila
                row = {
                    'Banco': banco_name,
                    'Producto_Codigo': producto_codigo,
                    'Producto_Nombre': producto_nombre,
                    'Concepto': nombre_concepto,
                    'Descripcion_Breve': descripcion_breve,
                    'Tipo': tipo,
                    'Tasa_Porcentaje_MN': tasa_pct_mn,
                    'Tasa_Porcentaje_ME': tasa_pct_me,
                    'Monto_Fijo_MN': monto_fijo_mn,
                    'Monto_Fijo_ME': monto_fijo_me,
                    'Monto_Minimo_MN': monto_min_mn,
                    'Monto_Maximo_MN': monto_max_mn,
                    'Monto_Minimo_ME': monto_min_me,
                    'Monto_Maximo_ME': monto_max_me,
                    'Moneda': moneda,
                    'Fecha_Vigencia': fecha_vigencia,
                    'Fecha_Extraccion': fecha_extraccion,
                    'Periodicidad': periodicidad,
                    'Oportunidad_Cobro': oportunidad_cobro,
                    'Observaciones': observaciones
                }

                items_extraidos.append(row)

        logger.debug(f"  Extraídos {len(items_extraidos)} items de {json_file.name}")

    except Exception as e:
        logger.error(f"  Error procesando {json_file}: {e}")

    return items_extraidos


def main():
    logger.info("=" * 70)
    logger.info("📊 EXTRACCIÓN DE JSONs A CSV/EXCEL")
    logger.info("=" * 70)
    logger.info(f"📂 Directorio JSONs: {JSON_DIR}")
    logger.info(f"📁 Directorio output: {OUTPUT_DIR}")

    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Recopilar todos los items de todos los JSONs
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

    # Verificar que se extrajeron datos
    if not all_items:
        logger.error("❌ No se extrajeron items. Verifica los archivos JSON.")
        return

    logger.info(f"\n📊 Total items extraídos: {len(all_items)}")

    # Guardar CSV
    logger.info(f"\n💾 Guardando CSV: {OUTPUT_CSV}")

    fieldnames = [
        'Banco',
        'Producto_Codigo',
        'Producto_Nombre',
        'Concepto',
        'Descripcion_Breve',
        'Tipo',
        'Tasa_Porcentaje_MN',
        'Tasa_Porcentaje_ME',
        'Monto_Fijo_MN',
        'Monto_Fijo_ME',
        'Monto_Minimo_MN',
        'Monto_Maximo_MN',
        'Monto_Minimo_ME',
        'Monto_Maximo_ME',
        'Moneda',
        'Fecha_Vigencia',
        'Fecha_Extraccion',
        'Periodicidad',
        'Oportunidad_Cobro',
        'Observaciones'
    ]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_items)

    logger.success(f"✅ CSV guardado: {OUTPUT_CSV}")
    logger.info(f"   Tamaño: {OUTPUT_CSV.stat().st_size / 1024:.2f} KB")

    # Guardar Excel con formato mejorado
    logger.info(f"\n💾 Guardando Excel: {OUTPUT_EXCEL}")

    df = pd.DataFrame(all_items)

    # Crear Excel con formato
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # Hoja principal con todos los datos
        df.to_excel(writer, sheet_name='Tarifarios', index=False)

        # Hoja de resumen por banco
        resumen_df = pd.DataFrame([
            {'Banco': banco, 'Total_Items': count}
            for banco, count in sorted(bancos_stats.items())
        ])
        resumen_df.to_excel(writer, sheet_name='Resumen', index=False)

        # Hoja de resumen por tipo
        tipo_df = df.groupby('Tipo').size().reset_index(name='Cantidad')
        tipo_df.to_excel(writer, sheet_name='Por_Tipo', index=False)

        # Ajustar anchos de columna en la hoja principal
        worksheet = writer.sheets['Tarifarios']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)

    logger.success(f"✅ Excel guardado: {OUTPUT_EXCEL}")
    logger.info(f"   Tamaño: {OUTPUT_EXCEL.stat().st_size / 1024:.2f} KB")

    # Resumen final
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"Total items extraídos:     {len(all_items)}")
    logger.info(f"Total bancos procesados:   {len(bancos_stats)}")
    logger.info("")
    logger.info("Por banco:")
    for banco, count in sorted(bancos_stats.items()):
        logger.info(f"  {banco:30} {count:4} items")
    logger.info("")
    logger.info("Por tipo:")
    tipo_counts = df['Tipo'].value_counts()
    for tipo, count in tipo_counts.items():
        logger.info(f"  {tipo:30} {count:4} items")
    logger.info("=" * 70)

    logger.success("\n✅ Extracción completada exitosamente")
    logger.info(f"📄 CSV:   {OUTPUT_CSV}")
    logger.info(f"📊 Excel: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()
