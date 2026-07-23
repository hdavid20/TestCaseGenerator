import json
import urllib.request
import urllib.parse
import urllib.error
import re

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


def build_prompt(user_story, hu_code="", additional_context=None):
    parts = [f"CRITERIOS:\n{user_story}"]
    if hu_code:
        parts.insert(0, f"Código de HU: {hu_code}")
    if additional_context:
        parts.append(f"\nContexto adicional:\n{additional_context}")
    return "\n".join(parts)


def generate_test_cases(api_key, user_story, model="gemini-2.0-flash", hu_code="", additional_context=None):
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

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Error HTTP {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Error de conexión: {e.reason}")

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


def parse_table(text):
    lines = text.strip().split("\n")

    header_idx = -1
    for i, line in enumerate(lines):
        if "RESUMEN" in line and "Descripcion" in line and "Acción" in line:
            header_idx = i
            break

    if header_idx == -1:
        raise RuntimeError(
            "Gemini no generó la tabla esperada.\n\n"
            f"Respuesta cruda:\n{text[:1500]}"
        )

    data_lines = []
    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("|---"):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            stripped = stripped[1:-1]
        parts = [p.strip() for p in stripped.split("|")]
        if len(parts) >= 7:
            data_lines.append(parts)

    if not data_lines:
        for line in lines[header_idx + 1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("|---"):
                continue
            parts = [p.strip() for p in stripped.split("|")]
            if len(parts) >= 7:
                data_lines.append(parts)

    result = []
    for row in data_lines:
        entry = {
            "id": row[0] if len(row) > 0 else "",
            "resumen": row[1] if len(row) > 1 else "",
            "descripcion": row[2] if len(row) > 2 else "",
            "criterio": row[3] if len(row) > 3 else "",
            "accion": row[4] if len(row) > 4 else "",
            "datos_prueba": row[5] if len(row) > 5 else "",
            "resultado_esperado": row[6] if len(row) > 6 else "",
            "tipo_test": row[7] if len(row) > 7 else "Manual",
            "directorio": row[8] if len(row) > 8 else "",
        }
        result.append(entry)

    if not result:
        raise RuntimeError(
            "No se pudieron extraer filas de la tabla.\n\n"
            f"Respuesta cruda:\n{text[:1500]}"
        )

    return result
