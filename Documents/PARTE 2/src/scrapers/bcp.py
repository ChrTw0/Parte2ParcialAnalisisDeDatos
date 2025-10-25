"""
Scraper para BCP
"""
from typing import List
from urllib.parse import urljoin
from loguru import logger
from .base import BaseScraper
from ..models import TarifarioURL, BancoEnum


class BCPScraper(BaseScraper):
    """Scraper para BCP"""

    URL_BASE = "https://www.viabcp.com/tasasytarifas"

    def __init__(self):
        super().__init__(BancoEnum.BCP)

    def obtener_urls(self) -> List[TarifarioURL]:
        """
        Extrae todas las URLs de PDFs de la página de tasas y tarifas de BCP
        """
        urls_encontradas = []
        urls_vistas = set()

        logger.info(f"Scrapeando {self.URL_BASE}")
        try:
            response = self._hacer_request(self.URL_BASE)
            soup = self._parsear_html(response.text)

            # Buscar enlaces <a> con href
            enlaces = soup.find_all('a', href=True)

            for enlace in enlaces:
                href = enlace.get('href', '')

                if not href or not self._es_url_pdf(href):
                    continue

                # Construir URL completa
                if href.startswith('http'):
                    url_completa = href
                else:
                    url_completa = urljoin(self.URL_BASE, href)

                # Evitar duplicados
                if url_completa in urls_vistas:
                    continue
                urls_vistas.add(url_completa)

                # Extraer texto
                texto = enlace.get_text(strip=True)
                if not texto:
                    texto = enlace.get('title', '')
                if not texto:
                    texto = url_completa.split('/')[-1].replace('.pdf', '').replace('-', ' ')

                tipo_producto = self._inferir_tipo_producto(url_completa, texto)

                tarifario_url = TarifarioURL(
                    url=url_completa,
                    texto=texto,
                    tipo_producto=tipo_producto,
                    banco=self.banco
                )

                urls_encontradas.append(tarifario_url)
                logger.debug(f"✓ {texto[:50]}... -> {url_completa}")

        except Exception as e:
            logger.error(f"Error scrapeando BCP: {e}")

        logger.info(f"Total URLs encontradas en BCP: {len(urls_encontradas)}")
        return urls_encontradas

    def _inferir_tipo_producto(self, url: str, texto: str) -> str:
        """Infiere el tipo de producto desde la URL o texto"""
        texto_lower = (texto + " " + url).lower()

        if any(k in texto_lower for k in ['tarjeta', 'credito', 'debito']):
            return 'tarjetas'
        elif any(k in texto_lower for k in ['prestamo', 'credito']):
            return 'prestamos'
        elif any(k in texto_lower for k in ['cuenta', 'ahorro']):
            return 'cuentas'
        elif any(k in texto_lower for k in ['empresa', 'negocio']):
            return 'empresas'
        else:
            return 'otros'
