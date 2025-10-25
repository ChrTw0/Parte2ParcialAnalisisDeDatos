"""
Scrapers para cada banco
"""
from .base import BaseScraper
from .bbva import BBVAScraper
from .bcp import BCPScraper
from .interbank import InterbankScraper
from .scotiabank import ScotiabankScraper
from .banco_nacion import BancoNacionScraper

__all__ = [
    "BaseScraper",
    "BBVAScraper",
    "BCPScraper",
    "InterbankScraper",
    "ScotiabankScraper",
    "BancoNacionScraper",
]
