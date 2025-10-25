"""
Utilidades para descargar PDFs
"""
import hashlib
from pathlib import Path
from typing import Optional
import requests
from loguru import logger
from ..models import TarifarioURL, TarifarioMetadata, DownloadResult
from ..config import settings


class PDFDownloader:
    """Clase para descargar PDFs de tarifarios"""

    def __init__(self, carpeta_base: Optional[Path] = None):
        self.carpeta_base = carpeta_base or settings.TARIFARIOS_DIR
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.USER_AGENT
        })

    def descargar(self, tarifario_url: TarifarioURL) -> DownloadResult:
        """
        Descarga un PDF y retorna resultado con metadata
        """
        try:
            # Crear carpeta del banco si no existe
            carpeta_banco = self.carpeta_base / tarifario_url.banco.value.replace(" ", "_")
            carpeta_banco.mkdir(parents=True, exist_ok=True)

            # Generar nombre de archivo
            nombre_archivo = self._generar_nombre_archivo(tarifario_url)
            ruta_completa = carpeta_banco / nombre_archivo

            # Descargar
            logger.info(f"Descargando: {tarifario_url.texto}")
            response = self.session.get(
                tarifario_url.url,
                timeout=settings.REQUEST_TIMEOUT,
                stream=True
            )
            response.raise_for_status()

            # Guardar archivo
            with open(ruta_completa, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Calcular hash MD5
            hash_md5 = self._calcular_md5(ruta_completa)

            # Crear metadata
            metadata = TarifarioMetadata(
                banco=tarifario_url.banco,
                nombre_archivo=nombre_archivo,
                url_origen=tarifario_url.url,
                tamaño_bytes=ruta_completa.stat().st_size,
                hash_md5=hash_md5,
                tipo_producto=tarifario_url.tipo_producto,
                valido=True
            )

            logger.success(f"✅ Descargado: {nombre_archivo} ({metadata.tamaño_bytes:,} bytes)")

            return DownloadResult(
                metadata=metadata,
                ruta_archivo=str(ruta_completa),
                exito=True
            )

        except Exception as e:
            logger.error(f"❌ Error descargando {tarifario_url.url}: {e}")
            return DownloadResult(
                metadata=TarifarioMetadata(
                    banco=tarifario_url.banco,
                    nombre_archivo="",
                    url_origen=tarifario_url.url,
                    tamaño_bytes=0,
                    valido=False,
                    error=str(e)
                ),
                ruta_archivo="",
                exito=False,
                error=str(e)
            )

    def _generar_nombre_archivo(self, tarifario_url: TarifarioURL) -> str:
        """Genera nombre de archivo limpio"""
        # Extraer nombre del URL
        nombre_base = tarifario_url.url.split('/')[-1]

        # Si no termina en .pdf, usar texto del enlace
        if not nombre_base.endswith('.pdf'):
            nombre_base = tarifario_url.texto.replace(' ', '_').replace('/', '_') + '.pdf'

        # Limpiar caracteres especiales
        nombre_limpio = "".join(c for c in nombre_base if c.isalnum() or c in '._-')

        return nombre_limpio

    def _calcular_md5(self, ruta: Path) -> str:
        """Calcula hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        with open(ruta, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def cerrar(self):
        """Cierra la sesión"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar()
