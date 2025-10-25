# GUÍA DE IMPORTACIÓN A MYSQL
## Tarifarios Bancarios - Base de Datos

---

## DESCRIPCIÓN

Este documento explica cómo importar el dataset `tarifarios_bancarios.csv` a una base de datos MySQL usando el script `csv_a_mysql.py`.

**Dataset**: 1,383 registros de tarifas, comisiones, gastos y seguros de 5 bancos peruanos

---

## REQUISITOS PREVIOS

### 1. MySQL Instalado

Verifica que MySQL esté instalado y corriendo:

```bash
mysql --version
```

**Descarga MySQL** (si no lo tienes):
- Windows: https://dev.mysql.com/downloads/installer/
- Linux: `sudo apt install mysql-server`
- macOS: `brew install mysql`

### 2. Dependencia de Python

Instala el conector MySQL para Python:

```bash
pip install mysql-connector-python
```

O si usas el entorno `ocr_gemini`:

```bash
conda activate ocr_gemini
pip install mysql-connector-python
```

### 3. Configurar credenciales MySQL

Edita el archivo `config/.env` y agrega tus credenciales de MySQL:

```env
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=tu_password_aqui
MYSQL_PORT=3306
```

**IMPORTANTE**: Reemplaza `tu_password_aqui` con tu contraseña real de MySQL.

---

## ESTRUCTURA DE LA BASE DE DATOS

### Base de Datos: `tarifarios_bancarios`

El script crea automáticamente:

1. **Base de datos**: `tarifarios_bancarios`
2. **Tabla principal**: `tarifarios`
3. **Tabla de resumen**: `resumen_por_banco`

### Esquema de la Tabla `tarifarios`

```sql
CREATE TABLE tarifarios (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Información del banco y producto
    banco VARCHAR(100) NOT NULL,
    producto_codigo VARCHAR(200) NOT NULL,
    producto_nombre VARCHAR(500),

    -- Concepto
    concepto VARCHAR(500) NOT NULL,
    descripcion_breve TEXT,

    -- Clasificación
    tipo ENUM('TASA', 'COMISION', 'GASTO', 'SEGURO', 'OTRO') NOT NULL,

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
    moneda ENUM('MN', 'ME', 'AMBAS', 'EUR', ''),

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
);
```

### Esquema de la Tabla `resumen_por_banco`

```sql
CREATE TABLE resumen_por_banco (
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
);
```

---

## EJECUCIÓN DEL SCRIPT

### Paso 1: Verificar archivo CSV

Asegúrate de que existe el archivo:

```
PARTE 2/data/output/tarifarios_bancarios.csv
```

### Paso 2: Ejecutar el script

```bash
python scripts/csv_a_mysql.py
```

### Paso 3: Salida esperada

```
======================================================================
📊 IMPORTACIÓN DE TARIFARIOS BANCARIOS A MYSQL
======================================================================
✅ Archivo CSV encontrado: ...\data\output\tarifarios_bancarios.csv

📖 Leyendo archivo CSV...
✅ CSV leído: 1383 filas, 20 columnas

🧹 Limpiando datos...
✅ Datos limpios: 1383 filas

🔌 Conectando a MySQL...
   Host: localhost
   User: root
   Port: 3306
✅ Conexión exitosa a MySQL
✅ Base de datos 'tarifarios_bancarios' creada/verificada

📋 Creando tablas...
✅ Tabla 'tarifarios' creada/verificada
✅ Tabla 'resumen_por_banco' creada/verificada

📥 Insertando 1383 registros...
  Progreso: 100/1383 (7.2%)
  Progreso: 200/1383 (14.5%)
  ...
  Progreso: 1383/1383 (100.0%)

✅ Datos insertados: 1383 registros

📊 Calculando resumen por banco...
✅ Resumen calculado para 5 bancos:
  BBVA_Continental                : 180 items (65 tasas)
  BCP                             : 220 items (75 tasas)
  Interbank                       : 150 items (50 tasas)
  Scotiabank                      : 130 items (45 tasas)
  Banco_de_la_Nación              : 53 items (20 tasas)

======================================================================
📊 ESTADÍSTICAS DE LA BASE DE DATOS
======================================================================
Total de registros:        1,383

Distribución por tipo:
  TASA           :  255 ( 18.4%)
  COMISION       :  850 ( 61.5%)
  GASTO          :  200 ( 14.5%)
  SEGURO         :   50 (  3.6%)
  OTRO           :   28 (  2.0%)

Top 5 tasas MN más altas:
  112.99% - Scotiabank - Línea de Crédito Efectiva
  107.00% - BCP - American Express
   32.00% - Banco_de_la_Nación - Tarjeta Clásica Disposición
   30.00% - Interbank - Tarjeta Oro
   28.50% - BBVA_Continental - Préstamo Personal
======================================================================

✅ Importación completada exitosamente!
📁 Base de datos: tarifarios_bancarios
📊 Tabla principal: tarifarios
📈 Tabla resumen: resumen_por_banco
```

