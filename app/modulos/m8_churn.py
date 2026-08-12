# ============================================================
# M8 · ANÁLISIS DE DESERCIÓN DE CLIENTES (CHURN) — "El Errante"
# Pestaña 8 del dashboard (DOCUMENTO_MAESTRO §6 · M8)
# ------------------------------------------------------------
# Churn rate con FECHA DE CORTE CONFIGURABLE (auditable) y umbral
# de días sin visita:
#   • Días desde la última visita por cliente (Oro/VIP prioritarios)
#   • Fecha de corte: por defecto la última fecha del dataset
#     (31-dic-2025) — el parámetro se expone para reproducibilidad
#   • Clientes sin visita en el corte reciben 9999 días (en riesgo)
#   • Valor anual en riesgo = gasto anualizado de los clientes en riesgo
# Contexto de negocio: cuesta 5× más atraer un cliente nuevo en
# Coahuila que retener a un VIP en Nuevo León.
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_CRITICAL, COLOR_SUCCESS, COLOR_WARNING, header
from utils import fmt_money

UMBRAL_DIAS_DEFAULT = 45  # DOCUMENTO_MAESTRO §6 · M8
COSTO_ADQUISICION_X = 5   # adquirir cuesta 5× más que retener (regla de negocio)


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
# Análisis de churn
# ------------------------------------------------------------
def _analisis_churn(
    clientes: pd.DataFrame, df: pd.DataFrame, fecha_corte, umbral_dias: int
) -> pd.DataFrame:
    """Clientes con días sin visita hasta el corte.

    Un cliente sin ninguna visita registrada en el periodo (o cuya
    última visita no existe) recibe 9999 días → contabilizado en riesgo
    (consistente con M3/M5).
    """
    con_cliente = df[df["id_cliente_crm"].notna()]
    ultima = con_cliente.groupby("id_cliente_crm")["fecha_hora"].max()
    cli = clientes.copy()
    cli = cli.merge(ultima.rename("ultima_visita"), left_on="id_cliente",
                    right_index=True, how="left")
    cli["dias_sin_visita"] = (
        pd.Timestamp(fecha_corte) - cli["ultima_visita"]
    ).dt.days
    cli["dias_sin_visita"] = cli["dias_sin_visita"].fillna(9999)

    # Valor anual estimado: gasto total ÷ años desde alta (o 0.5 mínimo)
    gasto = con_cliente.groupby("id_cliente_crm")["monto"].sum().rename("gasto_total")
    cli = cli.merge(gasto, left_on="id_cliente", right_index=True, how="left")
    anos = np.maximum(
        (pd.Timestamp(fecha_corte) - pd.to_datetime(cli["fecha_alta"])).dt.days / 365.0,
        0.5,
    ).fillna(0.5)  # clientes sin fecha de alta válida: 0.5 años mínimos
    cli["valor_anual"] = cli["gasto_total"].fillna(0) / anos
    cli["en_riesgo"] = (
        cli["nivel"].isin(["Oro", "VIP"]) & (cli["dias_sin_visita"] > umbral_dias)
    )
    return cli


def _evolucion_churn(
    clientes: pd.DataFrame, df: pd.DataFrame, umbral_dias: int
) -> pd.DataFrame:
    """Churn rate por corte mensual (evolución del riesgo en el tiempo)."""
    con_cliente = df[df["id_cliente_crm"].notna()]
    if con_cliente.empty:
        return pd.DataFrame()
    ultima = con_cliente.groupby("id_cliente_crm")["fecha_hora"].max()
    uo = clientes[clientes["nivel"].isin(["Oro", "VIP"])]
    uo = uo.merge(ultima.rename("ultima_visita"), left_on="id_cliente",
                  right_index=True, how="left")
    cortes = pd.date_range(con_cliente["fecha_hora"].min().normalize(),
                           con_cliente["fecha_hora"].max().normalize(), freq="ME")
    filas = []
    for corte in cortes:
        dias = (corte - uo["ultima_visita"]).dt.days.fillna(9999)
        n_riesgo = int((dias > umbral_dias).sum())
        filas.append({"corte": corte, "en_riesgo": n_riesgo,
                      "total": len(uo)})
    ev = pd.DataFrame(filas)
    if len(ev):
        ev["tasa"] = ev["en_riesgo"] / ev["total"]
    return ev


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------
def _histograma_dias(cli: pd.DataFrame, umbral_dias: int) -> go.Figure:
    """Distribución de días sin visita (solo clientes con visita conocida)."""
    d = cli[cli["dias_sin_visita"] < 9999]["dias_sin_visita"]
    fig = go.Figure(go.Histogram(
        x=d, nbinsx=40, marker_color=COLOR_WARNING, opacity=0.85,
        hovertemplate="%{x:.0f} días: %{y} clientes<extra></extra>",
    ))
    fig.add_vline(
        x=umbral_dias, line_dash="dash", line_color=COLOR_CRITICAL, line_width=2,
        annotation_text=f"Umbral {umbral_dias} días",
        annotation_font_color=COLOR_CRITICAL,
    )
    fig.update_layout(
        **_template(), height=360,
        xaxis=dict(title="Días desde la última visita (clientes activos)"),
        yaxis=dict(title="Clientes"),
        title=dict(text="Distribución de antigüedad de la última visita",
                   font=dict(size=14)),
    )
    return fig


