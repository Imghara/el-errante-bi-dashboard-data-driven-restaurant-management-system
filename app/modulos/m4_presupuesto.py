# ============================================================
# M4 · PRESUPUESTO DE VENTAS VS REAL — Proyecto "El Errante"
# Pestaña 4 del dashboard (DOCUMENTO_MAESTRO §6 · M4)
# ------------------------------------------------------------
# Contenido:
#   • Gauges de cumplimiento por sucursal (pipeline/gauge)
#   • Barras mensuales: real vs meta presupuestada
#   • Serie temporal de cumplimiento con umbral de alerta (90%)
#   • Tabla detallada por mes y sucursal
# Reglas de negocio:
#   • Presupuesto anual desglosado mensual (absorbe estacionalidad)
#   • % Cumplimiento = Real / Meta (90% = umbral de alerta M5)
#   • Real 5-10% abajo en Ene/Feb/Sep/Oct, +12% en Cuaresma
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_CRITICAL, COLOR_SUCCESS, COLOR_WARNING, header
from utils import fmt_money

# Umbrales alineados con DOCUMENTO_MAESTRO §5.2 y §6 (M5):
#   • UMBRAL_CRITICO = 0.90 → estado 🚨 Alerta (regla M5: cumplimiento < 90%)
#   • UMBRAL_VIGILANCIA = 0.95 → inicio de la zona ⚠️ Vigilar (90–95%)
# Los datos simulan caídas de 5-10% en Ene/Feb/Sep/Oct, por lo que muchos
# meses caen en la zona de vigilancia; el crítico (<90%) es un evento raro.
UMBRAL_CRITICO = 0.90
UMBRAL_VIGILANCIA = 0.95
PALETA_SUCURSAL = {"S1": COLOR_SUCCESS, "S2": COLOR_WARNING, "S3": "#5B8DEF"}
COLOR_DEFAULT = "#64748B"


def _template() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor="#13315C", font_color="#F8FAFC"),
    )


# ------------------------------------------------------------
# Datos: real vs meta
# ------------------------------------------------------------
def _real_vs_meta(df: pd.DataFrame, presupuesto: pd.DataFrame,
                  sucursales_sel: list) -> pd.DataFrame:
    """Une ventas reales mensuales con la meta presupuestada."""
    real_mensual = (
        df.groupby(["mes_ano", "id_sucursal"])["monto"]
        .sum()
        .rename("real_ventas")
        .reset_index()
    )
    comp = presupuesto.merge(
        real_mensual, on=["mes_ano", "id_sucursal"], how="left"
    )
    comp = comp[comp["id_sucursal"].isin(sucursales_sel)]
    comp["real_ventas"] = comp["real_ventas"].fillna(0.0)
    # Un mes sin ventas registradas en el periodo filtrado es 0% → 🚨 alerta
    comp["cumplimiento"] = comp["real_ventas"] / comp["meta_ventas"]
    comp["varianza"] = comp["real_ventas"] - comp["meta_ventas"]
    comp["mes"] = pd.to_datetime(comp["mes_ano"] + "-01")
    return comp.sort_values(["mes", "id_sucursal"])


def _estado(cumplimiento: float) -> str:
    """Estado semántico según umbrales del documento (verde/ámbar/rojo).
    §5.2: ✅ ≥ 100% · ⚠️ 90–99.9% · 🚨 < 90%."""
    if cumplimiento >= 1.0:
        return "ok"
    if cumplimiento >= UMBRAL_CRITICO:
        return "warn"
    return "crit"


# ------------------------------------------------------------
# Gauges de cumplimiento por sucursal
# ------------------------------------------------------------
def _gauge(cumplimiento: float, nombre: str, subtitulo: str) -> go.Figure:
    color = {
        "ok": COLOR_SUCCESS, "warn": COLOR_WARNING, "crit": COLOR_CRITICAL,
    }[_estado(cumplimiento)]
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=cumplimiento * 100,
        number={"suffix": "%", "font": {"size": 42, "color": color}},
        delta={"reference": 100, "increasing": {"color": COLOR_SUCCESS},
               "decreasing": {"color": COLOR_CRITICAL},
               "suffix": "pp"},
        title={"text": f"<b>{nombre}</b><br><span style='font-size:12px;color:#94A3B8'>"
                        f"{subtitulo}</span>",
               "font": {"size": 16}},
        gauge={
            "axis": {"range": [None, 130], "tickwidth": 1,
                     "tickcolor": "#94A3B8"},
            "bar": {"color": color, "thickness": 0.32},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 90], "color": "rgba(231,76,60,0.18)"},
                {"range": [90, 100], "color": "rgba(245,166,35,0.18)"},
                {"range": [100, 130], "color": "rgba(27,163,156,0.18)"},
            ],
            "threshold": {"line": {"color": "white", "width": 2},
                          "thickness": 0.75, "value": 100},
        },
    ))
    fig.update_layout(height=260, margin=dict(l=30, r=30, t=70, b=20))
    return fig


