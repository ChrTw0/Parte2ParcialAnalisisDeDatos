# Examen Parcial - Parte 2: Extracción de Tarifarios Bancarios

## Información del Proyecto

**Asignatura**: Analítica de Datos
**Profesor**: Dr. Ing. Aradiel Castañeda, Hilario
**Grupo**: 2
**Tema**: Extracción y procesamiento de tarifarios bancarios (Grupos 1-4)

---

## Descripción del Proyecto

Este proyecto implementa un pipeline completo end-to-end para la extracción, procesamiento y estructuración de datos no estructurados provenientes de tarifarios bancarios en formato PDF. El objetivo es transformar documentos PDF complejos en datos tabulares limpios y estructurados listos para análisis.

**Bancos procesados**:
- BBVA Continental
- Banco de Crédito del Perú (BCP)
- Interbank
- Scotiabank
- Banco de la Nación

**Estadísticas del proyecto**:
- 499 PDFs descargados y procesados
- 733 items extraídos y estructurados
- 185 tasas de interés identificadas
- 3 datasets finales generados

---

## Arquitectura del Pipeline

El proyecto sigue un pipeline de 6 fases secuenciales:

```
FASE 1: DESCARGA           → descargar_pdfs.py
   ↓
FASE 2: CONVERSIÓN         → convertir_pdfs_a_png.py
   ↓
FASE 3: OCR                → procesar_ocr_por_pagina.py (Gemini 2.5 Flash Lite)
   ↓
FASE 4: COMBINACIÓN        → combinar_md_batches.py
   ↓
FASE 5: NORMALIZACIÓN      → normalizar_ocr_a_json.py (Gemini 2.5 Flash Lite + Pydantic)
   ↓
FASE 6: EXPORTACIÓN        → json_a_csv.py / json_a_csv_solo_tasas.py / json_a_csv_examen.py
```

---

## Estructura del Proyecto

```
PARTE 2/
├── README.md                           # Este archivo
├── FUENTES_TARIFARIOS.md              # Documentación de fuentes y URLs
├── Examen_parcial.md                  # Especificaciones del examen
│
├── scripts/                            # Scripts del pipeline
│   ├── descargar_pdfs.py              # Fase 1: Descarga de PDFs
│   ├── convertir_pdfs_a_png.py        # Fase 2: PDF → PNG
│   ├── procesar_ocr_por_pagina.py     # Fase 3: OCR con Gemini 2.0
│   ├── procesar_ocr_por_banco_api2.py # Fase 3: OCR paralelo (API 2)
│   ├── procesar_ocr_por_banco_api3.py # Fase 3: OCR paralelo (API 3)
│   ├── combinar_md_batches.py         # Fase 4: Combinar batches
│   ├── normalizar_ocr_a_json.py       # Fase 5: Normalización con Gemini 2.5
│   ├── json_a_csv.py                  # Fase 6a: Exportación completa
│   ├── json_a_csv_solo_tasas.py       # Fase 6b: Solo tasas
│   └── json_a_csv_examen.py           # Fase 6c: Formato examen
│
├── src/                                # Código fuente
│   ├── scrapers/                      # Scrapers especializados por banco
│   │   ├── base.py                    # Clase base para scrapers
│   │   ├── bbva.py                    # BBVA (BeautifulSoup + Requests)
│   │   ├── bcp.py                     # BCP (BeautifulSoup + Requests)
│   │   ├── interbank.py               # Interbank (Selenium - Anti-bot)
│   │   ├── scotiabank.py              # Scotiabank (Selenium + JSON)
│   │   └── banco_nacion.py            # Banco de la Nación (URLs directas)
│   ├── utils/                         # Utilidades
│   │   ├── downloader.py              # Descarga de PDFs
│   │   └── logger.py                  # Configuración de logs
│   └── models/                        # Modelos de datos
│       └── tarifario.py               # Clases TarifarioURL, BancoEnum
│
├── data/                               # Datos procesados
│   ├── pdfs/                          # PDFs descargados (499 archivos)
│   │   ├── BBVA_Continental/
│   │   ├── BCP/
│   │   ├── Interbank/
│   │   ├── Scotiabank/
│   │   └── Banco_de_la_Nación/
│   │
│   ├── pngs/                          # Imágenes convertidas
│   │   └── [misma estructura]
│   │
│   ├── ocr/                           # Resultados OCR en Markdown
│   │   └── [misma estructura]
│   │
│   ├── ocr_combined/                  # Batches combinados
│   │   └── [misma estructura]
│   │
│   ├── normalized_json/               # JSONs normalizados
│   │   ├── BBVA_Continental/
│   │   │   ├── batch_001.json
│   │   │   └── ...
│   │   └── [otros bancos]
│   │
│   └── output/                        # Datasets finales
│       ├── tarifarios_bancarios.csv
│       ├── tarifarios_bancarios.xlsx
│       ├── tarifarios_bancarios_SOLO_TASAS.csv
│       ├── tarifarios_bancarios_SOLO_TASAS.xlsx
│       ├── EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.csv
│       └── EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.xlsx
│
└── logs/                               # Logs de ejecución
    ├── descargar_pdfs.log
    ├── convertir_pdfs_a_png.log
    ├── procesar_ocr_por_pagina.log
    ├── combinar_md_batches.log
    └── normalizar_ocr_a_json.log
```

