# ============================================================
# CAPTURAS DEL DASHBOARD — Proyecto "El Errante" (README F7)
# ------------------------------------------------------------
# Toma capturas reales del dashboard con Playwright (Chromium)
# para el README de portafolio: módulo 01 (Consolidado),
# 06 (Pronóstico) y 10 (Auditoría).
# Requisitos: app corriendo en http://localhost:8501
#   pip install playwright && playwright install chromium
# Uso: python scripts/capturas_dashboard.py
# Autor: Buffy | Fase: F7 (2026-08-12)
# ============================================================

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
URL = "http://localhost:8501"

MODULOS = {
    "captura_consolidado.png": "01 · Consolidado Financiero & ROI",
    "captura_forecast.png": "06 · Pronóstico & Inventario",
    "captura_auditoria.png": "10 · Auditoría de Incentivos",
}

# Texto de encabezado propio de cada módulo: garantiza que la navegación
# realmente ocurrió antes de capturar (evita falsos positivos si un clic
# fallara silenciosamente y se quedara en el módulo 01).
ENCABEZADO = {
    "01 · Consolidado Financiero & ROI": "Consolidado Financiero y ROI",
    "06 · Pronóstico & Inventario": "Pronóstico de Ventas e Inventario",
    "10 · Auditoría de Incentivos": "Auditoría de Calidad del Programa",
}

VISTA = {"width": 1600, "height": 1150}


def medir_contenido(ruta: Path) -> float:
    """Fracción de píxeles claros (indica render real del tema oscuro)."""
    try:
        from PIL import Image
        import numpy as np
        a = np.array(Image.open(ruta))
        return float((a.max(axis=2) > 150).mean())
    except Exception:
        return 0.0


def main() -> int:
    ok = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VISTA)
        page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
        # Esperar el render real (KPIs del módulo 01)
        page.wait_for_selector('[data-testid="stMetric"]', timeout=180_000)
        page.wait_for_timeout(5000)  # deja que Plotly dibuje
        for nombre, modulo in MODULOS.items():
            ruta = ASSETS / nombre
            try:
                if modulo != "01 · Consolidado Financiero & ROI":
                    page.get_by_text(modulo, exact=True).first.click()
                    # Esperar el encabezado del módulo destino (rerun + render)
                    page.get_by_text(ENCABEZADO[modulo]).first.wait_for(
                        timeout=90_000
                    )
                    page.wait_for_timeout(4000)
                page.screenshot(path=str(ruta))
                c = medir_contenido(ruta)
                estado = "OK" if c > 0.01 else "¿VACÍA?"
                print(f"  {nombre}: contenido-claro={c:.3f} -> {estado}")
                ok += 1 if c > 0.01 else 0
            except Exception as e:  # noqa: BLE001
                print(f"  {nombre}: ERROR {e}")
        browser.close()
    print(f"Capturas válidas: {ok}/{len(MODULOS)}")
    return 0 if ok == len(MODULOS) else 1


if __name__ == "__main__":
    sys.exit(main())
