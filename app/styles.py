# ============================================================
# STYLES — Proyecto "El Errante" (BI & Incentivos)
# Hoja de estilos del tema "Océano & Arena" (DOCUMENTO_MAESTRO §5)
# Autor: Buffy | Generado: 2026-08-11 | Versión: 0.1.0
# ============================================================

import streamlit as st

# Paleta oficial (debe coincidir con src/config.py)
COLOR_PRIMARY = "#0B2545"
COLOR_PRIMARY_LIGHT = "#13315C"
COLOR_SUCCESS = "#1BA39C"
COLOR_WARNING = "#F5A623"
COLOR_CRITICAL = "#E74C3C"
COLOR_TEXT = "#F8FAFC"
COLOR_TEXT_DARK = "#1E293B"
COLOR_TEXT_MUTED = "#94A3B8"

CSS = f"""
<style>
/* ---------- Fuentes ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, sans-serif;
}}

/* ---------- Encabezados ---------- */
h1, h2, h3, h4 {{
    font-family: 'Poppins', sans-serif;
    letter-spacing: -0.02em;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {COLOR_PRIMARY} 0%, {COLOR_PRIMARY_LIGHT} 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}}
section[data-testid="stSidebar"] * {{
    color: {COLOR_TEXT};
}}

/* ---------- Contenedor principal ---------- */
.stApp {{
    background: radial-gradient(1200px 600px at 80% -10%, #123a5e 0%, {COLOR_PRIMARY} 55%, {COLOR_PRIMARY} 100%);
}}
[data-testid="stHeader"] {{
    background: transparent;
}}

/* ---------- Tarjetas / métricas ---------- */
div[data-testid="stMetric"] {{
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
div[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.35);
}}
div[data-testid="stMetric"] label {{
    color: {COLOR_TEXT_MUTED} !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
div[data-testid="stMetricValue"] {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.55rem !important;
}}

/* ---------- Encabezado de página ---------- */
.errante-header {{
    background: linear-gradient(120deg, {COLOR_SUCCESS} 0%, #0E7C78 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 2.1rem;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}}
.errante-subtitle {{
    color: {COLOR_TEXT_MUTED};
    font-size: 0.95rem;
    margin-bottom: 1.2rem;
}}

/* ---------- Badge de alerta ---------- */
.errante-badge {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}
.errante-badge-ok    {{ background: rgba(27,163,156,0.18); color: {COLOR_SUCCESS}; border: 1px solid rgba(27,163,156,0.4); }}
.errante-badge-warn  {{ background: rgba(245,166,35,0.15);  color: {COLOR_WARNING}; border: 1px solid rgba(245,166,35,0.4); }}
.errante-badge-crit  {{ background: rgba(231,76,60,0.16);   color: {COLOR_CRITICAL}; border: 1px solid rgba(231,76,60,0.45); }}

/* ---------- Divisores y widgets ---------- */
hr {{
    border-color: rgba(255,255,255,0.08);
}}
[data-testid="stDateInput"] input, [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
    background: {COLOR_PRIMARY_LIGHT};
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.12);
}}
[data-testid="stDateInput"] input {{ color: {COLOR_TEXT}; }}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px 10px 0 0;
    font-weight: 600;
}}

/* ---------- Tablas ---------- */
[data-testid="stDataFrame"] {{
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    overflow: hidden;
}}

/* ---------- Pie de página ---------- */
.errante-footer {{
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.08);
    text-align: center;
    color: {COLOR_TEXT_MUTED};
    font-size: 0.78rem;
    letter-spacing: 0.04em;
}}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar {{ width: 9px; height: 9px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.15); border-radius: 9px; }}
</style>
"""


def aplicar_css() -> None:
    """Inyecta el CSS global del tema Océano & Arena."""
    st.markdown(CSS, unsafe_allow_html=True)


def header(titulo: str, subtitulo: str) -> None:
    """Encabezado de página con degradado turquesa."""
    st.markdown(
        f'<div class="errante-header">{titulo}</div>'
        f'<div class="errante-subtitle">{subtitulo}</div>',
        unsafe_allow_html=True,
    )


def badge(estado: str, texto: str) -> str:
    """Genera un badge semántico HTML: ok | warn | crit."""
    cls = {"ok": "ok", "warn": "warn", "crit": "crit"}.get(estado, "ok")
    return f'<span class="errante-badge errante-badge-{cls}">{texto}</span>'
