# Fuentes de Tarifarios Bancarios Perú 2025

## Enlaces Oficiales Verificados (Octubre 2025)

### 1. BBVA Continental

**Página principal de tarifas:**
- https://www.bbva.pe/personas/recomendacion-productos.html

**PDFs directos:**
- **Tarjetas de Crédito Persona Natural**: https://www.bbva.pe/content/dam/public-web/peru/documents/prefooter/personas-naturales-y-microempresas/tarjetas-de-credito-persona-natural.pdf
- **Préstamos**: https://www.bbva.pe/content/dam/public-web/peru/documents/prefooter/personas-naturales-y-microempresas/TARIFARIO-PRESTAMOS.pdf
- **Cuenta Empresas**: https://www.bbva.pe/content/dam/public-web/peru/documents/prefooter/pequenas-medianas-y-grandes-empresas/Tarifario-PJ_Cuenta-Empresas.pdf
- **Fórmulas Tarjetas**: https://www.bbva.pe/content/dam/public-web/peru/documents/personas/tarjetas/tarjeta-de-credito/formulas-tarjetas-credito-bbva.pdf
- **Membresías**: https://www.bbva.pe/content/dam/public-web/peru/documents/personas/tarjetas/tarjeta-de-credito/membresia-bbva.pdf

**Estado**: ✅ PDFs accesibles directamente

---

### 2. BCP (Banco de Crédito del Perú)

**Página principal:**
- https://www.viabcp.com/tasasytarifas

**Características:**
- Sistema interactivo (no PDF directo)
- Requiere navegación en la web
- Posiblemente con contenido dinámico/JavaScript

**Estado**: ⚠️ Requiere scraping dinámico

---

### 3. Interbank

**Página principal:**
- https://interbank.pe/tasas-tarifas

**Ayuda específica de tarjetas:**
- https://interbank.pe/centro-de-ayuda/tarjetas-de-credito/tasas-comisiones-e-intereses

**Características:**
- Sistema interactivo con múltiples PDFs
- Requiere selección de producto
- Actualizaciones desde enero 2025 (Resolución SBS N° 03883-2024)

**Estado**: ⚠️ Requiere scraping dinámico o navegación

---

### 4. Scotiabank

**Página principal:**
- https://www.scotiabank.com.pe/Acerca-de/Tarifario/default

**Características:**
- Sistema de búsqueda por segmento y producto
- No hay PDF único consolidado
- Tarifario interactivo

**Estado**: ⚠️ Requiere scraping dinámico complejo

---

### 5. Banco de la Nación

**Página principal:**
- https://www.bn.com.pe/tasas-comisiones/tarifario.asp

**PDF directo:**
- **Tarifario 2025 Consolidado**: https://www.bn.com.pe/tasas-comisiones/Tarifario-BN.pdf

**PDFs específicos:**
- **Tarjetas de Crédito**: https://www.bn.com.pe/tasas-comisiones/tasas-tarjeta-credito.pdf
- **Préstamos Multired Consumo**: https://www.bn.com.pe/tasas-comisiones/tasas-prestamos-consumo.pdf
- **Comisiones Ventanillas y Agentes**: https://www.bn.com.pe/canales-atencion/documentos/comision-ventanillas-agentesBN.pdf

**Estado**: ✅ PDFs accesibles directamente

---

## Técnicas de Web Scraping por Tipo de Fuente

### Técnica 1: Descarga Directa de PDFs (BBVA, Banco de la Nación)

**Librerías necesarias:**
```python
import requests
from pathlib import Path
from datetime import datetime
```

**Código:**
```python
def descargar_pdf_directo(url, nombre_archivo, carpeta_destino="TARIFARIOS"):
    """
    Descarga PDF directamente desde URL
    """
    Path(carpeta_destino).mkdir(exist_ok=True)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Guardar PDF
        ruta_completa = Path(carpeta_destino) / nombre_archivo
        with open(ruta_completa, 'wb') as f:
            f.write(response.content)

        # Metadata
        metadata = {
            'banco': nombre_archivo.split('_')[0],
            'url': url,
            'fecha_descarga': datetime.now().isoformat(),
            'tamaño_bytes': len(response.content)
        }

        return ruta_completa, metadata

    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return None, None
```