def _gauges(comp: pd.DataFrame, sucursales: pd.DataFrame):
    """Un gauge por sucursal con el cumplimiento acumulado del periodo."""
    agg = (
        comp.groupby("id_sucursal")
        .agg(real=("real_ventas", "sum"), meta=("meta_ventas", "sum"))
        .reset_index()
    )
    agg["cumpl"] = agg["real"] / agg["meta"]
    info = sucursales.set_index("id_sucursal")

    cols = st.columns(len(agg))
    for col, (_, r) in zip(cols, agg.iterrows()):
        entidad = info.loc[r["id_sucursal"], "entidad"]
        col.plotly_chart(
            _gauge(r["cumpl"], f"Sucursal {r['id_sucursal']}",
                   f"{entidad} · {fmt_money(r['real'])}"),
            width="stretch",
        )


# ------------------------------------------------------------
# Barras mensuales real vs meta
# ------------------------------------------------------------
def _barras(comp: pd.DataFrame):
    fig = go.Figure()
    for suc in sorted(comp["id_sucursal"].unique()):
        d = comp[comp["id_sucursal"] == suc].sort_values("mes")
        fig.add_trace(go.Bar(
            x=d["mes"], y=d["real_ventas"], name=f"Real {suc}",
            marker_color=PALETA_SUCURSAL.get(suc, COLOR_DEFAULT), opacity=0.9,
            customdata=d["cumplimiento"],
            hovertemplate="%{x|%b %Y}<br>Real: $%{y:,.0f}<br>"
            "Cumplimiento: %{customdata:.1%}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=d["mes"], y=d["meta_ventas"], name=f"Meta {suc}",
            mode="lines+markers", line=dict(color=PALETA_SUCURSAL.get(suc, COLOR_DEFAULT), width=2, dash="dot"),
            marker=dict(size=4),
            hovertemplate="%{x|%b %Y}<br>Meta: $%{y:,.0f}<extra></extra>",
        ))
    fig.update_layout(
        **_template(), height=420, barmode="group",
        legend=dict(orientation="h", y=1.12, x=0),
        yaxis=dict(tickformat=",.0f", title="Ventas ($)"),
        xaxis=dict(title="", tickformat="%b %Y"),
        title=dict(text="Ventas reales vs meta mensual", font=dict(size=14)),
    )
    return fig


# ------------------------------------------------------------
# Serie temporal de cumplimiento
# ------------------------------------------------------------
def _serie_cumplimiento(comp: pd.DataFrame):
    """Cumplimiento mensual por sucursal con umbral de alerta del 90%."""
    fig = go.Figure()
    for suc in sorted(comp["id_sucursal"].unique()):
        d = comp[comp["id_sucursal"] == suc].sort_values("mes")
        fig.add_trace(go.Scatter(
            x=d["mes"], y=d["cumplimiento"], name=f"{suc}",
            mode="lines+markers",
            line=dict(color=PALETA_SUCURSAL.get(suc, COLOR_DEFAULT), width=2.4),
            marker=dict(size=6),
            customdata=d[["real_ventas", "meta_ventas"]],
            hovertemplate="%{x|%b %Y}<br>Cumplimiento: %{y:.1%}"
            "<br>Real: $%{customdata[0]:,.0f}<br>Meta: $%{customdata[1]:,.0f}"
            "<extra></extra>",
        ))
    fig.add_hrect(
        y0=UMBRAL_CRITICO, y1=UMBRAL_VIGILANCIA, fillcolor=COLOR_WARNING,
        opacity=0.08, line_width=0,
    )
    fig.add_hline(
        y=1.0, line_dash="dash", line_color="white",
        annotation_text="Meta (100%)", annotation_position="top left",
    )
    fig.add_hline(
        y=UMBRAL_CRITICO, line_dash="dot", line_color=COLOR_CRITICAL,
        annotation_text=f"Alerta crítica ({UMBRAL_CRITICO:.0%})",
        annotation_position="bottom left",
        annotation_font_color=COLOR_CRITICAL,
    )
    fig.update_layout(
        **_template(), height=380,
        legend=dict(orientation="h", y=1.12, x=0),
        yaxis=dict(tickformat=".0%", title="Cumplimiento"),
        xaxis=dict(title="", tickformat="%b %Y"),
        title=dict(text="Cumplimiento mensual por sucursal", font=dict(size=14)),
    )
    return fig