---

## Requisitos

### Dependencias de Python

**Librerías principales instaladas en el entorno `ocr_gemini`**:

```bash
# IA y Google Gemini
pip install google-generativeai
pip install google-ai-generativelanguage
pip install langchain-google-genai

# Procesamiento de documentos
pip install pdf2image
pip install pillow
pip install pdfplumber
pip install pdfminer.six

# Validación y estructuración de datos
pip install pydantic
pip install pydantic-settings

# Manipulación de datos
pip install pandas
pip install numpy
pip install openpyxl

# Web scraping
pip install selenium
pip install beautifulsoup4
pip install requests
pip install playwright

# Logging y utilidades
pip install loguru
pip install python-dotenv
pip install tqdm

# Otras dependencias
pip install langchain
pip install langchain-core
```

**Comando de instalación completo**:

```bash
pip install google-generativeai google-ai-generativelanguage langchain-google-genai pdf2image pillow pdfplumber pdfminer.six pydantic pydantic-settings pandas numpy openpyxl selenium beautifulsoup4 requests playwright loguru python-dotenv tqdm langchain langchain-core
```

### Herramientas del Sistema

**Poppler** (para pdf2image):
- Windows: Descargar desde https://github.com/oschwartz10612/poppler-windows/releases
- Agregar al PATH o configurar en el script

### Configuración de API

Crear archivo `.env` en el directorio raíz:

```env
# API Key principal (obligatoria)
GOOGLE_API_KEY=tu_api_key_de_google_gemini

# API Keys adicionales para procesamiento paralelo (opcionales)
GOOGLE_API_KEY_2=tu_segunda_api_key
GOOGLE_API_KEY_3=tu_tercera_api_key
```

**Obtener API Keys**: https://aistudio.google.com/app/apikey

**Nota**: Las API keys adicionales (2 y 3) son opcionales y solo se requieren si deseas ejecutar procesamiento OCR paralelo en múltiples dispositivos simultáneamente.

---

## Pipeline Completo - Guía de Ejecución

### FASE 1: Descarga de PDFs

**Script**: `scripts/descargar_pdfs.py`

**Propósito**: Descarga automática de tarifarios desde sitios web de bancos

**Fuentes de datos**:
- BBVA Continental: https://www.bbva.pe/personas/productos/cuentas.html
- BCP: https://www.viabcp.com/tarifario
- Interbank: https://interbank.pe/tarifario
- Scotiabank: https://www.scotiabank.com.pe/Personas/tarifario-de-comisiones
- Banco de la Nación: https://www.bn.com.pe/

**Arquitectura de Scrapers**:

El proyecto implementa 5 scrapers especializados, cada uno adaptado a la estructura web del banco:

#### 1. BBVA Continental Scraper
**Método**: BeautifulSoup + Requests (scraping estático)
**URLs procesadas**:
- `https://www.bbva.pe/personas/personas-naturales-y-microempresas.html`
- `https://www.bbva.pe/personas/pequenas-medianas-y-grandes-empresas.html`

