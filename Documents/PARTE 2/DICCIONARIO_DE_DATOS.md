# DICCIONARIO DE DATOS
## Sistema de Extracción y Normalización de Tarifarios Bancarios

**Proyecto**: Analítica de Datos - Grupo 2
**Fecha de creación**: 2025-10-25
**Versión**: 1.0

---

## ÍNDICE

1. [Base de Datos MySQL](#1-base-de-datos-mysql)
2. [Archivos CSV/Excel](#2-archivos-csvexcel)
3. [Archivos JSON Normalizados](#3-archivos-json-normalizados)
4. [Archivos Markdown (OCR)](#4-archivos-markdown-ocr)
5. [Archivos de Metadatos](#5-archivos-de-metadatos)
6. [Enumeraciones y Catálogos](#6-enumeraciones-y-catálogos)

---

## 1. BASE DE DATOS MYSQL

### 1.1 Base de Datos: `tarifarios_bancarios`

**Descripción**: Base de datos relacional que almacena información estructurada de tarifas, comisiones, gastos y seguros de bancos peruanos.

**Charset**: `utf8mb4`
**Collation**: `utf8mb4_unicode_ci`

---

### 1.2 Tabla: `tarifarios`

**Descripción**: Tabla principal que contiene todos los items extraídos de los tarifarios bancarios.

**Total de registros**: 1,323 (aproximado)

| Campo | Tipo | Nulo | Clave | Descripción | Ejemplo |
|-------|------|------|-------|-------------|---------|
| **id** | INT | NO | PRI (AUTO_INCREMENT) | Identificador único del registro | 1, 2, 3... |
| **banco** | VARCHAR(100) | NO | INDEX | Nombre de la institución bancaria | "BBVA_Continental", "BCP", "Interbank" |
| **producto_codigo** | VARCHAR(200) | NO | INDEX | Código único del producto/documento | "tarjetas-credito", "adelanto-ppjj" |
| **producto_nombre** | VARCHAR(500) | SÍ | - | Nombre descriptivo del producto | "Tarjeta de Crédito Visa Clásica" |
| **concepto** | VARCHAR(500) | SÍ | - | Nombre del item/concepto tarifario | "Tasa de Interés Compensatoria", "Comisión por Mantenimiento" |
| **descripcion_breve** | TEXT | SÍ | - | Descripción corta generada por IA (10-15 palabras) | "Tasa anual aplicada a compras con tarjeta de crédito" |
| **tipo** | VARCHAR(20) | SÍ | INDEX | Clasificación del item | "TASA", "COMISION", "GASTO", "SEGURO", "OTRO" |
| **tasa_porcentaje_mn** | DECIMAL(10,4) | SÍ | - | Tasa porcentual en Moneda Nacional (soles) | 27.0000, 32.5000, 112.9900 |
| **tasa_porcentaje_me** | DECIMAL(10,4) | SÍ | - | Tasa porcentual en Moneda Extranjera (dólares/euros) | 25.0000, 107.0000 |
| **monto_fijo_mn** | DECIMAL(15,2) | SÍ | - | Monto fijo en soles (S/) | 5.00, 15.50, 100.00 |
| **monto_fijo_me** | DECIMAL(15,2) | SÍ | - | Monto fijo en dólares/euros ($, €) | 2.50, 10.00 |
| **monto_minimo_mn** | DECIMAL(15,2) | SÍ | - | Monto mínimo en soles | 7.00, 50.00 |
| **monto_maximo_mn** | DECIMAL(15,2) | SÍ | - | Monto máximo en soles | 375.00, 1000.00 |
| **monto_minimo_me** | DECIMAL(15,2) | SÍ | - | Monto mínimo en dólares/euros | 3.00, 20.00 |
| **monto_maximo_me** | DECIMAL(15,2) | SÍ | - | Monto máximo en dólares/euros | 100.00, 500.00 |
| **moneda** | VARCHAR(20) | SÍ | INDEX | Tipo de moneda aplicable | "MN", "ME", "AMBAS", "EUR" |
| **fecha_vigencia** | VARCHAR(20) | SÍ | - | Fecha desde la cual está vigente el item | "15/05/2018", "24/03/2008" |
| **fecha_extraccion** | VARCHAR(20) | SÍ | - | Fecha en que se extrajo el dato | "2025-10-24" |
| **periodicidad** | VARCHAR(200) | SÍ | - | Frecuencia de aplicación | "Anual", "Mensual", "Trimestral", "Por operación" |
| **oportunidad_cobro** | VARCHAR(500) | SÍ | - | Momento en que se aplica el cargo | "Al momento de la operación", "Mensual sobre saldo" |
| **observaciones** | TEXT | SÍ | - | Información adicional concatenada | "Tipo: TASA \| Compras \| Cliente: Persona Natural" |
| **fecha_carga** | TIMESTAMP | NO | - | Timestamp automático de inserción en BD | "2025-10-25 07:14:48" |

**Índices**:
- `PRIMARY KEY (id)`
- `INDEX idx_banco (banco)`
- `INDEX idx_tipo (tipo)`
- `INDEX idx_producto (producto_codigo)`
- `INDEX idx_moneda (moneda)`
- `INDEX idx_banco_tipo (banco, tipo)` - Índice compuesto

---

### 1.3 Tabla: `resumen_por_banco`

**Descripción**: Tabla de resumen con estadísticas agregadas por banco.

**Total de registros**: 5 (uno por banco)

| Campo | Tipo | Nulo | Clave | Descripción | Ejemplo |
|-------|------|------|-------|-------------|---------|
| **id** | INT | NO | PRI (AUTO_INCREMENT) | Identificador único | 1, 2, 3, 4, 5 |
| **banco** | VARCHAR(100) | NO | UNIQUE | Nombre del banco | "BBVA_Continental" |
| **total_items** | INT | SÍ | - | Total de items del banco | 422 |
| **total_tasas** | INT | SÍ | - | Total de tasas de interés | 44 |
| **total_comisiones** | INT | SÍ | - | Total de comisiones | 320 |
| **total_gastos** | INT | SÍ | - | Total de gastos | 45 |
| **total_seguros** | INT | SÍ | - | Total de seguros | 10 |
| **total_otros** | INT | SÍ | - | Total de otros items | 3 |
| **tasa_promedio_mn** | DECIMAL(10,4) | SÍ | - | Promedio de tasas en MN | 24.6400 |
| **tasa_maxima_mn** | DECIMAL(10,4) | SÍ | - | Tasa más alta en MN | 112.9900 |
| **tasa_minima_mn** | DECIMAL(10,4) | SÍ | - | Tasa más baja en MN | 0.0000 |
| **fecha_actualizacion** | TIMESTAMP | NO | - | Última actualización (automática) | "2025-10-25 07:14:48" |

---

## 2. ARCHIVOS CSV/EXCEL

### 2.1 Dataset Completo: `tarifarios_bancarios.csv`

**Ruta**: `data/output/tarifarios_bancarios.csv`
**Formato**: CSV (UTF-8 con BOM)
**Filas**: 1,323 + 1 encabezado
**Columnas**: 20

| # | Columna | Tipo de Dato | Nulo | Descripción | Valores Posibles |
|---|---------|--------------|------|-------------|------------------|
| 1 | Banco | String | NO | Nombre de la institución bancaria | "BBVA_Continental", "BCP", "Interbank", "Scotiabank", "Banco_de_la_Nación" |
| 2 | Producto_Codigo | String | NO | Identificador del producto/documento | "tarjetas-credito", "prestamos-personales" |
| 3 | Producto_Nombre | String | SÍ | Nombre legible del producto | "Tarjeta de Crédito Visa Clásica" |
| 4 | Concepto | String | SÍ | Nombre del concepto tarifario | "Tasa de Interés Compensatoria" |
| 5 | Descripcion_Breve | String | SÍ | Descripción corta (IA generada) | "Tasa anual para compras con tarjeta" |
| 6 | Tipo | String | SÍ | Clasificación del item | "TASA", "COMISION", "GASTO", "SEGURO", "OTRO" |
| 7 | Tasa_Porcentaje_MN | Float | SÍ | Tasa % en Moneda Nacional | 27.0, 32.5, 112.99 |
| 8 | Tasa_Porcentaje_ME | Float | SÍ | Tasa % en Moneda Extranjera | 25.0, 107.0 |
| 9 | Monto_Fijo_MN | Float | SÍ | Monto fijo en soles | 5.0, 15.5 |
| 10 | Monto_Fijo_ME | Float | SÍ | Monto fijo en dólares/euros | 2.5, 10.0 |
| 11 | Monto_Minimo_MN | Float | SÍ | Monto mínimo en soles | 7.0, 50.0 |
| 12 | Monto_Maximo_MN | Float | SÍ | Monto máximo en soles | 375.0, 1000.0 |
| 13 | Monto_Minimo_ME | Float | SÍ | Monto mínimo en dólares/euros | 3.0, 20.0 |
| 14 | Monto_Maximo_ME | Float | SÍ | Monto máximo en dólares/euros | 100.0, 500.0 |
| 15 | Moneda | String | SÍ | Tipo de moneda | "MN", "ME", "AMBAS", "EUR" |
| 16 | Fecha_Vigencia | String | SÍ | Fecha de vigencia (DD/MM/YYYY) | "15/05/2018", "24/03/2008" |
| 17 | Fecha_Extraccion | String | SÍ | Fecha de extracción (YYYY-MM-DD) | "2025-10-24" |
| 18 | Periodicidad | String | SÍ | Frecuencia de aplicación | "Anual", "Mensual", "Por operación" |
| 19 | Oportunidad_Cobro | String | SÍ | Momento de aplicación | "Al momento de la operación" |
| 20 | Observaciones | Text | SÍ | Información adicional | "Tipo: TASA \| Compras \| Cliente: Persona Natural" |

**Archivo Excel asociado**: `tarifarios_bancarios.xlsx`

**Hojas del Excel**:
1. **Tarifarios**: Dataset completo (1,323 filas × 20 columnas)
2. **Resumen**: Resumen por banco (5 filas)
3. **Por_Tipo**: Distribución por tipo de item (5 filas: TASA, COMISION, GASTO, SEGURO, OTRO)

---

### 2.2 Dataset Solo Tasas: `tarifarios_bancarios_SOLO_TASAS.csv`

**Ruta**: `data/output/tarifarios_bancarios_SOLO_TASAS.csv`
**Formato**: CSV (UTF-8 con BOM)
**Filas**: ~269 + 1 encabezado
**Columnas**: 15 (subset del dataset completo)

**Filtro aplicado**: `Tipo == "TASA" AND (Tasa_Porcentaje_MN IS NOT NULL OR Tasa_Porcentaje_ME IS NOT NULL)`

**Columnas incluidas**:
- Banco
- Producto_Codigo
- Producto_Nombre
- Concepto
- Descripcion_Breve
- Tipo (siempre "TASA")
- Tasa_Porcentaje_MN
- Tasa_Porcentaje_ME
- Moneda
- Fecha_Vigencia
- Fecha_Extraccion
- Periodicidad
- Oportunidad_Cobro
- Observaciones

**Archivo Excel asociado**: `tarifarios_bancarios_SOLO_TASAS.xlsx`

**Hojas del Excel**:
1. **Tasas**: Dataset filtrado
2. **Resumen_Por_Banco**: Total de tasas por banco
3. **Por_Categoria**: Distribución por categoría de tasa
4. **Top_20_Tasas_MN**: Top 20 tasas más altas en soles
5. **Top_20_Tasas_ME**: Top 20 tasas más altas en dólares

---

### 2.3 Dataset Formato Examen: `EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.csv`

**Ruta**: `data/output/EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.csv`
**Formato**: CSV (UTF-8 con BOM)
**Filas**: 1,323 + 1 encabezado
**Columnas**: 6

| # | Columna | Tipo de Dato | Descripción | Ejemplo |
|---|---------|--------------|-------------|---------|
| 1 | Banco | String | Nombre del banco | "BCP" |
| 2 | Producto | String | Nombre del producto | "Tarjeta de Crédito Visa Clásica" |
| 3 | Tasa | String | Tasa/monto formateado | "MN: 27% \| ME: 32%", "MN: S/ 5.00" |
| 4 | Moneda | String | Tipo de moneda | "MN", "ME", "AMBAS" |
| 5 | Fecha de registro | String | Fecha de vigencia | "15/05/2018" |
| 6 | Observaciones | Text | Información concatenada | "Tipo: TASA \| Compras \| Periodicidad: Anual \| Cliente: Persona Natural" |

**Formato del campo "Tasa"**:
- Tasas porcentuales: `"MN: 27% | ME: 32%"`
- Montos fijos: `"MN: S/ 5.00 | ME: $ 3.00"`
- Rangos: `"MN: S/ 7.00 - S/ 375.00"`
- Solo MN: `"MN: 27%"`
- Solo ME: `"ME: 25%"`

**Archivo Excel asociado**: `EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.xlsx`

**Hojas del Excel**:
1. **Tarifarios Bancarios**: Dataset en formato examen
2. **Resumen por Banco**: Estadísticas por banco
3. **Metadatos**: Información del proyecto

---

## 3. ARCHIVOS JSON NORMALIZADOS

### 3.1 Estructura de Archivos JSON

**Ruta**: `data/normalized_json/{BANCO}/batch_{NNN}.json`
**Formato**: JSON (UTF-8)
**Cantidad**: ~50 archivos (varía según banco)

**Ejemplo de ruta**: `data/normalized_json/BCP/batch_001.json`

---

### 3.2 Esquema JSON: Nivel Raíz

```json
{
  "batch_metadata": {
    "batch_id": "batch_001",
    "total_documentos": 10,
    "fecha_procesamiento": "2025-10-24T17:30:00"
  },
  "documentos": [...],
  "resumen_batch": {
    "documentos_con_datos": 8,
    "documentos_indice": 1,
    "documentos_vacios": 0,
    "documentos_corruptos_parciales": 1
  }
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| batch_metadata | Object | Metadatos del batch procesado |
| batch_metadata.batch_id | String | Identificador del batch ("batch_001", "batch_002", ...) |
| batch_metadata.total_documentos | Integer | Cantidad de documentos en el batch (típicamente 10) |
| batch_metadata.fecha_procesamiento | String (ISO 8601) | Timestamp de procesamiento |
| documentos | Array[Documento] | Lista de documentos procesados |
| resumen_batch | Object | Resumen del batch |
| resumen_batch.documentos_con_datos | Integer | Documentos con datos extraídos |
| resumen_batch.documentos_indice | Integer | Documentos que solo contienen índice/TOC |
| resumen_batch.documentos_vacios | Integer | Documentos sin contenido |
| resumen_batch.documentos_corruptos_parciales | Integer | Documentos con contenido parcialmente corrupto |

---

### 3.3 Esquema JSON: Objeto `Documento`

```json
{
  "archivo": "tarjetas-credito-visa.md",
  "metadata": {...},
  "items": [...],
  "notas_documento": [...],
  "control_calidad": {...}
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| archivo | String | Nombre del archivo .md original |
| metadata | Object (Metadata) | Metadatos del documento |
| items | Array[Item] | Items extraídos del documento |
| notas_documento | Array[NotaDocumento] | Notas al pie del documento |
| control_calidad | Object (ControlCalidad) | Métricas de calidad de extracción |

---

### 3.4 Esquema JSON: Objeto `Metadata`

```json
{
  "banco": "BCP",
  "producto_codigo": "tarjetas-credito-visa",
  "producto_nombre": "Tarjeta de Crédito Visa Clásica",
  "descripcion_breve": "Financiamiento revolvente con tarjeta Visa para personas naturales",
  "fecha_extraccion": "2025-10-24",
  "fecha_vigencia": "15/05/2018",
  "tipo_cambio_referencial": null,
  "tipo_cliente": "Persona Natural",
  "segmento": "Banca Personal",
  "tiene_contenido_corrupto": false,
  "fuente_archivo": "BCP/tarjetas-credito-visa.md",
  "referencias_externas": []
}
```

| Campo | Tipo | Nulo | Descripción |
|-------|------|------|-------------|
| banco | String | NO | Nombre del banco |
| producto_codigo | String | NO | Código del producto (filename sin extensión) |
| producto_nombre | String | SÍ | Nombre legible del producto |
| descripcion_breve | String | SÍ | Descripción generada por IA (1-2 líneas) |
| fecha_extraccion | String (YYYY-MM-DD) | NO | Fecha de extracción |
| fecha_vigencia | String (DD/MM/YYYY) | SÍ | Fecha de vigencia del tarifario |
| tipo_cambio_referencial | Object | SÍ | Tipo de cambio de referencia {usd_pen, eur_pen} |
| tipo_cliente | String | SÍ | "Persona Natural", "Persona Jurídica", "Ambos" |
| segmento | String | SÍ | "Pyme", "No Pyme", "General" |
| tiene_contenido_corrupto | Boolean | NO | Indica si hay contenido duplicado/corrupto |
| fuente_archivo | String | NO | Path relativo al archivo .md |
| referencias_externas | Array[ReferenciaExterna] | NO | Referencias a otros tarifarios |

---

### 3.5 Esquema JSON: Objeto `Item`

```json
{
  "id": "1",
  "jerarquia": {...},
  "clasificacion": {...},
  "concepto": {...},
  "valores": {...},
  "aplicacion": {...},
  "metadata_item": {...}
}
```

| Campo | Tipo | Nulo | Descripción |
|-------|------|------|-------------|
| id | String | NO | UUID o número secuencial |
| jerarquia | Object (Jerarquia) | SÍ | Información jerárquica del item |
| clasificacion | Object (Clasificacion) | NO | Tipo y categoría del item |
| concepto | Object (Concepto) | NO | Nombre y descripción |
| valores | Object (Valores) | SÍ | Valores monetarios (MN/ME) |
| aplicacion | Object (Aplicacion) | SÍ | Vigencia, periodicidad, condiciones |
| metadata_item | Object (MetadataItem) | SÍ | Metadata adicional del item |

---

### 3.6 Esquema JSON: Objeto `Clasificacion`

```json
{
  "tipo": "TASA",
  "subtipo": "Interés Compensatorio",
  "categoria": "Tarjetas de Crédito"
}
```

| Campo | Tipo | Nulo | Descripción | Valores Posibles |
|-------|------|------|-------------|------------------|
| tipo | String (ENUM) | NO | Tipo principal | "TASA", "COMISION", "GASTO", "SEGURO", "OTRO" |
| subtipo | String | SÍ | Subtipo específico | "Desgravamen", "Vehicular", "Mantenimiento" |
| categoria | String | SÍ | Categoría del producto | "Tarjetas de Crédito", "Préstamos Personales" |

---

### 3.7 Esquema JSON: Objeto `Valores`

```json
{
  "moneda": "AMBAS",
  "mn": {
    "tasa_porcentaje": 27.0,
    "monto_fijo": null,
    "monto_minimo": null,
    "monto_maximo": null,
    "unidad": "%",
    "texto_original": "27,00%"
  },
  "me": {
    "tasa_porcentaje": 32.0,
    "monto_fijo": null,
    "monto_minimo": null,
    "monto_maximo": null,
    "unidad": "%",
    "texto_original": "32,00%",
    "conversion_pen": null
  }
}
```

| Campo | Tipo | Nulo | Descripción |
|-------|------|------|-------------|
| moneda | String (ENUM) | NO | Tipo de moneda | "MN", "ME", "AMBAS" |
| mn | Object (ValoresMoneda) | SÍ | Valores en Moneda Nacional |
| me | Object (ValoresMonedaExtranjera) | SÍ | Valores en Moneda Extranjera |

**Objeto `ValoresMoneda`**:

| Campo | Tipo | Nulo | Descripción |
|-------|------|------|-------------|
| tasa_porcentaje | Float | SÍ | Tasa en porcentaje (27.0 = 27%) |
| monto_fijo | Float | SÍ | Monto fijo |
| monto_minimo | Float | SÍ | Monto mínimo |
| monto_maximo | Float | SÍ | Monto máximo |
| unidad | String | SÍ | Unidad ("%", "S/", "$", "€") |
| texto_original | String | SÍ | Valor como aparece en el documento |

**Objeto `ValoresMonedaExtranjera`** (extiende `ValoresMoneda`):

| Campo Adicional | Tipo | Nulo | Descripción |
|-----------------|------|------|-------------|
| conversion_pen | Float | SÍ | Conversión a PEN si está disponible |

---

### 3.8 Esquema JSON: Objeto `Aplicacion`

```json
{
  "vigencia": "15/05/2018",
  "periodicidad": "Anual",
  "oportunidad_cobro": "Mensual sobre saldo",
  "forma_aplicacion": null,
  "condiciones": "Aplicable a compras no financiadas"
}
```

| Campo | Tipo | Nulo | Descripción |
|-------|------|------|-------------|
| vigencia | String (DD/MM/YYYY) | SÍ | Fecha de vigencia |
| periodicidad | String | SÍ | "Mensual", "Anual", "Trimestral", "Por operación" |
| oportunidad_cobro | String | SÍ | Momento de cobro |
| forma_aplicacion | String | SÍ | Forma de aplicación del cargo |
| condiciones | String | SÍ | Condiciones adicionales |

---

### 3.9 Esquema JSON: Objeto `ControlCalidad`

```json
{
  "total_items_extraidos": 50,
  "items_con_datos_completos": 45,
  "items_con_datos_parciales": 3,
  "items_solo_encabezados": 2,
  "referencias_sin_resolver": ["(1)", "(2)"],
  "advertencias": [],
  "tipo_documento": "NORMAL"
}
```

| Campo | Tipo | Descripción | Valores Posibles |
|-------|------|-------------|------------------|
| total_items_extraidos | Integer | Total de items extraídos (sin contar encabezados) | 0, 1, 2, ... |
| items_con_datos_completos | Integer | Items con todos los campos requeridos | 0, 1, 2, ... |
| items_con_datos_parciales | Integer | Items con algunos campos faltantes | 0, 1, 2, ... |
| items_solo_encabezados | Integer | Encabezados de sección sin datos | 0, 1, 2, ... |
| referencias_sin_resolver | Array[String] | Referencias cruzadas no resueltas | ["(1)", "(2)", "Ver Tarifario N°110"] |
| advertencias | Array[String] | Advertencias de procesamiento | ["Documento corrupto parcialmente"] |
| tipo_documento | String (ENUM) | Tipo de documento | "NORMAL", "INDICE", "VACIO", "CORRUPTO" |

---

## 4. ARCHIVOS MARKDOWN (OCR)

### 4.1 Archivos OCR por Página

**Ruta**: `data/ocr/{BANCO}/{PRODUCTO}.md`
**Formato**: Markdown
**Encoding**: UTF-8
**Cantidad**: ~499 archivos (uno por PDF procesado)

**Estructura**:
```markdown
| TASAS | Porcentaje MN | Porcentaje ME | Observación y Vigencia |
|-------|---------------|---------------|------------------------|
| Descuento de Letras | 32,00% | 25,00% | Aplica por adelantado Vigente desde 24/03/2008 |
| Interés moratorio | 15% | 10,00% | |

| COMISIONES | Porcentaje | MN | ME | Observación y Vigencia |
|------------|------------|----|----|------------------------|
| Por Administración de Cartera | - | S/7.00 | $2.50 | Aplica a documentos menores a S/1,000. Vigente desde 16/12/2013 |
```

**Características**:
- Tablas en formato Markdown (`|` delimitadores)
- Preserva estructura original del PDF
- Puede contener múltiples tablas separadas por líneas en blanco
- Símbolos preservados: %, S/, $, €

---

### 4.2 Archivos Temporales (Página por Página)

**Ruta**: `data/temp/{BANCO}/{PRODUCTO}/page_{NNNN}.md`
**Formato**: Markdown
**Cantidad**: ~2,500 archivos (archivos intermedios, uno por página PNG)

**Ejemplo**: `data/temp/BCP/tarjetas-credito-visa/page_0001.md`

**Nota**: Estos archivos son temporales y se combinan en un solo archivo `.md` en `data/ocr/`.

---

## 5. ARCHIVOS DE METADATOS

### 5.1 Archivo: `FUENTES_TARIFARIOS.md`

**Descripción**: Documentación de las fuentes de datos web scrapeadas.

**Contenido**:
- URLs de cada banco
- Método de scraping utilizado
- Fecha de última extracción
- Observaciones sobre cambios en estructura web

---

### 5.2 Archivo: `ocr_progress.json`

**Ruta**: `PARTE 2/ocr_progress.json`
**Formato**: JSON

**Estructura**:
```json
{
  "processed_pdfs": [
    "BCP/tarjetas-credito-visa",
    "BBVA_Continental/adelanto-ppjj"
  ],
  "failed_pdfs": [
    {
      "pdf": "Interbank/producto-x",
      "error": "Timeout after 120s"
    }
  ],
  "total_time": 18234.56
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| processed_pdfs | Array[String] | Lista de PDFs procesados exitosamente |
| failed_pdfs | Array[Object] | Lista de PDFs con errores |
| failed_pdfs[].pdf | String | Ruta relativa del PDF |
| failed_pdfs[].error | String | Mensaje de error |
| total_time | Float | Tiempo total de procesamiento (segundos) |

---

### 5.3 Archivo: `manifest.txt`

**Ruta**: `data/batches_combinados/manifest.txt`
**Formato**: Texto plano

**Contenido**:
- Total de archivos .md procesados
- Total de batches creados
- Archivos por batch
- Resumen por banco
- Detalle de cada batch (archivos incluidos, tamaño, tokens estimados)

---

### 5.4 Archivo: `reporte_descarga.json`

**Ruta**: `data/processed/reporte_descarga.json`
**Formato**: JSON

**Estructura**:
```json
{
  "fecha": "2025-10-24T15:30:00",
  "bancos": [
    {
      "banco": "BBVA_Continental",
      "urls_encontradas": 120,
      "descargas_exitosas": 118,
      "descargas_fallidas": 2,
      "urls": [...]
    }
  ]
}
```

---

## 6. ENUMERACIONES Y CATÁLOGOS

### 6.1 Enum: `BancoEnum`

**Descripción**: Catálogo de bancos procesados.

| Valor | Nombre Completo |
|-------|-----------------|
| BBVA_Continental | BBVA Continental |
| BCP | Banco de Crédito del Perú |
| Interbank | Interbank |
| Scotiabank | Scotiabank Perú |
| Banco_de_la_Nación | Banco de la Nación |

---

### 6.2 Enum: `TipoItem`

**Descripción**: Clasificación de items tarifarios.

| Valor | Descripción | Ejemplos |
|-------|-------------|----------|
| TASA | Tasas de interés (compensatorias, moratorias, rendimientos) | "Tasa de Interés Compensatoria", "Tasa Moratoria" |
| COMISION | Cargos por servicios, transacciones, mantenimiento | "Comisión por Mantenimiento", "Comisión por Retiro" |
| GASTO | Portes, envíos, notificaciones | "Porte por Estado de Cuenta", "Envío de Courier" |
| SEGURO | Primas, coberturas | "Seguro de Desgravamen", "Seguro Vehicular" |
| OTRO | Items no clasificables en anteriores | "Penalidad", "Cargo por Incumplimiento" |

---

### 6.3 Enum: `TipoMoneda`

**Descripción**: Tipos de moneda.

| Valor | Descripción |
|-------|-------------|
| MN | Moneda Nacional (Soles - S/) |
| ME | Moneda Extranjera (Dólares - $ / Euros - €) |
| AMBAS | Aplica a ambas monedas |
| EUR | Específicamente Euros (€) |

---

### 6.4 Enum: `Periodicidad`

**Descripción**: Frecuencia de aplicación de cargos.

| Valor | Descripción |
|-------|-------------|
| Anual | Una vez al año |
| Mensual | Cada mes |
| Trimestral | Cada 3 meses |
| Semestral | Cada 6 meses |
| Por operación | Cada vez que se realiza la operación |
| Única vez | Solo una vez (ej: afiliación) |
| Diaria | Todos los días |

---

### 6.5 Enum: `TipoCliente`

**Descripción**: Tipo de cliente al que aplica el tarifario.

| Valor | Descripción |
|-------|-------------|
| Persona Natural | Clientes individuales |
| Persona Jurídica | Empresas |
| Ambos | Aplica a ambos tipos |

---

### 6.6 Enum: `Segmento`

**Descripción**: Segmento de cliente.

| Valor | Descripción |
|-------|-------------|
| Pyme | Pequeñas y Medianas Empresas |
| No Pyme | Grandes Empresas |
| General | Todos los segmentos |
| Banca Personal | Personas naturales |
| Banca Empresarial | Empresas grandes |

---

### 6.7 Enum: `TipoDocumento`

**Descripción**: Clasificación de documentos procesados.

| Valor | Descripción |
|-------|-------------|
| NORMAL | Documento con datos extractables |
| INDICE | Documento que solo contiene índice/TOC |
| VACIO | Documento sin contenido |
| CORRUPTO | Documento con contenido parcialmente corrupto (repeticiones, errores OCR) |

---

## 7. REGLAS DE NEGOCIO Y VALIDACIONES

### 7.1 Reglas de Clasificación de Tipos

**TASA**:
- Contiene palabras clave: "tasa", "interés", "TEA", "TEM", "rendimiento"
- Tiene valor en campo `tasa_porcentaje_mn` o `tasa_porcentaje_me`
- Unidad: `%`

**COMISION**:
- Contiene palabras clave: "comisión", "comision", "cargo"
- Generalmente tiene `monto_fijo_mn` o `monto_fijo_me`
- Unidad: `S/`, `$`, `€`

**GASTO**:
- Contiene palabras clave: "porte", "envío", "notificación", "gasto"
- Similar a comisión pero relacionado con servicios administrativos

**SEGURO**:
- Contiene palabras clave: "seguro", "prima", "cobertura", "desgravamen"
- Puede ser tasa porcentual o monto fijo

**OTRO**:
- Items que no encajan en las categorías anteriores
- Ejemplos: penalidades, cargos especiales

---

### 7.2 Reglas de Validación de Tasas

1. **Rango válido**: 0% ≤ tasa ≤ 200%
2. **Tasas moratorias**: Generalmente ≤ 13.58% (límite SBS)
3. **Tasas compensatorias**: Generalmente 15% - 120%
4. **Tasas de rendimiento**: Generalmente 0.1% - 10%

---

### 7.3 Reglas de Validación de Montos

1. **Monto mínimo < Monto máximo** (si ambos están presentes)
2. **Montos no negativos**
3. **Montos fijos típicamente**: S/ 0 - S/ 1,000 (comisiones), S/ 0 - S/ 10,000 (seguros)

---

### 7.4 Reglas de Conversión de Fechas

**Formato de entrada** (en PDFs):
- `DD/MM/YYYY`
- `DD-MM-YYYY`
- `DD.MM.YYYY`
- `Vigente desde DD/MM/YYYY`

**Formato normalizado**:
- `fecha_vigencia`: `DD/MM/YYYY` (String)
- `fecha_extraccion`: `YYYY-MM-DD` (String ISO)
- `fecha_procesamiento`: `YYYY-MM-DDTHH:MM:SS` (String ISO 8601)

---

## 8. GLOSARIO DE TÉRMINOS

| Término | Definición |
|---------|------------|
| **Batch** | Grupo de 10 documentos (PDFs) combinados en un solo archivo .txt para procesamiento con Gemini |
| **BOM** | Byte Order Mark - Marca de inicio de UTF-8 (`\ufeff`) |
| **OCR** | Optical Character Recognition - Reconocimiento Óptico de Caracteres |
| **Scraper** | Script que extrae datos de páginas web |
| **Tarifario** | Documento oficial que lista tasas, comisiones, gastos y seguros de un banco |
| **TEA** | Tasa Efectiva Anual |
| **TEM** | Tasa Efectiva Mensual |
| **MN** | Moneda Nacional (Soles peruanos - S/) |
| **ME** | Moneda Extranjera (Dólares - $ / Euros - €) |
| **PPNN** | Persona Natural |
| **PPJJ** | Persona Jurídica |
| **SBS** | Superintendencia de Banca, Seguros y AFP |
| **Desgravamen** | Seguro que cubre deuda en caso de fallecimiento |
| **Adelanto** | Financiamiento anticipado sobre documentos comerciales |
| **Disposición de efectivo** | Retiro de dinero en efectivo con tarjeta de crédito |

---

## 9. CONTACTO Y REFERENCIAS

**Proyecto**: Sistema de Extracción y Normalización de Tarifarios Bancarios
**Curso**: Analítica de Datos
**Institución**: Universidad Nacional de Ingeniería - FIIS
**Grupo**: 2

**Documentos relacionados**:
- `README.md` - Documentación general del proyecto
- `MYSQL_IMPORT_GUIDE.md` - Guía de importación a MySQL
- `FUENTES_TARIFARIOS.md` - Documentación de fuentes de datos
- `Examen_parcial.md` - Especificaciones del examen

**Fecha de última actualización**: 2025-10-25
**Versión del diccionario**: 1.0
