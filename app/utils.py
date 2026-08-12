# ============================================================
# UTILS — Proyecto "El Errante" (BI & Incentivos)
# Carga de datos con caché y helpers de formato (Fase 3)
# Autor: Buffy | Generado: 2026-08-11 | Versión: 0.1.0
# ============================================================

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Garantizar acceso a src/config.py (constantes centrales)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
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


# ------------------------------------------------------------
# Carga de datos (con caché de Streamlit)
# ------------------------------------------------------------
@st.cache_data(show_spinner="Cargando datos de El Errante...")
def cargar_ventas() -> pd.DataFrame:
    """fact_ventas con fechas parseadas."""
    df = pd.read_csv(CSV_FACT_VENTAS)
    for col in ("fecha_hora", "hora_apertura_mesa", "hora_cierre_mesa"):
        df[col] = pd.to_datetime(df[col])
    df["mes_ano"] = df["fecha_hora"].dt.strftime("%Y-%m")
    df["monto"] = df["precio_unitario_aplicado"] * df["cantidad"]
    return df


@st.cache_data(show_spinner=False)
def cargar_productos() -> pd.DataFrame:
    return pd.read_csv(CSV_DIM_PRODUCTOS)


@st.cache_data(show_spinner=False)
def cargar_sucursales() -> pd.DataFrame:
    return pd.read_csv(CSV_DIM_SUCURSALES)


@st.cache_data(show_spinner=False)
def cargar_meseros() -> pd.DataFrame:
    return pd.read_csv(CSV_DIM_MESEROS)


@st.cache_data(show_spinner=False)
def cargar_clientes_crm() -> pd.DataFrame:
    df = pd.read_csv(CSV_DIM_CLIENTES_CRM)
    if "fecha_salida" in df.columns:
        df["fecha_salida"] = pd.to_datetime(df["fecha_salida"], errors="coerce")
    df["fecha_alta"] = pd.to_datetime(df["fecha_alta"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def cargar_costos() -> pd.DataFrame:
    return pd.read_csv(CSV_FACT_COSTOS)


@st.cache_data(show_spinner=False)
def cargar_presupuesto() -> pd.DataFrame:
    return pd.read_csv(CSV_FACT_PRESUPUESTO)


@st.cache_data(show_spinner=False)
def cargar_encuestas() -> pd.DataFrame:
    return pd.read_csv(CSV_FACT_ENCUESTAS)


@st.cache_data(show_spinner=False)
def ventas_con_roi() -> pd.DataFrame:
    """Ventas enriquecidas con costo del mes y ROI por línea de detalle.

    ROI = (Precio_Venta - Costo_Elaboracion) / Costo_Elaboracion
    """
    v = cargar_ventas()
    c = cargar_costos()
    df = v.merge(c, on=["id_producto", "mes_ano"], how="left")
    df["roi"] = (df["precio_unitario_aplicado"] - df["costo_elaboracion"]) / df[
        "costo_elaboracion"
    ]
    df["costo_total"] = df["costo_elaboracion"] * df["cantidad"]
    return df


# ------------------------------------------------------------
# Helpers de formato y métricas
# ------------------------------------------------------------
def fmt_money(valor: float) -> str:
    return f"${valor:,.0f}"


def fmt_pct(valor: float) -> str:
    return f"{valor:.1%}"


def kpi_delta(actual: float, anterior: float) -> tuple[str, bool]:
    """Devuelve (texto_delta, es_positivo) comparando dos periodos."""
    if anterior == 0 or anterior is None:
        return "", True
    cambio = (actual - anterior) / abs(anterior)
    return f"{cambio:+.1%}", cambio >= 0


def periodo_anterior(
    df: pd.DataFrame, fecha_min: pd.Timestamp, fecha_max: pd.Timestamp
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Devuelve el rango de igual duración inmediatamente anterior.

    Nota: si el rango anterior cae antes del inicio de los datos (p. ej. al
    seleccionar todo el histórico), el comparativo queda vacío y el delta del
    KPI se muestra sin cambio (comportamiento esperado).
    """
    duracion = fecha_max - fecha_min
    return fecha_min - duracion, fecha_min - pd.Timedelta(days=1)
