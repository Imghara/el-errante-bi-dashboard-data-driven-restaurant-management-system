# ============================================================
# M10 · AUDITORÍA DE CALIDAD DEL PROGRAMA DE INCENTIVOS (ANTI-FRAUDE)
# Pestaña 10 del dashboard (DOCUMENTO_MAESTRO §6 · M10)
# ------------------------------------------------------------
# Contrasta las COMISIONES ganadas por cada mesero con la
# CALIFICACIÓN DEL SERVICIO que otorgan los clientes en las
# encuestas ligadas a sus tickets. Detecta "canibalización" /
# venta impositiva: crecimiento de comisiones a costa de la
# experiencia del cliente.
#   • Motor de comisiones REUTILIZADO de M2 (_calc_incentivos)
#   • Estados: Saludable ✅ · Vigilar ⚠️ (calif < 3.5) ·
#     Crítico 🚨 (calif < 3.5 Y comisión ≥ mediana = venta impositiva)
#   • Zona de riesgo en el scatter: altas comisiones + baja calificación
# Regla de negocio (maestro §6 M10): si un mesero es top en bebidas
# pero sus mesas reportan "servicio impositivo", el indicador se
# enciende en amarillo/rojo para alertar crecimiento NO sano.
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modulos.m2_incentivos import PALETA_SUCURSAL, _calc_incentivos  # motor M2
from styles import (
    COLOR_CRITICAL,
    COLOR_PRIMARY_LIGHT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    header,
)
from utils import fmt_money, fmt_pct

# Política estándar auditada (la del programa M2 por defecto)
TASA_COMISION = 0.05
MULT_ALTO = 1.5
UMBRAL_SERVICIO = 3.5   # config.UMBRAL_SERVICIO_SALUDABLE (maestro §6 M10)

