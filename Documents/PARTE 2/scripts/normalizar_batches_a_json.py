#!/usr/bin/env python3
"""
Normalización de batches .txt a JSON estructurado usando Gemini + Pydantic
Convierte archivos combinados en JSONs con esquema validado
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Cargar variables de entorno
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / "config" / ".env")

# Directorios
BATCHES_DIR = PROJECT_ROOT / "data" / "batches_combinados"
OUTPUT_DIR = PROJECT_ROOT / "data" / "normalized_json"

# Configuración Gemini
MODEL_NAME = "gemini-2.5-flash-lite"
MAX_WORKERS = 3  # Procesamiento paralelo con 3 hilos (para evitar rate limit)
DELAY_BETWEEN_BATCHES = 2  # Segundos de pausa entre procesamiento de resultados


# ============================================================================
# ESQUEMA PYDANTIC PARA VALIDACIÓN
# ============================================================================

class MetadataItem(BaseModel):
    referencia: Optional[str] = Field(None, description="Referencia cruzada (ej: (1), (2))")
    nota_explicativa: Optional[str] = Field(None, description="Nota explicativa del ítem")
    requiere_evaluacion: Optional[bool] = Field(None, description="Si requiere evaluación crediticia")
    aplica_itf: Optional[bool] = Field(None, description="Si aplica ITF")
    observaciones_adicionales: List[str] = Field(default_factory=list)
    texto_fila_completo: Optional[str] = Field(None, description="Texto original para auditoría")


class ValoresMoneda(BaseModel):
    tasa_porcentaje: Optional[float] = None
    monto_fijo: Optional[float] = None
    monto_minimo: Optional[float] = None
    monto_maximo: Optional[float] = None
    unidad: Optional[str] = Field(None, description="%, S/, $, €")
    texto_original: Optional[str] = Field(None, description="Valor como aparece en tabla")


class ValoresMonedaExtranjera(ValoresMoneda):
    conversion_pen: Optional[float] = Field(None, description="Conversión a PEN si está disponible")


class Valores(BaseModel):
    moneda: str = Field(..., description="MN | ME | AMBAS")
    mn: Optional[ValoresMoneda] = None
    me: Optional[ValoresMonedaExtranjera] = None


class Aplicacion(BaseModel):
    vigencia: Optional[str] = Field(None, description="DD/MM/YYYY")
    periodicidad: Optional[str] = Field(None, description="Mensual | Anual | Trimestral | Por operación")
    oportunidad_cobro: Optional[str] = None
    forma_aplicacion: Optional[str] = None
    condiciones: Optional[str] = None


class Clasificacion(BaseModel):
    tipo: str = Field(..., description="TASA | COMISION | GASTO | SEGURO | OTRO")
    subtipo: Optional[str] = Field(None, description="ej: Desgravamen, Vehicular")
    categoria: Optional[str] = None


class Jerarquia(BaseModel):
    nivel: Optional[str] = Field(None, description="ej: 1.1.1.1")
    seccion: Optional[str] = Field(None, description="ej: COMISIONES")
    subseccion: Optional[str] = None
    es_encabezado: bool = False


class Concepto(BaseModel):
    nombre: str = Field(..., description="Nombre completo del ítem")
    descripcion_breve: Optional[str] = Field(None, description="10-15 palabras máx, generada por IA")
    descripcion_detallada: Optional[str] = Field(None, description="Observaciones completas")


class Item(BaseModel):
    id: str = Field(..., description="UUID o número secuencial")
    jerarquia: Optional[Jerarquia] = None
    clasificacion: Clasificacion
    concepto: Concepto
    valores: Optional[Valores] = None
    aplicacion: Optional[Aplicacion] = None
    metadata_item: Optional[MetadataItem] = None


class ReferenciaExterna(BaseModel):
    tipo: str = Field(..., description="tarifario_cruzado | normativa | otro")
    referencia: str
    banco: Optional[str] = None
    mencionado_en_item_id: Optional[str] = None


class TipoCambioReferencial(BaseModel):
    usd_pen: Optional[float] = None
    eur_pen: Optional[float] = None


class Metadata(BaseModel):
    banco: str
    producto_codigo: str = Field(..., description="Filename sin extensión")
    producto_nombre: Optional[str] = Field(None, description="Nombre legible")
    descripcion_breve: Optional[str] = Field(None, description="1-2 líneas del producto")
    fecha_extraccion: str = Field(..., description="YYYY-MM-DD")
    fecha_vigencia: Optional[str] = Field(None, description="DD/MM/YYYY")
    tipo_cambio_referencial: Optional[TipoCambioReferencial] = None
    tipo_cliente: Optional[str] = Field(None, description="Persona Natural | Persona Jurídica | Ambos")
    segmento: Optional[str] = Field(None, description="Pyme | No Pyme | General")
    tiene_contenido_corrupto: bool = False
    fuente_archivo: str = Field(..., description="Path relativo")
    referencias_externas: List[ReferenciaExterna] = Field(default_factory=list)


class NotaDocumento(BaseModel):
    referencia: str = Field(..., description="ej: (1)")
    texto: str = Field(..., description="Explicación completa")


class ControlCalidad(BaseModel):
    total_items_extraidos: int
    items_con_datos_completos: int = 0
    items_con_datos_parciales: int = 0
    items_solo_encabezados: int = 0
    referencias_sin_resolver: List[str] = Field(default_factory=list)
    advertencias: List[str] = Field(default_factory=list)
    tipo_documento: str = Field(..., description="NORMAL | INDICE | VACIO | CORRUPTO")


class Documento(BaseModel):
    archivo: str
    metadata: Metadata
    items: List[Item] = Field(default_factory=list)
    notas_documento: List[NotaDocumento] = Field(default_factory=list)
    control_calidad: ControlCalidad


class BatchOutput(BaseModel):
    batch_metadata: dict = Field(..., description="Info del batch procesado")
    documentos: List[Documento]
    resumen_batch: dict


# ============================================================================
# PROMPT DE NORMALIZACIÓN
# ============================================================================

PROMPT_NORMALIZACION = """You are a banking tariff data extraction and normalization specialist for Peruvian banks.

