#!/usr/bin/env python3
"""
Script para importar tarifarios_bancarios.csv a MySQL
Crea base de datos, tablas y carga los datos con validación
"""
import sys
import pandas as pd
import mysql.connector
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Optional
import os
from dotenv import load_dotenv

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Directorios
PROJECT_ROOT = Path(__file__).parent.parent
CSV_FILE = PROJECT_ROOT / "data" / "output" / "tarifarios_bancarios.csv"

# Cargar configuración desde .env
load_dotenv(PROJECT_ROOT / "config" / ".env")

# Configuración de MySQL (valores por defecto si no están en .env)
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "port": int(os.getenv("MYSQL_PORT", "3306"))
}

DATABASE_NAME = "tarifarios_bancarios"


def crear_conexion(database: Optional[str] = None) -> mysql.connector.MySQLConnection:
    """Crea conexión a MySQL"""
    config = MYSQL_CONFIG.copy()
    if database:
        config["database"] = database

    try:
        conn = mysql.connector.connect(**config)
        logger.success(f"✅ Conexión exitosa a MySQL{' (DB: ' + database + ')' if database else ''}")
        return conn
    except mysql.connector.Error as e:
        logger.error(f"❌ Error conectando a MySQL: {e}")
        raise


def crear_base_datos(conn: mysql.connector.MySQLConnection):
    """Crea la base de datos si no existe"""
    cursor = conn.cursor()

    try:
        # Crear base de datos
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        logger.success(f"✅ Base de datos '{DATABASE_NAME}' creada/verificada")

        # Seleccionar base de datos
        cursor.execute(f"USE {DATABASE_NAME}")
        logger.info(f"📊 Usando base de datos '{DATABASE_NAME}'")

    except mysql.connector.Error as e:
        logger.error(f"❌ Error creando base de datos: {e}")
        raise
    finally:
        cursor.close()