**Ejemplo de uso:**
```python
urls_directas = {
    'BBVA_tarjetas_credito.pdf': 'https://www.bbva.pe/content/dam/public-web/peru/documents/prefooter/personas-naturales-y-microempresas/tarjetas-de-credito-persona-natural.pdf',
    'BBVA_prestamos.pdf': 'https://www.bbva.pe/content/dam/public-web/peru/documents/prefooter/personas-naturales-y-microempresas/TARIFARIO-PRESTAMOS.pdf',
    'BancoNacion_tarifario_2025.pdf': 'https://www.bn.com.pe/tasas-comisiones/tarifario-BN.pdf',
    'BancoNacion_tarjetas.pdf': 'https://www.bn.com.pe/tasas-comisiones/tasas-tarjeta-credito.pdf'
}

for nombre, url in urls_directas.items():
    ruta, meta = descargar_pdf_directo(url, nombre)
    if ruta:
        print(f"✅ Descargado: {ruta}")
```

---

### Técnica 2: Selenium con Chrome (BCP, Interbank, Scotiabank)

**Para sitios con contenido dinámico/JavaScript**

**Librerías necesarias:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
```

**Código:**
```python
def scrape_con_selenium(url_base, wait_time=5):
    """
    Scraping con Selenium para sitios dinámicos
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Sin interfaz gráfica
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

    # Configurar descarga automática de PDFs
    prefs = {
        "download.default_directory": str(Path("TARIFARIOS").absolute()),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url_base)
        time.sleep(wait_time)

        # Buscar enlaces a PDFs
        enlaces_pdf = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")

        urls_encontradas = []
        for enlace in enlaces_pdf:
            href = enlace.get_attribute('href')
            texto = enlace.text
            urls_encontradas.append({'url': href, 'texto': texto})

        return urls_encontradas

    finally:
        driver.quit()
```

**Ejemplo BCP:**
```python
# Buscar PDFs en la página de tarifas de BCP
urls_bcp = scrape_con_selenium('https://www.viabcp.com/tasasytarifas')

for item in urls_bcp:
    print(f"Encontrado: {item['texto']} -> {item['url']}")
    # Descargar cada PDF encontrado
    descargar_pdf_directo(item['url'], f"BCP_{item['texto']}.pdf")
```

---

### Técnica 3: BeautifulSoup + Requests (para HTML estático)

**Para páginas con enlaces a PDFs en HTML simple**

**Librerías necesarias:**
```python
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
```

**Código:**
```python
def buscar_pdfs_en_pagina(url_base):
    """
    Busca todos los enlaces PDF en una página HTML
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url_base, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Buscar enlaces a PDF
    enlaces_pdf = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '.pdf' in href.lower():
            url_completa = urljoin(url_base, href)
            texto = link.get_text(strip=True) or link.get('title', 'Sin título')
            enlaces_pdf.append({
                'url': url_completa,
                'texto': texto
            })

    return enlaces_pdf
```

**Ejemplo:**
```python
# Buscar en página de BBVA
pdfs_bbva = buscar_pdfs_en_pagina('https://www.bbva.pe/personas/recomendacion-productos.html')

for pdf in pdfs_bbva:
    print(f"📄 {pdf['texto']}: {pdf['url']}")
```

---

### Técnica 4: Playwright (alternativa moderna a Selenium)

**Más rápido y eficiente para scraping moderno**

**Instalación:**
```bash
pip install playwright
playwright install chromium
```

**Código:**
```python
from playwright.sync_api import sync_playwright
import time

