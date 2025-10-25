"""
Scraper para Interbank (requiere Selenium por bloqueo anti-bot)
"""
from typing import List, Optional
from urllib.parse import urljoin
from loguru import logger
from .base import BaseScraper
from ..models import TarifarioURL, BancoEnum

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium no está instalado. InterbankScraper usará requests (puede fallar por 403)")


class InterbankScraper(BaseScraper):
    """Scraper para Interbank - Sistema de tabs dinámicos (requiere Selenium)"""

    URL_BASE = "https://interbank.pe/tasas-tarifas"

    # Tabs exactos encontrados manualmente
    TABS = [
        "banca-personas---cuentas",
        "banca-personas---tarjetas",
        "banca-personas---creditos",
        "banca-persona---pagos-y-servicios",
        "banca-empresas---cuentas",
        "banca-empresas---financiamientos",
        "banca-empresas---servicios",
        "banca-empresa---comercio-exterior",
        "banca-empresa---reactiva-peru",
        "banca-pequena-empresa---comercio-exterior",
        "banca-pequena-empresa---servicios",
        "banca-pequena-empresa---creditos",
        "banca-pequena-empresa---cuentas",
        "banca-pequena-empresa---leasing-bpe",
    ]

    def __init__(self):
        super().__init__(BancoEnum.INTERBANK)
        self.driver: Optional[webdriver.Chrome] = None

    def _iniciar_selenium(self):
        """Inicializa el driver de Selenium"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium no está instalado. Ejecuta: pip install selenium webdriver-manager")

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Especificar ubicación de Edge
        options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

        try:
            service = Service(EdgeChromiumDriverManager().install())
        except Exception as e:
            logger.warning(f"No se pudo descargar driver automáticamente: {e}")
            logger.info("Intentando usar driver del sistema...")
            service = Service()

        self.driver = webdriver.Edge(service=service, options=options)

        # Evadir detección de Selenium
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logger.debug("Selenium driver iniciado para Interbank")

    def obtener_urls(self) -> List[TarifarioURL]:
        """
        Extrae todas las URLs de PDFs de Interbank usando Selenium
        """
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium no disponible. Interbank bloquea requests normales.")
            logger.info("Instala con: pip install selenium webdriver-manager")
            return []

        urls_encontradas = []
        urls_vistas = set()

        try:
            self._iniciar_selenium()

            # URLs a scrapear
            urls_a_scrapear = [self.URL_BASE]
            for tab in self.TABS:
                urls_a_scrapear.append(f"{self.URL_BASE}?tabs={tab}")

            logger.info(f"Scrapeando Interbank con Selenium: {len(urls_a_scrapear)} URLs")

            for idx, url in enumerate(urls_a_scrapear, 1):
                try:
                    logger.debug(f"[{idx}/{len(urls_a_scrapear)}] {url}")

                    self.driver.get(url)

                    # Esperar a que cargue el contenido
                    import time
                    time.sleep(2)

                    # Buscar todos los enlaces a PDF
                    enlaces = self.driver.find_elements(By.TAG_NAME, "a")

                    for enlace in enlaces:
                        try:
                            href = enlace.get_attribute("href")

                            if not href or not self._es_url_pdf(href):
                                continue

                            # Evitar duplicados
                            if href in urls_vistas:
                                continue
                            urls_vistas.add(href)

                            # Extraer texto
                            texto = enlace.text.strip()
                            if not texto:
                                texto = enlace.get_attribute('title') or ''
                            if not texto:
                                texto = enlace.get_attribute('aria-label') or ''
                            if not texto:
                                texto = href.split('/')[-1].replace('.pdf', '').replace('-', ' ')

                            tipo_producto = self._inferir_tipo_producto(href, texto)

                            tarifario_url = TarifarioURL(
                                url=href,
                                texto=texto,
                                tipo_producto=tipo_producto,
                                banco=self.banco
                            )

                            urls_encontradas.append(tarifario_url)
                            logger.debug(f"  ✓ {texto[:50]}...")

                        except Exception as e:
                            continue

                except Exception as e:
                    logger.warning(f"Error scrapeando {url}: {e}")
                    continue

            logger.info(f"Total URLs encontradas en Interbank: {len(urls_encontradas)}")

        except Exception as e:
            logger.error(f"Error scrapeando Interbank con Selenium: {e}")

        finally:
            if self.driver:
                self.driver.quit()
                logger.debug("Selenium driver cerrado")

        return urls_encontradas

    def _inferir_tipo_producto(self, url: str, texto: str) -> str:
        """Infiere el tipo de producto desde la URL o texto"""
        texto_lower = (texto + " " + url).lower()

        if any(k in texto_lower for k in ['tarjeta', 'credito', 'debito', 'visa', 'mastercard']):
            return 'tarjetas'
        elif any(k in texto_lower for k in ['prestamo', 'credito', 'convenio', 'financiamiento']):
            return 'prestamos'
        elif any(k in texto_lower for k in ['cuenta', 'ahorro', 'deposito']):
            return 'cuentas'
        elif any(k in texto_lower for k in ['hipotecario', 'vivienda']):
            return 'hipotecarios'
        elif any(k in texto_lower for k in ['comercio', 'exterior']):
            return 'comercio_exterior'
        elif any(k in texto_lower for k in ['leasing']):
            return 'leasing'
        elif any(k in texto_lower for k in ['servicio', 'pago']):
            return 'servicios'
        else:
            return 'otros'

    def cerrar(self):
        """Cierra el driver de Selenium si está activo"""
        if self.driver:
            self.driver.quit()
        super().cerrar()