def _evolucion(ev: pd.DataFrame) -> go.Figure:
    """Serie temporal del churn rate mensual."""
    fig = go.Figure(go.Scatter(
        x=ev["corte"], y=ev["tasa"], mode="lines+markers",
        line=dict(color=COLOR_CRITICAL, width=2.6), marker=dict(size=6),
        hovertemplate="%{x|%b %Y}<br>Churn: %{y:.1%}<extra></extra>",
    ))
    fig.update_layout(
        **_template(), height=360,
        yaxis=dict(tickformat=".0%", title="Churn rate (Oro/VIP)"),
        xaxis=dict(title="Fecha de corte"),
        title=dict(text="Evolución mensual del churn rate de clientes de alto valor",
                   font=dict(size=14)),
    )
    return fig


def _barras_por_nivel(cli: pd.DataFrame) -> go.Figure:
    """Clientes en riesgo por nivel."""
    agg = (
        cli.groupby("nivel")
        .agg(total=("id_cliente", "size"), riesgo=("en_riesgo", "sum"))
        .reindex(["Plata", "Oro", "VIP"])
        .reset_index()
    )
    agg["total"] = agg["total"].fillna(0)
    agg["riesgo"] = agg["riesgo"].fillna(0)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["nivel"], y=agg["total"], name="Total",
        marker_color="#13315C", opacity=0.9,
        hovertemplate="%{x}: %{y} clientes<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=agg["nivel"], y=agg["riesgo"], name="En riesgo",
        marker_color=COLOR_CRITICAL, opacity=0.9,
        hovertemplate="%{x}: %{y} en riesgo<extra></extra>",
    ))
    fig.update_layout(
        **_template(), height=360, barmode="overlay",
        yaxis=dict(title="Clientes"),
        title=dict(text="Clientes en riesgo por nivel", font=dict(size=14)),
    )
    return fig