INPUT: A concatenated text file containing multiple banking tariff documents separated by delimiters:
- ---DOCUMENT_START--- marks the beginning of each document
- Metadata lines: FILE_NUMBER, BANCO, PRODUCTO, FILENAME, FILEPATH
- ---CONTENT_START--- marks the beginning of markdown content
- ---CONTENT_END--- marks the end of content

OUTPUT: A structured JSON following the exact schema below.

CRITICAL EXTRACTION RULES:

1. **Document Processing:**
   - Process ALL documents in order (count by ---DOCUMENT_START--- markers)
   - Maintain exact 1:1 correspondence between input docs and output array
   - If a document is empty or only has index → set total_items_extraidos = 0, tipo_documento = "INDICE"
   - If corrupted with repetitions → extract ONLY unique rows, set tiene_contenido_corrupto = true

2. **Item Classification:**
   - Identify section headers (TASAS, COMISIONES, GASTOS, SEGUROS)
   - Classify each row as: TASA, COMISION, GASTO, SEGURO, or OTRO
   - Extract hierarchical numbering (1.1.1.1, etc.) if present
   - Mark header rows with es_encabezado = true

3. **Value Extraction:**
   - Parse percentages: "32,00%" → 32.00 (float)
   - Parse currency amounts: "S/ 15.00" → 15.00
   - Parse ranges: "Mínimo: S/7.00 Máximo: S/375.00" → separate monto_minimo and monto_maximo
   - Parse conversions in brackets: "$ 46 [S/ 181.70]" → me.monto_fijo=46.0, me.conversion_pen=181.70
   - Store original text in texto_original for traceability

4. **Date Extraction:**
   - Extract dates from: "Vigente desde DD/MM/YYYY"
   - Format: "DD/MM/YYYY" (string, not date object)

