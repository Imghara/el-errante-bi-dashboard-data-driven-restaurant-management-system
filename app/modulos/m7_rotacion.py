# ============================================================
# M7 · ROTACIÓN DE MESAS Y EFICIENCIA DEL SERVICIO — "El Errante"
# Pestaña 7 del dashboard (DOCUMENTO_MAESTRO §6 · M7)
# ------------------------------------------------------------
# Analiza el tiempo de ocupación de mesa (hora_apertura_mesa →
# hora_cierre_mesa) y su cruce con el rendimiento de los meseros:
#   • Tiempo de ocupación promedio y distribución por sucursal
#   • Eficiencia de mesa ($/min) por mesero: ticket alto + tiempo
#     largo = posible "secuestro de mesa"; ticket alto + tiempo
#     corto = eficiencia real (liberación en horas pico)
#   • Variación por hora del día (las horas pico rotan más rápido)
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_CRITICAL, COLOR_SUCCESS, COLOR_WARNING, header
from utils import fmt_money

PALETA_SUCURSAL = {"S1": COLOR_SUCCESS, "S2": COLOR_WARNING, "S3": "#5B8DEF"}


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
# Preparación: tickets con tiempo de ocupación
# ------------------------------------------------------------
def _tickets(df: pd.DataFrame) -> pd.DataFrame:
    """Colapsa las líneas a nivel ticket con tiempo de ocupación.

    Las columnas de fecha ya vienen parseadas por cargar_ventas();
    aquí solo se deriva el tiempo de ocupación.
    """
    d = df.copy()
    d["tiempo_min"] = (
        d["hora_cierre_mesa"] - d["hora_apertura_mesa"]
    ).dt.total_seconds() / 60
    d["hora"] = d["fecha_hora"].dt.hour
    d["dow"] = d["fecha_hora"].dt.dayofweek
    tick = (
        d.groupby("id_ticket")
        .agg(
            monto=("monto", "sum"),
            tiempo_min=("tiempo_min", "max"),
            id_mesero=("id_mesero", "first"),
            id_sucursal=("id_sucursal", "first"),
            hora=("hora", "first"),
            dow=("dow", "first"),
        )
        .reset_index()
    )
    return tick[tick["tiempo_min"] > 0]


def _por_mesero(tick: pd.DataFrame, meseros: pd.DataFrame) -> pd.DataFrame:
    """Rendimiento por mesero: ticket medio, tiempo medio, eficiencia $/min."""
    pm = (
        tick.groupby("id_mesero")
        .agg(
            ticket=("monto", "mean"),
            tiempo=("tiempo_min", "mean"),
            tickets=("monto", "size"),
        )
        .reset_index()
    )
    pm["usd_min"] = pm["ticket"] / pm["tiempo"]
    pm = pm.merge(
        meseros[["id_mesero", "nombre", "sucursal"]], on="id_mesero", how="left"
    )
    # Bandera de salud: ticket alto con eficiencia baja = secuestro potencial
    med_ticket = pm["ticket"].median()
    med_efic = pm["usd_min"].median()
    pm["bandera"] = np.where(
        (pm["ticket"] > med_ticket * 1.05) & (pm["usd_min"] < med_efic * 0.97),
        "warn",
        "ok",
    )
    return pm.sort_values("usd_min", ascending=False)


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------
def _scatter_eficiencia(pm: pd.DataFrame) -> go.Figure:
    """Ticket medio vs tiempo de ocupación; color y tamaño = $/min."""
    fig = px.scatter(
        pm,
        x="tiempo",
        y="ticket",
        size="usd_min",
        color="usd_min",
        color_continuous_scale=[[0, COLOR_CRITICAL], [0.5, COLOR_WARNING],
                                [1, COLOR_SUCCESS]],
        custom_data=pm[["usd_min", "tickets"]],
        labels={"tiempo": "Tiempo de ocupación (min)",
                "ticket": "Ticket promedio ($)",
                "usd_min": "$/min"},
    )
    # Etiqueta solo para los 5 más eficientes (evita solape de 48 nombres)
    top5 = pm.nlargest(5, "usd_min")["id_mesero"].tolist()
    fig.update_traces(
        text=pm["nombre"].where(pm["id_mesero"].isin(top5)),
        textposition="top center", textfont=dict(size=10, color="#F8FAFC"),
        hovertemplate="<b>%{customdata[1]:.0f} tickets</b><br>Ticket: $%{y:,.0f}<br>"
                      "Tiempo: %{x:.0f} min<br>Eficiencia: $%{customdata[0]:,.2f}/min"
                      "<extra></extra>",
    )
    fig.add_vline(x=pm["tiempo"].median(), line_dash="dash",
                  line_color="#94A3B8", annotation_text="Tiempo medio")
    fig.add_hline(y=pm["ticket"].median(), line_dash="dash",
                  line_color="#94A3B8", annotation_text="Ticket medio")
    fig.update_layout(
        **_template(), height=480,
        yaxis=dict(tickformat=",.0f"), xaxis=dict(range=[55, 100]),
        title=dict(text="Eficiencia de mesa por mesero (ticket vs tiempo)",
                   font=dict(size=14)),
    )
    return fig