def crear_tablas(conn: mysql.connector.MySQLConnection):
    """Crea las tablas necesarias"""
    cursor = conn.cursor()

    # SQL para crear tabla principal
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS tarifarios (
        id INT AUTO_INCREMENT PRIMARY KEY,

        -- Información del banco y producto
        banco VARCHAR(100) NOT NULL,
        producto_codigo VARCHAR(200) NOT NULL,
        producto_nombre VARCHAR(500),

        -- Concepto
        concepto VARCHAR(500),
        descripcion_breve TEXT,

        -- Clasificación
        tipo VARCHAR(20),

        -- Valores para Moneda Nacional (MN)
        tasa_porcentaje_mn DECIMAL(10, 4),
        monto_fijo_mn DECIMAL(15, 2),
        monto_minimo_mn DECIMAL(15, 2),
        monto_maximo_mn DECIMAL(15, 2),

        -- Valores para Moneda Extranjera (ME)
        tasa_porcentaje_me DECIMAL(10, 4),
        monto_fijo_me DECIMAL(15, 2),
        monto_minimo_me DECIMAL(15, 2),
        monto_maximo_me DECIMAL(15, 2),

        -- Moneda
        moneda VARCHAR(20),

        -- Fechas
        fecha_vigencia VARCHAR(20),
        fecha_extraccion VARCHAR(20),

        -- Aplicación
        periodicidad VARCHAR(200),
        oportunidad_cobro VARCHAR(500),

        -- Observaciones
        observaciones TEXT,

        -- Metadatos de carga
        fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- Índices para búsquedas eficientes
        INDEX idx_banco (banco),
        INDEX idx_tipo (tipo),
        INDEX idx_producto (producto_codigo),
        INDEX idx_moneda (moneda),
        INDEX idx_banco_tipo (banco, tipo)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    # SQL para tabla de resumen por banco
    create_resumen_sql = """
    CREATE TABLE IF NOT EXISTS resumen_por_banco (
        id INT AUTO_INCREMENT PRIMARY KEY,
        banco VARCHAR(100) NOT NULL UNIQUE,
        total_items INT DEFAULT 0,
        total_tasas INT DEFAULT 0,
        total_comisiones INT DEFAULT 0,
        total_gastos INT DEFAULT 0,
        total_seguros INT DEFAULT 0,
        total_otros INT DEFAULT 0,
        tasa_promedio_mn DECIMAL(10, 4),
        tasa_maxima_mn DECIMAL(10, 4),
        tasa_minima_mn DECIMAL(10, 4),
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    try:
        logger.info("\n📋 Creando tablas...")

        # Crear tabla principal
        cursor.execute(create_table_sql)
        logger.success("✅ Tabla 'tarifarios' creada/verificada")

        # Crear tabla de resumen
        cursor.execute(create_resumen_sql)
        logger.success("✅ Tabla 'resumen_por_banco' creada/verificada")

        conn.commit()

    except mysql.connector.Error as e:
        logger.error(f"❌ Error creando tablas: {e}")
        raise
    finally:
        cursor.close()


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y prepara los datos del DataFrame"""
    logger.info("\n🧹 Limpiando datos...")

    # Limpiar BOM si existe en columnas
    df.columns = df.columns.str.replace('\ufeff', '')

    # Limpiar espacios en blanco en columnas de texto
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Convertir cadenas problemáticas a NaN primero
    df = df.replace({
        '': pd.NA,
        'N/A': pd.NA,
        'nan': pd.NA,
        'NaN': pd.NA,
        'null': pd.NA,
        'NULL': pd.NA,
        'None': pd.NA
    })

    # Reemplazar todos los NaN/NA por None para MySQL
    df = df.where(pd.notnull(df), None)

    # Convertir columnas numéricas explícitamente
    numeric_cols = [
        'Tasa_Porcentaje_MN', 'Tasa_Porcentaje_ME',
        'Monto_Fijo_MN', 'Monto_Fijo_ME',
        'Monto_Minimo_MN', 'Monto_Maximo_MN',
        'Monto_Minimo_ME', 'Monto_Maximo_ME'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].where(pd.notnull(df[col]), None)

    logger.success(f"✅ Datos limpios: {len(df)} filas")

    return df


def truncar_tabla(conn: mysql.connector.MySQLConnection):
    """Trunca la tabla para empezar limpio"""
    cursor = conn.cursor()

    try:
        cursor.execute("TRUNCATE TABLE tarifarios")
        logger.info("🗑️  Tabla 'tarifarios' truncada")
        conn.commit()
    except mysql.connector.Error as e:
        logger.warning(f"⚠️  No se pudo truncar tabla (puede que esté vacía): {e}")
    finally:
        cursor.close()


def insertar_datos(conn: mysql.connector.MySQLConnection, df: pd.DataFrame):
    """Inserta los datos del DataFrame a MySQL"""
    cursor = conn.cursor()

    insert_sql = """
    INSERT INTO tarifarios (
        banco, producto_codigo, producto_nombre, concepto, descripcion_breve,
        tipo, tasa_porcentaje_mn, tasa_porcentaje_me, monto_fijo_mn, monto_fijo_me,
        monto_minimo_mn, monto_maximo_mn, monto_minimo_me, monto_maximo_me,
        moneda, fecha_vigencia, fecha_extraccion, periodicidad, oportunidad_cobro,
        observaciones
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """

    logger.info(f"\n📥 Insertando {len(df)} registros...")

    try:
        # Insertar en lotes de 100
        batch_size = 100
        total_insertados = 0
        errores = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]

            for idx, row in batch.iterrows():
                try:
                    # Función helper para convertir valores
                    def convert_value(val):
                        """Convierte valores problemáticos a None"""
                        if pd.isna(val):
                            return None
                        if isinstance(val, str):
                            val_lower = val.lower().strip()
                            if val_lower in ['nan', 'none', 'null', 'n/a', '']:
                                return None
                        return val

                    values = (
                        convert_value(row['Banco']),
                        convert_value(row['Producto_Codigo']),
                        convert_value(row['Producto_Nombre']),
                        convert_value(row['Concepto']),
                        convert_value(row['Descripcion_Breve']),
                        convert_value(row['Tipo']),
                        convert_value(row['Tasa_Porcentaje_MN']),
                        convert_value(row['Tasa_Porcentaje_ME']),
                        convert_value(row['Monto_Fijo_MN']),
                        convert_value(row['Monto_Fijo_ME']),
                        convert_value(row['Monto_Minimo_MN']),
                        convert_value(row['Monto_Maximo_MN']),
                        convert_value(row['Monto_Minimo_ME']),
                        convert_value(row['Monto_Maximo_ME']),
                        convert_value(row['Moneda']),
                        convert_value(row['Fecha_Vigencia']),
                        convert_value(row['Fecha_Extraccion']),
                        convert_value(row['Periodicidad']),
                        convert_value(row['Oportunidad_Cobro']),
                        convert_value(row['Observaciones'])
                    )

                    cursor.execute(insert_sql, values)
                    total_insertados += 1

                except mysql.connector.Error as e:
                    errores += 1
                    if errores <= 10:  # Mostrar solo los primeros 10 errores
                        logger.warning(f"⚠️  Error en fila {idx}: {e}")
                        logger.debug(f"   Banco: {row['Banco']} - Concepto: {str(row['Concepto'])[:50]}")
                        # Mostrar valores problemáticos
                        for i, col in enumerate(['Banco', 'Producto_Codigo', 'Concepto', 'Tipo']):
                            val = row[col]
                            logger.debug(f"   {col}: {val} (type: {type(val).__name__})")

            # Commit cada batch
            conn.commit()
            logger.info(f"  Progreso: {min(i + batch_size, len(df))}/{len(df)} ({(min(i + batch_size, len(df)) / len(df) * 100):.1f}%)")

        logger.success(f"\n✅ Datos insertados: {total_insertados} registros")
        if errores > 0:
            logger.warning(f"⚠️  Errores encontrados: {errores} registros")

    except Exception as e:
        logger.error(f"❌ Error general insertando datos: {e}")
        raise
    finally:
        cursor.close()