---

## CONSULTAS SQL ÚTILES

### 1. Ver todos los registros

```sql
USE tarifarios_bancarios;
SELECT * FROM tarifarios LIMIT 10;
```

### 2. Contar registros por banco

```sql
SELECT banco, COUNT(*) as total
FROM tarifarios
GROUP BY banco
ORDER BY total DESC;
```

### 3. Top 10 tasas más altas (MN)

```sql
SELECT banco, concepto, tasa_porcentaje_mn
FROM tarifarios
WHERE tipo = 'TASA' AND tasa_porcentaje_mn IS NOT NULL
ORDER BY tasa_porcentaje_mn DESC
LIMIT 10;
```

### 4. Comisiones por banco

```sql
SELECT banco, COUNT(*) as total_comisiones
FROM tarifarios
WHERE tipo = 'COMISION'
GROUP BY banco
ORDER BY total_comisiones DESC;
```

### 5. Productos por banco

```sql
SELECT banco, COUNT(DISTINCT producto_codigo) as total_productos
FROM tarifarios
GROUP BY banco
ORDER BY total_productos DESC;
```

### 6. Ver resumen por banco

```sql
SELECT * FROM resumen_por_banco;
```

### 7. Tasas promedio por banco

```sql
SELECT banco, tasa_promedio_mn, tasa_maxima_mn, tasa_minima_mn
FROM resumen_por_banco
ORDER BY tasa_promedio_mn DESC;
```

### 8. Buscar por concepto

```sql
SELECT banco, concepto, tipo, tasa_porcentaje_mn
FROM tarifarios
WHERE concepto LIKE '%tarjeta%'
AND tipo = 'TASA'
ORDER BY tasa_porcentaje_mn DESC;
```

### 9. Filtrar por fecha de vigencia

```sql
SELECT banco, concepto, fecha_vigencia
FROM tarifarios
WHERE fecha_vigencia LIKE '%2025%'
ORDER BY fecha_vigencia DESC;
```

### 10. Comparar tasas entre bancos (mismo producto)

```sql
SELECT banco, concepto, tasa_porcentaje_mn
FROM tarifarios
WHERE concepto LIKE '%tarjeta clásica%'
AND tipo = 'TASA'
ORDER BY tasa_porcentaje_mn DESC;
```

---

## CARACTERÍSTICAS DEL SCRIPT

### ✅ Validación y Limpieza Automática

- Elimina BOM (Byte Order Mark) de UTF-8
- Convierte valores vacíos (`''`, `'N/A'`) a `NULL`
- Limpia espacios en blanco
- Reemplaza `NaN` de pandas por `NULL` de MySQL

### ✅ Inserción por Lotes

- Inserta en batches de 100 registros
- Muestra progreso en tiempo real
- Manejo de errores por fila (continúa si una fila falla)

### ✅ Resumen Automático

- Calcula estadísticas por banco
- Genera tabla `resumen_por_banco` con métricas agregadas
- Actualiza automáticamente al insertar datos

### ✅ Índices Optimizados

- `idx_banco`: Búsquedas por banco
- `idx_tipo`: Filtrar por tipo (TASA, COMISION, etc.)
- `idx_producto`: Buscar por producto específico
- `idx_moneda`: Filtrar por moneda
- `idx_banco_tipo`: Consultas compuestas banco + tipo

---

## SOLUCIÓN DE PROBLEMAS

### Error: "Access denied for user 'root'@'localhost'"

**Causa**: Contraseña incorrecta o usuario sin permisos

**Solución**:
1. Verifica tu contraseña en `config/.env`
2. Resetea la contraseña de MySQL:

