# ============================================================
# M2 · PROGRAMA DE INCENTIVOS — Proyecto "El Errante"
# Pestaña 2 del dashboard (DOCUMENTO_MAESTRO §6 · M2)
# ------------------------------------------------------------
# Contenido:
#   • Simulador de comisiones (sliders) con proyección de ingreso extra
#   • Leaderboard de los 48 meseros (filtrable por sucursal)
#   • Exclusión del producto ancla del cálculo de incentivos
#   • Rankings de bebidas vistosas y platillos de temporada
# Reglas de negocio:
#   • Incentivo = utilidad de la línea × tasa_comisión × multiplicador
#   • Multiplicador alto: bebidas y variantes de platillos con ROI > 100%
#   • El ancla (Sopa de Mariscos) NO genera incentivos
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_SUCCESS, COLOR_WARNING, header
from utils import fmt_money, fmt_pct

# Elasticidad: crecimiento estimado de ventas por cada 1.0x de multiplicador extra
ELASTICIDAD = 0.35

PALETA_SUCURSAL = {"S1": COLOR_SUCCESS, "S2": COLOR_WARNING, "S3": "#5B8DEF"}


def _template() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor="#13315C", font_color="#F8FAFC"),
    )


# ------------------------------------------------------------
# Motor de cálculo de incentivos
# ------------------------------------------------------------
def _calc_incentivos(df: pd.DataFrame, tasa: float, mult_alto: float) -> pd.DataFrame:
    """Añade columnas de utilidad, multiplicador y comisión por línea.

    - utilidad = monto - costo_total (margen en $ de la línea)
    - alto_roi: bebidas o variantes de platillos con ROI > 100%
    - comisión = utilidad × tasa × multiplicador (0 si el producto es ancla)
    """
    d = df.copy()
    d["utilidad"] = d["monto"] - d["costo_total"]
    alto_roi = (d["categoria"] == "Bebida") | (
        (d["subcategoria"] == "Variante") & (d["roi"] > 1.0)
    )
    incentivable = ~d["es_ancla"]
    d["multiplicador"] = np.where(alto_roi & incentivable, mult_alto, 1.0)
    d["comision_linea"] = np.where(
        incentivable, d["utilidad"] * tasa * d["multiplicador"], 0.0
    )
    d["_alto_roi"] = alto_roi & incentivable
    return d


def _proyeccion(d: pd.DataFrame, tasa: float, mult_alto: float) -> dict:
    """Proyección de ingreso extra al estimular productos de alto ROI.

    Modelo: el multiplicador extra genera un crecimiento estimado de ventas
    en esas líneas; el margen incremental menos la comisión sobre ese margen
    y menos el aumento de comisión sobre las ventas alto-ROI existentes es el
    beneficio neto proyectado para la sucursal.
    """
    margen_alto = d.loc[d["_alto_roi"], "utilidad"].sum()
    crecimiento = max((mult_alto - 1.0) * ELASTICIDAD, 0.0)
    margen_extra = margen_alto * crecimiento
    comision_extra = margen_extra * tasa * mult_alto
    # Costo de subir la comisión sobre las ventas alto-ROI ya existentes
    costo_base = margen_alto * tasa * max(mult_alto - 1.0, 0.0)
    neto_extra = margen_extra - comision_extra - costo_base
    return {
        "crecimiento": crecimiento,
        "margen_extra": margen_extra,
        "comision_extra": comision_extra,
        "costo_base": costo_base,
        "neto_extra": neto_extra,
    }


# ------------------------------------------------------------
# Leaderboard de meseros
# ------------------------------------------------------------
def _leaderboard(d: pd.DataFrame, meseros: pd.DataFrame) -> pd.DataFrame:
    """Ranking de meseros por comisión ganada (excluye el ancla)."""
    inc = d[d["comision_linea"] > 0]
    lb = (
        inc.groupby("id_mesero")
        .agg(
            comision=("comision_linea", "sum"),
            ventas_incentivadas=("monto", "sum"),
            tickets=("id_ticket", "nunique"),
        )
        .reset_index()
        .merge(
            meseros[["id_mesero", "nombre", "sucursal"]], on="id_mesero"
        )
        .sort_values("comision", ascending=False)
    )
    lb["rank"] = range(1, len(lb) + 1)
    lb["medalla"] = lb["rank"].map(
        {1: "🥇", 2: "🥈", 3: "🥉"}
    ).fillna("")
    lb["medalla"] = lb["medalla"].astype(str)
    return lb