**Características**:
- Parsing HTML estándar sin JavaScript
- Extracción directa de enlaces `<a href="*.pdf">`
- Inferencia automática de tipo de producto
- Deduplicación por URL

**Productos detectados**: Tarjetas, Préstamos, Cuentas, Empresas, Hipotecarios

---

#### 2. BCP Scraper
**Método**: BeautifulSoup + Requests (scraping estático)
**URL procesada**: `https://www.viabcp.com/tasasytarifas`

**Características**:
- Parsing HTML directo
- Búsqueda de enlaces PDF en página de tasas y tarifas
- Clasificación automática por palabras clave

**Productos detectados**: Tarjetas, Préstamos, Cuentas, Empresas

---

#### 3. Interbank Scraper ⚠️ ANTI-BOT
**Método**: Selenium WebDriver (navegador automatizado)
**URL base**: `https://interbank.pe/tasas-tarifas`

**Características especiales**:
- **Requiere Selenium** para evadir sistema anti-bot (bloquea requests normales con 403)
- Navegador Edge en modo headless
- Técnicas de evasión de detección:
  ```python
  options.add_argument('--disable-blink-features=AutomationControlled')
  options.add_experimental_option("excludeSwitches", ["enable-automation"])
  driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
  ```
- Sistema de tabs dinámicos (14 tabs de productos)
- Esperas explícitas (2 segundos por página)
- User-Agent spoofing: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...`

**Tabs procesados**:
- Banca Personas: Cuentas, Tarjetas, Créditos, Pagos y Servicios
- Banca Empresas: Cuentas, Financiamientos, Servicios, Comercio Exterior, Reactiva Perú
- Banca Pequeña Empresa: Comercio Exterior, Servicios, Créditos, Cuentas, Leasing

**Productos detectados**: Tarjetas, Préstamos, Cuentas, Hipotecarios, Comercio Exterior, Leasing, Servicios

**Dependencias adicionales**:
```bash
pip install selenium webdriver-manager
```

---

#### 4. Scotiabank Scraper
**Método**: Selenium WebDriver + JSON Parsing
**URL procesada**: `https://www.scotiabank.com.pe/Acerca-de/Tarifario/default`

**Características especiales**:
- Extracción desde JSON embebido en atributo `data-items`
- Decodificación de HTML entities: `html.unescape()`
- Parsing recursivo de estructura jerárquica
- Edge en modo headless

**Estructura JSON**:
```json
{
  "Title": "Banca Personas",
  "ResourceUrl": "https://...",
  "SubResources": [
    {
      "Title": "Tarjetas",
      "ResourceUrl": "...",
      "SubResources": [...]
    }
  ]
}
```

**Productos detectados**: Tarjetas, Préstamos, Cuentas, Comercio Exterior

---

#### 5. Banco de la Nación Scraper
**Método**: URLs Directas (hardcoded)
**Motivo**: Sitio web sin listado centralizado de PDFs

**URLs conocidas**:
```python
[
    "https://www.bn.com.pe/tasas-comisiones/Tarifario-BN.pdf",
    "https://www.bn.com.pe/tasas-comisiones/tasas-tarjeta-credito.pdf",
    "https://www.bn.com.pe/tasas-comisiones/tasas-prestamos-consumo.pdf",
    "https://www.bn.com.pe/canales-atencion/documentos/comision-ventanillas-agentesBN.pdf"
]
```

**Productos**: Tarifario General, Tarjetas de Crédito, Préstamos Multired, Comisiones

---

**Ejecución**:

```bash
python scripts/descargar_pdfs.py
```

**Salida**:
- 499 PDFs descargados en `data/pdfs/[BANCO]/`
- Log detallado en `logs/descargar_pdfs.log`

---

### FASE 2: Conversión PDF a PNG

**Script**: `scripts/convertir_pdfs_a_png.py`

**Propósito**: Convertir PDFs a imágenes PNG de alta calidad para OCR

**Características**:
- Conversión a 300 DPI para máxima calidad
- Procesamiento por lotes (batch)
- Manejo de PDFs multipágina
- Nomenclatura consistente: `{nombre_base}_page_{n}.png`

**Ejecución**:

```bash
python scripts/convertir_pdfs_a_png.py
```

**Salida**:
- Imágenes PNG en `data/pngs/[BANCO]/`
- Una imagen por página de PDF
- Log en `logs/convertir_pdfs_a_png.log`

---

### FASE 3: OCR con Google Gemini 2.5 Flash Lite

**Script**: `scripts/procesar_ocr_por_pagina.py`

**Propósito**: Extracción de texto y tablas usando visión multimodal

**Modelo**: `gemini-2.5-flash-lite`

**Prompt de extracción**:
```
Eres un extractor experto de datos financieros.
Extrae TODAS las tablas de este documento de tarifario bancario.

FORMATO DE SALIDA: Markdown puro
- Usa tablas Markdown con | y |--|
- Preserva EXACTAMENTE el contenido original
- NO agregues encabezados adicionales
- NO omitas filas

IMPORTANTE:
- Si hay múltiples tablas, sepáralas con línea en blanco
- Respeta celdas combinadas usando texto descriptivo
- Preserva símbolos: %, $, S/
```

**Características**:
- Procesamiento página por página
- Batch de 10 páginas por archivo de salida
- Reintentos automáticos (max 3)
- Rate limiting: 60 RPM
- Timeout: 120 segundos por página

**Ejecución**:

```bash
python scripts/procesar_ocr_por_pagina.py
```

**Salida**:
- Archivos Markdown en `data/ocr/[BANCO]/`
- Formato: `{nombre_base}_batch_{n}.md`
- Log detallado en `logs/procesar_ocr_por_pagina.log`

#### Procesamiento Paralelo con Múltiples APIs

**Scripts**: `scripts/procesar_ocr_por_banco_api2.py` y `scripts/procesar_ocr_por_banco_api3.py`

**Propósito**: Paralelizar el procesamiento OCR usando múltiples API keys de Google Gemini

**Características**:
- Permite procesar diferentes bancos simultáneamente en diferentes dispositivos
- Cada script usa una API key diferente para evitar límites de rate
- API 2: Usa variable de entorno `GOOGLE_API_KEY_2`
- API 3: Usa variable de entorno `GOOGLE_API_KEY_3`
- Comparten el mismo registro de progreso (`ocr_progress.json`)

**Configuración de múltiples API keys**:

Agregar al archivo `.env`:

```env
GOOGLE_API_KEY=tu_primera_api_key
GOOGLE_API_KEY_2=tu_segunda_api_key
GOOGLE_API_KEY_3=tu_tercera_api_key
```

**Ejecución paralela**:

```bash
# Terminal 1 (API 1) - Procesar BBVA
python scripts/procesar_ocr_por_pagina.py

# Terminal 2 (API 2) - Procesar BCP
python scripts/procesar_ocr_por_banco_api2.py BCP

# Terminal 3 (API 3) - Procesar Interbank
python scripts/procesar_ocr_por_banco_api3.py Interbank
```

**Listar bancos disponibles**:

```bash
python scripts/procesar_ocr_por_banco_api2.py --list
```

**Ventajas del procesamiento paralelo**:
- Reduce tiempo total de procesamiento en ~3x
- Aprovecha múltiples API keys (límite: 60 RPM por key)
- Permite distribuir trabajo entre múltiples dispositivos
- Manejo centralizado de progreso evita duplicados

**Ejemplo de uso distribuido**:
```bash
# PC 1: Procesar BBVA Continental con API 1
python scripts/procesar_ocr_por_pagina.py

# PC 2: Procesar BCP con API 2
python scripts/procesar_ocr_por_banco_api2.py BCP

# PC 3: Procesar Interbank con API 3
python scripts/procesar_ocr_por_banco_api3.py Interbank
```

---

### FASE 4: Combinación de Batches

**Script**: `scripts/combinar_md_batches.py`

**Propósito**: Consolidar batches OCR en archivos únicos por PDF

**Lógica**:
- Agrupa batches por nombre base (ej: `producto_batch_1.md`, `producto_batch_2.md`)
- Combina en orden secuencial
- Preserva saltos de línea y estructura
- Genera un `.md` final por PDF original

**Ejecución**:

```bash
python scripts/combinar_md_batches.py
```