5. **Description Generation (AI Task):**
   - Generate "descripcion_breve" (10-15 words) for each item's concepto
   - Focus on WHAT is charged and WHEN
   - Example: "Comisión por gestión de cartera menor a S/1,000" → "Cargo mensual por administración de documentos de bajo monto"

6. **Cross-Reference Capture:**
   - Detect references to other tariffs: "Ver Tarifario N°110", "Consultar Tarifa..."
   - Store in metadata.referencias_externas
   - Detect footnote markers: (1), (2), etc.
   - Match with notes section at document end

7. **Quality Control:**
   - Count total extracted items (excluding headers)
   - Classify as: items_con_datos_completos (has values), items_con_datos_parciales (missing some), items_solo_encabezados
   - Detect document type: NORMAL, INDICE, VACIO, CORRUPTO

8. **Anti-Hallucination Rules:**
   - NEVER invent data not present in source
   - If field is unclear → set to null
   - If no items found → return empty items array
   - If document is index/TOC → total_items_extraidos = 0

EXAMPLE INPUT:
```
---DOCUMENT_START---
FILE_NUMBER: 1/2
BANCO: BBVA_Continental
PRODUCTO: adelanto-ppjj
FILENAME: adelanto-ppjj.md
FILEPATH: BBVA_Continental/adelanto-ppjj.md
---CONTENT_START---
| TASAS | Porcentaje MN | Porcentaje ME | Observación y Vigencia |
| Descuento de Letras | 32,00% | 25,00% | Aplica por adelantado Vigente desde 24/03/2008 |
| Interés moratorio | 15% | 10,00% | |
| COMISIONES | Porcentaje | MN | ME | Observación y Vigencia |
| Por Administración de Cartera | - | S/7.00 | $2.50 | Aplica a documentos menores a S/1,000. Vigente desde 16/12/2013 |
---CONTENT_END---

---DOCUMENT_START---
FILE_NUMBER: 2/2
BANCO: BCP
PRODUCTO: Tarifario-indice
FILENAME: Tarifario-indice.md
FILEPATH: BCP/Tarifario-indice.md
---CONTENT_START---
| Sección | Código |
| Tarjeta de Crédito | A |
| Préstamos | B |
---CONTENT_END---
```

