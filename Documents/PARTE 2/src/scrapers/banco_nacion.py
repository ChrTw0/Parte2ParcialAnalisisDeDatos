"""
Scraper para Banco de la Nación
"""
from typing import List
from loguru import logger
from .base import BaseScraper
from ..models import TarifarioURL, BancoEnum


class BancoNacionScraper(BaseScraper):
    """Scraper para Banco de la Nación"""

    # PDFs conocidos
    URLS_DIRECTAS = [
        {
            "url": "https://www.bn.com.pe/tasas-comisiones/Tarifario-BN.pdf",
            "texto": "Tarifario General 2025",
            "tipo": "general"
        },
        {
            "url": "https://www.bn.com.pe/tasas-comisiones/tasas-tarjeta-credito.pdf",
            "texto": "Tarjetas de Crédito",
            "tipo": "tarjetas"
        },
        {
            "url": "https://www.bn.com.pe/tasas-comisiones/tasas-prestamos-consumo.pdf",
            "texto": "Préstamos Multired Consumo",
            "tipo": "prestamos"
        },
        {
            "url": "https://www.bn.com.pe/canales-atencion/documentos/comision-ventanillas-agentesBN.pdf",
            "texto": "Comisiones Ventanillas y Agentes",
            "tipo": "comisiones"
        }
    ]

    def __init__(self):
        super().__init__(BancoEnum.BANCO_NACION)

    def obtener_urls(self) -> List[TarifarioURL]:
        """
        Retorna las URLs conocidas del Banco de la Nación
        """
        urls_encontradas = []

        for item in self.URLS_DIRECTAS:
            tarifario_url = TarifarioURL(
                url=item["url"],
                texto=item["texto"],
                tipo_producto=item["tipo"],
                banco=self.banco
            )
            urls_encontradas.append(tarifario_url)
            logger.debug(f"Agregado: {item['texto']} -> {item['url']}")

        logger.info(f"Total URLs en Banco de la Nación: {len(urls_encontradas)}")
        return urls_encontradas
