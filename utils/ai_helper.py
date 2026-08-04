import json
import urllib.request
import urllib.parse
import urllib.error
import re
import time
import unicodedata

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

SYSTEM_PROMPT = """Quiero que actúes como un Analista QA profesional senior.
Tu tarea es procesar criterios de aceptación proporcionados por el usuario y generar 2 resultados obligatorios.
Por cada criterio ingresado, documenta EXACTAMENTE en este formato:

C.(SOLO EL # del criterio sin el parentesis)
Acción:
[Descripción clara de la acción en una sola oración, NO en lista numerada]
Datos de Prueba:
[Datos claros y concretos]
Resultados Esperados:
[Resultado esperado claro]

REGLAS:
* Mantener exactamente la numeración original (C1, C2, C3...)
* No cambiar los nombres de los campos:
  Acción
  Datos de Prueba
  Resultados Esperados
* La "Acción" debe ser una oración continua (NO usar pasos numerados)
* Redacción clara, precisa y sin redundancia
* Este resultado será la única fuente para construir la tabla

RESULTADO 2:
Construir una tabla reutilizando EXACTAMENTE la información del RESULTADO 1.

FORMATO DE LA TABLA:
ID | RESUMEN | Descripcion | Criterio de Aceptación | Acción | Datos de Prueba | Resultado Esperado | Tipo de Test | DIRECTORIO DE REPOSITORIO DE TEST

REGLAS ESTRICTAS:
1. ID: Numérico secuencial iniciando en 1
2. RESUMEN: Identificador del criterio (Ej: C1)
3. Descripcion: Usar EXACTAMENTE el texto original del criterio ingresado por el usuario
4. Criterio de Aceptación: Identificador del criterio (Ej: C1)
5. Acción: COPIAR EXACTAMENTE desde RESULTADO 1
6. Datos de Prueba: COPIAR EXACTAMENTE desde RESULTADO 1
7. Resultado Esperado: COPIAR EXACTAMENTE desde RESULTADO 1
8. Tipo de Test: Siempre: Manual
9. DIRECTORIO DE REPOSITORIO DE TEST: Usar el código de la HU proporcionado por el usuario

REGLAS GENERALES:
* RESULTADO 2 es una transformación estructurada del RESULTADO 1
* No reinterpretar, no optimizar, no resumir
* Mantener consistencia total entre ambos resultados"""


