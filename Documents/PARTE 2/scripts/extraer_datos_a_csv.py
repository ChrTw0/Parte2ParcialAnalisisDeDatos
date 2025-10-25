#!/usr/bin/env python3
"""
Script para extraer datos de archivos Markdown (OCR) y generar CSV
"""
import sys
from pathlib import Path
import pandas as pd
import re
from datetime import datetime
from tqdm import tqdm
from loguru import logger
import json

# Expresiones regulares para extraer datos
PATTERNS = {
    'tasa_porcentaje': r'(\d+\.?\d*)\s*%',
    'monto_soles': r'S/\.?\s*(\d+\.?\d*)',
    'monto_dolares': r'US?\$\s*(\d+\.?\d*)',
    'tcea': r'TCEA:?\s*(\d+\.?\d*)\s*%',
    'tea': r'TEA:?\s*(\d+\.?\d*)\s*%',
    'tem': r'TEM:?\s*(\d+\.?\d*)\s*%',
}

def extraer_banco_desde_path(md_path: Path) -> str:
    """Extrae el nombre del banco desde la ruta del archivo"""
    # data/ocr/BBVA_Continental/archivo/pagina_001.md
    parts = md_path.parts
    if len(parts) >= 3 and parts[0] == 'data' and parts[1] == 'ocr':
        return parts[2]
    return "Desconocido"


def parsear_tabla_markdown(md_content: str) -> list:
    """
    Parsea tablas en formato Markdown y extrae filas

    Ejemplo de tabla Markdown:
    | Producto | Tasa | Moneda |
    |----------|------|--------|
    | Crédito  | 15%  | S/     |
    """
    filas = []

    # Buscar tablas (líneas que empiezan con |)
    lineas = md_content.split('\n')
    tabla_actual = []
    headers = []

    for linea in lineas:
        linea = linea.strip()

        # Detectar inicio de tabla
        if linea.startswith('|') and linea.endswith('|'):
            # Separar celdas
            celdas = [c.strip() for c in linea.split('|')[1:-1]]

            # Ignorar líneas separadoras (---)
            if all('---' in c or '-' * 3 in c for c in celdas):
                continue

            # Primera línea de tabla = headers
            if not headers:
                headers = celdas
                continue

            # Filas de datos
            if len(celdas) == len(headers):
                fila = dict(zip(headers, celdas))
                filas.append(fila)

    return filas