COLOR_ESTADO = {
    "Saludable": COLOR_SUCCESS,
    "Vigilar": COLOR_WARNING,
    "Crítico": COLOR_CRITICAL,
    "Sin datos": "#94A3B8",
}


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
# Auditoría por mesero
# ------------------------------------------------------------
def _auditoria(df: pd.DataFrame, encuestas: pd.DataFrame,
               meseros: pd.DataFrame) -> pd.DataFrame:
    """Comisiones + encuestas por mesero, con estado de salud del incentivo."""
    d = _calc_incentivos(df, TASA_COMISION, MULT_ALTO)

    # Comisiones (solo líneas incentivadas) y ventas
    inc = d[d["comision_linea"] > 0]
    agg = inc.groupby("id_mesero").agg(
        comision=("comision_linea", "sum"),
        ventas=("monto", "sum"),
        tickets=("id_ticket", "nunique"),
    )
    beb = d[d["categoria"] == "Bebida"].groupby("id_mesero")["monto"].sum()
    agg = agg.join(beb.rename("ventas_bebidas")).fillna(0.0)
    agg["mix_bebidas"] = agg["ventas_bebidas"] / agg["ventas"].replace(0, np.nan)

    # Encuestas ligadas a tickets del periodo filtrado (respeta filtros globales)
    tickets_validos = set(df["id_ticket"].unique())
    enc = encuestas[encuestas["id_ticket"].isin(tickets_validos)].copy()
    enc["es_negativo"] = enc["sentimiento"] == "negativo"
    cal = enc.groupby("id_mesero").agg(
        calif=("calificacion_servicio", "mean"),
        n_encuestas=("id_encuesta", "count"),
        pct_negativo=("es_negativo", "mean"),
    )
    comentario_neg = (
        enc[enc["es_negativo"]]
        .groupby("id_mesero")["comentario"]
        .agg(lambda s: s.mode().iloc[0] if len(s) else "")
        .rename("comentario")
    )

    aud = (
        meseros[["id_mesero", "nombre", "sucursal"]]
        .merge(agg, on="id_mesero", how="left")
        .merge(cal, on="id_mesero", how="left")
        .merge(comentario_neg, on="id_mesero", how="left")
    )
    aud[["comision", "ventas", "tickets", "ventas_bebidas"]] = aud[
        ["comision", "ventas", "tickets", "ventas_bebidas"]
    ].fillna(0.0)
    med_comision = aud["comision"].median()

    def estado(fila: pd.Series) -> str:
        if pd.isna(fila["calif"]):
            return "Sin datos"
        # Crítico = venta impositiva: calificación baja CON comisiones reales
        # por encima de la mediana (guarda: sin comisiones no hay "venta")
        if (fila["calif"] < UMBRAL_SERVICIO and fila["comision"] > 0
                and fila["comision"] >= med_comision):
            return "Crítico"
        if fila["calif"] < UMBRAL_SERVICIO:
            return "Vigilar"
        return "Saludable"

    aud["estado"] = aud.apply(estado, axis=1)
    aud["comentario"] = aud["comentario"].fillna("")
    return aud


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------
def _scatter_riesgo(aud: pd.DataFrame, med_comision: float) -> go.Figure:
    """Comisión vs calificación con zona de riesgo (canibalización)."""
    aud = aud[aud["estado"] != "Sin datos"]
    fig = px.scatter(
        aud,
        x="calif",
        y="comision",
        color="estado",
        size="n_encuestas",
        custom_data=["nombre", "sucursal", "comision", "calif", "n_encuestas"],
        color_discrete_map=COLOR_ESTADO,
    )
    # Zona de riesgo: calificación < 3.5 y comisión ≥ mediana
    y_max = max(aud["comision"].max() * 1.08, med_comision * 1.2)
    fig.add_shape(
        type="rect", x0=1, x1=UMBRAL_SERVICIO, y0=med_comision, y1=y_max,
        fillcolor="rgba(231, 76, 60, 0.12)", line=dict(width=0),
    )
    fig.add_vline(
        x=UMBRAL_SERVICIO, line_dash="dash", line_color=COLOR_WARNING,
        annotation_text=f"Servicio saludable {UMBRAL_SERVICIO}",
        annotation_font_color=COLOR_WARNING,
    )
    fig.add_hline(
        y=med_comision, line_dash="dot", line_color="#94A3B8",
        annotation_text=f"Mediana comisión ${med_comision:,.0f}",
        annotation_font_color="#94A3B8",
    )
    fig.add_annotation(
        x=UMBRAL_SERVICIO - 0.75, y=y_max * 0.96, showarrow=False,
        text="🚨 Zona de venta impositiva", font=dict(color=COLOR_CRITICAL, size=12),
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            "Comisión: $%{customdata[2]:,.0f} · Calificación: %{customdata[3]:.2f}<br>"
            "Encuestas: %{customdata[4]}<extra></extra>"
        ),
        marker=dict(opacity=0.88, line=dict(width=1, color="#0B2545")),
    )
    fig.update_layout(
        **_template(), height=430,
        xaxis=dict(title="Calificación media del servicio (1-5)", range=[0.8, 5.2]),
        yaxis=dict(title="Comisión ganada ($)", tickformat=",.0f"),
        title=dict(text="Salud del incentivo: comisiones vs satisfacción del cliente",
                   font=dict(size=14)),
    )
    return fig


def _barras_sucursal(aud: pd.DataFrame) -> go.Figure:
    """Calificación media y % de meseros en riesgo por sucursal."""
    por_suc = aud.groupby("sucursal").agg(
        calif=("calif", "mean"),
        n=("id_mesero", "count"),
        en_riesgo=("estado", lambda s: s.isin(["Vigilar", "Crítico"]).mean()),
    ).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=por_suc["sucursal"], y=por_suc["calif"], name="Calif. media",
        marker_color=[PALETA_SUCURSAL[s] for s in por_suc["sucursal"]],
        opacity=0.9,
        hovertemplate="%{x}: %{y:.2f} de 5<extra></extra>",
    ))
    fig.add_hline(
        y=UMBRAL_SERVICIO, line_dash="dash", line_color=COLOR_WARNING,
        annotation_text=f"Umbral {UMBRAL_SERVICIO}",
        annotation_font_color=COLOR_WARNING,
    )
    fig.update_layout(
        **_template(), height=340,
        yaxis=dict(title="Calificación media", range=[0, 5]),
        title=dict(text="Calificación del servicio por sucursal", font=dict(size=14)),
        showlegend=False,
    )
    return fig


