# ============================================================
# M3 · CRM & MARKETING — Proyecto "El Errante"
# Pestaña 3 del dashboard (DOCUMENTO_MAESTRO §6 · M3 y M8)
# ------------------------------------------------------------
# Contenido:
#   • Embudo de clientes por nivel (Plata/Oro/VIP) y por sucursal
#   • Correlación ancla -> bebidas (regla M3 de la especificación)
#   • Detección de deserción (churn): Oro/VIP sin visita en 45 días (M8)
# Reglas de negocio:
#   • 40% de los tickets están ligados al CRM (programa de lealtad)
#   • Un cliente Oro/VIP sin compra en 45 días = "Riesgo de Deserción"
#   • La fecha de corte de churn = fecha máxima del rango seleccionado
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_CRITICAL, COLOR_SUCCESS, COLOR_WARNING, header

UMBRAL_CHURN_DIAS = 45  # DOCUMENTO_MAESTRO §6 · M8
NIVEL_COLOR = {"Plata": "#94A3B8", "Oro": COLOR_WARNING, "VIP": "#E6C45C"}


def _template() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor="#13315C", font_color="#F8FAFC"),
    )


# ------------------------------------------------------------
# Embudo de clientes
# ------------------------------------------------------------
def _embudo_nivel(cli: pd.DataFrame):
    """Embudo: clientes registrados → activos en el periodo → Oro/VIP activos."""
    registrados = len(cli)
    activos = cli["tiene_visita"].sum()
    oro_vip = cli[(cli["nivel"].isin(["Oro", "VIP"]))]["tiene_visita"].sum()
    fig = go.Figure(go.Funnel(
        y=["Registrados", "Activos en periodo", "Oro/VIP activos"],
        x=[registrados, activos, oro_vip],
        textinfo="value+percent initial",
        marker=dict(color=[COLOR_SUCCESS, "#2E9E97", "#E6C45C"]),
        connector=dict(line=dict(color="rgba(255,255,255,0.2)", width=1)),
        hovertemplate="%{y}: %{x:,} clientes<extra></extra>",
    ))
    fig.update_layout(
        **_template(),
        height=340,
        funnelgap=0.12,
        title=dict(text="Embudo de clientes del programa", font=dict(size=14)),
    )
    return fig


def _barras_sucursal_nivel(cli: pd.DataFrame):
    """Barras agrupadas: clientes activos por sucursal y nivel."""
    activos = cli[cli["tiene_visita"]]
    orden_nivel = ["Plata", "Oro", "VIP"]
    fig = px.bar(
        activos,
        x="id_sucursal",
        color="nivel",
        category_orders={"nivel": orden_nivel},
        color_discrete_map=NIVEL_COLOR,
        labels={"id_sucursal": "Sucursal", "count": "Clientes activos", "nivel": "Nivel"},
        custom_data=["id_sucursal", "nivel"],
    )
    fig.update_traces(
        hovertemplate="<b>Sucursal %{customdata[0]} · %{customdata[1]}</b><br>"
        "Clientes activos: %{y}<extra></extra>",
    )
    fig.update_layout(
        **_template(),
        height=340,
        barmode="group",
        legend=dict(orientation="h", y=1.12, x=0),
        title=dict(text="Clientes activos por sucursal y nivel", font=dict(size=14)),
    )
    return fig