```bash
# Windows
mysqladmin -u root password nueva_password

# Linux/Mac
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'nueva_password';
FLUSH PRIVILEGES;
```

---

### Error: "Can't connect to MySQL server"

**Causa**: MySQL no está corriendo

**Solución**:

```bash
# Windows
net start MySQL

# Linux
sudo service mysql start

# macOS
mysql.server start
```

---

### Error: "Database already exists"

**Causa**: Base de datos ya creada (no es un error crítico)

**Solución**: El script maneja esto automáticamente con `CREATE DATABASE IF NOT EXISTS`. Si quieres empezar de cero:

```sql
DROP DATABASE tarifarios_bancarios;
```

Luego vuelve a ejecutar el script.

---

### Error: "Duplicate entry for key 'PRIMARY'"

**Causa**: Intentando insertar datos duplicados

**Solución**: El script trunca la tabla antes de insertar. Si persiste, verifica que no haya procesos duplicados corriendo.

---

### Advertencia: "Errores encontrados: X registros"

**Causa**: Algunos registros tienen datos inválidos

**Solución**: El script continúa con los registros válidos. Revisa los logs para ver qué filas fallaron y por qué.

---

## CONEXIÓN DESDE OTROS LENGUAJES

### Python (pandas)

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('mysql+pymysql://root:password@localhost/tarifarios_bancarios')
df = pd.read_sql("SELECT * FROM tarifarios LIMIT 100", engine)
print(df.head())
```

### PHP

```php
<?php
$conn = new mysqli("localhost", "root", "password", "tarifarios_bancarios");

$result = $conn->query("SELECT * FROM tarifarios LIMIT 10");

while($row = $result->fetch_assoc()) {
    echo $row['banco'] . " - " . $row['concepto'] . "<br>";
}
?>
```

### Node.js

```javascript
const mysql = require('mysql2');

const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'password',
  database: 'tarifarios_bancarios'
});

connection.query('SELECT * FROM tarifarios LIMIT 10', (err, rows) => {
  console.log(rows);
});
```

---

## BACKUP Y EXPORTACIÓN

### Exportar base de datos completa

```bash
mysqldump -u root -p tarifarios_bancarios > backup_tarifarios.sql
```

### Importar desde backup

```bash
mysql -u root -p tarifarios_bancarios < backup_tarifarios.sql
```

### Exportar solo la tabla `tarifarios`

```bash
mysqldump -u root -p tarifarios_bancarios tarifarios > backup_tarifarios_tabla.sql
```

### Exportar a CSV desde MySQL

```sql
SELECT * FROM tarifarios
INTO OUTFILE '/tmp/export_tarifarios.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

---

## PRÓXIMOS PASOS

### Análisis Avanzado

1. **Dashboard con Grafana**:
   - Conectar MySQL a Grafana
   - Crear visualizaciones de tasas por banco
   - Monitorear cambios en tiempo real

2. **API REST**:
   - Crear API con Flask/FastAPI
   - Exponer endpoints para consultas
   - Autenticación con JWT

3. **Machine Learning**:
   - Predecir tendencias de tasas
   - Clustering de productos similares
   - Detección de anomalías

---

## ARCHIVO: scripts/csv_a_mysql.py

**Ubicación**: `PARTE 2/scripts/csv_a_mysql.py`

**Funciones principales**:

| Función | Descripción |
|---------|-------------|
| `crear_conexion()` | Establece conexión con MySQL |
| `crear_base_datos()` | Crea DB `tarifarios_bancarios` |
| `crear_tablas()` | Crea tablas `tarifarios` y `resumen_por_banco` |
| `limpiar_datos()` | Limpia y valida DataFrame |
| `insertar_datos()` | Inserta datos en lotes |
| `actualizar_resumen()` | Calcula estadísticas por banco |
| `mostrar_estadisticas()` | Muestra resumen final |

---

## CONTACTO Y SOPORTE

**Proyecto**: Sistema de Extracción de Tarifarios Bancarios
**Curso**: Analítica de Datos - UNI FIIS
**Grupo**: 2

Para reportar errores o sugerencias, revisar el README.md principal del proyecto.

---

**Fecha de creación**: 2025-10-25
**Última actualización**: 2025-10-25
**Versión**: 1.0