**Salida**:
- Archivos Markdown consolidados en `data/ocr_combined/[BANCO]/`
- Formato: `{nombre_base}.md`
- Log en `logs/combinar_md_batches.log`

---

### FASE 5: Normalización con IA + Pydantic

**Script**: `scripts/normalizar_ocr_a_json.py`

**Propósito**: Transformar Markdown crudo a JSON estructurado con esquema Pydantic

**Modelo**: `gemini-2.0-flash-exp` (visión + texto)

**Esquema Pydantic**:

```python
class MonedaValores(BaseModel):
    tasa_porcentaje: Optional[float]
    monto_fijo: Optional[float]
    monto_minimo: Optional[float]
    monto_maximo: Optional[float]

class ItemTarifario(BaseModel):
    concepto: Dict[str, Any]
    clasificacion: Dict[str, str]
    valores: Dict[str, Any]
    aplicacion: Dict[str, Any]
    jerarquia: Dict[str, Any]
    metadata_item: Dict[str, List[str]]

class DocumentoTarifario(BaseModel):
    metadata: Dict[str, str]
    items: List[ItemTarifario]

class BatchTarifarios(BaseModel):
    banco: str
    batch_id: str
    fecha_procesamiento: str
    documentos: List[DocumentoTarifario]
```

**Prompt de normalización**:
```
Eres un experto en normalización de datos financieros bancarios.

TAREA: Convertir el texto Markdown a JSON estructurado siguiendo EXACTAMENTE el esquema Pydantic.

CLASIFICACIÓN DE TIPOS:
- TASA: Intereses compensatorios, moratorios, rendimientos
- COMISION: Cargos por servicios, transacciones, mantenimiento
- GASTO: Portes, envíos, notificaciones
- SEGURO: Primas, coberturas
- OTRO: No clasificable en anteriores

IMPORTANTE:
- Normaliza fechas a DD/MM/YYYY
- Convierte porcentajes a float (ej: "27%" → 27.0)
- Separa MN y ME correctamente
- Identifica encabezados (es_encabezado: true)
```

**Características**:
- Procesamiento batch a batch
- Validación estricta con Pydantic
- Reintentos en caso de error de parsing
- Timeout: 180 segundos por batch

**Ejecución**:

```bash
python scripts/normalizar_ocr_a_json.py
```

**Salida**:
- JSONs estructurados en `data/normalized_json/[BANCO]/batch_XXX.json`
- Log detallado en `logs/normalizar_ocr_a_json.log`

---

### FASE 6: Exportación a CSV/Excel

**3 scripts especializados**:

#### 6a. Dataset Completo

**Script**: `scripts/json_a_csv.py`

**Columnas**:
```
Banco, Producto_Codigo, Producto_Nombre, Concepto, Descripcion_Breve,
Tipo, Tasa_Porcentaje_MN, Tasa_Porcentaje_ME, Monto_Fijo_MN, Monto_Fijo_ME,
Monto_Minimo_MN, Monto_Maximo_MN, Monto_Minimo_ME, Monto_Maximo_ME,
Moneda, Fecha_Vigencia, Fecha_Extraccion, Periodicidad, Oportunidad_Cobro,
Observaciones
```

**Ejecución**:

```bash
python scripts/json_a_csv.py
```

**Salida**:
- `data/output/tarifarios_bancarios.csv`
- `data/output/tarifarios_bancarios.xlsx` (con hojas: Tarifarios, Resumen, Por_Tipo)

---

#### 6b. Solo Tasas

**Script**: `scripts/json_a_csv_solo_tasas.py`

**Filtro**: Solo items con `clasificacion.tipo == "TASA"`

**Columnas adicionales**:
```
Subtipo, Categoria
```

**Ejecución**:

```bash
python scripts/json_a_csv_solo_tasas.py
```

**Salida**:
- `data/output/tarifarios_bancarios_SOLO_TASAS.csv`
- `data/output/tarifarios_bancarios_SOLO_TASAS.xlsx` (con hojas: Tasas, Resumen_Por_Banco, Por_Categoria, Top_20_Tasas_MN, Top_20_Tasas_ME)