def _tabla_riesgo(cli: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    """Clientes Oro/VIP en riesgo ordenados por valor anual."""
    t = cli[cli["en_riesgo"]].sort_values("valor_anual", ascending=False).head(top_n)
    if t.empty:
        return t
    t = t.copy()
    t["Cliente"] = t["nombre"]
    t["Nivel"] = t["nivel"]
    t["Sucursal"] = t["sucursal_frecuente"]
    d = t["dias_sin_visita"].clip(upper=999).astype(int)
    t["Días sin visita"] = np.where(d >= 999, "999+", d.astype(str))
    t["Valor anual"] = t["valor_anual"].map(lambda x: f"${x:,.0f}")
    t["Plan"] = "🎁 Sopa gratis + 2 bebidas marketing"
    return t[["Cliente", "Nivel", "Sucursal", "Días sin visita",
              "Valor anual", "Plan"]]


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df, clientes_crm, sucursales, fecha_min, fecha_max,
           sucursales_sel) -> None:
    header(
        "Análisis de Deserción de Clientes",
        "Churn rate de clientes Oro/VIP con fecha de corte configurable. "
        "Cuesta 5× más adquirir un cliente nuevo que retener a uno VIP.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    # ---- Parámetros auditable del análisis ----
    c1, c2 = st.columns([1.2, 1])
    f_min = pd.Timestamp(df["fecha_hora"].min().date())
    f_max = pd.Timestamp(df["fecha_hora"].max().date())
    fecha_corte = c1.date_input(
        "Fecha de corte del análisis",
        value=f_max.date(), min_value=f_min.date(), max_value=f_max.date(),
        help="Clientes sin visita desde esta fecha hasta el umbral se marcan "
             "en riesgo. Por defecto: última fecha del dataset (auditable).",
    )
    umbral_dias = c2.slider(
        "Umbral de churn (días sin visita)", 30, 120, UMBRAL_DIAS_DEFAULT, 5,
        help="Días sin compra a partir de los cuales un cliente Oro/VIP se "
             "considera en riesgo de deserción.",
    )
    st.caption(
        f"📌 **Parámetros**: corte = {fecha_corte} · umbral = {umbral_dias} días. "
        f"Estos valores son parte del análisis y se exponen para reproducibilidad."
    )

    cli = _analisis_churn(clientes_crm, df, fecha_corte, umbral_dias)
    uo = cli[cli["nivel"].isin(["Oro", "VIP"])]
    n_riesgo = int(uo["en_riesgo"].sum())
    valor_riesgo = float(uo.loc[uo["en_riesgo"], "valor_anual"].sum())
    tasa = n_riesgo / len(uo) if len(uo) else 0

    # ---- KPIs ----
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Clientes registrados", f"{len(clientes_crm)}",
        f"{len(uo)} Oro/VIP",
        help="Base total del programa de lealtad.",
    )
    k2.metric(
        "Oro/VIP en riesgo", f"{n_riesgo}",
        f"de {len(uo)}",
        delta_color="inverse" if n_riesgo else "normal",
        help=f"Clientes de alto valor sin compra en los últimos {umbral_dias} días.",
    )
    k3.metric(
        "Tasa de deserción", f"{tasa:.1%}",
        f"corte {fecha_corte}",
        delta_color="inverse" if tasa > 0.2 else "normal",
        help="Porcentaje de la base Oro/VIP en riesgo en la fecha de corte.",
    )
    k4.metric(
        "Valor anual en riesgo", fmt_money(valor_riesgo),
        "si no se retiene",
        help="Gasto anualizado estimado de los clientes en riesgo.",
    )

    # ---- Gráficos ----
    c_hist, c_evo = st.columns(2)
    with c_hist:
        st.plotly_chart(_histograma_dias(cli, umbral_dias), width="stretch")
    with c_evo:
        ev = _evolucion_churn(clientes_crm, df, umbral_dias)
        if not ev.empty:
            st.plotly_chart(_evolucion(ev), width="stretch")

    # ---- Por nivel + contexto de negocio ----
    c_niv, c_ctx = st.columns([1, 1])
    with c_niv:
        st.plotly_chart(_barras_por_nivel(cli), width="stretch")
    with c_ctx:
        st.markdown("#### 💡 Contexto de negocio")
        st.markdown(
            f"- Retener un cliente **VIP en Nuevo León** cuesta 5× menos que "
            f"adquirir un cliente nuevo en **Coahuila**."
        )
        st.markdown(
            f"- Si se retiene al **{n_riesgo} cliente(s) en riesgo**, se "
            f"protegen **{fmt_money(valor_riesgo)}** de valor anual estimado."
        )
        st.markdown(
            f"- Plan de reactivación activo: **Sopa de Mariscos gratis con 2 "
            f"bebidas de marketing** para Oro/VIP sin compra en "
            f"{umbral_dias} días."
        )
        st.caption(
            "El churn se calcula sobre la **fecha de corte configurable** y "
            "no sobre la fecha real del sistema, porque el histórico es una "
            "simulación 2024-2025 (decisión documentada en el maestro §6 · M8)."
        )

    # ---- Tabla de clientes en riesgo ----
    st.markdown("#### 👥 Clientes de alto valor en riesgo (por valor anual)")
    tabla = _tabla_riesgo(cli)
    if tabla.empty:
        st.success("Sin clientes Oro/VIP en riesgo para el corte y umbral actuales.")
    else:
        st.dataframe(tabla, width="stretch", hide_index=True)
        st.caption(
            f"Mostrando los {len(tabla)} de mayor valor. El resto del segmento "
            f"en riesgo ({n_riesgo - len(tabla)} clientes) queda registrado "
            f"en el detalle del CRM."
        )