# ------------------------------------------------------------
# Tabla detalle
# ------------------------------------------------------------
def _tabla(comp: pd.DataFrame, sucursales: pd.DataFrame):
    tabla = comp.copy()
    tabla = tabla.merge(
        sucursales[["id_sucursal", "entidad"]], on="id_sucursal"
    )
    tabla["Mes"] = tabla["mes"].dt.strftime("%b %Y")
    tabla["Sucursal"] = tabla["id_sucursal"]
    tabla["Entidad"] = tabla["entidad"]
    tabla["Real"] = tabla["real_ventas"].map(lambda x: f"${x:,.0f}")
    tabla["Meta"] = tabla["meta_ventas"].map(lambda x: f"${x:,.0f}")
    tabla["Cumplimiento"] = tabla["cumplimiento"].map(lambda x: f"{x:.1%}")
    tabla["Varianza"] = tabla["varianza"].map(lambda x: f"${x:+,.0f}")
    tabla["Estado"] = tabla["cumplimiento"].map(
        lambda x: {"ok": "✅ Meta", "warn": "⚠️ Vigilar", "crit": "🚨 Alerta"}[_estado(x)]
    )
    return tabla[["Mes", "Sucursal", "Entidad", "Real", "Meta", "Cumplimiento",
                  "Varianza", "Estado"]]


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df: pd.DataFrame, presupuesto: pd.DataFrame, sucursales: pd.DataFrame,
           fecha_min, fecha_max, sucursales_sel) -> None:
    header(
        "Presupuesto de Ventas vs Real",
        "La meta financiera mensual asignada a cada sucursal frente a lo "
        "efectivamente facturado.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    comp = _real_vs_meta(df, presupuesto, sucursales_sel)
    if comp.empty:
        st.info("No hay presupuesto definido para el periodo seleccionado.")
        return

    # ---- KPIs ----
    total_real = comp["real_ventas"].sum()
    total_meta = comp["meta_ventas"].sum()
    cumpl_global = total_real / total_meta if total_meta else 0
    meses_bajo_meta = comp[comp["cumplimiento"] < 1.0]
    meses_criticos = comp[comp["cumplimiento"] < UMBRAL_CRITICO]
    mejor = comp.loc[comp["cumplimiento"].idxmax()]
    peor = comp.loc[comp["cumplimiento"].idxmin()]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Ventas reales", fmt_money(total_real),
        f"vs meta {fmt_money(total_meta)}",
        help="Facturación real acumulada del periodo.",
    )
    c2.metric(
        "Cumplimiento global", f"{cumpl_global:.1%}",
        f"{total_real - total_meta:+,.0f} vs meta",
        delta_color="normal" if cumpl_global >= UMBRAL_CRITICO else "inverse",
        help="Real / Meta acumulados del periodo seleccionado.",
    )
    c3.metric(
        "Meses bajo meta", f"{len(meses_bajo_meta)}",
        f"de {len(comp)} · {len(meses_criticos)} críticos",
        delta_color="inverse" if len(meses_bajo_meta) else "normal",
        help=f"Meses con cumplimiento < 100% de la meta. Críticos (<{UMBRAL_CRITICO:.0%}) "
             f"disparan la alerta M5.",
    )
    c4.metric(
        "Mejor mes", mejor["mes"].strftime("%b %Y"),
        f"{mejor['cumplimiento']:.0%} · {mejor['id_sucursal']}",
        help="Mes con mayor cumplimiento en el periodo.",
    )

    # ---- Gauges por sucursal ----
    st.markdown("#### 🎯 Cumplimiento por sucursal (periodo acumulado)")
    _gauges(comp, sucursales)

    # ---- Barras + serie de cumplimiento ----
    c_barras, c_serie = st.columns([1.15, 0.85])
    with c_barras:
        st.plotly_chart(_barras(comp), width="stretch")
    with c_serie:
        st.plotly_chart(_serie_cumplimiento(comp), width="stretch")

    # ---- Tabla detalle ----
    st.markdown("#### 📋 Detalle mensual por sucursal")
    st.dataframe(_tabla(comp, sucursales), width="stretch", hide_index=True)
