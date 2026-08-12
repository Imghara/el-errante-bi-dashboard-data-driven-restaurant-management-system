# ============================================================
# M6 · PRONÓSTICO DE VENTAS E INVENTARIO — Proyecto "El Errante"
# Pestaña 6 del dashboard (DOCUMENTO_MAESTRO §6 · M6)
# ------------------------------------------------------------
# Regresión estacional ligera (GradientBoosting) sobre la serie
# SEMANAL por sucursal → pronóstico a N semanas con banda de
# confianza + conversión a insumos (kg de marisco y cajas de
# cerveza) + impacto de la compra anticipada.
# El pronóstico parte de la última semana del rango seleccionado.
# Se reporta el MAPE del backtest y el de una referencia ingenua
# (persistencia) para dar contexto al error.
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.2.0
# ============================================================

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_SUCCESS, COLOR_WARNING, header
from utils import fmt_money

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from models.forecast import (  # noqa: E402
    CERVEZAS_POR_CAJA,
    KG_MARISCO_POR_SOPA,
    PRECIO_MARISCO_KG,
    convertir_insumos,
    entrenar_y_pronosticar,
    serie_semanal,
)

PALETA_SUCURSAL = {"S1": COLOR_SUCCESS, "S2": COLOR_WARNING, "S3": "#5B8DEF"}
COLOR_DEFAULT = "#94A3B8"