def _histograma(tick: pd.DataFrame) -> go.Figure:
    """Distribución del tiempo de ocupación por sucursal."""
    fig = go.Figure()
    for suc, color in PALETA_SUCURSAL.items():
        t = tick[tick["id_sucursal"] == suc]["tiempo_min"]
        if len(t):
            fig.add_trace(go.Histogram(
                x=t, name=suc, nbinsx=40, opacity=0.75,
                marker_color=color,
                hovertemplate="%{x:.0f}-%{x+5:.0f} min: %{y} tickets<extra></extra>",
            ))
    fig.update_layout(
        **_template(), height=380, barmode="overlay",
        xaxis=dict(title="Tiempo de ocupación (min)"),
        yaxis=dict(title="Tickets"),
        title=dict(text="Distribución del tiempo de ocupación por sucursal",
                   font=dict(size=14)),
    )
    return fig


def _por_hora(tick: pd.DataFrame) -> go.Figure:
    """Tiempo medio de ocupación por hora del día."""
    h = (
        tick.groupby("hora")["tiempo_min"]
        .mean()
        .reset_index()
        .sort_values("hora")
    )
    fig = go.Figure(go.Scatter(
        x=h["hora"], y=h["tiempo_min"], mode="lines+markers",
        line=dict(color=COLOR_SUCCESS, width=2.6), marker=dict(size=7),
        hovertemplate="%{x}:00 h<br>Tiempo medio: %{y:.0f} min<extra></extra>",
    ))
    # Zona de horas pico (13-15 y 20-22)
    fig.add_vrect(x0=13, x1=15, fillcolor=COLOR_WARNING, opacity=0.12,
                  line_width=0, annotation_text="Pico comida",
                  annotation_position="top left")
    fig.add_vrect(x0=20, x1=22, fillcolor=COLOR_WARNING, opacity=0.12,
                  line_width=0, annotation_text="Pico cena",
                  annotation_position="top left")
    fig.update_layout(
        **_template(), height=380,
        xaxis=dict(title="Hora de apertura de mesa", dtick=2, range=[10, 23.5]),
        yaxis=dict(title="Tiempo medio (min)"),
        title=dict(text="Tiempo de ocupación por hora — las mesas rotan más "
                        "rápido en horas pico", font=dict(size=14)),
    )
    return fig


def _por_dia(tick: pd.DataFrame) -> go.Figure:
    """Ticket y tiempo por día de la semana."""
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    d = tick.groupby("dow").agg(
        ticket=("monto", "mean"), tiempo=("tiempo_min", "mean")
    ).reindex(range(7)).reset_index()
    d["día"] = d["dow"].map(lambda x: dias[int(x)] if x == x else "")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=d["día"], y=d["ticket"], name="Ticket medio ($)",
        marker_color=COLOR_WARNING, opacity=0.9,
        hovertemplate="%{x}: ticket $%{y:,.0f}<extra></extra>",
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=d["día"], y=d["tiempo"], name="Tiempo (min)", mode="lines+markers",
        line=dict(color=COLOR_SUCCESS, width=2.4), marker=dict(size=6),
        hovertemplate="%{x}: %{y:.0f} min<extra></extra>",
        yaxis="y2",
    ))
    fig.update_layout(
        **_template(), height=360,
        yaxis=dict(title="Ticket medio ($)", tickformat=",.0f"),
        yaxis2=dict(title="Tiempo (min)", overlaying="y", side="right",
                    showgrid=False),
        title=dict(text="Ticket y tiempo de ocupación por día de la semana",
                   font=dict(size=14)),
    )
    return fig


