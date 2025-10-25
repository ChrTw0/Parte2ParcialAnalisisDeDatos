"""
Scraper para BBVA Continental
"""
from typing import List
from urllib.parse import urljoin
from loguru import logger
from .base import BaseScraper
from ..models import TarifarioURL, BancoEnum


class BBVAScraper(BaseScraper):
    """Scraper para BBVA Continental"""

    # URLs base para scrapear
    URLS_BASE = [
        "https://www.bbva.pe/personas/personas-naturales-y-microempresas.html",
        "https://www.bbva.pe/personas/pequenas-medianas-y-grandes-empresas.html"
    ]

    def __init__(self):
        super().__init__(BancoEnum.BBVA)

    def obtener_urls(self) -> List[TarifarioURL]:
        """
        Extrae todas las URLs de PDFs de las páginas de BBVA
        """
        urls_encontradas = []
        urls_vistas = set()  # Para evitar duplicados

        for url_base in self.URLS_BASE:
            logger.info(f"Scrapeando {url_base}")
            try:
                response = self._hacer_request(url_base)
                soup = self._parsear_html(response.text)

                # Buscar todos los enlaces <a> con href
                enlaces = soup.find_all('a', href=True)

                for enlace in enlaces:
                    href = enlace.get('href', '')

                    # Verificar si es PDF
                    if not href or not self._es_url_pdf(href):
                        continue

                    # Construir URL completa
                    if href.startswith('http'):
                        url_completa = href
                    else:
                        url_completa = urljoin(url_base, href)

                    # Evitar duplicados
                    if url_completa in urls_vistas:
                        continue
                    urls_vistas.add(url_completa)

                    # Extraer texto descriptivo
                    texto = enlace.get_text(strip=True)
                    if not texto:
                        texto = enlace.get('title', '')
                    if not texto:
                        texto = enlace.get('aria-label', '')
                    if not texto:
                        # Extraer del nombre del archivo
                        texto = url_completa.split('/')[-1].replace('.pdf', '').replace('-', ' ')

                    # Inferir tipo de producto
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
                logger.error(f"Error scrapeando {url_base}: {e}")
                continue

        # Eliminar duplicados por URL
        urls_unicas = []
        urls_set = set()
        for url in urls_encontradas:
            if url.url not in urls_set:
                urls_set.add(url.url)
                urls_unicas.append(url)

        logger.info(f"Total URLs encontradas en BBVA: {len(urls_unicas)}")
        return urls_unicas

    def _inferir_tipo_producto(self, url: str, texto: str) -> str:
        """Infiere el tipo de producto desde la URL o texto"""
        texto_lower = (texto + " " + url).lower()

        if any(k in texto_lower for k in ['tarjeta', 'credito', 'debito']):
            return 'tarjetas'
        elif any(k in texto_lower for k in ['prestamo', 'credito']):
            return 'prestamos'
        elif any(k in texto_lower for k in ['cuenta', 'ahorro', 'deposito']):
            return 'cuentas'
        elif any(k in texto_lower for k in ['empresa', 'pyme', 'corporativo']):
            return 'empresas'
        elif any(k in texto_lower for k in ['hipotecario', 'vivienda']):
            return 'hipotecarios'
        else:
            return 'otros'
