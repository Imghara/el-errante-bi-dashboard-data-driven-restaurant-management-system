# ============================================================
# APP — Proyecto "El Errante" (BI & Incentivos)
# Entrada principal del dashboard Streamlit (Fase 3 · CP3)
# ------------------------------------------------------------
# Ejecución local:
#   .venv/Scripts/python.exe -m streamlit run app/app.py
# Navegación: módulos M1..M10 (ver DOCUMENTO_MAESTRO §5.4 y §6)
# Autor: Buffy | Generado: 2026-08-11 | Versión: 0.1.0
# ============================================================

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Asegurar que la raíz del proyecto esté en sys.path (imports app.*)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="El Errante · BI",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from styles import aplicar_css  # noqa: E402
from utils import (  # noqa: E402
    cargar_clientes_crm,
    cargar_encuestas,
    cargar_meseros,
    cargar_presupuesto,
    cargar_productos,
    cargar_sucursales,
    ventas_con_roi,
)

aplicar_css()

# ------------------------------------------------------------
# Carga de datos (cacheada)
# ------------------------------------------------------------
ventas = ventas_con_roi()
sucursales = cargar_sucursales()
presupuesto = cargar_presupuesto()
meseros = cargar_meseros()
productos = cargar_productos()
clientes_crm = cargar_clientes_crm()
encuestas = cargar_encuestas()

# ------------------------------------------------------------
# Sidebar: navegación y filtros globales
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; margin-bottom: 0.4rem;">
            <div style="font-family:'Poppins'; font-size:1.5rem; font-weight:800;
                 background:linear-gradient(120deg,#1BA39C,#F5A623);
                 -webkit-background-clip:text; background-clip:text; color:transparent;">
                🌊 EL ERRANTE
            </div>
            <div style="font-size:0.75rem; color:#94A3B8; letter-spacing:0.14em;
                 text-transform:uppercase; margin-bottom: 1rem;">
                Business Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🧭 Módulos")
    modulo = st.radio(
        "Selecciona un módulo",
        [
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
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Filtros globales")

    fecha_min = ventas["fecha_hora"].min().date()
    fecha_max = ventas["fecha_hora"].max().date()
    rango = st.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )
    if isinstance(rango, tuple) and len(rango) == 2:
        f_min, f_max = rango
    else:
        f_min, f_max = fecha_min, fecha_max

    opciones_suc = sucursales["id_sucursal"].tolist()
    entidad_por_suc = dict(zip(sucursales["id_sucursal"], sucursales["entidad"]))
    suc_sel = st.multiselect(
        "Sucursales",
        options=opciones_suc,
        default=opciones_suc,
        format_func=lambda s: f"{s} · {entidad_por_suc[s]}",
    )
    if not suc_sel:
        st.warning("Selecciona al menos una sucursal.")
        st.stop()

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.7rem; color:#94A3B8;'>"
        "Portafolio BI · Simulación 2024-2025<br>"
        "Nuevo León · Coahuila · Tamaulipas</div>",
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# Filtro temporal aplicado a ventas
# ------------------------------------------------------------
ventas_filt = ventas[
    (ventas["fecha_hora"].dt.date >= f_min) & (ventas["fecha_hora"].dt.date <= f_max)
]

# ------------------------------------------------------------
# Guarda global: sin datos en el periodo seleccionado (estado vacío)
# ------------------------------------------------------------
if ventas_filt.empty:
    st.warning(
        "No hay ventas registradas en el rango de fechas seleccionado. "
        "Amplía el periodo para explorar el dashboard."
    )
    st.stop()

# ------------------------------------------------------------
# Render del módulo seleccionado
# ------------------------------------------------------------
from modulos.m1_consolidado import render as render_m1  # noqa: E402
from modulos.m2_incentivos import render as render_m2  # noqa: E402
from modulos.m3_crm import render as render_m3  # noqa: E402
from modulos.m4_presupuesto import render as render_m4  # noqa: E402
from modulos.m5_alertas import render as render_m5  # noqa: E402
from modulos.m6_forecast import render as render_m6  # noqa: E402
from modulos.m7_rotacion import render as render_m7  # noqa: E402
from modulos.m8_churn import render as render_m8  # noqa: E402
from modulos.m9_elasticidad import render as render_m9  # noqa: E402
from modulos.m10_auditoria import render as render_m10  # noqa: E402

if modulo.startswith("01"):
    render_m1(
        ventas_filt,
        sucursales,
        presupuesto,
        pd.Timestamp(f_min),
        pd.Timestamp(f_max),
        suc_sel,
    )
elif modulo.startswith("02"):
    render_m2(ventas_filt, meseros, productos, suc_sel)
elif modulo.startswith("03"):
    render_m3(ventas_filt, clientes_crm, suc_sel)
elif modulo.startswith("04"):
    render_m4(
        ventas_filt,
        presupuesto,
        sucursales,
        pd.Timestamp(f_min),
        pd.Timestamp(f_max),
        suc_sel,
    )
elif modulo.startswith("05"):
    render_m5(
        ventas_filt,
        presupuesto,
        sucursales,
        clientes_crm,
        encuestas,
        meseros,
        pd.Timestamp(f_min),
        pd.Timestamp(f_max),
        suc_sel,
    )
elif modulo.startswith("06"):
    render_m6(
        ventas_filt,
        sucursales,
        pd.Timestamp(f_min),
        pd.Timestamp(f_max),
        suc_sel,
    )
elif modulo.startswith("07"):
    render_m7(ventas_filt, meseros, sucursales, suc_sel)
elif modulo.startswith("08"):
    render_m8(
        ventas_filt,
        clientes_crm,
        sucursales,
        pd.Timestamp(f_min),
        pd.Timestamp(f_max),
        suc_sel,
    )
elif modulo.startswith("09"):
    render_m9(ventas_filt, productos, suc_sel)
elif modulo.startswith("10"):
    render_m10(ventas_filt, meseros, encuestas, suc_sel)

# ------------------------------------------------------------
# Pie de página (identidad del dashboard)
# ------------------------------------------------------------
st.markdown(
    """
    <div class="errante-footer">
        🌊 El Errante · BI &amp; Incentivos — Simulación 2024-2025 ·
        Nuevo León · Coahuila · Tamaulipas
    </div>
    """,
    unsafe_allow_html=True,
)