def _tabla_meseros(pm: pd.DataFrame) -> pd.DataFrame:
    t = pm.copy()
    t["Mesero"] = t["nombre"]
    t["Sucursal"] = t["sucursal"]
    t["Ticket"] = t["ticket"].map(lambda x: f"${x:,.0f}")
    t["Tiempo"] = t["tiempo"].map(lambda x: f"{x:.0f} min")
    t["Eficiencia"] = t["usd_min"].map(lambda x: f"${x:.2f}/min")
    t["Tickets"] = t["tickets"]
    t["Estado"] = t["bandera"].map(
        {"ok": "✅ Eficiente", "warn": "⚠️ Secuestro potencial"}
    )
    return t[["Mesero", "Sucursal", "Ticket", "Tiempo", "Eficiencia",
              "Tickets", "Estado"]]


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df, meseros, sucursales, sucursales_sel) -> None:
    header(
        "Rotación de Mesas y Eficiencia del Servicio",
        "Tiempo de ocupación por mesa cruzado con el rendimiento de cada "
        "mesero para distinguir eficiencia real de 'secuestro de mesa'.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    tick = _tickets(df)
    if tick.empty:
        st.info("Sin tickets con datos de apertura/cierre en la selección.")
        return

    pm = _por_mesero(tick, meseros)

    # ---- KPIs ----
    tiempo_medio = tick["tiempo_min"].mean()
    ticket_medio = tick["monto"].mean()
    efic_global = ticket_medio / tiempo_medio
    # Rotación estimada: con jornadas pico de ~7 h (12:00-23:00)
    HORAS_SERVICIO = 7 * 60
    rotacion = HORAS_SERVICIO / tiempo_medio

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Tiempo de ocupación", f"{tiempo_medio:.0f} min",
        f"p90 {tick['tiempo_min'].quantile(0.9):.0f} min",
        help="Tiempo promedio que una mesa permanece ocupada "
             "(apertura → cierre).",
    )
    c2.metric(
        "Ticket promedio", fmt_money(ticket_medio),
        f"{tick['monto'].count():,.0f} tickets",
        help="Gasto promedio por mesa atendida.",
    )
    c3.metric(
        "Eficiencia de mesa", f"${efic_global:.2f}/min",
        "ingreso por minuto",
        help="Ticket promedio ÷ tiempo de ocupación. Mide cuánto genera "
             "cada minuto de mesa.",
    )
    c4.metric(
        "Rotación estimada", f"{rotacion:.1f} mesas/día",
        f"jornada {HORAS_SERVICIO // 60} h",
        help="Veces que una mesa podría reasignarse en una jornada pico "
             "de servicio (12:00-23:00).",
    )

    # ---- Scatter de eficiencia por mesero ----
    st.markdown("#### 🎯 Eficiencia por mesero (ticket vs tiempo)")
    st.plotly_chart(_scatter_eficiencia(pm), width="stretch")
    st.caption(
        "Cuadrante superior izquierdo = **eficiencia real** (ticket alto, "
        "mesa liberada rápido). Cuadrante superior derecho con eficiencia "
        "baja = posible **secuestro de mesa**: el ticket alto no justifica "
        "la mesa ocupada (bandera ⚠️)."
    )

    # ---- Distribución + hora del día ----
    c_hist, c_hora = st.columns(2)
    with c_hist:
        st.plotly_chart(_histograma(tick), width="stretch")
    with c_hora:
        st.plotly_chart(_por_hora(tick), width="stretch")

    # ---- Día de la semana + tabla ----
    c_dia, c_tabla = st.columns([0.9, 1.1])
    with c_dia:
        st.plotly_chart(_por_dia(tick), width="stretch")
    with c_tabla:
        st.markdown("#### 📋 Rendimiento por mesero")
        st.dataframe(_tabla_meseros(pm), width="stretch", hide_index=True)

    # ---- Insight de negocio ----
    n_warn = int((pm["bandera"] == "warn").sum())
    pico = tick["hora"].isin([13, 14, 15, 20, 21, 22])
    entidades = " / ".join(
        sucursales.set_index("id_sucursal").reindex(sucursales_sel)["entidad"].tolist()
    )
    st.info(
        f"**Insight de negocio** ({entidades}): el tiempo de ocupación baja en "
        f"horas pico ({tick[pico]['tiempo_min'].mean():.0f} min vs "
        f"{tick[~pico]['tiempo_min'].mean():.0f} min en valle) — el servicio "
        f"acelera la liberación de mesas cuando la demanda lo exige. "
        f"**{n_warn} mesero(s)** presentan perfil de secuestro potencial "
        f"(ticket alto con eficiencia baja) y deberían revisarse en el módulo "
        f"de Auditoría (M10)."
    )