# ------------------------------------------------------------
# Correlación ancla -> bebidas (regla M3)
# ------------------------------------------------------------
def _correlacion_ancla(df: pd.DataFrame):
    """Compara tickets con/sin Sopa Ancla: líneas de bebidas y variedades.

    Regla de negocio: las mesas que consumen el ancla terminan ordenando
    más de 2 variedades de cervezas o aguas preparadas, salvando el margen
    del ticket familiar.
    """
    ancla_id = df.loc[df["es_ancla"], "id_producto"].iloc[0] if df["es_ancla"].any() else None
    if ancla_id is None:
        return None, None, None

    tickets_ancla = set(df[df["id_producto"] == ancla_id]["id_ticket"].unique())
    bebidas = df[df["categoria"] == "Bebida"]
    variedades = (
        bebidas.groupby("id_ticket")["id_producto"]
        .nunique()
        .rename("variedades_bebida")
    )
    resumen = variedades.reset_index()
    resumen["con_ancla"] = resumen["id_ticket"].isin(tickets_ancla)
    resumen["mas_2_variedades"] = resumen["variedades_bebida"] > 2

    # Promedios y % de tickets con >2 variedades
    stats = resumen.groupby("con_ancla").agg(
        variedades_prom=("variedades_bebida", "mean"),
        pct_mas_2=("mas_2_variedades", "mean"),
    ).reindex([False, True])
    stats.index = ["Sin ancla", "Con ancla"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stats.index, y=stats["variedades_prom"], name="Variedades de bebidas (prom.)",
        marker_color=[COLOR_WARNING, COLOR_SUCCESS],
        customdata=stats["pct_mas_2"],
        hovertemplate="%{x}<br>Variedades prom.: %{y:.2f}<br>"
        "% con >2 variedades: %{customdata:.0%}<extra></extra>",
    ))
    fig.add_hline(
        y=2, line_dash="dash", line_color="white",
        annotation_text=">2 variedades (regla M3)",
        annotation_position="top left",
    )
    fig.update_layout(
        **_template(),
        height=360,
        showlegend=False,
        yaxis=dict(title="Variedades de bebida por mesa"),
        title=dict(text="La Sopa Ancla impulsa el ticket de bebidas", font=dict(size=14)),
    )
    return fig, stats, len(tickets_ancla)


