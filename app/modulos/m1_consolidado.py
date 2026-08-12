# ============================================================
# M1 · CONSOLIDADO FINANCIERO Y ROI — Proyecto "El Errante"
# Pestaña 1 del dashboard (DOCUMENTO_MAESTRO §6 · M1)
# ------------------------------------------------------------
# Contenido:
#   • Tarjetas KPI globales (ventas, ticket promedio, ROI, mix bebidas)
#   • Mapa geográfico dinámico de las 3 sucursales
#   • Serie temporal con zoom/filtro (meses de incumplimiento vs Cuaresma)
#   • ROI promedio mensual con umbral crítico del 45% (categoría Alimentos)
# Autor: Buffy | Generado: 2026-08-11 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_CRITICAL, COLOR_SUCCESS, COLOR_WARNING, header
from utils import fmt_money, fmt_pct, kpi_delta, periodo_anterior

# Umbral de alerta ROI (DOCUMENTO_MAESTRO §6 · M5)
UMBRAL_ROI = 0.45

PALETA_SUCURSAL = {"S1": COLOR_SUCCESS, "S2": COLOR_WARNING, "S3": "#5B8DEF"}


def _template() -> dict:
    """Configuración base de layout para gráficos Plotly (tema oscuro)."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor="#13315C", font_color="#F8FAFC"),
    )


def _kpis(df: pd.DataFrame, fecha_min, fecha_max):
    """Tarjetas KPI del periodo seleccionado, con delta vs periodo anterior."""
    actual = df
    # Periodo anterior equivalente (vacío si cae antes del inicio de los datos)
    f_ant_min, f_ant_max = periodo_anterior(actual, fecha_min, fecha_max)
    anterior = actual[
        (actual["fecha_hora"] >= f_ant_min) & (actual["fecha_hora"] <= f_ant_max)
    ]

    def calc(d):
        ventas = d["monto"].sum()
        tickets = d["id_ticket"].nunique()
        ticket_prom = ventas / tickets if tickets else 0
        costo = d["costo_total"].sum()
        roi = (ventas - costo) / costo if costo else 0
        mix = d.loc[d["categoria"] == "Bebida", "monto"].sum() / ventas if ventas else 0
        return ventas, ticket_prom, roi, mix

    v, tp, roi, mix = calc(actual)
    v_a, tp_a, roi_a, mix_a = calc(anterior)

    items = [
        ("Ventas totales", fmt_money(v), kpi_delta(v, v_a)[0],
         "Facturación total del periodo seleccionado"),
        ("Ticket promedio", fmt_money(tp), kpi_delta(tp, tp_a)[0],
         "Ingreso promedio por mesa/ticket"),
        ("ROI promedio", fmt_pct(roi), kpi_delta(roi, roi_a)[0],
         "Margen de ganancia sobre costo (ventas - costo) / costo"),
        ("Mix de bebidas", fmt_pct(mix), kpi_delta(mix, mix_a)[0],
         "Participación de bebidas en el ticket (motor de margen)"),
    ]
    c1, c2, c3, c4 = st.columns(4)
    for col, (label, valor, delta_txt, ayuda) in zip((c1, c2, c3, c4), items):
        color = "inverse" if (label == "ROI promedio" and roi < UMBRAL_ROI) else "normal"
        col.metric(label, valor, delta_txt, delta_color=color, help=ayuda)


def _mapa(df: pd.DataFrame, sucursales: pd.DataFrame):
    """Mapa geográfico de las sucursales con tamaño = ventas del periodo."""
    agg = (
        df.groupby("id_sucursal")["monto"]
        .sum()
        .rename("ventas")
        .reset_index()
        .merge(sucursales, on="id_sucursal")
    )
    fig = px.scatter_geo(
        agg,
        lat="lat",
        lon="lon",
        size="ventas",
        color="id_sucursal",
        color_discrete_map=PALETA_SUCURSAL,
        hover_name="nombre",
        hover_data={"ventas": ":.0f", "entidad": True, "num_meseros": True},
        projection="natural earth",
        center=dict(lat=24.5, lon=-101.5),
        size_max=42,
    )
    fig.update_traces(
        marker=dict(line=dict(width=1.5, color="white")),
        hovertemplate="<b>%{hovertext}</b><br>"
        "Entidad: %{customdata[1]}<br>"
        "Meseros: %{customdata[2]}<br>"
        "Ventas: $%{customdata[0]:,.0f}<extra></extra>",
    )
    fig.update_layout(**_template(), height=420)
    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="rgba(255,255,255,0.25)",
        showland=True,
        landcolor="#0d1f38",
        showcountries=True,
        countrycolor="rgba(255,255,255,0.3)",
        showframe=False,
    )
    return fig


def _serie_temporal(df: pd.DataFrame):
    """Serie de ventas diarias por sucursal con zoom y selector de rango."""
    diario = (
        df.groupby([df["fecha_hora"].dt.date, "id_sucursal"])["monto"]
        .sum()
        .reset_index()
    )
    diario.columns = ["fecha", "id_sucursal", "monto"]
    fig = px.line(
        diario,
        x="fecha",
        y="monto",
        color="id_sucursal",
        color_discrete_map=PALETA_SUCURSAL,
        labels={"fecha": "", "monto": "Ventas ($)", "id_sucursal": "Sucursal"},
    )
    fig.update_traces(line=dict(width=1.6), hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>")
    fig.update_layout(
        **_template(),
        height=400,
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.06),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(step="all", label="Todo"),
                ]
            ),
        ),
        yaxis=dict(tickformat=",.0f"),
    )
    return fig


def _real_vs_presupuesto(df: pd.DataFrame, presupuesto: pd.DataFrame):
    """Barras mensuales: real vs meta presupuestada (meses de incumplimiento)."""
    real_mensual = (
        df.groupby(["mes_ano", "id_sucursal"])["monto"].sum().reset_index()
    )
    comp = real_mensual.merge(
        presupuesto[["mes_ano", "id_sucursal", "meta_ventas"]],
        on=["mes_ano", "id_sucursal"],
    )
    comp["cumplimiento"] = comp["monto"] / comp["meta_ventas"]
    comp["mes"] = pd.to_datetime(comp["mes_ano"] + "-01")

    fig = go.Figure()
    for suc in sorted(comp["id_sucursal"].unique()):
        d = comp[comp["id_sucursal"] == suc].sort_values("mes")
        fig.add_trace(go.Bar(
            x=d["mes"],
            y=d["cumplimiento"],
            name=f"Real {suc}",
            marker_color=PALETA_SUCURSAL[suc],
            opacity=0.85,
            customdata=d[["monto", "meta_ventas"]],
            hovertemplate="%{x|%b %Y}<br>Cumplimiento: %{y:.0%}"
            "<br>Real: $%{customdata[0]:,.0f}<br>Meta: $%{customdata[1]:,.0f}"
            "<extra></extra>",
        ))
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color="white",
        annotation_text="Meta (100%)",
        annotation_position="top left",
    )
    fig.add_hline(
        y=0.90,
        line_dash="dot",
        line_color=COLOR_WARNING,
        annotation_text="Umbral alerta (90%)",
        annotation_position="bottom left",
        annotation_font_color=COLOR_WARNING,
    )
    fig.update_layout(
        **_template(),
        height=340,
        barmode="group",
        legend=dict(orientation="h", y=1.12, x=0),
        yaxis=dict(tickformat=".0%", title="Cumplimiento"),
        xaxis=dict(title=""),
    )
    return fig


def _roi_mensual(df: pd.DataFrame):
    """ROI mensual de la categoría Alimentos con umbral crítico de 45%."""
    alimentos = df[df["categoria"] == "Alimento"].copy()
    mensual = alimentos.groupby("mes_ano").agg(
        ventas=("monto", "sum"), costo=("costo_total", "sum")
    ).reset_index()
    mensual["roi"] = (mensual["ventas"] - mensual["costo"]) / mensual["costo"]
    mensual["mes"] = pd.to_datetime(mensual["mes_ano"] + "-01")

    fig = go.Figure()
    colores = [
        COLOR_CRITICAL if r < UMBRAL_ROI else COLOR_SUCCESS
        for r in mensual["roi"]
    ]
    fig.add_trace(go.Bar(
        x=mensual["mes"],
        y=mensual["roi"],
        marker_color=colores,
        customdata=mensual[["ventas", "costo"]],
        hovertemplate="%{x|%b %Y}<br>ROI: %{y:.1%}"
        "<br>Ventas: $%{customdata[0]:,.0f}<br>Costo: $%{customdata[1]:,.0f}"
        "<extra></extra>",
    ))
    fig.add_hline(
        y=UMBRAL_ROI,
        line_dash="dash",
        line_color=COLOR_CRITICAL,
        annotation_text=f"Umbral crítico ({UMBRAL_ROI:.0%})",
        annotation_position="top right",
        annotation_font_color=COLOR_CRITICAL,
    )
    fig.update_layout(
        **_template(),
        height=340,
        yaxis=dict(tickformat=".0%", title="ROI Alimentos"),
        xaxis=dict(title=""),
    )
    return fig


def _tabla_sucursales(df: pd.DataFrame, sucursales: pd.DataFrame):
    """Resumen por sucursal del periodo seleccionado."""
    agg = df.groupby("id_sucursal").agg(
        ventas=("monto", "sum"),
        tickets=("id_ticket", "nunique"),
        costo=("costo_total", "sum"),
    ).reset_index()
    # Divisiones seguras (evita inf/NaN si una sucursal no tiene tickets o costo)
    agg["ticket_promedio"] = agg["ventas"].div(agg["tickets"].replace(0, np.nan)).fillna(0)
    agg["roi"] = (agg["ventas"] - agg["costo"]).div(
        agg["costo"].replace(0, np.nan)
    ).fillna(0)
    ventas_bebidas = (
        df[df["categoria"] == "Bebida"].groupby("id_sucursal")["monto"].sum()
    )
    agg["mix_bebidas"] = (
        ventas_bebidas.reindex(agg["id_sucursal"]).fillna(0).values
        / agg["ventas"].replace(0, np.nan)
    ).fillna(0)

    tabla = agg.merge(
        sucursales[["id_sucursal", "entidad", "ciudad", "num_meseros"]],
        on="id_sucursal",
    )
    tabla["roi"] = tabla["roi"].map(lambda x: f"{x:.1%}")
    tabla["mix_bebidas"] = tabla["mix_bebidas"].map(lambda x: f"{x:.1%}")
    tabla["ticket_promedio"] = tabla["ticket_promedio"].map(lambda x: f"${x:,.0f}")
    tabla["ventas"] = tabla["ventas"].map(lambda x: f"${x:,.0f}")
    tabla = tabla.rename(columns={
        "id_sucursal": "Sucursal",
        "entidad": "Entidad",
        "ciudad": "Ciudad",
        "num_meseros": "Meseros",
        "ventas": "Ventas",
        "tickets": "Tickets",
        "ticket_promedio": "Ticket prom.",
        "roi": "ROI",
        "mix_bebidas": "Mix bebidas",
    })
    return tabla[["Sucursal", "Entidad", "Ciudad", "Meseros", "Ventas", "Tickets",
                  "Ticket prom.", "ROI", "Mix bebidas"]]


def render(df: pd.DataFrame, sucursales: pd.DataFrame, presupuesto: pd.DataFrame,
           fecha_min, fecha_max, sucursales_sel) -> None:
    """Pinta el módulo M1 · Consolidado Financiero y ROI."""
    header(
        "Consolidado Financiero y ROI",
        "Visión ejecutiva de las 3 sucursales: ventas, margen y estacionalidad.",
    )

    # ---- Filtro por sucursal (además del rango de fechas global) ----
    df = df[df["id_sucursal"].isin(sucursales_sel)]

    # ---- Guarda: sin datos en el periodo seleccionado ----
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    # ---- KPIs ----
    _kpis(df, fecha_min, fecha_max)

    # ---- Mapa + tabla sucursales ----
    c_mapa, c_tabla = st.columns([1.15, 0.85])
    with c_mapa:
        st.markdown("#### 🗺️ Mapa geográfico de sucursales")
        st.plotly_chart(_mapa(df, sucursales), width="stretch")
    with c_tabla:
        st.markdown("#### 📊 Resumen por sucursal")
        st.dataframe(
            _tabla_sucursales(df, sucursales),
            width="stretch",
            hide_index=True,
        )

    # ---- Serie temporal ----
    st.markdown("#### 📈 Evolución diaria de ventas")
    st.caption(
        "Usa el selector de rango y el control deslizante para hacer zoom. "
        "Observa los meses de Cuaresma (Mar-Abr) frente a la cuesta de enero."
    )
    st.plotly_chart(_serie_temporal(df), width="stretch")

    # ---- Real vs Presupuesto + ROI mensual ----
    c_pres, c_roi = st.columns(2)
    with c_pres:
        st.markdown("#### 🎯 Cumplimiento de presupuesto (mensual)")
        st.plotly_chart(
            _real_vs_presupuesto(df, presupuesto), width="stretch"
        )
    with c_roi:
        st.markdown("#### 💎 ROI mensual — Alimentos")
        st.caption(
            "Motor de alertas: si el ROI cae del 45% se dispara el plan de contingencia "
            "(incentivo a bebidas, ajuste de porciones)."
        )
        st.plotly_chart(_roi_mensual(df), width="stretch")