EXAMPLE OUTPUT (follow this exact structure):
{{
  "batch_metadata": {{
    "batch_id": "batch_001",
    "total_documentos": 2,
    "fecha_procesamiento": "2025-10-24T17:30:00"
  }},
  "documentos": [
    {{
      "archivo": "adelanto-ppjj.md",
      "metadata": {{
        "banco": "BBVA_Continental",
        "producto_codigo": "adelanto-ppjj",
        "producto_nombre": "Adelanto en Cuenta Corriente - Personas Jurídicas",
        "descripcion_breve": "Financiamiento por adelanto de documentos comerciales para empresas",
        "fecha_extraccion": "2025-10-24",
        "fecha_vigencia": "24/03/2008",
        "tipo_cambio_referencial": null,
        "tipo_cliente": "Persona Jurídica",
        "segmento": null,
        "tiene_contenido_corrupto": false,
        "fuente_archivo": "BBVA_Continental/adelanto-ppjj.md",
        "referencias_externas": []
      }},
      "items": [
        {{
          "id": "1",
          "jerarquia": {{
            "nivel": null,
            "seccion": "TASAS",
            "subseccion": null,
            "es_encabezado": false
          }},
          "clasificacion": {{
            "tipo": "TASA",
            "subtipo": null,
            "categoria": "Financiamiento"
          }},
          "concepto": {{
            "nombre": "Descuento de Letras",
            "descripcion_breve": "Tasa anual por descuento anticipado de letras comerciales",
            "descripcion_detallada": "Aplica por adelantado Vigente desde 24/03/2008"
          }},
          "valores": {{
            "moneda": "AMBAS",
            "mn": {{
              "tasa_porcentaje": 32.0,
              "monto_fijo": null,
              "monto_minimo": null,
              "monto_maximo": null,
              "unidad": "%",
              "texto_original": "32,00%"
            }},
            "me": {{
              "tasa_porcentaje": 25.0,
              "monto_fijo": null,
              "monto_minimo": null,
              "monto_maximo": null,
              "unidad": "%",
              "texto_original": "25,00%",
              "conversion_pen": null
            }}
          }},
          "aplicacion": {{
            "vigencia": "24/03/2008",
            "periodicidad": "Anual",
            "oportunidad_cobro": "Por adelantado",
            "forma_aplicacion": null,
            "condiciones": null
          }},
          "metadata_item": {{
            "referencia": null,
            "nota_explicativa": null,
            "requiere_evaluacion": null,
            "aplica_itf": null,
            "observaciones_adicionales": [],
            "texto_fila_completo": "| Descuento de Letras | 32,00% | 25,00% | Aplica por adelantado Vigente desde 24/03/2008 |"
          }}
        }},
        {{
          "id": "2",
          "jerarquia": {{
            "nivel": null,
            "seccion": "COMISIONES",
            "subseccion": null,
            "es_encabezado": false
          }},
          "clasificacion": {{
            "tipo": "COMISION",
            "subtipo": null,
            "categoria": "Administración"
          }},
          "concepto": {{
            "nombre": "Por Administración de Cartera",
            "descripcion_breve": "Cargo fijo por gestión de documentos comerciales de bajo monto",
            "descripcion_detallada": "Aplica a documentos menores a S/1,000. Vigente desde 16/12/2013"
          }},
          "valores": {{
            "moneda": "AMBAS",
            "mn": {{
              "tasa_porcentaje": null,
              "monto_fijo": 7.0,
              "monto_minimo": null,
              "monto_maximo": null,
              "unidad": "S/",
              "texto_original": "S/7.00"
            }},
            "me": {{
              "tasa_porcentaje": null,
              "monto_fijo": 2.5,
              "monto_minimo": null,
              "monto_maximo": null,
              "unidad": "$",
              "texto_original": "$2.50",
              "conversion_pen": null
            }}
          }},
          "aplicacion": {{
            "vigencia": "16/12/2013",
            "periodicidad": null,
            "oportunidad_cobro": null,
            "forma_aplicacion": null,
            "condiciones": "Documentos menores a S/1,000"
          }},
          "metadata_item": {{
            "referencia": null,
            "nota_explicativa": null,
            "requiere_evaluacion": null,
            "aplica_itf": null,
            "observaciones_adicionales": [],
            "texto_fila_completo": "| Por Administración de Cartera | - | S/7.00 | $2.50 | Aplica a documentos menores a S/1,000. Vigente desde 16/12/2013 |"
          }}
        }}
      ],
      "notas_documento": [],
      "control_calidad": {{
        "total_items_extraidos": 2,
        "items_con_datos_completos": 2,
        "items_con_datos_parciales": 0,
        "items_solo_encabezados": 0,
        "referencias_sin_resolver": [],
        "advertencias": [],
        "tipo_documento": "NORMAL"
      }}
    }},
    {{
      "archivo": "Tarifario-indice.md",
      "metadata": {{
        "banco": "BCP",
        "producto_codigo": "Tarifario-indice",
        "producto_nombre": "Índice de Tarifario",
        "descripcion_breve": "Tabla de contenidos del tarifario general",
        "fecha_extraccion": "2025-10-24",
        "fecha_vigencia": null,
        "tipo_cambio_referencial": null,
        "tipo_cliente": null,
        "segmento": null,
        "tiene_contenido_corrupto": false,
        "fuente_archivo": "BCP/Tarifario-indice.md",
        "referencias_externas": []
      }},
      "items": [],
      "notas_documento": [],
      "control_calidad": {{
        "total_items_extraidos": 0,
        "items_con_datos_completos": 0,
        "items_con_datos_parciales": 0,
        "items_solo_encabezados": 0,
        "referencias_sin_resolver": [],
        "advertencias": ["Documento solo contiene índice, sin datos extractables"],
        "tipo_documento": "INDICE"
      }}
    }}
  ],
  "resumen_batch": {{
    "documentos_con_datos": 1,
    "documentos_indice": 1,
    "documentos_vacios": 0,
    "documentos_corruptos_parciales": 0
  }}
}}