def actualizar_resumen(conn: mysql.connector.MySQLConnection):
    """Actualiza la tabla de resumen con estadísticas"""
    cursor = conn.cursor()

    logger.info("\n📊 Calculando resumen por banco...")

    try:
        # Limpiar tabla de resumen
        cursor.execute("TRUNCATE TABLE resumen_por_banco")

        # Insertar estadísticas
        insert_resumen_sql = """
        INSERT INTO resumen_por_banco (
            banco, total_items, total_tasas, total_comisiones,
            total_gastos, total_seguros, total_otros,
            tasa_promedio_mn, tasa_maxima_mn, tasa_minima_mn
        )
        SELECT
            banco,
            COUNT(*) as total_items,
            SUM(CASE WHEN tipo = 'TASA' THEN 1 ELSE 0 END) as total_tasas,
            SUM(CASE WHEN tipo = 'COMISION' THEN 1 ELSE 0 END) as total_comisiones,
            SUM(CASE WHEN tipo = 'GASTO' THEN 1 ELSE 0 END) as total_gastos,
            SUM(CASE WHEN tipo = 'SEGURO' THEN 1 ELSE 0 END) as total_seguros,
            SUM(CASE WHEN tipo = 'OTRO' THEN 1 ELSE 0 END) as total_otros,
            AVG(tasa_porcentaje_mn) as tasa_promedio_mn,
            MAX(tasa_porcentaje_mn) as tasa_maxima_mn,
            MIN(tasa_porcentaje_mn) as tasa_minima_mn
        FROM tarifarios
        GROUP BY banco
        ORDER BY banco
        """

        cursor.execute(insert_resumen_sql)
        conn.commit()

        # Mostrar resumen
        cursor.execute("SELECT * FROM resumen_por_banco")
        resultados = cursor.fetchall()

        logger.success(f"✅ Resumen calculado para {len(resultados)} bancos:")

        for row in resultados:
            banco = row[1]
            total = row[2]
            tasas = row[3]
            logger.info(f"  {banco:30s}: {total:4d} items ({tasas:3d} tasas)")

    except mysql.connector.Error as e:
        logger.error(f"❌ Error actualizando resumen: {e}")
        raise
    finally:
        cursor.close()


