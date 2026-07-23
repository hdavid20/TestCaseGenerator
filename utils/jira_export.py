import csv
import os
import re


def generate_jira_csv(test_cases, filepath):
    fieldnames = [
        "ID",
        "Resumen",
        "Descripcion",
        "Criterio de Aceptación",
        "Acción",
        "Datos de Prueba",
        "Resultado Esperado",
        "Tipo de Test",
        "Directorio",
    ]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tc in test_cases:
            writer.writerow({
                "ID": tc.get("id", ""),
                "Resumen": tc.get("resumen", ""),
                "Descripcion": tc.get("descripcion", ""),
                "Criterio de Aceptación": tc.get("criterio", ""),
                "Acción": tc.get("accion", ""),
                "Datos de Prueba": tc.get("datos_prueba", ""),
                "Resultado Esperado": tc.get("resultado_esperado", ""),
                "Tipo de Test": tc.get("tipo_test", "Manual"),
                "Directorio": tc.get("directorio", ""),
            })

    return filepath


def generate_xray_csv(test_cases, filepath):
    fieldnames = [
        "Issue Type",
        "Summary",
        "Description",
        "Test Steps",
        "Labels",
    ]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tc in test_cases:
            desc = (
                f"Descripcion: {tc.get('descripcion', '')}\n"
                f"Criterio: {tc.get('criterio', '')}\n"
                f"Acción: {tc.get('accion', '')}\n"
                f"Datos de Prueba: {tc.get('datos_prueba', '')}\n"
                f"Directorio: {tc.get('directorio', '')}"
            )
            steps = (
                f"<html:ol xmlns:html='http://www.w3.org/1999/xhtml'>"
                f"<html:li>{tc.get('accion', '')}</html:li>"
                f"</html:ol>"
            )
            writer.writerow({
                "Issue Type": "Test",
                "Summary": f"{tc.get('resumen', '')} - {tc.get('descripcion', '')[:80]}",
                "Description": desc,
                "Test Steps": steps,
                "Labels": "generado-ia",
            })

    return filepath


def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:100]
