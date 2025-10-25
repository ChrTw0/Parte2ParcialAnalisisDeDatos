# Tarifarios Scraper - Estructura del Proyecto

## 📁 Estructura de Directorios

```
PARTE 2/
├── src/                          # Código fuente
│   ├── __init__.py
│   ├── config.py                # Configuración global
│   ├── api/                     # API FastAPI
│   │   ├── __init__.py
│   │   └── main.py             # Endpoints de la API
│   ├── models/                  # Modelos de datos (Pydantic)
│   │   ├── __init__.py
│   │   └── tarifario.py        # Modelos de tarifarios
│   ├── scrapers/                # Scrapers por banco
│   │   ├── __init__.py
│   │   ├── base.py             # Clase base abstracta
│   │   ├── bbva.py             # Scraper BBVA
│   │   ├── bcp.py              # Scraper BCP
│   │   ├── interbank.py        # Scraper Interbank
│   │   ├── scotiabank.py       # Scraper Scotiabank
│   │   └── banco_nacion.py     # Scraper Banco de la Nación
│   └── utils/                   # Utilidades
│       ├── __init__.py
│       ├── downloader.py       # Descarga de PDFs
│       └── logger.py           # Configuración de logs
├── scripts/                     # Scripts CLI
│   └── run_scraper.py          # Script principal de scraping
├── tests/                       # Tests
│   ├── __init__.py
│   ├── unit/                   # Tests unitarios
│   ├── integration/            # Tests de integración
│   └── test_scrapers.py        # Tests de scrapers
├── data/                        # Datos procesados
│   ├── raw/                    # Datos crudos
│   └── processed/              # Datos procesados
├── TARIFARIOS/                  # PDFs descargados
│   ├── BBVA_Continental/
│   ├── BCP/
│   ├── Interbank/
│   ├── Scotiabank/
│   └── Banco_de_la_Nación/
├── logs/                        # Logs de la aplicación
├── requirements.txt             # Dependencias
├── .env.example                # Ejemplo de variables de entorno
├── .gitignore
└── README_PROYECTO.md          # Este archivo
```

## 🚀 Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
```

### 2. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

## 📋 Uso

### Opción 1: API FastAPI

**Iniciar servidor:**
```bash
python -m src.api.main
# O usando uvicorn directamente:
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Endpoints disponibles:**

- `GET /` - Información del proyecto
- `GET /health` - Health check
- `GET /bancos` - Listar bancos disponibles
- `POST /scrape/{banco}` - Scrapear URLs de un banco
- `POST /download/{banco}` - Descargar PDFs de un banco
- `POST /download/all` - Descargar todos los tarifarios

**Ejemplos con curl:**

```bash
# Listar bancos
curl http://localhost:8000/bancos

# Scrapear BBVA
curl -X POST http://localhost:8000/scrape/BBVA%20Continental

# Descargar tarifarios de BCP
curl -X POST http://localhost:8000/download/BCP

# Descargar todos
curl -X POST http://localhost:8000/download/all
```

**Documentación interactiva:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Opción 2: Script CLI

```bash
python scripts/run_scraper.py
```

Esto ejecutará el scraping de todos los bancos y descargará los PDFs automáticamente.

### Opción 3: Uso programático

```python
from src.scrapers import BBVAScraper
from src.utils import PDFDownloader

# Scrapear URLs
with BBVAScraper() as scraper:
    urls = scraper.obtener_urls()
    print(f"Encontradas {len(urls)} URLs")

# Descargar PDFs
downloader = PDFDownloader()
for url in urls:
    resultado = downloader.descargar(url)
    if resultado.exito:
        print(f"✅ {resultado.metadata.nombre_archivo}")
```

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src tests/

# Test específico
pytest tests/test_scrapers.py -v
```

## 🏗️ Arquitectura

### Patrón de Diseño

El proyecto utiliza:
- **Strategy Pattern**: Cada banco tiene su propio scraper que implementa `BaseScraper`
- **Dependency Injection**: Configuración centralizada en `settings`
- **Repository Pattern**: Separación de lógica de scraping y descarga

### Flujo de Datos

```
1. API/CLI Request
   ↓
2. Scraper específico (BBVA, BCP, etc.)
   ↓
3. Extracción de URLs desde HTML
   ↓
4. PDFDownloader
   ↓
5. Descarga y almacenamiento
   ↓
6. Generación de metadata
   ↓
7. Response con resultados
```

### Modelos de Datos

- **TarifarioURL**: URL de un PDF con metadata
- **TarifarioMetadata**: Metadata de un PDF descargado
- **ScrapingResult**: Resultado de un proceso de scraping
- **DownloadResult**: Resultado de una descarga

## 🔧 Configuración

Archivo `.env`:

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Paths
DATA_DIR=./data
TARIFARIOS_DIR=./TARIFARIOS

# Scraping
USER_AGENT="Mozilla/5.0..."
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
DELAY_BETWEEN_REQUESTS=1
```

## 📊 Bancos Soportados

| Banco | Scraper | Estado | Método |
|-------|---------|--------|--------|
| BBVA Continental | ✅ | Implementado | BeautifulSoup |
| BCP | ✅ | Implementado | BeautifulSoup |
| Interbank | ✅ | Implementado | BeautifulSoup |
| Scotiabank | ⚠️ | Pendiente | Selenium requerido |
| Banco de la Nación | ✅ | Implementado | URLs hardcodeadas |

## 🐛 Troubleshooting

### Error: "No module named 'src'"

```bash
# Ejecutar desde la raíz del proyecto:
python -m src.api.main
# No: python src/api/main.py
```

### Error al descargar PDFs

Verificar:
1. URLs válidas
2. Conexión a internet
3. Permisos de escritura en carpeta TARIFARIOS
4. User-Agent válido en configuración

## 📝 TODO

- [ ] Implementar scraper de Scotiabank con Selenium
- [ ] Agregar caché de URLs scrapeadas
- [ ] Implementar sistema de notificaciones
- [ ] Agregar validación de integridad de PDFs
- [ ] Implementar extracción automática de datos de PDFs
- [ ] Agregar base de datos para almacenar metadata
- [ ] Implementar sistema de versionado de tarifarios
- [ ] Agregar comparación de tarifas entre bancos

## 📄 Licencia

Proyecto académico - Universidad Nacional de Ingeniería

---

**Grupo 2** - Analítica de Datos
Fecha: Octubre 2025