def scrape_con_playwright(url, selector_esperar=None):
    """
    Scraping con Playwright (más rápido que Selenium)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        # Capturar descargas
        descargas = []
        page.on("download", lambda download: descargas.append(download))

        page.goto(url, wait_until='networkidle')

        if selector_esperar:
            page.wait_for_selector(selector_esperar, timeout=10000)

        # Extraer enlaces PDF
        enlaces = page.query_selector_all('a[href*=".pdf"]')

        urls_pdf = []
        for enlace in enlaces:
            href = enlace.get_attribute('href')
            texto = enlace.inner_text()
            if href:
                urls_pdf.append({'url': href, 'texto': texto})

        browser.close()
        return urls_pdf
```

---

### Técnica 5: Scraping con API REST (si existe)

**Algunos bancos exponen APIs internas**

**Código:**
```python
def buscar_api_interna(url_base):
    """
    Intenta detectar llamadas API en el sitio
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Habilitar logging de red
    caps = options.to_capabilities()
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get(url_base)
    time.sleep(5)

    # Analizar logs de red
    logs = driver.get_log('performance')

    apis_detectadas = []
    for entry in logs:
        message = json.loads(entry['message'])['message']
        if 'Network.requestWillBeSent' in message['method']:
            url = message['params']['request']['url']
            if 'api' in url.lower() or 'json' in url.lower():
                apis_detectadas.append(url)

    driver.quit()
    return list(set(apis_detectadas))