def _grafico_leaderboard(lb: pd.DataFrame, top_n: int = 10):
    top = lb.head(top_n).iloc[::-1]  # invertir para ranking vertical
    fig = px.bar(
        top,
        x="comision",
        y="nombre",
        orientation="h",
        color="sucursal",
        color_discrete_map=PALETA_SUCURSAL,
        labels={"comision": "Comisión ($)", "nombre": "", "sucursal": "Sucursal"},
        custom_data=["rank", "ventas_incentivadas"],
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="<b>#%{customdata[0]} %{y}</b><br>"
        "Comisión: $%{x:,.0f}<br>"
        "Ventas incentivadas: $%{customdata[1]:,.0f}<extra></extra>",
    )
    fig.update_layout(
        **_template(),
        height=420,
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(tickformat=",.0f"),
    )
    return fig


def _tabla_leaderboard(lb: pd.DataFrame) -> pd.DataFrame:
    tabla = lb.copy()
    tabla = tabla.rename(columns={
        "rank": "Rank",
        "medalla": "",
        "nombre": "Mesero",
        "sucursal": "Suc.",
        "comision": "Comisión",
        "ventas_incentivadas": "Ventas incent.",
        "tickets": "Tickets",
    })
    tabla["Comisión"] = tabla["Comisión"].map(lambda x: f"${x:,.0f}")
    tabla["Ventas incent."] = tabla["Ventas incent."].map(lambda x: f"${x:,.0f}")
    return tabla[["Rank", "", "Mesero", "Suc.", "Comisión", "Ventas incent.", "Tickets"]]


# ------------------------------------------------------------
# Rankings especiales (bebidas vistosas y platillos de temporada)
# ------------------------------------------------------------
def _rankings_especiales(d: pd.DataFrame, productos: pd.DataFrame):
    """Top 5 de meseros en bebidas vistosas y platillos de temporada."""
    etiquetas = productos[["id_producto", "etiquetas"]].copy()
    etiquetas["es_vistoso"] = etiquetas["etiquetas"].str.contains("vistoso", na=False)
    etiquetas["es_temporada"] = etiquetas["etiquetas"].str.contains("temporada", na=False)
    d = d.merge(etiquetas[["id_producto", "es_vistoso", "es_temporada"]], on="id_producto")

    def top(col, cat):
        mask = d[col] & (d["categoria"] == cat)
        agg = (
            d[mask]
            .groupby(["id_mesero"])
            .agg(ventas=("monto", "sum"), unidades=("cantidad", "sum"))
            .reset_index()
            .sort_values("ventas", ascending=False)
            .head(5)
        )
        return agg

    return top("es_vistoso", "Bebida"), top("es_temporada", "Alimento")


