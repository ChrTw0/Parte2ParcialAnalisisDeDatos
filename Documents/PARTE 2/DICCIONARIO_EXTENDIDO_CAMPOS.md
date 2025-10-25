# DICCIONARIO EXTENDIDO DE CAMPOS
## Definiciones Detalladas y Casos Especiales

**Proyecto**: Sistema de Extracción y Normalización de Tarifarios Bancarios
**Fecha**: 2025-10-25
**Versión**: 1.0

---

## ÍNDICE

1. [Campo: MONEDA](#1-campo-moneda)
2. [Campo: TIPO](#2-campo-tipo)
3. [Campo: CONCEPTO](#3-campo-concepto)
4. [Campo: OBSERVACIONES](#4-campo-observaciones)
5. [Campo: PERIODICIDAD](#5-campo-periodicidad)
6. [Campo: OPORTUNIDAD_COBRO](#6-campo-oportunidad_cobro)
7. [Campos: VALORES MONETARIOS](#7-campos-valores-monetarios)
8. [Campo: FECHA_VIGENCIA](#8-campo-fecha_vigencia)
9. [Campo: PRODUCTO_CODIGO](#9-campo-producto_codigo)
10. [Casos Especiales y Excepciones](#10-casos-especiales-y-excepciones)

---

## 1. CAMPO: MONEDA

### Definición Técnica
Indica la moneda o monedas en las que se aplica el item tarifario.

### Valores Posibles

| Valor | Significado | Casos de Uso | Frecuencia |
|-------|-------------|--------------|------------|
| **MN** | Moneda Nacional (Soles - S/) | Item aplica SOLO en soles peruanos | ~40% |
| **ME** | Moneda Extranjera (Dólares - $ / Euros - €) | Item aplica SOLO en moneda extranjera | ~25% |
| **AMBAS** | Aplica a MN y ME | Item tiene valores tanto en soles como en dólares/euros | ~30% |
| **EUR** | Específicamente Euros | Item aplica solo en euros (productos descontinuados) | <1% |
| **(vacío)** | No especificado | Items informativos sin valor monetario | ~4% |

---

### Casos Especiales

#### Caso 1: MONEDA = "AMBAS" con valores diferentes

**Ejemplo**:
```
Moneda: AMBAS
Concepto: Tasa de Interés Compensatoria - Tarjeta Clásica
Tasa_Porcentaje_MN: 27.0%
Tasa_Porcentaje_ME: 32.0%
```

**Significado**: El cliente puede usar la tarjeta en soles O dólares, pero la tasa es diferente:
- Si usa en soles → 27%
- Si usa en dólares → 32%

**NO significa**: "27% + 32%" ni "promedio de 29.5%"

---

#### Caso 2: MONEDA = "ME" pero tiene valores en MN

**Ejemplo**:
```
Moneda: ME
Concepto: Comisión por Retiro en Cajero
Monto_Fijo_MN: NULL
Monto_Fijo_ME: 3.00 (dólares)
```

**Significado**: La comisión es de $3.00 USD, aunque la cuenta esté en soles, se cobra el equivalente.

---

#### Caso 3: MONEDA = "EUR" (Euros)

**Contexto**: Solo aparece en BBVA Continental en el producto "Contiahorro Euros"

**Ejemplo**:
```
Banco: BBVA_Continental
Producto: Contiahorro-Euros
Moneda: EUR
Tasa_Porcentaje_ME: 0.50%
```

**Estado**: ❌ Producto descontinuado desde 01/04/2019

**Tratamiento en análisis**:
- Incluir en categoría "ME" para estadísticas generales
- Documentar como caso especial en observaciones

---

#### Caso 4: MONEDA = (vacío/NULL)

**Ejemplo**:
```
Moneda: NULL
Concepto: "Advertencia: Las tasas están sujetas a cambios"
Tipo: OTRO
```

**Significado**: Item informativo sin valor monetario asociado

**Frecuencia**: ~257 registros (19.4%) - Ver `registros_sin_valores.csv`

---

### Reglas de Interpretación

1. **Si Moneda = "MN"**: Solo usar campos `*_MN`, ignorar campos `*_ME`
2. **Si Moneda = "ME"**: Solo usar campos `*_ME`, ignorar campos `*_MN`
3. **Si Moneda = "AMBAS"**: Verificar AMBOS conjuntos de campos, pueden tener valores diferentes
4. **Si Moneda = NULL**: Item probablemente informativo, verificar campo `Tipo`

---

### Conversiones y Equivalencias

**NO hacer conversiones automáticas** salvo que el campo `conversion_pen` esté presente en el JSON.

**Ejemplo INCORRECTO**:
```python
# ❌ NO hacer esto
if moneda == "ME":
    monto_soles = monto_me * tipo_cambio_del_dia
```

**Razón**: El tarifario registra el valor oficial, no valores convertidos.

---

## 2. CAMPO: TIPO

### Definición Técnica
Clasificación principal del item tarifario según su naturaleza financiera.

### Valores Posibles

| Valor | Definición | Palabras Clave | Ejemplos Reales | Frecuencia |
|-------|------------|----------------|-----------------|------------|
| **TASA** | Porcentaje que se aplica sobre un monto base (capital, saldo, deuda) | "tasa", "interés", "TEA", "TEM", "rendimiento", "%" | "Tasa de Interés Compensatoria: 27%", "Rendimiento CTS: 3.5%" | 20.7% |
| **COMISION** | Cargo fijo por un servicio o transacción bancaria | "comisión", "comision", "cargo", "membresía" | "Comisión por Mantenimiento Mensual: S/ 5.00", "Cargo por Retiro: S/ 3.00" | 58.0% |
| **GASTO** | Costos de terceros que el banco traslada al cliente | "porte", "envío", "gasto", "notarial", "registral" | "Porte de Estado de Cuenta: S/ 3.50", "Servicios Notariales: Según Tarifario" | 10.9% |
| **SEGURO** | Primas o coberturas de seguros asociados al producto | "seguro", "prima", "cobertura", "desgravamen", "protección" | "Seguro de Desgravamen: 0.05% mensual", "Prima Anual: $50" | 4.7% |
| **OTRO** | Items que no encajan en las categorías anteriores | "advertencia", "nota", "información", "requisito" | "Nota: Tasas sujetas a evaluación", "Información sobre Defensoría" | 5.7% |
| **IMPUESTO** | Impuestos gubernamentales (muy raro) | "ITF", "impuesto", "tributo" | "Impuesto a las Transacciones Financieras - ITF" | <0.1% |
| **TRIBUTO** | Tributos fiscales (muy raro) | "tributo", "contribución" | "Contribución al Fondo de Seguro de Depósitos" | <0.1% |

---

### Reglas de Clasificación (Algoritmo de IA)

#### Regla 1: Si tiene `tasa_porcentaje` y palabras clave → TASA

```python
if (tasa_porcentaje_mn or tasa_porcentaje_me) and any(keyword in concepto.lower() for keyword in ['tasa', 'interés', 'tea', 'tem', 'rendimiento']):
    tipo = "TASA"
```

#### Regla 2: Si tiene `monto_fijo` y palabras clave → COMISION

```python
if (monto_fijo_mn or monto_fijo_me) and any(keyword in concepto.lower() for keyword in ['comisión', 'comision', 'cargo', 'membresía']):
    tipo = "COMISION"
```

#### Regla 3: Gastos de terceros → GASTO

```python
if any(keyword in concepto.lower() for keyword in ['notarial', 'registral', 'porte', 'envío', 'certificado']):
    tipo = "GASTO"
```

#### Regla 4: Seguros → SEGURO

```python
if any(keyword in concepto.lower() for keyword in ['seguro', 'desgravamen', 'prima', 'cobertura']):
    tipo = "SEGURO"
```

#### Regla 5: Por defecto → OTRO

```python
if not (tasa_porcentaje or monto_fijo) and tipo is None:
    tipo = "OTRO"
```

---

### Casos Especiales

#### Caso 1: TASA con monto_fijo (híbrido)

**Ejemplo**:
```
Tipo: TASA
Concepto: Interés Moratorio
Tasa_Porcentaje_MN: 15.0%
Monto_Minimo_MN: 5.00
```

**Significado**: Se cobra el **mayor** entre:
- 15% de la deuda vencida
- S/ 5.00 (mínimo)

**Regla de clasificación**: Si tiene TASA → clasificar como "TASA" aunque tenga montos

---

#### Caso 2: TIPO = NULL (8 registros - error)

**Ejemplo**:
```
Tipo: NULL
Concepto: NULL
Banco: BBVA_Continental
Producto: generales-ppjj
```

**Causa**: Error de extracción OCR
**Tratamiento**: Marcar para revisión manual

---

#### Caso 3: COMISION con valor 0 o "Exonerado"

**Ejemplo**:
```
Tipo: COMISION
Concepto: Consultas por Banca Internet
Monto_Fijo_MN: NULL
Observaciones: "Sin costo"
```

**Significado**: La comisión existe como concepto pero está **exonerada**

**Frecuencia**: ~92 registros de tipo COMISION sin valores

---

## 3. CAMPO: CONCEPTO

### Definición Técnica
Nombre o descripción del item tarifario tal como aparece en el documento original del banco.

**Tipo de dato**: String (VARCHAR 500)
**Nulo permitido**: Sí (8 casos de error OCR)

---

### Formatos Encontrados

#### Formato 1: Concepto Simple

```
Concepto: "Comisión por Mantenimiento Mensual"
```

**Características**:
- Una sola línea
- Descripción directa
- 70% de los casos

---

#### Formato 2: Concepto Jerárquico (con separadores)

```
Concepto: "Operaciones en Cuenta - Conversi­ón de moneda"
Concepto: "Uso de Cajero Automático (Otros Bancos)"
Concepto: "Transferencias > Interbancarias > Via CCE"
```

**Características**:
- Usa separadores: `-`, `>`, `|`, `(`
- Indica jerarquía del documento
- 20% de los casos

**Tratamiento en análisis**: Preservar tal cual, no separar

---

#### Formato 3: Concepto con Numeración

```
Concepto: "1.1. TASAS DE INTERÉS"
Concepto: "2.3.1 Comisión por Mantenimiento"
```

**Características**:
- Incluye numeración del documento original
- Útil para reconstruir jerarquía
- 5% de los casos

---

#### Formato 4: Concepto Descriptivo Largo

```
Concepto: "Retiro de dinero realizado en una localidad distinta donde se contrató la Cuenta"
```

**Características**:
- Descripción detallada (>50 caracteres)
- Más común en BBVA y BCP
- 10% de los casos

---

### Casos Problemáticos

#### Caso 1: Concepto = NULL (ERROR)

```
Concepto: NULL
Banco: BBVA_Continental
Producto: Comisiones-Adquirencia-el-2025
```

**Causa**: Fallo en OCR o tabla sin encabezado
**Frecuencia**: 8 registros (0.6%)
**Tratamiento**: Marcar como error, revisar PDF original

---

#### Caso 2: Concepto = "nan" (string literal)

```
Concepto: "nan"
```

**Causa**: Pandas convirtió NaN a string durante procesamiento
**Solución aplicada**: Se limpia a NULL en script de importación

---

#### Caso 3: Concepto duplicado con diferentes valores

```
Fila 1:
  Concepto: "Tasa de Interés Compensatoria"
  Tasa_MN: 27%
  Observaciones: "Compras"

Fila 2:
  Concepto: "Tasa de Interés Compensatoria"
  Tasa_MN: 32%
  Observaciones: "Disposición de efectivo"
```

**Significado**: NO es duplicado, son diferentes tipos de operación con el mismo nombre base

**Tratamiento**: Conservar ambos, diferenciar por `Observaciones`

---

### Reglas de Normalización Aplicadas

1. **Trim espacios**: Se eliminan espacios al inicio/fin
2. **Preservar mayúsculas/minúsculas**: Se respeta capitalización original
3. **NO traducir**: Se mantiene texto exacto del PDF
4. **Caracteres especiales**: Se preservan símbolos (%, $, °, ª)

---

## 4. CAMPO: OBSERVACIONES

### Definición Técnica
Campo de texto libre que concatena información adicional del item que no encaja en campos estructurados.

**Tipo de dato**: TEXT (ilimitado)
**Nulo permitido**: Sí
**Formato**: Campos separados por ` | ` (pipe con espacios)

---

### Estructura del Campo

```
Observaciones: "Tipo: TASA | Compras | Periodicidad: Anual | Cliente: Persona Natural | Vigente desde 15/05/2018"
```

**Componentes**:
1. **Tipo**: Redundante con campo `Tipo` (para verificación)
2. **Contexto operativo**: "Compras", "Disposición de efectivo", etc.
3. **Periodicidad**: Redundante con campo `Periodicidad`
4. **Cliente**: Tipo de cliente (Persona Natural/Jurídica)
5. **Segmento**: Pyme, Banca Personal, etc.
6. **Vigencia**: Fecha de vigencia (redundante con `Fecha_Vigencia`)
7. **Condiciones especiales**: Texto libre

---

### Patrones Comunes

#### Patrón 1: Observaciones de Vigencia

```
"Vigente desde 15/05/2018"
"Vigente hasta el 29/11/2022"
"Vigencia desde 25/11/2011"
```

**Extracción recomendada**:
```python
import re
match = re.search(r'Vigente desde (\d{2}/\d{2}/\d{4})', observaciones)
if match:
    fecha_vigencia = match.group(1)
```

---

#### Patrón 2: Observaciones de Condiciones

```
"Aplica a documentos menores a S/1,000"
"Se cobra a partir de la 1ra consulta"
"Sujeto a evaluación crediticia"
```

**Uso**: Condiciones que NO están en campos estructurados

---

#### Patrón 3: Observaciones de Cliente

```
"Cliente: Persona Natural"
"Cliente: Persona Jurídica"
"Cliente: Persona Natural con Negocio"
```

**Valores encontrados**:
- "Persona Natural" (PN)
- "Persona Jurídica" (PJ)
- "Persona Natural con Negocio"
- "Ambos"

---

#### Patrón 4: Observaciones de Segmento

```
"Segmento: Pyme"
"Segmento: No Pyme"
"Segmento: Microempresa"
"Segmento: Empresas"
```

---

#### Patrón 5: Observaciones Complejas (Múltiples Condiciones)

```
"Por ventanilla y Agente Express y Cajero Automático BBVA - Aplicable al beneficiario del depósito. - Vigente desde 30/11/2022 | Condiciones: Aplicable al beneficiario"
```

**Características**:
- Múltiples oraciones separadas por `-` o `.`
- Información redundante
- Requiere parsing manual para extraer datos específicos

---

### Casos Especiales

#### Caso 1: Observaciones = NULL

**Frecuencia**: ~15% de registros
**Significado**: No hay información adicional, campos estructurados son suficientes

---

#### Caso 2: Observaciones con Referencias Cruzadas

```
"Ver Tarifario N°110 para más detalles"
"Consultar Tarifa de Servicios Notariales vigente"
"Según Tarifario de Registros Públicos al momento del acto"
```

**Uso**: Indica que el valor NO está en este documento, referencia externa

---

#### Caso 3: Observaciones con Fórmulas

```
"Aplica sobre la deuda impaga, en función a los días transcurridos de la deuda"
"Se cobra dependiendo del saldo medio mensual en la cuenta"
```

**Uso**: Explica cómo se calcula el valor (útil para modelado)

---

### Extracción de Metadatos de Observaciones

```python
def extract_metadata_from_observaciones(obs: str) -> dict:
    """Extrae metadatos estructurados de observaciones"""
    if not obs:
        return {}

    metadata = {}

    # Extraer tipo de cliente
    if "Cliente: Persona Natural" in obs:
        metadata['tipo_cliente'] = "Persona Natural"
    elif "Cliente: Persona Jurídica" in obs:
        metadata['tipo_cliente'] = "Persona Jurídica"

    # Extraer segmento
    segmento_match = re.search(r'Segmento: ([^|]+)', obs)
    if segmento_match:
        metadata['segmento'] = segmento_match.group(1).strip()

    # Extraer condiciones especiales
    cond_match = re.search(r'Condiciones: ([^|]+)', obs)
    if cond_match:
        metadata['condiciones'] = cond_match.group(1).strip()

    return metadata
```

---

## 5. CAMPO: PERIODICIDAD

### Definición Técnica
Frecuencia con la que se aplica el cargo o se calcula la tasa.

**Tipo de dato**: String (VARCHAR 200)
**Nulo permitido**: Sí (~30% de registros)

---

### Valores Encontrados (Ordenados por Frecuencia)

| Valor | Frecuencia | Significado | Ejemplos |
|-------|------------|-------------|----------|
| **Por operación** | ~35% | Se cobra cada vez que se realiza la operación | Retiro en cajero, Transferencia |
| **Mensual** | ~25% | Se cobra/calcula cada mes | Mantenimiento de cuenta, Interés sobre saldo |
| **Anual** | ~20% | Se cobra/calcula una vez al año | Membresía anual, TEA |
| **NULL** | ~15% | No especificado o no aplica | Items informativos, gastos variables |
| **Única vez** | ~3% | Se cobra solo una vez (al inicio) | Afiliación, Emisión inicial |
| **Trimestral** | ~1% | Cada 3 meses | CTS, Algunos seguros |
| **Semestral** | <1% | Cada 6 meses | Raros, seguros específicos |
| **Diaria** | <1% | Todos los días | TEA calculada diariamente |

---

### Casos Especiales

#### Caso 1: Periodicidad Múltiple

```
Periodicidad: "Mensual / Anual"
Concepto: "Mantenimiento de Tarjeta"
Tasa_MN: 5.00 (mensual)
Observaciones: "Opción de pago mensual S/5 o anual S/50"
```

**Significado**: Cliente puede elegir entre pago mensual o anual

---

#### Caso 2: Periodicidad Condicional

```
Periodicidad: "Mensual"
Concepto: "Comisión por Saldo Menor al Mínimo"
Observaciones: "Solo se cobra si el saldo promedio es menor a S/500"
```

**Significado**: Mensual, pero condicionado a cumplir criterio

---

#### Caso 3: Periodicidad en Observaciones (no en campo)

```
Periodicidad: NULL
Observaciones: "Vigente desde 15/05/2018 | Periodicidad: Anual"
```

**Causa**: Error de extracción, quedó en observaciones
**Solución**: Extraer programáticamente con regex

---

### Conversión a Frecuencia Anualizada

Para comparar tasas con diferentes periodicidades:

```python
def anualizar_tasa(tasa: float, periodicidad: str) -> float:
    """Convierte tasa a equivalente anual"""
    conversiones = {
        'Diaria': 365,
        'Mensual': 12,
        'Trimestral': 4,
        'Semestral': 2,
        'Anual': 1
    }

    if periodicidad in conversiones:
        # Fórmula de interés compuesto
        return ((1 + tasa/100) ** conversiones[periodicidad] - 1) * 100

    return tasa  # Si es "Por operación", no se anualiza
```

---

## 6. CAMPO: OPORTUNIDAD_COBRO

### Definición Técnica
Momento exacto en el que se aplica el cargo o se capitaliza el interés.

**Tipo de dato**: String (VARCHAR 500)
**Nulo permitido**: Sí (~40% de registros)

---

### Valores Típicos

| Valor | Frecuencia | Significado | Contexto |
|-------|------------|-------------|----------|
| **Al momento de la operación** | ~25% | Se cobra en el instante que ocurre | Retiros ATM, Transferencias |
| **Mensual sobre saldo** | ~15% | Se cobra/capitaliza mensualmente sobre el saldo | Intereses de cuenta de ahorros |
| **Por adelantado** | ~10% | Se cobra al inicio del período | Descuento de letras |
| **Fin de mes** | ~8% | Se cobra el último día del mes | Mantenimiento mensual |
| **Al vencimiento** | ~5% | Se cobra cuando vence el plazo | Depósitos a plazo |
| **NULL** | ~37% | No especificado | Items informativos o no aplica |

---

### Casos Especiales

#### Caso 1: Oportunidad Diferida

```
Oportunidad_Cobro: "A los 30 días de realizada la operación"
Concepto: "Comisión por Devolución de Cheque"
```

**Significado**: No se cobra inmediatamente, hay un plazo de gracia

---

#### Caso 2: Oportunidad Condicional

```
Oportunidad_Cobro: "Solo si el saldo es menor al mínimo al cierre del mes"
Concepto: "Comisión por Bajo Saldo"
```

**Significado**: Evaluación al cierre del mes, cargo condicional

---

#### Caso 3: Capitalización de Intereses

```
Oportunidad_Cobro: "Capitalización diaria, pago mensual"
Concepto: "Interés de Cuenta de Ahorros"
```

**Significado**: Se **calcula** diario, pero se **paga/abona** mensualmente

---

## 7. CAMPOS: VALORES MONETARIOS

### 7.1 Campos de Tasa Porcentual

**Campos**: `Tasa_Porcentaje_MN`, `Tasa_Porcentaje_ME`
**Tipo de dato**: DECIMAL(10, 4)
**Rango válido**: 0.0000 - 200.0000
**Unidad**: Porcentaje (27.0000 = 27%)

---

#### Interpretación

```
Tasa_Porcentaje_MN: 27.0000
```

**Significa**: 27% anual (si Periodicidad = "Anual")
**NO significa**: 0.27 (decimal)

**Conversión a decimal**:
```python
tasa_decimal = tasa_porcentaje / 100
# 27.0 → 0.27
```

---

#### Casos Especiales

##### Caso 1: Tasa > 100%

```
Tasa_Porcentaje_MN: 112.99
Banco: Scotiabank
Concepto: "Línea de Crédito Efectiva - Disposición de Efectivo"
```

**Validación**: ✅ CORRECTO - Verificado en web oficial
**Contexto**: Tasas muy altas para créditos de alto riesgo

---

##### Caso 2: Tasa = 0

```
Tasa_Porcentaje_MN: 0.0000
Concepto: "Rendimiento de Cuenta Corriente"
```

**Significado**: No genera intereses (cuenta corriente estándar)

---

##### Caso 3: Tasa con 4 decimales

```
Tasa_Porcentaje_MN: 3.2500
Concepto: "Rendimiento CTS"
```

**Precisión**: Importante para cálculos exactos de intereses
**Ejemplo cálculo**:
```
Capital: S/ 10,000
Tasa: 3.2500% anual
Interés anual = 10,000 * 0.032500 = S/ 325.00
```

---

### 7.2 Campos de Montos Fijos

**Campos**: `Monto_Fijo_MN`, `Monto_Fijo_ME`
**Tipo de dato**: DECIMAL(15, 2)
**Rango típico**: 0.00 - 1,000.00 (comisiones), 0.00 - 10,000.00 (seguros)
**Unidad**: Soles (S/) o Dólares/Euros ($, €)

---

#### Interpretación

```
Monto_Fijo_MN: 5.00
```

**Significa**: S/ 5.00 soles exactos
**Precisión**: 2 decimales (centavos)

---

#### Casos Especiales

##### Caso 1: Monto con Conversión Incluida

```
Monto_Fijo_ME: 46.00
Observaciones: "$ 46 [S/ 181.70]"
```

**Significado**:
- Monto oficial: $46.00 USD
- Conversión referencial: S/ 181.70 (tipo de cambio ~3.95)
- **NO almacenar conversión en campo**, solo monto original

---

##### Caso 2: Monto Cero (Exonerado)

```
Monto_Fijo_MN: NULL
Concepto: "Consultas por Banca Internet"
Observaciones: "Sin costo"
```

**Significado**: Servicio exonerado
**Frecuencia**: ~92 registros de COMISION sin valores

---

### 7.3 Campos de Rangos (Mínimo/Máximo)

**Campos**:
- `Monto_Minimo_MN`, `Monto_Maximo_MN`
- `Monto_Minimo_ME`, `Monto_Maximo_ME`

**Tipo de dato**: DECIMAL(15, 2)
**Frecuencia**: Solo ~10% de registros tienen estos valores

---

#### Interpretación

```
Concepto: "Comisión por Administración de Cartera"
Monto_Minimo_MN: 7.00
Monto_Maximo_MN: 375.00
```

**Significado**: La comisión varía entre S/ 7.00 y S/ 375.00 según el monto del documento

**Regla de cálculo** (si está en observaciones):
```
Si documento < S/ 1,000 → S/ 7.00
Si documento > S/ 50,000 → S/ 375.00
Si S/ 1,000 ≤ documento ≤ S/ 50,000 → Escala progresiva
```

---

#### Casos Especiales

##### Caso 1: Solo Mínimo (sin Máximo)

```
Monto_Minimo_MN: 5.00
Monto_Maximo_MN: NULL
```

**Significado**: "Mínimo S/ 5.00, sin límite superior"

---

##### Caso 2: Solo Máximo (sin Mínimo)

```
Monto_Minimo_MN: NULL
Monto_Maximo_MN: 100.00
```

**Significado**: "Hasta S/ 100.00 máximo"

---

##### Caso 3: Mínimo = Máximo

```
Monto_Minimo_MN: 10.00
Monto_Maximo_MN: 10.00
```

**Significado**: Monto fijo de S/ 10.00 (redundante con `Monto_Fijo_MN`)
**Causa**: Forma de expresión del PDF original

---

### 7.4 Reglas de Prioridad de Valores

Cuando un registro tiene múltiples campos de valores:

**Prioridad 1**: `Tasa_Porcentaje`
```python
if tasa_porcentaje_mn is not None:
    usar tasa_porcentaje_mn
```

**Prioridad 2**: `Monto_Fijo`
```python
elif monto_fijo_mn is not None:
    usar monto_fijo_mn
```

**Prioridad 3**: `Monto_Minimo` / `Monto_Maximo`
```python
elif monto_minimo_mn or monto_maximo_mn:
    usar rango
```

---

## 8. CAMPO: FECHA_VIGENCIA

### Definición Técnica
Fecha a partir de la cual el item tarifario está vigente.

**Tipo de dato**: String (VARCHAR 20)
**Formato**: DD/MM/YYYY
**Nulo permitido**: Sí (~25% de registros)

---

### Formatos Encontrados

| Formato | Frecuencia | Ejemplo | Válido |
|---------|------------|---------|--------|
| **DD/MM/YYYY** | 70% | "15/05/2018" | ✅ Estándar |
| **D/M/YYYY** | 5% | "1/8/2012" | ✅ Válido |
| **DD/MM/YY** | 2% | "15/05/18" | ⚠️ Ambiguo |
| **NULL** | 23% | NULL | ✅ No especificado |

---

### Conversión Recomendada

```python
from datetime import datetime

def parse_fecha_vigencia(fecha_str: str) -> datetime:
    """Convierte fecha_vigencia a objeto datetime"""
    if not fecha_str:
        return None

    # Intentar formato DD/MM/YYYY
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        pass

    # Intentar formato D/M/YYYY
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        pass

    return None
```

---

### Casos Especiales

#### Caso 1: Fecha en Observaciones (duplicada)

```
Fecha_Vigencia: "15/05/2018"
Observaciones: "Vigente desde 15/05/2018 | Cliente: Persona Natural"
```

**Tratamiento**: Usar campo `Fecha_Vigencia`, ignorar texto en observaciones

---

#### Caso 2: Fecha de Fin de Vigencia

```
Fecha_Vigencia: "15/05/2018"
Observaciones: "Vigente hasta el 29/11/2022"
```

**Significado**:
- Inicio: 15/05/2018
- Fin: 29/11/2022 (producto descontinuado)

**Extracción del fin**:
```python
import re
match = re.search(r'hasta.*?(\d{2}/\d{2}/\d{4})', observaciones)
if match:
    fecha_fin = match.group(1)
```

---

#### Caso 3: Múltiples Fechas (Cambios de Tarifa)

```
Registro 1:
  Concepto: "Comisión por Mantenimiento"
  Fecha_Vigencia: "01/01/2015"
  Monto_Fijo_MN: 3.00

Registro 2:
  Concepto: "Comisión por Mantenimiento"
  Fecha_Vigencia: "01/06/2020"
  Monto_Fijo_MN: 5.00
```

**Significado**: Cambio de tarifa a lo largo del tiempo
**Análisis temporal**: Usar `Fecha_Vigencia` para reconstruir historial

---

## 9. CAMPO: PRODUCTO_CODIGO

### Definición Técnica
Identificador único del producto/documento tarifario, derivado del nombre del archivo PDF original.

**Tipo de dato**: String (VARCHAR 200)
**Nulo permitido**: No
**Formato**: Slug (minúsculas, guiones, sin espacios)

---

### Convenciones de Nomenclatura

#### Convención 1: Tipo de Producto + Detalles

```
"tarjetas-credito-visa-clasica"
"prestamos-personales-libre-disponibilidad"
"cuenta-ahorro-digital"
```

**Patrón**: `{tipo}-{subtipo}-{variante}`

---

#### Convención 2: Público Objetivo

```
"adelanto-ppjj"         → Personas Jurídicas
"cuenta-sueldo-ppnn"    → Personas Naturales
"tarjetas-empresariales-ppjj"
```

**Sufijos**:
- `ppnn`: Persona Natural
- `ppjj`: Persona Jurídica
- `pyme`: Pequeña y Mediana Empresa

---

#### Convención 3: Estado del Producto

```
"cuenta-negocio-ppnn_No-vigente"
"Tarifario-leasing-personas-naturales-y-micro-May21"
```

**Indicadores**:
- `_No-vigente`: Producto descontinuado
- `-May21`: Fecha de última actualización

---

### Casos Especiales

#### Caso 1: Productos Genéricos

```
"generales-ppjj"
"constancias-y-duplicados-ppjj"
"TRANSFERENCIAS_GIROS-Y-ORDENES_DE_PAGO_PJ"
```

**Significado**: Documentos generales que agrupan múltiples servicios

---

#### Caso 2: Productos con Caracteres Especiales

```
"BANCA_ELECTRONICA_PJ.1_SWIFT"
"Comisiones-Adquirencia-el-2025"
"cuenta-de-ahorro-12-cuenta-digital"
```

**Tratamiento**: Preservar guiones bajos `_`, puntos `.`, números

---

#### Caso 3: Productos Duplicados (Mismo Código, Diferente Banco)

```
Banco: BBVA_Continental
Producto_Codigo: "tarjetas-credito"

Banco: BCP
Producto_Codigo: "tarjetas-credito"
```

**Clave única**: Combinación de `Banco` + `Producto_Codigo`

---

### Generación de Clave Única

```python
def generar_clave_unica(banco: str, producto_codigo: str) -> str:
    """Genera clave única para producto"""
    return f"{banco}:{producto_codigo}"

# Ejemplo: "BBVA_Continental:tarjetas-credito"
```

---

## 10. CASOS ESPECIALES Y EXCEPCIONES

### 10.1 Registros sin Ningún Valor Monetario

**Total**: 257 registros (19.4%)
**Archivo**: `registros_sin_valores.csv`

**Distribución**:
- COMISION: 92 registros (servicios exonerados)
- TASA: 66 registros (encabezados o tasas negociables)
- OTRO: 54 registros (información legal)
- GASTO: 39 registros (gastos variables de terceros)

**Tratamiento**: Conservar para contexto, filtrar en análisis cuantitativo

---

### 10.2 Productos Descontinuados

#### Contiahorro Euros (BBVA)

```
Producto_Codigo: "Contiahorro-Euros"
Moneda: "EUR"
Estado: Descontinuado desde 01/04/2019
```

**Tratamiento**:
- Incluir en dataset para análisis histórico
- Marcar como descontinuado en análisis actual
- Clasificar EUR como ME para estadísticas

---

### 10.3 Tasas Extremas Verificadas

#### Tasa 112.99% (Scotiabank)

```
Banco: Scotiabank
Concepto: "Línea de Crédito Efectiva - Disposición de Efectivo"
Tasa_Porcentaje_MN: 112.99
Estado: ✅ VERIFICADO (24 archivos .md + web oficial)
```

**Contexto**: Tasa real para créditos de alto riesgo

---

#### Tasa 107% (BCP - American Express)

```
Banco: BCP
Concepto: "American Express - Disposición de Efectivo"
Tasa_Porcentaje_MN: 107.00
Estado: ✅ VERIFICADO (web oficial)
```

---

### 10.4 ITF (Impuesto a las Transacciones Financieras)

```
Concepto: "Impuesto a las transacciones financieras - ITF"
Tipo: IMPUESTO
Todos los campos de valores: NULL
```

**Tasa legal**: 0.005% (fijo por ley)
**Razón de NULL**: No está en las columnas porque se aplica automáticamente por normativa

---

### 10.5 Errores Conocidos (8 registros)

#### Concepto = NULL

```
Total: 8 registros
Causa: Error de extracción OCR
Acción: Documentado, marcar para revisión manual
```

**Ejemplos**:
- Fila 56: BBVA - Comisiones-Adquirencia-el-2025
- Fila 83: BBVA - cuenta-negocio-ppnn_No-vigente
- Fila 218: BBVA - generales-ppjj
- Fila 294: BBVA - constancias-y-duplicados-ppjj

---

## APÉNDICE A: QUERIES SQL ÚTILES

### A.1 Registros con Valores Completos

```sql
SELECT *
FROM tarifarios
WHERE (tasa_porcentaje_mn IS NOT NULL OR tasa_porcentaje_me IS NOT NULL)
   OR (monto_fijo_mn IS NOT NULL OR monto_fijo_me IS NOT NULL);
-- Resultado: ~1,066 registros (80.6%)
```

---

### A.2 Registros Solo con Tasas

```sql
SELECT *
FROM tarifarios
WHERE tipo = 'TASA'
  AND (tasa_porcentaje_mn IS NOT NULL OR tasa_porcentaje_me IS NOT NULL);
-- Resultado: ~269 registros
```

---

### A.3 Extraer Tipo de Cliente de Observaciones

```sql
SELECT
    banco,
    concepto,
    CASE
        WHEN observaciones LIKE '%Persona Natural%' THEN 'Persona Natural'
        WHEN observaciones LIKE '%Persona Jurídica%' THEN 'Persona Jurídica'
        ELSE 'No especificado'
    END AS tipo_cliente
FROM tarifarios;
```

---

### A.4 Productos Descontinuados

```sql
SELECT *
FROM tarifarios
WHERE producto_codigo LIKE '%No-vigente%'
   OR observaciones LIKE '%Vigente hasta%'
   OR producto_codigo LIKE '%Contiahorro-Euros%';
```

---

### A.5 Registros con Errores (Concepto NULL)

```sql
SELECT *
FROM tarifarios
WHERE concepto IS NULL;
-- Resultado: 8 registros
```

---

## APÉNDICE B: EXPRESIONES REGULARES ÚTILES

### B.1 Extraer Fecha de Vigencia de Observaciones

```python
import re

# Patrón: "Vigente desde DD/MM/YYYY"
pattern = r'Vigente desde (\d{1,2}/\d{1,2}/\d{4})'
match = re.search(pattern, observaciones)
if match:
    fecha = match.group(1)
```

---

### B.2 Extraer Tipo de Cliente

```python
pattern = r'Cliente:\s*([^|]+)'
match = re.search(pattern, observaciones)
if match:
    tipo_cliente = match.group(1).strip()
```

---

### B.3 Extraer Segmento

```python
pattern = r'Segmento:\s*([^|]+)'
match = re.search(pattern, observaciones)
if match:
    segmento = match.group(1).strip()
```

---

### B.4 Detectar Montos con Conversión

```python
# Patrón: "$ 46 [S/ 181.70]"
pattern = r'\$\s*([\d,]+(?:\.\d{2})?)\s*\[S/\s*([\d,]+(?:\.\d{2})?)\]'
match = re.search(pattern, texto)
if match:
    monto_usd = float(match.group(1).replace(',', ''))
    conversion_pen = float(match.group(2).replace(',', ''))
```

---

## GLOSARIO TÉCNICO EXTENDIDO

| Término | Definición Completa |
|---------|---------------------|
| **Slug** | Identificador URL-friendly (minúsculas, guiones, sin espacios). Ej: "tarjetas-credito-visa" |
| **Parsing** | Proceso de analizar texto no estructurado y extraer datos estructurados |
| **NULL vs Vacío** | NULL = ausencia de valor; Vacío ("") = string sin contenido |
| **Capitalización** | Uso de mayúsculas/minúsculas (Title Case, UPPER CASE, lower case) |
| **Regex** | Expresión regular, patrón de búsqueda de texto |
| **Anualizar** | Convertir una tasa de cualquier periodicidad a su equivalente anual (TEA) |
| **Encabezado** | Fila que agrupa otros items pero no tiene valor propio (es_encabezado: true) |
| **Item híbrido** | Registro que tiene tanto tasa_porcentaje como monto_fijo |
| **Conversión referencial** | Equivalente en otra moneda, NO es el valor oficial |
| **Exonerado** | Servicio que existe pero no tiene costo (monto = NULL pero concepto existe) |

---

**Fecha de última actualización**: 2025-10-25
**Versión**: 1.0
**Documento relacionado**: DICCIONARIO_DE_DATOS.md
