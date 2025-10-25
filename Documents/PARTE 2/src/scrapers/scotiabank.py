"""
Scraper para Scotiabank (extrae URLs desde JSON embebido en data-items)
"""
from typing import List, Optional
import json
import html
from loguru import logger
from .base import BaseScraper
from ..models import TarifarioURL, BancoEnum

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium no está instalado. ScotiabankScraper no funcionará.")


class ScotiabankScraper(BaseScraper):
    """
    Scraper para Scotiabank - Extrae URLs desde JSON en atributo data-items
    La página tiene todos los PDFs en un JSON embebido, no necesita navegación
    """

    URL_BASE = "https://www.scotiabank.com.pe/Acerca-de/Tarifario/default"

    def __init__(self):
        super().__init__(BancoEnum.SCOTIABANK)
        self.driver: Optional[webdriver.Edge] = None

    def _iniciar_selenium(self):
        """Inicializa el driver de Selenium"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium no está instalado. Ejecuta: pip install selenium webdriver-manager")

        options = Options()
        options.add_argument('--headless')  # Sin interfaz gráfica
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'user-agent={self.session.headers["User-Agent"]}')

        # Especificar ubicación de Edge
        options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

        try:
            service = Service(EdgeChromiumDriverManager().install())
        except Exception as e:
            logger.warning(f"No se pudo descargar driver automáticamente: {e}")
            logger.info("Intentando usar driver del sistema...")
            service = Service()

        self.driver = webdriver.Edge(service=service, options=options)
        logger.debug("Selenium driver iniciado")

    def obtener_urls(self) -> List[TarifarioURL]:
        """
        Extrae URLs de PDFs desde el JSON embebido en data-items
        """
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium no disponible. Instala con: pip install selenium webdriver-manager")
            return []

        urls_encontradas = []
        urls_vistas = set()

        try:
            self._iniciar_selenium()
            logger.info(f"Navegando a {self.URL_BASE}")

            self.driver.get(self.URL_BASE)

            # Esperar a que cargue la página
            import time
            time.sleep(5)  # Aumentar espera

            # Buscar el elemento con data-items
            try:
                # Intentar diferentes formas de buscar el elemento
                section = None

                # Método 1: Por CSS selector completo
                try:
                    section = self.driver.find_element(By.CSS_SELECTOR, "section.cascadingDropdownLinks[data-items]")
                except:
                    pass

                # Método 2: Buscar por clase y luego verificar atributo
                if not section:
                    try:
                        sections = self.driver.find_elements(By.CLASS_NAME, "cascadingDropdownLinks")
                        for s in sections:
                            if s.get_attribute("data-items"):
                                section = s
                                break
                    except:
                        pass

                # Método 3: Buscar por tag y filtrar
                if not section:
                    sections = self.driver.find_elements(By.TAG_NAME, "section")
                    for s in sections:
                        if s.get_attribute("data-items"):
                            section = s
                            logger.info("Elemento encontrado por búsqueda en tags")
                            break

                if not section:
                    # Guardar HTML para debug
                    html_content = self.driver.page_source
                    with open("scotiabank_error.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.error("No se encontró elemento con data-items. HTML guardado en scotiabank_error.html")
                    raise Exception("No se encontró section.cascadingDropdownLinks[data-items]")

                data_items_raw = section.get_attribute("data-items")

                # Decodificar HTML entities
                data_items_decoded = html.unescape(data_items_raw)

                # Parsear el JSON
                data = json.loads(data_items_decoded)
                logger.info(f"JSON parseado correctamente: {len(data)} segmentos de banca")

                # Recorrer recursivamente el JSON para extraer todos los PDFs
                self._extract_pdfs_from_json(data, urls_encontradas, urls_vistas)

                logger.info(f"Total URLs encontradas en Scotiabank: {len(urls_encontradas)}")

            except Exception as e:
                logger.error(f"Error extrayendo data-items: {e}")
                raise

        except Exception as e:
            logger.error(f"Error scrapeando Scotiabank: {e}")

        finally:
            if self.driver:
                self.driver.quit()
                logger.debug("Selenium driver cerrado")

        return urls_encontradas

    def _extract_pdfs_from_json(self, data, urls_encontradas, urls_vistas, path=""):
        """Extrae recursivamente todas las URLs de PDF del JSON"""
        if isinstance(data, dict):
            # Extraer información del nodo actual
            title = data.get("Title", "")
            resource_url = data.get("ResourceUrl")

            # Construir ruta jerárquica
            current_path = f"{path} > {title}" if path else title

            # Si tiene URL y es PDF, agregarlo
            if resource_url and self._es_url_pdf(resource_url):
                if resource_url not in urls_vistas:
                    urls_vistas.add(resource_url)

                    tarifario_url = TarifarioURL(
                        url=resource_url,
                        texto=current_path,
                        tipo_producto=self._inferir_tipo_producto(resource_url, current_path),
                        banco=self.banco
                    )

                    urls_encontradas.append(tarifario_url)
                    logger.debug(f"✓ {current_path[:60]}...")

            # Recursión en SubResources
            if "SubResources" in data:
                self._extract_pdfs_from_json(data["SubResources"], urls_encontradas, urls_vistas, current_path)

        elif isinstance(data, list):
            # Si es lista, procesar cada elemento
            for item in data:
                self._extract_pdfs_from_json(item, urls_encontradas, urls_vistas, path)

    def _inferir_tipo_producto(self, url: str, texto: str) -> str:
        """Infiere el tipo de producto desde la URL o texto"""
        texto_lower = (texto + " " + url).lower()

        if any(k in texto_lower for k in ['tarjeta', 'credito']):
            return 'tarjetas'
        elif any(k in texto_lower for k in ['prestamo', 'credito']):
            return 'prestamos'
        elif any(k in texto_lower for k in ['cuenta', 'ahorro']):
            return 'cuentas'
        elif any(k in texto_lower for k in ['comercio', 'exterior', 'carta']):
            return 'comercio_exterior'
        else:
            return 'otros'

    def cerrar(self):
        """Cierra el driver de Selenium si está activo"""
        if self.driver:
            self.driver.quit()
        super().cerrar()