SYSTEM_PROMPT_EXHAUSTIVE = """Quiero que actúes como un Analista QA Senior con amplia experiencia en análisis funcional, diseño de casos de prueba, aseguramiento de calidad y pruebas de software.

Tu misión es analizar la Historia de Usuario y sus criterios de aceptación para identificar TODOS los escenarios de prueba posibles, garantizando la máxima cobertura funcional y no funcional.

NO debes limitarte a un único escenario por criterio.

Debes pensar como un QA Senior que busca prevenir defectos antes de que lleguen a producción.

ANÁLISIS OBLIGATORIO

Para cada criterio de aceptación identifica todos los escenarios aplicables, incluyendo, cuando corresponda:

Escenarios Funcionales
Flujo principal
Flujo alternativo
Flujo opcional
Flujo de recuperación
Flujo de cancelación
Escenarios Positivos
Uso correcto
Datos válidos
Operación exitosa
Escenarios Negativos
Datos inválidos
Campos vacíos
Valores nulos
Información inexistente
Información duplicada
Operaciones no permitidas
Acciones fuera del flujo esperado
Validaciones
Campos obligatorios
Longitud mínima
Longitud máxima
Tipo de dato
Formato correcto
Espacios en blanco
Mayúsculas y minúsculas
Caracteres especiales
Tildes
Emojis
Caracteres Unicode
Valores Límite
Valor mínimo
Valor máximo
Justo por debajo del mínimo
Justo por encima del máximo
Valor cero
Valor negativo
Valor extremadamente grande
Reglas de Negocio
Todas las reglas funcionales
Dependencias entre campos
Restricciones
Combinaciones válidas
Combinaciones inválidas
Estados permitidos
Estados no permitidos
Transiciones entre estados
Seguridad
Roles
Permisos
Usuario sin permisos
Usuario bloqueado
Sesión expirada
Accesos restringidos
Manipulación de parámetros
SQL Injection
XSS
HTML Injection
Integración
Comunicación entre módulos
Comunicación con APIs
Base de datos
Persistencia de información
Sincronización de datos
Auditoría
Logs
Excepciones
Error del servidor
Timeout
Sin conexión
Servicio no disponible
API con error
Base de datos caída
Archivo corrupto
Interfaz
Mensajes informativos
Mensajes de error
Confirmaciones
Colores
Iconos
Botones
Navegación
Responsive
Rendimiento
Grandes volúmenes de datos
Alto número de registros
Múltiples usuarios
Concurrencia
Tiempo de respuesta
Compatibilidad
Navegadores
Sistemas Operativos
Resoluciones
Dispositivos
Accesibilidad
Navegación por teclado
Lectores de pantalla
Contraste
Etiquetas
Orden de tabulación
REGLAS IMPORTANTES
No existe un límite de escenarios.
Un criterio puede generar 3, 10, 20 o más escenarios.
Genera todos los escenarios razonables.
No omitas escenarios importantes.
No combines escenarios diferentes.
Cada escenario debe ser independiente.
Siempre incluye escenarios positivos y negativos.
Incluye valores límite cuando apliquen.
Incluye reglas de negocio cuando apliquen.
Incluye excepciones cuando apliquen.
Incluye seguridad cuando aplique.
Incluye integración cuando aplique.
Incluye rendimiento cuando aplique.
Incluye compatibilidad cuando aplique.
Incluye accesibilidad cuando aplique.
RESULTADO 1

Por cada escenario identificado documenta EXACTAMENTE el siguiente formato:

C.(Número del criterio)

Escenario:
(Nombre corto del escenario)

Tipo:
(Positivo | Negativo | Validación | Límite | Seguridad | Integración | Excepción | Rendimiento | Concurrencia | Compatibilidad | Accesibilidad | Flujo Alternativo)

Acción:
(Una sola oración continua, sin pasos numerados.)

Datos de Prueba:
(Datos específicos para ejecutar el escenario.)

Resultados Esperados:
(Resultado esperado claro, verificable y medible.)

REGLAS DEL RESULTADO 1
Mantener la numeración original de los criterios (C1, C2, C3...)
Si un criterio genera varios escenarios, repetir el identificador del criterio en cada uno.
Cada escenario debe ser completamente independiente.
No resumir.
No omitir información.
Redacción clara y profesional.
RESULTADO 2

Construir una tabla reutilizando EXACTAMENTE la información del Resultado 1.

FORMATO DE LA TABLA

| ID | RESUMEN | Descripción | Criterio de Aceptación | Escenario | Tipo | Acción | Datos de Prueba | Resultado Esperado | Tipo de Test | DIRECTORIO DE REPOSITORIO DE TEST |

REGLAS
ID numérico consecutivo iniciando en 1.
RESUMEN: Identificador del criterio (Ejemplo: C1).
Descripción: Copiar EXACTAMENTE el texto original del criterio de aceptación proporcionado por el usuario.
Criterio de Aceptación: Identificador del criterio.
Escenario: Copiar EXACTAMENTE del Resultado 1.
Tipo: Copiar EXACTAMENTE del Resultado 1.
Acción: Copiar EXACTAMENTE del Resultado 1.
Datos de Prueba: Copiar EXACTAMENTE del Resultado 1.
Resultado Esperado: Copiar EXACTAMENTE del Resultado 1.
Tipo de Test: Manual.
DIRECTORIO DE REPOSITORIO DE TEST: Utilizar el código de la Historia de Usuario proporcionado por el usuario.

IMPORTANTE: En la tabla, el valor de la columna "Tipo" debe ser UN SOLO tipo (ejemplo: Positivo, Negativo, Validación). NO usar el carácter "|" dentro de ninguna celda, ya que rompe el formato de la tabla."""


def build_prompt(user_story, hu_code="", additional_context=None):
    parts = [f"CRITERIOS:\n{user_story}"]
    if hu_code:
        parts.insert(0, f"Código de HU: {hu_code}")
    if additional_context:
        parts.append(f"\nContexto adicional:\n{additional_context}")
    return "\n".join(parts)


MAX_RETRIES = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


def _post_with_retry(url, payload):
    data = json.dumps(payload).encode("utf-8")
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            last_error = RuntimeError(f"Error HTTP {e.code}: {error_body}")
            if e.code not in RETRY_STATUS_CODES or attempt == MAX_RETRIES - 1:
                raise last_error
        except urllib.error.URLError as e:
            last_error = RuntimeError(f"Error de conexión: {e.reason}")
            if attempt == MAX_RETRIES - 1:
                raise last_error

        time.sleep(2 ** attempt)

    raise last_error