def extraer_datos_de_markdown(md_path: Path) -> list:
    """
    Extrae datos estructurados de un archivo Markdown

    Returns:
        list de dicts con datos extraídos
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        banco = extraer_banco_desde_path(md_path)
        pdf_name = md_path.parent.name
        pagina = int(re.search(r'pagina_(\d+)', md_path.stem).group(1))

        # Intentar parsear tablas primero
        filas_tabla = parsear_tabla_markdown(content)

        datos = []

        if filas_tabla:
            # Datos extraídos de tabla
            for fila in filas_tabla:
                dato = {
                    'Banco': banco,
                    'Producto': fila.get('Producto', '') or fila.get('Concepto', ''),
                    'Concepto': fila.get('Concepto', '') or fila.get('Descripción', ''),
                    'Tasa/Comisión': extraer_valor_numerico(fila),
                    'Moneda': extraer_moneda(fila),
                    'Tipo': determinar_tipo(fila),
                    'Unidad': extraer_unidad(fila),
                    'Fecha_Registro': datetime.now().strftime('%Y-%m-%d'),
                    'Observaciones': fila.get('Observaciones', '') or fila.get('Notas', ''),
                    'Fuente_PDF': pdf_name,
                    'Página': pagina,
                    'Metodo_Extraccion': 'DeepSeek-OCR-Tabla'
                }
                datos.append(dato)
        else:
            # Si no hay tabla, buscar patrones en texto libre
            # (Implementación básica, mejorar según necesidad)
            logger.debug(f"Sin tabla en {md_path.name}, buscando patrones...")

        return datos

    except Exception as e:
        logger.error(f"Error procesando {md_path}: {e}")
        return []


def extraer_valor_numerico(fila: dict) -> float:
    """Extrae valor numérico de una fila de tabla"""
    for key, value in fila.items():
        if any(k in key.lower() for k in ['tasa', 'comision', 'monto', 'importe', 'valor']):
            # Buscar número
            match = re.search(r'(\d+\.?\d*)', str(value))
            if match:
                return float(match.group(1))
    return 0.0


def extraer_moneda(fila: dict) -> str:
    """Extrae moneda de una fila"""
    text = ' '.join(str(v) for v in fila.values()).upper()

    if 'S/' in text or 'SOLES' in text or 'PEN' in text:
        return 'S/'
    elif 'US$' in text or '$' in text or 'USD' in text or 'DÓLARES' in text:
        return 'US$'
    elif 'UF' in text:
        return 'UF'
    else:
        return 'N/A'


def determinar_tipo(fila: dict) -> str:
    """Determina si es Tasa o Comisión"""
    text = ' '.join(str(v) for v in fila.values()).lower()

    if any(k in text for k in ['tea', 'tem', 'tcea', 'tasa', '%']):
        return 'Tasa'
    elif any(k in text for k in ['comision', 'comisión', 'cobro', 'cargo', 's/', 'us$']):
        return 'Comisión'
    else:
        return 'N/A'


def extraer_unidad(fila: dict) -> str:
    """Extrae unidad del valor"""
    text = ' '.join(str(v) for v in fila.values())

    if '%' in text:
        return 'Porcentaje'
    elif 'S/' in text or 'US$' in text:
        return 'Monto'
    else:
        return 'N/A'


def main():
    """Procesa todos los archivos Markdown y genera CSV"""

    logger.info("=" * 70)
    logger.info("📊 EXTRACCIÓN DE DATOS A CSV")
    logger.info("=" * 70)

    # Verificar directorio OCR
    ocr_dir = Path("data/ocr")
    if not ocr_dir.exists():
        logger.error(f"❌ Directorio {ocr_dir} no existe")
        logger.info("   Ejecuta primero: python procesar_ocr_deepseek.py")
        return

    # Obtener todos los archivos Markdown
    md_files = list(ocr_dir.rglob("*.md"))

    if not md_files:
        logger.error(f"❌ No se encontraron archivos .md en {ocr_dir}")
        return

    logger.info(f"📄 Total de archivos Markdown: {len(md_files)}")

    # Procesar cada archivo
    todos_los_datos = []

    logger.info("\n🔄 Extrayendo datos...")

    for md_path in tqdm(md_files, desc="Procesando Markdown", unit="file"):
        datos = extraer_datos_de_markdown(md_path)
        todos_los_datos.extend(datos)

    # Crear DataFrame
    if not todos_los_datos:
        logger.warning("⚠️ No se extrajeron datos de ningún archivo")
        return

    df = pd.DataFrame(todos_los_datos)

    # Estadísticas
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN DE EXTRACCIÓN")
    logger.info("=" * 70)
    logger.info(f"Archivos procesados:   {len(md_files)}")
    logger.info(f"Filas extraídas:       {len(df)}")
    logger.info(f"Bancos únicos:         {df['Banco'].nunique()}")
    logger.info(f"Productos únicos:      {df['Producto'].nunique()}")

    logger.info("\nDistribución por banco:")
    for banco, count in df['Banco'].value_counts().items():
        logger.info(f"  - {banco}: {count} filas")

    # Guardar CSV
    csv_path = Path("data/processed/tarifarios.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    logger.success(f"\n✅ CSV guardado: {csv_path}")

    # Guardar Excel con múltiples hojas
    excel_path = Path("data/processed/tarifarios.xlsx")

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Hoja principal con todos los datos
        df.to_excel(writer, sheet_name='Todos', index=False)

        # Hoja por banco
        for banco in df['Banco'].unique():
            df_banco = df[df['Banco'] == banco]
            # Nombre de hoja válido (máx 31 caracteres)
            sheet_name = banco[:31]
            df_banco.to_excel(writer, sheet_name=sheet_name, index=False)

    logger.success(f"✅ Excel guardado: {excel_path}")

    logger.info("=" * 70)
    logger.info("✅ PROCESO COMPLETADO")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