def mostrar_estadisticas(conn: mysql.connector.MySQLConnection):
    """Muestra estadísticas finales de la base de datos"""
    cursor = conn.cursor()

    logger.info("\n" + "=" * 70)
    logger.info("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
    logger.info("=" * 70)

    try:
        # Total de registros
        cursor.execute("SELECT COUNT(*) FROM tarifarios")
        total = cursor.fetchone()[0]
        logger.info(f"Total de registros:        {total:,}")

        # Por tipo
        cursor.execute("""
            SELECT tipo, COUNT(*) as total
            FROM tarifarios
            GROUP BY tipo
            ORDER BY total DESC
        """)
        logger.info("\nDistribución por tipo:")
        for tipo, count in cursor.fetchall():
            logger.info(f"  {tipo:15s}: {count:4d} ({count/total*100:5.1f}%)")

        # Por banco
        cursor.execute("""
            SELECT banco, COUNT(*) as total
            FROM tarifarios
            GROUP BY banco
            ORDER BY total DESC
        """)
        logger.info("\nDistribución por banco:")
        for banco, count in cursor.fetchall():
            logger.info(f"  {banco:30s}: {count:4d} ({count/total*100:5.1f}%)")

        # Top 5 tasas MN
        cursor.execute("""
            SELECT banco, concepto, tasa_porcentaje_mn
            FROM tarifarios
            WHERE tipo = 'TASA' AND tasa_porcentaje_mn IS NOT NULL
            ORDER BY tasa_porcentaje_mn DESC
            LIMIT 5
        """)
        logger.info("\nTop 5 tasas MN más altas:")
        for banco, concepto, tasa in cursor.fetchall():
            logger.info(f"  {tasa:7.2f}% - {banco} - {concepto[:50]}")

        logger.info("=" * 70)

    except mysql.connector.Error as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
    finally:
        cursor.close()


def main():
    logger.info("=" * 70)
    logger.info("📊 IMPORTACIÓN DE TARIFARIOS BANCARIOS A MYSQL")
    logger.info("=" * 70)

    # Verificar que existe el CSV
    if not CSV_FILE.exists():
        logger.error(f"❌ Archivo CSV no encontrado: {CSV_FILE}")
        return

    logger.success(f"✅ Archivo CSV encontrado: {CSV_FILE}")

    # Leer CSV
    logger.info("\n📖 Leyendo archivo CSV...")
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
        logger.success(f"✅ CSV leído: {len(df)} filas, {len(df.columns)} columnas")
        logger.info(f"   Columnas: {', '.join(df.columns.tolist()[:5])}...")
    except Exception as e:
        logger.error(f"❌ Error leyendo CSV: {e}")
        return

    # Limpiar datos
    df = limpiar_datos(df)

    # Conectar a MySQL
    logger.info("\n🔌 Conectando a MySQL...")
    logger.info(f"   Host: {MYSQL_CONFIG['host']}")
    logger.info(f"   User: {MYSQL_CONFIG['user']}")
    logger.info(f"   Port: {MYSQL_CONFIG['port']}")

    try:
        # Conexión inicial (sin database)
        conn = crear_conexion()

        # Crear base de datos
        crear_base_datos(conn)
        conn.close()

        # Reconectar a la base de datos específica
        conn = crear_conexion(DATABASE_NAME)

        # Crear tablas
        crear_tablas(conn)

        # Limpiar tabla
        truncar_tabla(conn)

        # Insertar datos
        insertar_datos(conn, df)

        # Actualizar resumen
        actualizar_resumen(conn)

        # Mostrar estadísticas
        mostrar_estadisticas(conn)

        logger.success("\n✅ Importación completada exitosamente!")
        logger.info(f"📁 Base de datos: {DATABASE_NAME}")
        logger.info(f"📊 Tabla principal: tarifarios")
        logger.info(f"📈 Tabla resumen: resumen_por_banco")

    except Exception as e:
        logger.error(f"❌ Error en el proceso: {e}")
        raise
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            logger.info("\n🔌 Conexión cerrada")


if __name__ == "__main__":
    main()
