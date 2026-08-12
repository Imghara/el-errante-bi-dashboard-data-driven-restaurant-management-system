# ============================================================
# CONFTEST — Proyecto "El Errante" (BI & Incentivos)
# Configuración compartida de pytest: rutas y fixtures de datos.
# Fase 6 · Pruebas automatizadas (CP6)
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import sys
from pathlib import Path

import pandas as pd
import pytest

# Asegurar importaciones: raíz (models), src/ (config) y app/ (módulos)
ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT, ROOT / "src", ROOT / "app"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from config import (  # noqa: E402
    CSV_DIM_CLIENTES_CRM,
    CSV_DIM_MESEROS,
    CSV_DIM_PRODUCTOS,
    CSV_DIM_SUCURSALES,
    CSV_FACT_COSTOS,
    CSV_FACT_ENCUESTAS,
    CSV_FACT_PRESUPUESTO,
    CSV_FACT_VENTAS,
)


def _leer(ruta: Path, fechas: list[str] | None = None) -> pd.DataFrame:
    """Lee un CSV y salta la prueba si los datos no fueron generados."""
    if not ruta.exists():
        pytest.skip(f"No existe {ruta} — ejecuta primero: python src/data_factory.py")
    df = pd.read_csv(ruta)
    for col in fechas or []:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


# ------------------------------------------------------------
# Fixtures de datos (se cargan UNA vez por sesión de pytest)
# ------------------------------------------------------------
@pytest.fixture(scope="session")
def ventas() -> pd.DataFrame:
    return _leer(
        CSV_FACT_VENTAS,
        fechas=["fecha_hora", "hora_apertura_mesa", "hora_cierre_mesa"],
    )


@pytest.fixture(scope="session")
def sucursales() -> pd.DataFrame:
    return _leer(CSV_DIM_SUCURSALES)


@pytest.fixture(scope="session")
def meseros() -> pd.DataFrame:
    return _leer(CSV_DIM_MESEROS)


@pytest.fixture(scope="session")
def productos() -> pd.DataFrame:
    return _leer(CSV_DIM_PRODUCTOS)


@pytest.fixture(scope="session")
def clientes_crm() -> pd.DataFrame:
    return _leer(CSV_DIM_CLIENTES_CRM)


@pytest.fixture(scope="session")
def costos() -> pd.DataFrame:
    return _leer(CSV_FACT_COSTOS)


@pytest.fixture(scope="session")
def presupuesto() -> pd.DataFrame:
    return _leer(CSV_FACT_PRESUPUESTO)


@pytest.fixture(scope="session")
def encuestas() -> pd.DataFrame:
    return _leer(CSV_FACT_ENCUESTAS)


@pytest.fixture(scope="session")
def ventas_con_monto(ventas: pd.DataFrame) -> pd.DataFrame:
    """Ventas con monto calculado (precio × cantidad)."""
    v = ventas.copy()
    v["monto"] = v["precio_unitario_aplicado"] * v["cantidad"]
    return v
