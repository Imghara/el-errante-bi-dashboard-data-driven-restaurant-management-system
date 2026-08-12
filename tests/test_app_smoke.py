# ============================================================
# TEST_APP_SMOKE — Proyecto "El Errante" (BI & Incentivos)
# Prueba integral del dashboard con AppTest (CP6 · Fase 6)
#   • Los 10 módulos renderizan sin excepciones ni mensajes de error
#   • Guardas de estado vacío: M6 (forecast < 90 días) y M9 (elasticidad < 6 meses)
# Marcadas como `e2e`: pesadas (cada instancia carga la app con 708k líneas).
#   Corrida rápida local:  .venv/Scripts/python.exe -m pytest -m "not e2e"
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.1
# ============================================================

import datetime as dt
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from config import CSV_FACT_VENTAS

if not CSV_FACT_VENTAS.exists():
    pytest.skip(
        "Datos no generados — ejecuta primero: python src/data_factory.py",
        allow_module_level=True,
    )

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app" / "app.py")
TIMEOUT = 300  # segundos por ejecución (carga de datos pesada)

pytestmark = pytest.mark.e2e

MODULOS = [
    "01 · Consolidado Financiero & ROI",
    "02 · Programa de Incentivos",
    "03 · CRM & Marketing",
    "04 · Presupuesto vs Real",
    "05 · Centro de Alertas",
    "06 · Pronóstico & Inventario",
    "07 · Rotación de Mesas",
    "08 · Deserción de Clientes",
    "09 · Elasticidad de Precios",
    "10 · Auditoría de Incentivos",
]

# Encabezado esperado por módulo (primer markdown de header() en cada render)
ENCABEZADOS = {
    "01": "Consolidado Financiero y ROI",
    "02": "Programa de Incentivos",
    "03": "CRM & Marketing",
    "04": "Presupuesto de Ventas vs Real",
    "05": "Centro de Alertas · Sistema Experto",
    "06": "Pronóstico de Ventas e Inventario",
    "07": "Rotación de Mesas y Eficiencia del Servicio",
    "08": "Análisis de Deserción de Clientes",
    "09": "Matriz de Elasticidad de Precios",
    "10": "Auditoría de Calidad del Programa de Incentivos",
}


def _app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=TIMEOUT)


def _renderizo_encabezado(at: AppTest, prefijo: str) -> bool:
    esperado = ENCABEZADOS[prefijo]
    return any(esperado in str(m.value) for m in at.markdown)


def test_navegacion_10_modulos():
    """Todos los módulos renderizan su encabezado sin excepción ni st.error."""
    at = _app()
    at.run()
    assert not at.exception, f"M1: {at.exception}"
    assert _renderizo_encabezado(at, "01"), "M1: encabezado no encontrado"

    for modulo in MODULOS:
        at.radio[0].set_value(modulo)
        at.run()
        assert not at.exception, f"{modulo}: {at.exception}"
        assert not at.error, f"{modulo}: st.error = {[str(e.value) for e in at.error]}"
        prefijo = modulo[:2]
        assert _renderizo_encabezado(at, prefijo), f"{modulo}: encabezado no renderizado"


def test_estado_vacio_forecast():
    """M6 con menos de 90 días de histórico muestra la guarda informativa."""
    at = _app()
    at.run()
    at.radio[0].set_value("06 · Pronóstico & Inventario")
    at.date_input[0].set_value((dt.date(2024, 1, 1), dt.date(2024, 2, 1)))
    at.run()
    assert not at.exception, at.exception
    assert any("al menos 90 días" in str(i.value) for i in at.info)


def test_estado_vacio_elasticidad():
    """M9 con menos de 6 meses muestra la advertencia de rango insuficiente."""
    at = _app()
    at.run()
    at.radio[0].set_value("09 · Elasticidad de Precios")
    at.date_input[0].set_value((dt.date(2024, 1, 1), dt.date(2024, 3, 1)))
    at.run()
    assert not at.exception, at.exception
    assert any("Se necesitan al menos" in str(i.value) for i in at.warning)


def test_filtro_una_sucursal():
    """Con una sola sucursal seleccionada la app sigue renderizando M1."""
    at = _app()
    at.run()
    at.multiselect[0].set_value(["S2"])
    at.run()
    assert not at.exception, at.exception
    assert not at.error, at.error
    assert _renderizo_encabezado(at, "01")