def _grafico_ranking(agg: pd.DataFrame, meseros: pd.DataFrame, titulo: str):
    if agg.empty:
        return None
    a = agg.merge(meseros[["id_mesero", "nombre", "sucursal"]], on="id_mesero")
    a = a.iloc[::-1]
    fig = px.bar(
        a,
        x="ventas",
        y="nombre",
        orientation="h",
        color="sucursal",
        color_discrete_map=PALETA_SUCURSAL,
        labels={"ventas": "Ventas ($)", "nombre": "", "sucursal": ""},
        custom_data=["unidades"],
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Ventas: $%{x:,.0f}<br>"
        "Unidades: %{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        **_template(),
        height=300,
        showlegend=False,
        xaxis=dict(tickformat=",.0f"),
        title=dict(text=titulo, font=dict(size=14)),
    )
    return fig


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df: pd.DataFrame, meseros: pd.DataFrame, productos: pd.DataFrame,
           sucursales_sel: list) -> None:
    header(
        "Programa de Incentivos",
        "Simula comisiones basadas en el margen real de cada producto y compara "
        "el rendimiento de los 48 meseros.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    # ---- Simulador de comisiones ----
    st.markdown("#### 🎚️ Simulador de comisiones")
    c_tasa, c_mult, _ = st.columns([1, 1, 2])
    with c_tasa:
        tasa = st.slider(
            "Comisión sobre utilidad (%)",
            min_value=0.0, max_value=15.0, value=5.0, step=0.5,
            help="Porcentaje del margen que recibe el mesero por línea vendida.",
        ) / 100.0
    with c_mult:
        mult_alto = st.slider(
            "Multiplicador alto ROI (bebidas y variantes)",
            min_value=1.0, max_value=3.0, value=1.5, step=0.1,
            help="Refuerza el incentivo en bebidas y variantes con ROI > 100%.",
        )

    d = _calc_incentivos(df, tasa, mult_alto)
    proy = _proyeccion(d, tasa, mult_alto)

    # ---- KPIs del programa ----
    total_comision = d["comision_linea"].sum()
    utilidad_total = d["utilidad"].sum()
    pct_utilidad = total_comision / utilidad_total if utilidad_total else 0
    lb = _leaderboard(d, meseros)
    top1 = lb.iloc[0] if not lb.empty else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Comisiones del periodo", fmt_money(total_comision),
        help="Suma de incentivos a meseros con la configuración actual.",
    )
    c2.metric(
        "% utilidad a incentivos", fmt_pct(pct_utilidad),
        help="Porción del margen total destinada al programa de incentivos.",
    )
    c3.metric(
        "Mesero #1", top1["nombre"] if top1 is not None else "—",
        fmt_money(top1["comision"]) if top1 is not None else None,
        help="Líder del leaderboard por comisión ganada.",
    )
    c4.metric(
        "Proyección ingreso extra", fmt_money(proy["neto_extra"]),
        f"crecimiento estimado {proy['crecimiento']:.1%}",
        help="Margen incremental estimado al estimular productos de alto ROI, "
        "menos la comisión extra pagada.",
    )

    st.caption(
        f"Modelo de proyección: con multiplicador {mult_alto:.1f}x se estima un "
        f"{proy['crecimiento']:.1%} de crecimiento en líneas de alto ROI → margen extra "
        f"{fmt_money(proy['margen_extra'])} − comisión extra {fmt_money(proy['comision_extra'])} "
        f"− costo sobre ventas existentes {fmt_money(proy['costo_base'])} "
        f"= {fmt_money(proy['neto_extra'])} netos para la sucursal."
    )

    # ---- Leaderboard ----
    st.markdown("#### 🏆 Leaderboard de meseros (sin Sopa Ancla)")
    c_graf, c_tab = st.columns([1.15, 0.85])
    with c_graf:
        if lb.empty:
            st.info("Con comisión 0% no hay incentivos que calcular. Sube el slider.")
        else:
            st.plotly_chart(_grafico_leaderboard(lb), width="stretch")
    with c_tab:
        if lb.empty:
            st.info("—")
        else:
            st.dataframe(
                _tabla_leaderboard(lb.head(15)),
                width="stretch",
                hide_index=True,
            )
    st.caption(
        "El cálculo excluye la Sopa de Mariscos (producto ancla). "
        "Las bebidas y variantes de alto ROI reciben el multiplicador configurado."
    )

    # ---- Rankings especiales ----
    st.markdown("#### 🥤 Rankings especiales")
    c_vist, c_temp = st.columns(2)
    top_vistoso, top_temporada = _rankings_especiales(d, productos)
    with c_vist:
        fig = _grafico_ranking(top_vistoso, meseros, "Bebidas vistosas (marketing)")
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin ventas de bebidas vistosas en el periodo.")
    with c_temp:
        fig = _grafico_ranking(top_temporada, meseros, "Platillos de temporada")
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin ventas de platillos de temporada en el periodo.")