**Estadísticas**:
- 185 tasas extraídas
- Tasas MN: promedio 24.64%, rango 0-112.99%
- Tasas ME: promedio 20.42%, rango 0-107%

---

#### 6c. Formato Examen

**Script**: `scripts/json_a_csv_examen.py`

**Columnas (según especificaciones del examen)**:
```
Banco, Producto, Tasa, Moneda, Fecha de registro, Observaciones
```

**Formato campo "Tasa"**:
```
MN: 27% | ME: 32%
MN: S/ 5.00 | ME: $ 3.00
MN: 21% - 26%
```

**Ejecución**:

```bash
python scripts/json_a_csv_examen.py
```

**Salida**:
- `data/output/EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.csv`
- `data/output/EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.xlsx` (con hojas: Tarifarios Bancarios, Resumen por Banco, Metadatos)

---

## Resultados del Proyecto

### Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| PDFs procesados | 499 |
| Páginas convertidas | ~2,500 (estimado) |
| Items extraídos | 733 |
| Tasas identificadas | 185 |
| Comisiones identificadas | ~400 (estimado) |
| Bancos cubiertos | 5 |

### Distribución por Banco

| Banco | PDFs | Items Extraídos |
|-------|------|-----------------|
| BBVA Continental | ~120 | ~180 |
| BCP | ~150 | ~220 |
| Interbank | ~100 | ~150 |
| Scotiabank | ~90 | ~130 |
| Banco de la Nación | ~39 | ~53 |

### Top Tasas Identificadas

**Moneda Nacional (MN)**:
1. Scotiabank - Línea de Crédito Efectiva: 112.99%
2. BCP - American Express: 107%
3. Banco de la Nación - Tarjeta Clásica Disposición: 32%

**Moneda Extranjera (ME)**:
1. BCP - American Express: 107%
2. Scotiabank - Tarjeta Oro: 89%
3. Interbank - Tarjeta Platinum: 72%

---

## Validación de Datos

### Metodología de Validación

Se aplicó una estrategia de validación en 3 niveles:

1. **Validación interna**: Comparación CSV final vs JSONs normalizados
2. **Validación contra fuente**: Comparación CSV vs archivos .md originales (OCR)
3. **Validación web**: Búsquedas en sitios oficiales de bancos

### Resultados de Validación

**Banco de la Nación - Tasas Tarjeta de Crédito**:

| Producto | Tasa Compras | Tasa Disposición | Estado |
|----------|--------------|------------------|--------|
| Tarjeta Clásica | 27% | 32% | ✅ Validado |
| Tarjeta Gold | 25% | 30% | ✅ Validado |
| Tarjeta Platinum | 21% | 26% | ✅ Validado |
| Tasa Moratoria | 11.79% | - | ✅ Validado |

**Scotiabank - Línea de Crédito**:
- Tasa 112.99%: ✅ Confirmado en 24 archivos .md y sitio web oficial

**BCP - American Express**:
- Tasa 107%: ✅ Confirmado en sitio web oficial

**Tasas Moratorias**:
- Rango: 11.78% - 13.58%
- Estado: ✅ Dentro de límites regulatorios SBS

### Casos Especiales

**EUROS (EUR)**:
- Ocurrencias: 7 menciones (< 1% del dataset)
- Banco: Solo BBVA Continental
- Producto: Contiahorro Euros
- Estado: ❌ Descontinuado desde 01/04/2019
- Tratamiento: Incluido en categoría "ME" con detalle en "Observaciones"

---

## Datasets Finales

### 1. Dataset Completo

**Archivo**: `data/output/tarifarios_bancarios.xlsx`

**Contenido**:
- Hoja "Tarifarios": 733 filas × 20 columnas
- Hoja "Resumen": Resumen por banco
- Hoja "Por_Tipo": Distribución TASA/COMISION/GASTO/SEGURO

**Casos de uso**:
- Análisis exploratorio completo
- Comparación entre bancos
- Estudios de comisiones y gastos

---

### 2. Dataset Solo Tasas

**Archivo**: `data/output/tarifarios_bancarios_SOLO_TASAS.xlsx`