# ------------------------------------------------------------
# Churn (M8)
# ------------------------------------------------------------
def _analisis_churn(df: pd.DataFrame, cli: pd.DataFrame):
    """Días desde la última visita por cliente y detección de riesgo (>45d)."""
    fecha_corte = df["fecha_hora"].max()

    con_cliente = df[df["id_cliente_crm"].notna()]
    ultima_visita = (
        con_cliente.groupby("id_cliente_crm")["fecha_hora"].max().rename("ultima_visita")
    )
    cli = cli.merge(ultima_visita, left_on="id_cliente", right_index=True, how="left")
    cli["dias_sin_visita"] = (fecha_corte - cli["ultima_visita"]).dt.days
    # Clientes sin visita en la ventana = máximo abandono (NaN -> 9999 días)
    cli["dias_sin_visita"] = cli["dias_sin_visita"].fillna(9999)
    cli["en_riesgo"] = (
        cli["nivel"].isin(["Oro", "VIP"]) & (cli["dias_sin_visita"] > UMBRAL_CHURN_DIAS)
    )

    tabla = cli[cli["en_riesgo"]].sort_values("dias_sin_visita", ascending=False)
    tabla = tabla.rename(columns={
        "id_cliente": "ID", "nombre": "Cliente", "nivel": "Nivel",
        "sucursal_frecuente": "Suc.", "frecuencia_visitas_mensual": "Frec. mensual",
        "dias_sin_visita": "Días sin visita",
    })
    return fecha_corte, tabla[
        ["ID", "Cliente", "Nivel", "Suc.", "Frec. mensual", "Días sin visita"]
    ]


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df: pd.DataFrame, cli: pd.DataFrame, sucursales_sel: list) -> None:
    header(
        "CRM & Marketing",
        "Inteligencia de clientes: lealtad, correlación del ancla con bebidas "
        "y prevención de deserción.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    # ---- Preparar clientes: ¿tuvieron visita en el periodo? ----
    clientes_visita = set(df[df["id_cliente_crm"].notna()]["id_cliente_crm"].unique())
    cli = cli.copy()
    cli["tiene_visita"] = cli["id_cliente"].isin(clientes_visita)
    cli["id_sucursal"] = cli["sucursal_frecuente"]

    # ---- KPIs ----
    fecha_corte, tabla_churn = _analisis_churn(df, cli)
    n_riesgo = len(tabla_churn)
    n_oro_vip = len(cli[cli["nivel"].isin(["Oro", "VIP"])])
    activos = int(cli["tiene_visita"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes registrados", f"{len(cli):,}", help="Programa de lealtad (CRM).")
    c2.metric("Activos en el periodo", f"{activos:,}",
              f"{(activos/len(cli)):.0%} del padrón",
              help="Clientes con al menos una compra en el periodo.")
    c3.metric("Oro/VIP en riesgo", f"{n_riesgo:,}",
              f"de {n_oro_vip:,} Oro/VIP", delta_color="inverse",
              help=f"Sin visita en los últimos {UMBRAL_CHURN_DIAS} días al corte "
                   f"{fecha_corte:%d-%m-%Y}.")
    c4.metric("Tasa de deserción", f"{(n_riesgo/n_oro_vip):.0%}" if n_oro_vip else "—",
              help="Proporción de clientes de alto valor en riesgo de deserción.")

    # ---- Embudo + barras por sucursal ----
    c_embudo, c_barras = st.columns([1, 1])
    with c_embudo:
        st.plotly_chart(_embudo_nivel(cli), width="stretch")
    with c_barras:
        st.plotly_chart(_barras_sucursal_nivel(cli), width="stretch")

    # ---- Correlación ancla -> bebidas ----
    st.markdown("#### 🍤🍹 Correlación: la Sopa Ancla impulsa el ticket de bebidas")
    fig_corr, stats, n_tickets_ancla = _correlacion_ancla(df)
    if fig_corr is not None:
        c_corr, c_det = st.columns([1.2, 0.8])
        with c_corr:
            st.plotly_chart(fig_corr, width="stretch")
        with c_det:
            st.markdown(
                f"**Hipótesis de negocio (regla M3):** las mesas que piden la "
                f"Sopa de Mariscos terminan ordenando más variedades de bebidas."
            )
            con = stats.loc["Con ancla"]
            sin = stats.loc["Sin ancla"]
            st.metric("Variedades con ancla", f"{con['variedades_prom']:.2f}",
                      f"vs {sin['variedades_prom']:.2f} sin ancla")
            st.metric("% mesas con >2 variedades", f"{con['pct_mas_2']:.0%}",
                      f"vs {sin['pct_mas_2']:.0%} sin ancla",
                      delta_color="normal")
            st.caption(
                f"Basado en {n_tickets_ancla:,} tickets con ancla en el periodo."
            )
    else:
        st.info("No hay ventas de la Sopa de Mariscos en el periodo.")

    # ---- Churn ----
    st.markdown("#### 🚨 Prevención de deserción (churn)")
    st.caption(
        f"Corte de análisis: **{fecha_corte:%d-%m-%Y}** (última fecha del rango "
        f"seleccionado). Clientes Oro/VIP sin visita en {UMBRAL_CHURN_DIAS} días."
    )
    if not tabla_churn.empty:
        c_tab, c_est = st.columns([1.2, 0.8])
        with c_tab:
            st.dataframe(tabla_churn, width="stretch", hide_index=True)
        with c_est:
            st.warning(
                "**Plan de reactivación:** enviar incentivo personalizado "
                "«Sopa de Mariscos gratis en el consumo de 2 bebidas de "
                "marketing» a los clientes en riesgo."
            )
            st.markdown(
                f"<span style='color:{COLOR_CRITICAL}; font-weight:600;'>"
                f"{n_riesgo} clientes de alto valor requieren acción "
                f"preventiva antes de los 45 días.</span>",
                unsafe_allow_html=True,
            )
    else:
        st.success(
            "Sin clientes Oro/VIP en riesgo de deserción en este corte. 🎉"
        )