Now process the actual batch content below and return ONLY valid JSON following this exact structure.
Do NOT include markdown formatting, explanations, or any text outside the JSON.
"""


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def read_batch_file(batch_path: Path) -> str:
    """Lee el contenido del archivo batch"""
    return batch_path.read_text(encoding='utf-8')


def process_batch_with_gemini(batch_content: str, batch_path: Path, model, parser) -> dict:
    """
    Procesa un batch con Gemini y retorna JSON usando JsonOutputParser (sin validación Pydantic estricta)
    """
    logger.info(f"  🤖 Enviando a Gemini ({len(batch_content):,} chars)...")

    # Crear prompt completo con instrucciones del parser
    full_prompt = PROMPT_NORMALIZACION + "\n\n" + parser.get_format_instructions() + f"\n\nBATCH CONTENT:\n{batch_content}"

    try:
        # Invocar modelo con parser
        response = model.invoke(full_prompt)

        # Parsear con JsonOutputParser (sin validación Pydantic estricta)
        json_data = parser.parse(response.content)

        # Validación básica: verificar que tenga estructura mínima
        if not isinstance(json_data, dict):
            raise ValueError("La respuesta no es un diccionario válido")

        if "documentos" not in json_data:
            raise ValueError("El JSON no contiene el campo 'documentos'")

        total_docs = len(json_data.get('documentos', []))
        logger.success(f"  ✅ Batch procesado: {total_docs} documentos")

        return json_data

    except json.JSONDecodeError as e:
        logger.error(f"  ❌ Error parseando JSON: {e}")
        logger.debug(f"  Raw output (primeros 1000 chars): {response.content[:1000] if 'response' in locals() else 'No response'}")
        raise

    except Exception as e:
        logger.error(f"  ❌ Error procesando batch: {e}")
        if 'response' in locals():
            logger.debug(f"  Raw output (primeros 1000 chars): {response.content[:1000]}")
        raise


def save_json_output(json_data: dict, batch_path: Path, banco_name: str):
    """Guarda el JSON normalizado en la estructura de carpetas"""
    # Crear carpeta del banco
    banco_output_dir = OUTPUT_DIR / banco_name
    banco_output_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo JSON (mismo nombre que el batch)
    json_filename = batch_path.stem + ".json"
    json_path = banco_output_dir / json_filename

    # Guardar JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    logger.success(f"  💾 JSON guardado: {banco_name}/{json_filename}")

    return json_path


def process_single_batch(batch_info: tuple, model, parser) -> dict:
    """
    Función wrapper para procesar un batch en paralelo
    """
    banco_name, batch_path = batch_info

    try:
        # Leer batch
        batch_content = read_batch_file(batch_path)

        # Procesar con Gemini
        start_time = time.time()
        json_data = process_batch_with_gemini(batch_content, batch_path, model, parser)
        elapsed = time.time() - start_time

        # Guardar JSON
        json_path = save_json_output(json_data, batch_path, banco_name)

        # Estadísticas (con manejo seguro de campos opcionales)
        total_docs = len(json_data.get('documentos', []))
        total_items = sum(
            d.get('control_calidad', {}).get('total_items_extraidos', 0)
            for d in json_data.get('documentos', [])
        )

        return {
            "batch": f"{banco_name}/{batch_path.name}",
            "exito": True,
            "documentos": total_docs,
            "items": total_items,
            "tiempo": elapsed
        }

    except Exception as e:
        logger.error(f"  ❌ Error procesando {banco_name}/{batch_path.name}: {e}")
        return {
            "batch": f"{banco_name}/{batch_path.name}",
            "exito": False,
            "error": str(e)
        }


def main():
    logger.info("=" * 70)
    logger.info("🔄 NORMALIZACIÓN DE BATCHES A JSON CON GEMINI")
    logger.info("=" * 70)
    logger.info(f"📂 Directorio batches: {BATCHES_DIR}")
    logger.info(f"📁 Directorio output: {OUTPUT_DIR}")

    # Verificar API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY no configurada")
        logger.info(f"   Configura en: {PROJECT_ROOT / 'config' / '.env'}")
        return

    logger.success("✅ API Key encontrada")

    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Configurar modelo Gemini
    logger.info("\n🔧 Configurando Gemini 2.5 Flash lite...")
    model = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0,
        max_output_tokens=16384,
        google_api_key=api_key,
    )
    logger.success("✅ Modelo configurado")

    # Configurar JsonOutputParser
    logger.info("🔧 Configurando JsonOutputParser...")
    parser = JsonOutputParser(pydantic_object=BatchOutput)
    logger.success("✅ Parser configurado")

    # Buscar todos los batches
    logger.info("\n🔍 Buscando archivos batch...")
    batch_files = []

    for banco_dir in sorted(BATCHES_DIR.iterdir()):
        if not banco_dir.is_dir():
            continue

        banco_batches = list(banco_dir.glob("batch_*.txt"))
        if banco_batches:
            batch_files.extend([(banco_dir.name, b) for b in sorted(banco_batches)])

    logger.success(f"✅ Encontrados {len(batch_files)} batches")

    # Procesar batches en paralelo con 4 workers
    logger.info("\n" + "=" * 70)
    logger.info(f"🚀 PROCESANDO BATCHES EN PARALELO ({MAX_WORKERS} workers)")
    logger.info("=" * 70)

    resultados = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Enviar todos los batches al executor
        futures = {
            executor.submit(process_single_batch, batch_info, model, parser): batch_info
            for batch_info in batch_files
        }

        # Procesar conforme se completan
        for i, future in enumerate(as_completed(futures), 1):
            batch_info = futures[future]
            banco_name, batch_path = batch_info

            logger.info(f"\n[{i}/{len(batch_files)}] 🏦 {banco_name}/{batch_path.name}")

            try:
                resultado = future.result()
                resultados.append(resultado)

                if resultado["exito"]:
                    logger.info(f"  📊 Docs: {resultado['documentos']} | Items: {resultado['items']} | Tiempo: {resultado['tiempo']:.1f}s")
                else:
                    logger.error(f"  ❌ Error: {resultado.get('error', 'Desconocido')}")

            except Exception as e:
                logger.error(f"  ❌ Excepción procesando batch: {e}")
                resultados.append({
                    "batch": f"{banco_name}/{batch_path.name}",
                    "exito": False,
                    "error": str(e)
                })

            # Rate limit: pausar entre procesamiento de resultados
            # Con 3 workers y delay de 2s, evitamos exceder 250K tokens/min
            time.sleep(DELAY_BETWEEN_BATCHES)

    # Resumen final
    exitosos = [r for r in resultados if r.get("exito")]
    fallidos = [r for r in resultados if not r.get("exito")]

    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"Total batches procesados:  {len(resultados)}")
    logger.info(f"  - Exitosos:              {len(exitosos)} ✅")
    logger.info(f"  - Fallidos:              {len(fallidos)} ❌")

    if exitosos:
        total_docs = sum(r.get('documentos', 0) for r in exitosos)
        total_items = sum(r.get('items', 0) for r in exitosos)
        total_tiempo = sum(r.get('tiempo', 0) for r in exitosos)

        logger.info(f"\nDocumentos procesados:     {total_docs}")
        logger.info(f"Items extraídos:           {total_items}")
        logger.info(f"Tiempo total:              {total_tiempo/60:.1f} min")
        logger.info(f"Promedio por batch:        {total_tiempo/len(exitosos):.1f}s")

    if fallidos:
        logger.warning("\n⚠️  Batches fallidos:")
        for r in fallidos:
            logger.warning(f"  - {r['batch']}: {r.get('error', 'Desconocido')}")

    logger.success(f"\n✅ Normalización completada")
    logger.info(f"📁 JSONs guardados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