def generate_test_cases(api_key, user_story, model="gemini-flash-latest", hu_code="", additional_context=None):
    if not api_key:
        raise ValueError("API Key de Gemini no configurada.")

    prompt = build_prompt(user_story, hu_code, additional_context)
    url = GEMINI_ENDPOINT.format(model=model, key=api_key)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "system_instruction": {"parts": {"text": SYSTEM_PROMPT}},
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192,
        }
    }

    result = _post_with_retry(url, payload)

    text = extract_text(result)
    return parse_table(text)


def generate_exhaustive_test_cases(api_key, user_story, model="gemini-flash-latest", hu_code="", additional_context=None):
    if not api_key:
        raise ValueError("API Key de Gemini no configurada.")

    prompt = build_prompt(user_story, hu_code, additional_context)
    url = GEMINI_ENDPOINT.format(model=model, key=api_key)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "system_instruction": {"parts": {"text": SYSTEM_PROMPT_EXHAUSTIVE}},
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 65536,
        }
    }

    result = _post_with_retry(url, payload)

    text = extract_text(result)
    return parse_table(text)


def extract_text(response):
    try:
        candidates = response.get("candidates", [])
        if not candidates:
            raise RuntimeError("La API no devolvió candidatos.")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Respuesta inesperada de Gemini: {e}")


def _normalize_header(text):
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


HEADER_MAP = {
    "id": "id",
    "resumen": "resumen",
    "descripcion": "descripcion",
    "criterio de aceptacion": "criterio",
    "escenario": "escenario",
    "tipo": "tipo",
    "accion": "accion",
    "datos de prueba": "datos_prueba",
    "resultado esperado": "resultado_esperado",
    "tipo de test": "tipo_test",
    "directorio de repositorio de test": "directorio",
    "directorio": "directorio",
}


def parse_table(text):
    lines = text.strip().split("\n")

    header_idx = -1
    columns = {}
    for i, line in enumerate(lines):
        norm = _normalize_header(line)
        if "resumen" in norm and "descripcion" in norm and "accion" in norm:
            header_idx = i
            break

    if header_idx == -1:
        raise RuntimeError(
            "Gemini no generó la tabla esperada.\n\n"
            f"Respuesta cruda:\n{text[:1500]}"
        )

    header_line = lines[header_idx].strip()
    if header_line.startswith("|") and header_line.endswith("|"):
        header_line = header_line[1:-1]
    header_cells = [_normalize_header(c) for c in header_line.split("|")]

    for idx, cell in enumerate(header_cells):
        if cell in HEADER_MAP:
            columns[HEADER_MAP[cell]] = idx

    required = ["resumen", "descripcion", "criterio", "accion", "datos_prueba", "resultado_esperado"]
    missing = [c for c in required if c not in columns]
    if missing:
        raise RuntimeError(
            "La tabla de Gemini no contiene todas las columnas esperadas.\n\n"
            f"Columnas detectadas: {list(columns.keys())}\n"
            f"Faltantes: {missing}\n\nRespuesta cruda:\n{text[:1500]}"
        )

    data_lines = []
    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("|---"):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            stripped = stripped[1:-1]
        parts = [p.strip() for p in stripped.split("|")]
        if len(parts) >= len(columns):
            data_lines.append(parts)

    def get(row, key):
        idx = columns.get(key)
        if idx is None or idx >= len(row):
            return ""
        return row[idx]

    result = []
    for row in data_lines:
        entry = {
            "id": get(row, "id"),
            "resumen": get(row, "resumen"),
            "descripcion": get(row, "descripcion"),
            "criterio": get(row, "criterio"),
            "accion": get(row, "accion"),
            "datos_prueba": get(row, "datos_prueba"),
            "resultado_esperado": get(row, "resultado_esperado"),
            "tipo_test": get(row, "tipo_test") or "Manual",
            "directorio": get(row, "directorio"),
        }
        if "escenario" in columns:
            entry["escenario"] = get(row, "escenario")
        if "tipo" in columns:
            entry["tipo"] = get(row, "tipo")
        result.append(entry)

    if not result:
        raise RuntimeError(
            "No se pudieron extraer filas de la tabla.\n\n"
            f"Respuesta cruda:\n{text[:1500]}"
        )

    return result