**Contenido**:
- Hoja "Tasas": 185 filas × 15 columnas
- Hoja "Resumen_Por_Banco": Items por banco
- Hoja "Por_Categoria": Distribución por categoría
- Hoja "Top_20_Tasas_MN": Tasas más altas en soles
- Hoja "Top_20_Tasas_ME": Tasas más altas en dólares

**Casos de uso**:
- Análisis de tasas de interés
- Benchmarking de productos crediticios
- Estudios de competitividad

---

### 3. Dataset Formato Examen

**Archivo**: `data/output/EXAMEN_PARCIAL_Tarifarios_Bancarios_Grupo2.xlsx`

**Contenido**:
- Hoja "Tarifarios Bancarios": 733 filas × 6 columnas
- Hoja "Resumen por Banco": Estadísticas
- Hoja "Metadatos": Info del proyecto

**Columnas**:
1. **Banco**: Nombre de la institución
2. **Producto**: Nombre del producto financiero
3. **Tasa**: Tasa/monto formateado (ej: "MN: 27% | ME: 32%")
4. **Moneda**: MN | ME | AMBAS
5. **Fecha de registro**: Fecha de vigencia
6. **Observaciones**: Tipo, descripción, condiciones, periodicidad, cliente, segmento

**Casos de uso**:
- Entrega académica
- Presentación ejecutiva
- Análisis simplificado

---

## Solución de Problemas

### Error: "GOOGLE_API_KEY not found"

**Causa**: Variable de entorno no configurada

**Solución**:
```bash
export GOOGLE_API_KEY="tu_api_key_aqui"
```

O crear archivo `.env`:
```env
GOOGLE_API_KEY=tu_api_key_aqui
```

---

### Error: "Poppler not found"

**Causa**: pdf2image no encuentra poppler

**Solución Windows**:
1. Descargar poppler: https://github.com/oschwartz10612/poppler-windows/releases
2. Extraer en `C:\poppler`
3. Agregar al PATH: `C:\poppler\Library\bin`

O configurar en script:
```python
images = convert_from_path(
    pdf_path,
    poppler_path=r"C:\poppler\Library\bin"
)
```

---

### Error: "Rate limit exceeded"

**Causa**: Superado límite de 60 RPM de Gemini API

**Solución**: El script ya implementa rate limiting automático con `time.sleep()`. Si persiste:
1. Reducir batch size en `procesar_ocr_por_pagina.py`
2. Aumentar `sleep_time` entre requests

---

### Error: "Pydantic validation error"

**Causa**: JSON generado por Gemini no cumple esquema

**Solución**: El script ya implementa reintentos (3 max). Si persiste:
1. Revisar prompt de normalización
2. Verificar formato de entrada (.md)
3. Revisar logs en `logs/normalizar_ocr_a_json.log`

---

### PDFs no descargados

**Causa**: Cambios en estructura web del banco

**Solución**:
1. Revisar URLs en `FUENTES_TARIFARIOS.md`
2. Actualizar selectores CSS/XPath en `descargar_pdfs.py`
3. Verificar que Selenium WebDriver esté actualizado


---

## Tecnologías Utilizadas

### IA y Procesamiento

- **Google Gemini 2.5 Flash Lite**: OCR multimodal (visión + texto) y Normalización con structured output
- **Pydantic**: Validación de esquemas y tipos

### Procesamiento de Documentos

- **pdf2image**: Conversión PDF → PNG
- **Pillow (PIL)**: Manipulación de imágenes
- **poppler**: Backend para pdf2image

### Web Scraping

- **Selenium**: Automatización de navegador
- **BeautifulSoup**: Parsing HTML
- **requests**: Descarga HTTP

### Procesamiento de Datos

- **pandas**: Manipulación de DataFrames
- **openpyxl**: Lectura/escritura Excel
- **csv**: Manejo de archivos CSV

### Logging y Monitoreo

- **loguru**: Logging avanzado con colores
- **pathlib**: Manejo de rutas multiplataforma

---


## Autor

**Grupo 2** - Analítica de Datos
Universidad Nacional de Ingeniería
Facultad de Ingeniería Industrial y de Sistemas

---

## Fecha de Última Actualización

24 de octubre de 2025

---

## Licencia

Este proyecto es de uso académico para el curso de Analítica de Datos - UNI FIIS.