```

---

### Técnica 6: Automatización con Navegación Compleja

**Para sitios que requieren clicks e interacciones**

**Código:**
```python
def navegar_y_descargar_scotiabank():
    """
    Ejemplo específico para Scotiabank que requiere navegación
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible para debug
        page = browser.new_page()

        page.goto('https://www.scotiabank.com.pe/Acerca-de/Tarifario/default')

        # Esperar que cargue
        page.wait_for_load_state('networkidle')

        # Seleccionar segmento "Personas"
        page.click('text="Personas"')
        page.wait_for_timeout(2000)

        # Seleccionar familia "Tarjetas de Crédito"
        page.click('text="Tarjetas de Crédito"')
        page.wait_for_timeout(2000)

        # Extraer información visible
        contenido = page.content()

        # Buscar botón de descarga PDF si existe
        try:
            page.click('text="Descargar PDF"')
            page.wait_for_timeout(5000)
        except:
            print("No hay botón de descarga directa")

        browser.close()
```

---

## Script Completo de Descarga Automatizada

```python
#!/usr/bin/env python3
# descargar_tarifarios.py

import requests
from pathlib import Path
from datetime import datetime
import json
import time

# Configuración
CARPETA_DESTINO = Path("TARIFARIOS")
CARPETA_DESTINO.mkdir(exist_ok=True)

# Metadata de descarga
METADATA_FILE = CARPETA_DESTINO / "metadata_descargas.json"

def descargar_pdf(url, nombre, banco):
    """Descarga un PDF y guarda metadata"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        print(f"📥 Descargando {nombre}...")
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()

        # Guardar archivo
        ruta = CARPETA_DESTINO / nombre
        with open(ruta, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Crear metadata
        metadata = {
            'banco': banco,
            'nombre_archivo': nombre,
            'url_origen': url,
            'fecha_descarga': datetime.now().isoformat(),
            'tamaño_bytes': ruta.stat().st_size,
            'hash_md5': None  # Opcional: calcular hash
        }

        print(f"✅ Descargado: {ruta} ({metadata['tamaño_bytes']:,} bytes)")
        return metadata

    except Exception as e:
        print(f"❌ Error descargando {nombre}: {e}")
        return None

def main():
    """Descarga todos los tarifarios disponibles"""

    # Lista de PDFs a descargar
    tarifarios = [
        # BBVA
        {
            'url': 'https://www.bbva.pe/content/dam/public-web/peru/documents/prefooter/personas-naturales-y-microempresas/tarjetas-de-credito-persona-natural.pdf',
            'nombre': 'BBVA_tarjetas_credito_2025.pdf',
            'banco': 'BBVA Continental'
        },
        {
            'url': 'https://www.bbva.pe/content/dam/public-web/peru/documents/prefooter/personas-naturales-y-microempresas/TARIFARIO-PRESTAMOS.pdf',
            'nombre': 'BBVA_prestamos_2025.pdf',
            'banco': 'BBVA Continental'
        },
        {
            'url': 'https://www.bbva.pe/content/dam/public-web/peru/documents/personas/tarjetas/tarjeta-de-credito/membresia-bbva.pdf',
            'nombre': 'BBVA_membresia_2025.pdf',
            'banco': 'BBVA Continental'
        },

        # Banco de la Nación
        {
            'url': 'https://www.bn.com.pe/tasas-comisiones/tarifario-BN.pdf',
            'nombre': 'BancoNacion_tarifario_general_2025.pdf',
            'banco': 'Banco de la Nación'
        },
        {
            'url': 'https://www.bn.com.pe/tasas-comisiones/tasas-tarjeta-credito.pdf',
            'nombre': 'BancoNacion_tarjetas_credito_2025.pdf',
            'banco': 'Banco de la Nación'
        },
        {
            'url': 'https://www.bn.com.pe/tasas-comisiones/tasas-prestamos-consumo.pdf',
            'nombre': 'BancoNacion_prestamos_consumo_2025.pdf',
            'banco': 'Banco de la Nación'
        }
    ]

    # Descargar todos
    metadatos = []
    for tarif in tarifarios:
        meta = descargar_pdf(tarif['url'], tarif['nombre'], tarif['banco'])
        if meta:
            metadatos.append(meta)
        time.sleep(1)  # Delay entre descargas

    # Guardar metadata
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadatos, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Total descargados: {len(metadatos)}/{len(tarifarios)}")
    print(f"📋 Metadata guardada en: {METADATA_FILE}")

if __name__ == '__main__':
    main()
```

---

## Estrategia Recomendada

### Fase 1: Descargas Directas (IMPLEMENTAR PRIMERO)
1. ✅ BBVA - PDFs directos
2. ✅ Banco de la Nación - PDFs directos

### Fase 2: Scraping Dinámico (IMPLEMENTAR DESPUÉS)
3. ⚠️ BCP - Requiere Selenium/Playwright
4. ⚠️ Interbank - Requiere navegación
5. ⚠️ Scotiabank - Requiere interacción compleja

### Fase 3: Validación y Documentación
6. Verificar integridad de PDFs descargados
7. Documentar fuentes y fechas
8. Generar tabla comparativa de tarifas

---

## Comandos para Ejecutar

### Instalación de dependencias:
```bash
# Básico
pip install requests beautifulsoup4 lxml

# Selenium
pip install selenium webdriver-manager

# Playwright (recomendado)
pip install playwright
playwright install chromium

# Todas las librerías del proyecto
pip install requests beautifulsoup4 selenium playwright webdriver-manager pandas openpyxl
```

### Ejecutar descarga:
```bash
python descargar_tarifarios.py
```

---

## Notas Importantes

1. **Respetar robots.txt**: Verificar si el sitio permite scraping
2. **Rate limiting**: No hacer más de 1 solicitud por segundo
3. **User-Agent**: Usar un User-Agent realista
4. **Manejo de errores**: Implementar reintentos con backoff exponencial
5. **Logging**: Registrar todas las descargas y errores
6. **Versionado**: Incluir fecha en nombres de archivo

---

## Para Búsquedas Manuales

Si prefieres buscar manualmente, utiliza estos términos en Google:

```
site:bbva.pe filetype:pdf tarifario 2025
site:viabcp.com filetype:pdf tarifario
site:interbank.pe filetype:pdf tarifario tarjetas
site:scotiabank.com.pe filetype:pdf tarifario
site:bn.com.pe filetype:pdf tarifario 2025
```

O directamente en los sitios:
- BBVA: Ir a Personas > Productos > Ver tarifario
- BCP: Menú > Información > Tasas y Tarifas
- Interbank: Menú > Transparencia > Tasas y Tarifas
- Scotiabank: Acerca de > Tarifario
- Banco de la Nación: Transparencia > Tarifario

---

**Última actualización**: 23 de octubre de 2025
**Verificación de enlaces**: Todos los enlaces fueron verificados mediante búsqueda web