def _hex_rgba(hex_color: str, alpha: float) -> str:
    """Convierte #RRGGBB a rgba() para rellenos translúcidos."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _template() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor="#13315C", font_color="#F8FAFC"),
        legend=dict(orientation="h", y=1.12, x=0),
    )


# ------------------------------------------------------------
# Ratios de conversión por sucursal (del histórico)
# ------------------------------------------------------------
def _ratios(df: pd.DataFrame) -> dict:
    """Mix de bebidas, unidades de Sopa Ancla y de cerveza por $."""
    beb = df[df["categoria"] == "Bebida"]
    alim = df[df["categoria"] == "Alimento"]
    cerveza = df[df["subcategoria"] == "Cerveza"]

    tot_suc = df.groupby("id_sucursal")["monto"].sum()
    beb_suc = beb.groupby("id_sucursal")["monto"].sum()
    mix_bebidas = (beb_suc / tot_suc).round(4).to_dict()

    alim_suc = alim.groupby("id_sucursal")["monto"].sum()
    sopa_suc = df[df["es_ancla"]].groupby("id_sucursal")["cantidad"].sum()
    sopa_por_dolar = (sopa_suc / alim_suc).round(6).to_dict()

    beb_dolar = beb.groupby("id_sucursal")["monto"].sum()
    cerveza_uds = cerveza.groupby("id_sucursal")["cantidad"].sum()
    cerveza_por_dolar = (cerveza_uds / beb_dolar).round(6).to_dict()

    return {
        "mix_bebidas": mix_bebidas,
        "sopa_por_dolar_alimento": sopa_por_dolar,
        "cerveza_por_dolar_bebida": cerveza_por_dolar,
    }


# ------------------------------------------------------------
# Gráfico histórico + pronóstico
# ------------------------------------------------------------
def _grafico(resultado: dict, suc_sel: list) -> go.Figure:
    hist = resultado["historico"]
    pron = resultado["pronostico"]
    fig = go.Figure()

    for suc in sorted(suc_sel):
        color = PALETA_SUCURSAL.get(suc, COLOR_DEFAULT)
        h = hist[hist["id_sucursal"] == suc].sort_values("inicio_sem")
        fig.add_trace(go.Scatter(
            x=h["inicio_sem"], y=h["ventas"], name=f"{suc} histórico",
            mode="lines+markers", opacity=0.6,
            line=dict(color=color, width=1.4),
            marker=dict(size=4),
            hovertemplate="%{x|%d %b %y}<br>Ventas: $%{y:,.0f}<extra></extra>",
        ))
        p = pron[pron["id_sucursal"] == suc].sort_values("inicio_sem")
        fig.add_trace(go.Scatter(
            x=p["inicio_sem"], y=p["pronostico"], name=f"{suc} pronóstico",
            mode="lines+markers", line=dict(color=color, width=2.8),
            marker=dict(size=7, symbol="diamond"),
            customdata=p[["inferior", "superior"]],
            hovertemplate="%{x|%d %b %y}<br>Pronóstico: $%{y:,.0f}"
                          "<br>Banda 80%: $%{customdata[0]:,.0f} – "
                          "$%{customdata[1]:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=pd.concat([p["inicio_sem"], p["inicio_sem"][::-1]]),
            y=pd.concat([p["superior"], p["inferior"][::-1]]),
            fill="toself", fillcolor=_hex_rgba(color, 0.12),
            line=dict(width=0), showlegend=False,
            hoverinfo="skip",
        ))

    fig.update_layout(
        **_template(), height=440,
        yaxis=dict(tickformat=",.0f", title="Ventas semanales ($)"),
        xaxis=dict(title=""),
        title=dict(text="Histórico semanal vs pronóstico con banda de confianza (80%)",
                   font=dict(size=14)),
    )
    return fig


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df, sucursales, fecha_min, fecha_max, sucursales_sel) -> None:
    header(
        "Pronóstico de Ventas e Inventario",
        "Regresión estacional ligera sobre el histórico semanal para planear "
        "la compra de marisco y cerveza de las próximas semanas.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    # Guarda: contar DÍAS únicos con dt.normalize() — fecha_hora tiene resolución
    # de minutos, por lo que nunique() contaría timestamps y la guarda de 90 días
    # nunca se dispararía (bug detectado en QA F6). Short-circuit con df.empty.
    if df.empty or df["fecha_hora"].dt.normalize().nunique() < 90:
        st.info(
            "Se necesitan al menos 90 días de histórico para entrenar el modelo. "
            "Amplía el rango de fechas."
        )
        return

    c1, c2 = st.columns([1, 2])
    semanas = c1.slider(
        "Horizonte de pronóstico", 2, 8, 4, 1,
        help="Semanas hacia adelante que se proyectan.",
    )
    c1.caption(
        f"El modelo entrena con el histórico hasta la semana del "
        f"**{pd.Timestamp(fecha_max).strftime('%d %b %Y')}** (fecha máxima del filtro)."
    )

    @st.cache_data(show_spinner="Entrenando modelo de pronóstico...")
    def _run(df_, semanas_):
        serie = serie_semanal(df_)
        res = entrenar_y_pronosticar(serie, semanas=semanas_)
        ratios = _ratios(df_)
        insumos = convertir_insumos(res["pronostico"], ratios)
        return res, ratios, insumos

    resultado, ratios, insumos = _run(df, semanas)

    # ---- KPIs ----
    pron = resultado["pronostico"]
    total_pron = pron["pronostico"].sum()
    total_kg = insumos["kg_marisco"].sum()
    total_cajas = insumos["cajas_cerveza"].sum()
    mape = resultado["mape_backtest"]
    mape_ref = resultado["mape_referencia"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Ventas proyectadas", fmt_money(total_pron),
        f"{semanas} semanas",
        help="Facturación esperada del periodo pronosticado.",
    )
    k2.metric(
        "Marisco a comprar", f"{total_kg:,.0f} kg",
        f"{KG_MARISCO_POR_SOPA} kg/porción",
        help="Kilogramos de marisco según la conversión de la Sopa Ancla.",
    )
    k3.metric(
        "Cerveza a comprar", f"{total_cajas:,.0f} cajas",
        f"{CERVEZAS_POR_CAJA} uds/caja",
        help="Cajas de cerveza necesarias para cubrir el pronóstico.",
    )
    if mape == mape:
        ref_txt = f"ref. {mape_ref:.1%}" if mape_ref == mape_ref else ""
        k4.metric(
            "Error backtest (MAPE)", f"{mape:.1%}",
            ref_txt,
            delta_color="off",
            help="Error medio absoluto porcentual al re-proyectar la ventana ya "
                 f"conocida. La referencia ingenua (persistencia) marca {mape_ref:.1%}.",
        )
    else:
        k4.metric("Error backtest (MAPE)", "—", delta_color="off")

    # ---- Gráfico principal ----
    st.plotly_chart(_grafico(resultado, sucursales_sel), width="stretch")

    # ---- Tabla de conversión a insumos por semana ----
    st.markdown("#### 🛒 Compra recomendada por semana")
    tabla = insumos.copy()
    semanal = (
        tabla.groupby("Semana")
        .agg(
            ventas=("pronostico", "sum"),
            porciones_sopa=("porciones_sopa", "sum"),
            kg_marisco=("kg_marisco", "sum"),
            unidades_cerveza=("unidades_cerveza", "sum"),
            cajas_cerveza=("cajas_cerveza", "sum"),
        )
        .reset_index()
    )
    semanal["Ventas"] = semanal["ventas"].map(lambda x: f"${x:,.0f}")
    semanal["Sopa (uds)"] = semanal["porciones_sopa"].map(lambda x: f"{x:,.0f}")
    semanal["Marisco (kg)"] = semanal["kg_marisco"].map(lambda x: f"{x:,.0f}")
    semanal["Cerveza (uds)"] = semanal["unidades_cerveza"].map(lambda x: f"{x:,.0f}")
    semanal["Cajas"] = semanal["cajas_cerveza"].map(lambda x: f"{x:,.1f}")
    st.dataframe(
        semanal[["Semana", "Ventas", "Sopa (uds)", "Marisco (kg)",
                 "Cerveza (uds)", "Cajas"]],
        width="stretch", hide_index=True,
    )

    # ---- Impacto: compra anticipada ----
    st.markdown("#### ⚓ Impacto de la compra anticipada (protección del ROI)")
    c_imp, c_exp = st.columns([1, 1.4])
    costo_total = total_kg * PRECIO_MARISCO_KG
    ahorro = costo_total * 0.15  # shock máximo de +15% del mayorista (vedas)
    c_imp.metric(
        "Costo de compra hoy", fmt_money(costo_total),
        f"a {PRECIO_MARISCO_KG:,.0f} $/kg",
        help="Inversión si se compra al precio mayorista actual.",
    )
    c_imp.metric(
        "Ahorro si sube +15%", fmt_money(ahorro),
        "marisco vs Cuaresma",
        help="Diferencial evitado comprando anticipado antes de la subida "
             "estacional del marisco mayorista.",
    )
    c_exp.caption(
        "La compra anticipada en Tamaulipas (cerca del proveedor de costa) "
        "congela el precio del marisco antes de la temporada alta. El costo "
        "del insumo fluctúa **±15%** mes a mes por vedas y clima marítimo "
        "(regla de negocio §2.3), por lo que asegurar el inventario "
        "**protege el ROI de los platillos de raíz** y evita disparar la "
        "alerta del sistema experto (M5, umbral < 45%)."
    )
