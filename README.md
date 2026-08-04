# TestCaseGenerator

Aplicación de escritorio para QA que genera casos de prueba a partir de criterios de aceptación usando la API de **Gemini**. Exporta los resultados a CSV compatible con **Jira** y **Xray**.

## Requisitos

- Python 3.10+
- Una API key de [Google AI Studio](https://aistudio.google.com/apikey)

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python APP.py
```

1. Configurá tu API key en **Ajustes** (⚙) o definí la variable de entorno `GEMINI_API_KEY`.
2. Ingresá el código de la HU (ej: `HU-123`) y los criterios de aceptación. También podés cargarlos desde un `.docx` o `.pdf`.
3. Presioná **Generar Casos de Prueba** para un caso por criterio, o **Generar Todos los Escenarios** para obtener todos los escenarios posibles por criterio (funcionales, negativos, límites, seguridad, integración, rendimiento, compatibilidad, accesibilidad, etc.).
4. Editá o eliminá casos directamente en la lista, o exportá a CSV (Jira / Xray).

## Configuración

- La API key se guarda en `data/config.json`. **No comitear ese archivo**: está en `.gitignore`.
- Prioridad de la key: variable de entorno `GEMINI_API_KEY` > `data/config.json`.
- Al cerrar la app, los casos generados se autoguardan en `data/autosave_test_cases.json`.

## Build a ejecutable

```bash
build.bat
```

Genera `dist\TestCaseGenerator\TestCaseGenerator.exe` con PyInstaller. Si existe una carpeta `assets/` con `icon.ico`, se incluye como ícono.

## Estructura

```
APP.py                  Punto de entrada
config.py               Carga/guardado de configuración
views/main_window.py    Interfaz gráfica (CustomTkinter)
utils/ai_helper.py      Llamada a la API de Gemini y parseo de la tabla
utils/jira_export.py    Exportación CSV (Jira / Xray)
```