def _histograma_calif(aud: pd.DataFrame) -> go.Figure:
    """Distribución de la calificación media de los meseros."""
    fig = go.Figure(go.Histogram(
        x=aud[aud["estado"] != "Sin datos"]["calif"],
        nbinsx=14, marker_color=COLOR_PRIMARY_LIGHT, opacity=0.9,
        hovertemplate="Calif. %{x:.2f}: %{y} meseros<extra></extra>",
    ))
    fig.add_vline(
        x=UMBRAL_SERVICIO, line_dash="dash", line_color=COLOR_CRITICAL,
        annotation_text="3.5", annotation_font_color=COLOR_CRITICAL,
    )
    fig.update_layout(
        **_template(), height=340,
        xaxis=dict(title="Calificación media del mesero"),
        yaxis=dict(title="Meseros"),
        title=dict(text="Distribución de la calidad de servicio", font=dict(size=14)),
    )
    return fig


def _tabla_auditoria(aud: pd.DataFrame) -> pd.DataFrame:
    t = aud.copy()
    t = t.rename(columns={
        "nombre": "Mesero", "sucursal": "Suc.", "comision": "Comisión",
        "mix_bebidas": "Mix bebidas", "calif": "Calif.", "n_encuestas": "Encuestas",
        "pct_negativo": "% Neg.", "estado": "Estado", "comentario": "Comentario",
    })
    t["Comisión"] = t["Comisión"].map(lambda x: f"${x:,.0f}")
    t["Mix bebidas"] = t["Mix bebidas"].map(lambda x: f"{x:.0%}" if pd.notna(x) else "—")
    t["Calif."] = t["Calif."].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    t["Encuestas"] = t["Encuestas"].fillna(0).astype(int)
    t["% Neg."] = t["% Neg."].map(lambda x: f"{x:.0%}" if pd.notna(x) else "—")
    t["Estado"] = t["Estado"].map({
        "Saludable": "✅ Saludable", "Vigilar": "⚠️ Vigilar",
        "Crítico": "🚨 Crítico", "Sin datos": "—",
    })
    return t[["Mesero", "Suc.", "Comisión", "Mix bebidas", "Calif.", "Encuestas",
              "% Neg.", "Estado", "Comentario"]]


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df, meseros, encuestas, sucursales_sel) -> None:
    header(
        "Auditoría de Calidad del Programa de Incentivos",
        "Contrasta las comisiones ganadas con la satisfacción del cliente para "
        "detectar venta impositiva: crecimiento que no es sano a largo plazo.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    aud = _auditoria(df, encuestas, meseros)
    aud_suc = aud[aud["sucursal"].isin(sucursales_sel)]
    med_comision = float(aud_suc["comision"].median())

    # Sin encuestas ligadas al periodo -> no hay auditoría que mostrar
    if (aud_suc["estado"] != "Sin datos").sum() == 0:
        st.info(
            "Sin encuestas de servicio ligadas a tickets en el periodo y "
            "sucursales seleccionados. Amplía el rango de fechas para auditar "
            "la salud del programa de incentivos."
        )
        return

    n_total = len(aud_suc)
    n_sin_datos = int((aud_suc["estado"] == "Sin datos").sum())
    n_con_enc = n_total - n_sin_datos
    n_salud = int((aud_suc["estado"] == "Saludable").sum())
    n_crit = int((aud_suc["estado"] == "Crítico").sum())
    n_vig = int((aud_suc["estado"] == "Vigilar").sum())
    # ---- KPIs ----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Meseros auditados", f"{n_total}",
        f"{n_total - n_salud} con bandera",
        help="Los 48 meseros del programa, con sus encuestas ligadas a ticket.",
    )
    c2.metric(
        "Salud del incentivo", f"{n_salud / n_con_enc:.0%}" if n_con_enc else "—",
        f"{n_salud} de {n_con_enc} con encuestas",
        delta_color="normal",
        help="Porcentaje de meseros con encuestas sin bandera de servicio.",
    )
    c3.metric(
        "En vigilancia", f"{n_vig + n_crit}",
        f"{n_crit} críticos · {n_vig} a vigilar",
        delta_color="inverse",
        help="Calificación media < 3.5 (umbral de servicio saludable).",
    )
    n_neg_total = int(
        aud_suc["pct_negativo"].fillna(0).mul(aud_suc["n_encuestas"].fillna(0)).sum()
    )
    c4.metric(
        "Comentarios negativos", f"{n_neg_total:,}",
        "ligados a tickets auditados",
        delta_color="inverse",
        help="Encuestas negativas ('servicio impositivo', 'atención no agradable').",
    )

    st.caption(
        f"Política auditada: comisión {TASA_COMISION:.0%} + multiplicador "
        f"{MULT_ALTO:.1f}x en bebidas/variantes de alto ROI (igual que M2). "
        f"La zona roja del scatter marca la **venta impositiva**: comisión ≥ "
        f"mediana (${med_comision:,.0f}) con calificación < {UMBRAL_SERVICIO}."
    )

    # ---- Scatter de riesgo ----
    st.plotly_chart(_scatter_riesgo(aud_suc, med_comision), width="stretch")

    # ---- Por sucursal + distribución ----
    c_bar, c_hist = st.columns(2)
    with c_bar:
        st.plotly_chart(_barras_sucursal(aud_suc), width="stretch")
    with c_hist:
        st.plotly_chart(_histograma_calif(aud_suc), width="stretch")

    # ---- Banderas de venta impositiva ----
    st.markdown("#### 🚨 Banderas de venta impositiva (crecimiento NO sano)")
    criticos = aud_suc[aud_suc["estado"] == "Crítico"].sort_values(
        "comision", ascending=False
    )
    if criticos.empty:
        st.success(
            "Sin meseros en zona crítica: el crecimiento de comisiones va "
            "acompañado de buen servicio en todo el equipo."
        )
    else:
        for _, r in criticos.head(6).iterrows():
            with st.expander(
                f"🚨 {r['nombre']} · {r['sucursal']} — comisión "
                f"${r['comision']:,.0f} · calificación {r['calif']:.2f}"
            ):
                st.markdown(
                    f"- **Comisión**: {fmt_money(r['comision'])} sobre "
                    f"{fmt_money(r['ventas'])} vendidos ({r['tickets']:,} tickets)."
                )
                st.markdown(
                    f"- **Mix de bebidas**: {fmt_pct(r['mix_bebidas'])} — revisar "
                    f"si la presión de venta de bebidas daña la experiencia."
                )
                st.markdown(
                    f"- **Encuestas**: {int(r['n_encuestas'])} · negativas "
                    f"{fmt_pct(r['pct_negativo'])}."
                )
                if r["comentario"]:
                    st.markdown(f"> 💬 \"{r['comentario']}\"")
                st.markdown(
                    "**Plan**: reducir el multiplicador de bebidas para este "
                    "mesero, rotar sus mesas y acompañar con coaching de servicio "
                    "(maestro §6 · M10)."
                )

    # ---- Tabla completa de auditoría ----
    st.markdown("#### 📋 Expediente completo de los 48 meseros")
    st.dataframe(_tabla_auditoria(aud_suc), width="stretch", hide_index=True)
    st.caption(
        "Estado: ✅ Saludable (calif ≥ 3.5) · ⚠️ Vigilar (calif < 3.5) · "
        "🚨 Crítico (calif < 3.5 y comisión ≥ mediana = venta impositiva). "
        "Las encuestas se cruzan con los tickets del periodo filtrado "
        "(respetan los filtros globales de fecha y sucursal)."
    )
