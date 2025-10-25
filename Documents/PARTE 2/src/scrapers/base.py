"""
Clase base para todos los scrapers
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from loguru import logger
from ..models import TarifarioURL, BancoEnum
from ..config import settings


class BaseScraper(ABC):
    """Clase base abstracta para scrapers de bancos"""

    def __init__(self, banco: BancoEnum):
        self.banco = banco
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.USER_AGENT
        })

    @abstractmethod
    def obtener_urls(self) -> List[TarifarioURL]:
        """
        Obtiene todas las URLs de PDFs de tarifarios del banco.
        Debe ser implementado por cada scraper específico.
        """
        pass

    def _hacer_request(self, url: str, timeout: Optional[int] = None) -> requests.Response:
        """Realiza un request HTTP con manejo de errores"""
        timeout = timeout or settings.REQUEST_TIMEOUT
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Error al hacer request a {url}: {e}")
            raise

    def _parsear_html(self, html: str) -> BeautifulSoup:
        """Parsea HTML con BeautifulSoup"""
        return BeautifulSoup(html, 'lxml')

    def _es_url_pdf(self, url: str) -> bool:
        """Verifica si una URL apunta a un PDF"""
        return url.lower().endswith('.pdf') or '.pdf' in url.lower()

    def cerrar(self):
        """Cierra la sesión"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar()
