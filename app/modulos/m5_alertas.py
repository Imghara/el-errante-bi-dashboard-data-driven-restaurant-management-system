# ============================================================
# M5 · SISTEMA DE ALERTAS Y PLANES DE CONTINGENCIA — "El Errante"
# Pestaña 5 del dashboard (DOCUMENTO_MAESTRO §6 · M5)
# ------------------------------------------------------------
# Sistema experto: evalúa 5 reglas de negocio de forma reactiva
# sobre el periodo/sucursales seleccionados:
#   R1 · ROI en Peligro      (ROI alimentos del mes < 45%)
#   R2 · Caída de Meta       (cumplimiento presupuesto < 90%)
#   R3 · Mix Bebidas         (mix bebidas del ticket < 30%)
#   R4 · Churn               (Oro/VIP sin compra en 45 días)
#   R5 · Salud del Incentivo (top meseros en bebidas con calif < 3.5)
# Cada regla activa abre su plan de contingencia (popover).
# Incluye SIMULADOR DE ESCENARIOS DE ESTRÉS: shock de costo de
# marisco, caída de venta de bebidas y caída de demanda general
# para anticipar cuándo se cruzaría cada umbral.
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_CRITICAL, COLOR_SUCCESS, COLOR_WARNING, badge, header

# ------------------------------------------------------------
# Umbrales del sistema experto (DOCUMENTO_MAESTRO §6 · M5 y §11)
# ------------------------------------------------------------
UMBRAL_ROI = 0.45        # ROI categoría alimentos (platillos/mariscos)
UMBRAL_META = 0.90       # cumplimiento presupuesto mensual
UMBRAL_MIX = 0.30        # proporción de ingresos por bebidas
UMBRAL_CHURN_DIAS = 45   # días sin compra de Oro/VIP
UMBRAL_SALUD = 3.5       # calificación promedio de servicio
TOP_SALUD = 10           # top N meseros en venta de bebidas auditados

# Planes de contingencia (texto literal de la especificación)
PLAN_ROI = [
    "1. Incentivo a meseros al 8% solo en Aguas Naturales y Cervezas Artesanales.",
    "2. Ajuste temporal de porciones en variantes secundarias SIN tocar el ancla.",
]
PLAN_META = [
    "1. Campaña CRM: cupones de bebidas vistosas a clientes VIP/Oro (reactivar martes/miércoles).",
    "2. Concurso «Mesero Estrella»: bono en efectivo al que eleve su ticket promedio 15%.",
]
PLAN_MIX = [
    "1. Ofrecer «Bebida de Temporada Vistosa» antes de tomar la orden de la Sopa.",
    "2. Neuromarketing visual: mantelería y pantallas con coctelería de la casa.",
]
PLAN_CHURN = [
    "Enviar incentivo personalizado: Sopa de Mariscos gratis con 2 bebidas de marketing.",
]
PLAN_SALUD = [
    "Bandera amarilla: crecimiento no sano. Supervisar venta impositiva (conversación 1:1).",
]


def _template() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        margin=dict(l=40, r=20, t=45, b=40),
        hoverlabel=dict(bgcolor="#13315C", font_color="#F8FAFC"),
    )


# ------------------------------------------------------------
# Métricas por regla (por mes × sucursal)
# ------------------------------------------------------------
def _roi_alimentos_mensual(df: pd.DataFrame, shock_marisco: float) -> pd.Series:
    """ROI de la categoría Alimentos por mes×sucursal.

    El shock simula el alza del costo mayorista de marisco y se aplica
    sobre los platillos (Principal/Variante); el ancla y bebidas no lo
    reciben (regla de negocio: ancla con costo estable).
    """
    ali = df[df["categoria"] == "Alimento"].copy()
    es_platillo = ali["subcategoria"].isin(["Principal", "Variante"])
    ali["costo_escenario"] = ali["costo_total"].where(
        ~es_platillo, ali["costo_total"] * (1 + shock_marisco)
    )
    g = ali.groupby(["mes_ano", "id_sucursal"])
    return (g["monto"].sum() - g["costo_escenario"].sum()) / g[
        "costo_escenario"
    ].sum()


def _mix_bebidas_mensual(df: pd.DataFrame, caida_bebidas: float) -> pd.Series:
    """Mix de ingresos por bebidas por mes×sucursal (escenario con caída)."""
    tot = df.groupby(["mes_ano", "id_sucursal"])["monto"].sum()
    beb = (
        df[df["categoria"] == "Bebida"]
        .groupby(["mes_ano", "id_sucursal"])["monto"]
        .sum()
    )
    beb_esc = beb * (1 - caida_bebidas)
    return beb_esc / tot


def _cumplimiento_mensual(
    df: pd.DataFrame, presupuesto: pd.DataFrame, caida_demanda: float
) -> pd.Series:
    """Cumplimiento presupuesto (real×(1−caída) / meta) por mes×sucursal."""
    real = df.groupby(["mes_ano", "id_sucursal"])["monto"].sum() * (1 - caida_demanda)
    meta = presupuesto.set_index(["mes_ano", "id_sucursal"])["meta_ventas"]
    idx = real.index.intersection(meta.index)
    return (real.loc[idx] / meta.loc[idx]).dropna()


def _churn(clientes: pd.DataFrame, df: pd.DataFrame, fecha_corte) -> pd.DataFrame:
    """Oro/VIP sin compra en los últimos UMBRAL_CHURN_DIAS días.

    Un cliente sin ninguna visita en el periodo filtrado recibe 9999 días
    (contabilizado como en riesgo), consistente con la corrección de M3.
    """
    con_cliente = df[df["id_cliente_crm"].notna()]
    if con_cliente.empty:
        return pd.DataFrame()
    ultima = con_cliente.groupby("id_cliente_crm")["fecha_hora"].max()
    cli = clientes[clientes["nivel"].isin(["Oro", "VIP"])].copy()
    cli = cli.merge(ultima.rename("ultima_visita"), left_on="id_cliente",
                    right_index=True, how="left")
    cli["dias_sin_visita"] = (pd.Timestamp(fecha_corte) - cli["ultima_visita"]).dt.days
    cli["dias_sin_visita"] = cli["dias_sin_visita"].fillna(9999)
    cli = cli[cli["dias_sin_visita"] > UMBRAL_CHURN_DIAS]
    return cli.sort_values("dias_sin_visita", ascending=False)


def _salud_incentivo(
    df: pd.DataFrame, encuestas: pd.DataFrame, meseros: pd.DataFrame
) -> pd.DataFrame:
    """Top meseros en venta de bebidas vs calificación de servicio.

    Las encuestas se cruzan con los tickets del periodo filtrado para
    respetar los filtros globales (revisión M5).
    """
    if encuestas.empty:
        return pd.DataFrame()
    enc = encuestas[encuestas["id_ticket"].isin(df["id_ticket"])]
    if enc.empty:
        return pd.DataFrame()
    ventas_beb = (
        df[df["categoria"] == "Bebida"]
        .groupby("id_mesero")["monto"]
        .sum()
        .sort_values(ascending=False)
        .head(TOP_SALUD)
    )
    calif = (
        enc.groupby("id_mesero")["calificacion_servicio"]
        .mean()
        .rename("calif_promedio")
    )
    tab = (
        ventas_beb.rename("ventas_bebidas")
        .to_frame()
        .join(calif)
        .merge(meseros[["id_mesero", "nombre", "sucursal"]], on="id_mesero")
        .reset_index(drop=True)
    )
    tab["bandera"] = tab["calif_promedio"] < UMBRAL_SALUD
    return tab


# ------------------------------------------------------------
# Evaluación del sistema experto
# ------------------------------------------------------------
def _estado_regla(violaciones: int, unidades: int, con_vigilancia: bool) -> str:
    if violaciones > 0:
        return "crit"
    if con_vigilancia:
        return "warn"
    if unidades == 0:
        return "warn"
    return "ok"


def _evaluar(
    df: pd.DataFrame,
    presupuesto: pd.DataFrame,
    clientes: pd.DataFrame,
    encuestas: pd.DataFrame,
    meseros: pd.DataFrame,
    fecha_corte,
    shock_marisco: float,
    caida_bebidas: float,
    caida_demanda: float,
) -> list[dict]:
    reglas = []

    # R1 · ROI en Peligro
    roi = _roi_alimentos_mensual(df, shock_marisco)
    if len(roi):
        viol = int((roi < UMBRAL_ROI).sum())
        reglas.append(dict(
            id="roi", icono="🔥",
            nombre="ROI en Peligro",
            umbral=f"< {UMBRAL_ROI:.0%} alimentos",
            valor=f"mín {roi.min():.1%}",
            detalle=f"{viol} mes·sucursal con ROI de alimentos bajo el umbral"
                    f" (shock marisco +{shock_marisco:.0%})",
            violaciones=viol, unidades=len(roi),
            estado=_estado_regla(viol, len(roi),
                                 (roi < UMBRAL_ROI + 0.20).any()),
            plan=PLAN_ROI,
        ))

    # R2 · Caída de Meta Ventas
    cum = _cumplimiento_mensual(df, presupuesto, caida_demanda)
    if len(cum):
        viol = int((cum < UMBRAL_META).sum())
        reglas.append(dict(
            id="meta", icono="📉",
            nombre="Caída de Meta Ventas",
            umbral=f"< {UMBRAL_META:.0%}",
            valor=f"mín {cum.min():.1%}",
            detalle=f"{viol} mes·sucursal bajo el {UMBRAL_META:.0%} de la meta"
                    f" (demanda {caida_demanda:.0%}↓)",
            violaciones=viol, unidades=len(cum),
            estado=_estado_regla(viol, len(cum),
                                 (cum < UMBRAL_META + 0.05).any()),
            plan=PLAN_META,
        ))

    # R3 · Desviación Mix Bebidas
    mix = _mix_bebidas_mensual(df, caida_bebidas)
    if len(mix):
        viol = int((mix < UMBRAL_MIX).sum())
        reglas.append(dict(
            id="mix", icono="🥤",
            nombre="Desviación Mix Bebidas",
            umbral=f"< {UMBRAL_MIX:.0%} del ticket",
            valor=f"mín {mix.min():.1%}",
            detalle=f"{viol} mes·sucursal con mix de bebidas bajo el umbral"
                    f" (bebidas {caida_bebidas:.0%}↓)",
            violaciones=viol, unidades=len(mix),
            estado=_estado_regla(viol, len(mix),
                                 (mix < UMBRAL_MIX + 0.03).any()),
            plan=PLAN_MIX,
        ))

    # R4 · Riesgo de Deserción (Churn)
    churn = _churn(clientes, df, fecha_corte)
    n_churn = len(churn)
    reglas.append(dict(
        id="churn", icono="👥",
        nombre="Riesgo de Deserción",
        umbral=f"Oro/VIP > {UMBRAL_CHURN_DIAS} días",
        valor=f"{n_churn} clientes",
        detalle=f"{n_churn} clientes Oro/VIP sin compra en más de "
                f"{UMBRAL_CHURN_DIAS} días (corte {fecha_corte})",
        violaciones=n_churn, unidades=max(n_churn, 1),
        estado="crit" if n_churn > 0 else "ok",
        plan=PLAN_CHURN,
    ))

    # R5 · Salud del Incentivo
    salud = _salud_incentivo(df, encuestas, meseros)
    if not salud.empty:
        banderas = int(salud["bandera"].sum())
        reglas.append(dict(
            id="salud", icono="⚠️",
            nombre="Salud del Incentivo",
            umbral=f"calif < {UMBRAL_SALUD:.1f}",
            valor=f"{banderas}/{len(salud)} top con bandera",
            detalle=f"{banderas} de los {len(salud)} meseros top en bebidas "
                    f"tienen calificación < {UMBRAL_SALUD:.1f}",
            violaciones=banderas, unidades=len(salud),
            estado=_estado_regla(banderas, len(salud), False),
            plan=PLAN_SALUD,
        ))
    return reglas


# ------------------------------------------------------------
# Visualizaciones de apoyo
# ------------------------------------------------------------
def _heatmap(serie: pd.Series, titulo: str, umbral: float,
             color_ok: str, color_bad: str) -> go.Figure:
    """Heatmap mes×sucursal de una métrica con punto de corte del umbral."""
    tabla = serie.unstack("id_sucursal").sort_index()
    meses = pd.to_datetime(tabla.index + "-01").strftime("%b %y")
    zmax_v = max(float(tabla.values.max()) * 100 * 1.15, 60.0)
    # Fracciones del colorscale derivadas de zmax para garantizar orden
    # creciente (revisión M5): rojo hasta el umbral, ámbar hasta +15pp,
    # verde por encima.
    p_umbral = min((umbral * 100) / zmax_v, 1.0)
    p_ok = min(p_umbral + 0.15, 1.0)
    fig = go.Figure(go.Heatmap(
        z=tabla.values * 100,
        x=[f"S{s.split('S')[-1]}" for s in tabla.columns],
        y=meses,
        colorscale=[
            [0.0, color_bad],
            [p_umbral, color_bad],
            [min(p_umbral + 1e-6, 1.0), "#F5A623"],
            [p_ok, "#F5A623"],
            [min(p_ok + 1e-6, 1.0), color_ok],
            [1.0, color_ok],
        ],
        text=tabla.values.round(1),
        texttemplate="%{text}",
        textfont=dict(size=9, color="#F8FAFC"),
        hovertemplate="%{y} · %{x}<br>%{z:.1f}%<extra></extra>",
        zmin=0, zmax=zmax_v,
    ))
    fig.update_layout(
        **_template(), height=560, yaxis=dict(autorange="reversed"),
        title=dict(text=titulo, font=dict(size=13)),
    )
    return fig


def _resumen_escenario(reglas: list[dict]) -> dict:
    """Cuenta de alertas por severidad para los KPIs."""
    crit = sum(1 for r in reglas if r["estado"] == "crit")
    warn = sum(1 for r in reglas if r["estado"] == "warn")
    ok = sum(1 for r in reglas if r["estado"] == "ok")
    churn = next((r["violaciones"] for r in reglas if r["id"] == "churn"), 0)
    return dict(crit=crit, warn=warn, ok=ok, churn=churn)


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df, presupuesto, sucursales, clientes_crm, encuestas, meseros,
           fecha_min, fecha_max, sucursales_sel) -> None:
    header(
        "Centro de Alertas · Sistema Experto",
        "Las 5 reglas de negocio evaluadas en vivo. Usa el simulador para "
        "anticipar escenarios de estrés y su plan de contingencia.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    # ---- Simulador de escenarios de estrés ----
    with st.expander("🧪 Simulador de escenarios de estrés", expanded=True):
        st.caption(
            "Ajusta los shocks para ver **cuándo se cruzaría cada umbral** "
            "y qué plan de contingencia se activa."
        )
        c1, c2, c3 = st.columns(3)
        shock_marisco = c1.slider(
            "Alza de costo de marisco mayorista",
            0, 25, 0, 1, format="+%d%%",
            help="Afecta el ROI de platillos/mariscos (regla R1).",
        ) / 100
        caida_bebidas = c2.slider(
            "Caída de venta de bebidas (sin campaña)",
            0, 10, 0, 1, format="-%d%%",
            help="Afecta el mix de bebidas (regla R3).",
        ) / 100
        caida_demanda = c3.slider(
            "Caída de demanda general (mercado)",
            0, 10, 0, 1, format="-%d%%",
            help="Afecta el cumplimiento de presupuesto (regla R2).",
        ) / 100

    # ---- Evaluación del sistema experto ----
    reglas = _evaluar(
        df, presupuesto, clientes_crm, encuestas, meseros,
        fecha_max, shock_marisco, caida_bebidas, caida_demanda,
    )
    res = _resumen_escenario(reglas)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "🚨 Alertas activas", f"{res['crit']}",
        "de 5 reglas",
        delta_color="inverse" if res["crit"] else "normal",
        help="Reglas cuyo umbral se cruza con el escenario actual.",
    )
    c2.metric(
        "⚠️ En vigilancia", f"{res['warn']}",
        "cerca del umbral",
        help="Reglas sanas pero con unidades cerca de cruzar el umbral.",
    )
    c3.metric(
        "✅ Reglas sanas", f"{res['ok']}",
        "sin riesgo",
        help="Reglas con holgura respecto al umbral.",
    )
    c4.metric(
        "👥 Clientes en riesgo", f"{res['churn']}",
        "Oro/VIP > 45 días",
        delta_color="inverse" if res["churn"] else "normal",
        help="Clientes de alto valor en riesgo de deserción (R4).",
    )

    # ---- Cards de reglas ----
    st.markdown("#### 🧠 Evaluación de reglas del sistema experto")
    estilos = {
        "crit": ("🚨", COLOR_CRITICAL),
        "warn": ("⚠️", COLOR_WARNING),
        "ok": ("✅", COLOR_SUCCESS),
    }
    iconos_estado = {"crit": "🚨 ACTIVA", "warn": "⚠️ VIGILANCIA",
                     "ok": "✅ SANA"}

    cols = st.columns(3)
    for i, regla in enumerate(reglas):
        with cols[i % 3]:
            simb, color = estilos[regla["estado"]]
            with st.container(border=True):
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;margin-bottom:0.3rem;'>"
                    f"<span style='font-family:Poppins;font-weight:700;font-size:1.02rem;'>"
                    f"{regla['icono']} {regla['nombre']}</span>"
                    f"{badge(regla['estado'], iconos_estado[regla['estado']])}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"margin-bottom:0.25rem;'>"
                    f"<span style='color:#94A3B8;font-size:0.82rem;'>Umbral</span>"
                    f"<span style='font-weight:600;'>{regla['umbral']}</span>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;"
                    f"margin-bottom:0.4rem;'>"
                    f"<span style='color:#94A3B8;font-size:0.82rem;'>Peor valor</span>"
                    f"<span style='font-weight:700;color:{color};'>{regla['valor']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.caption(regla["detalle"])
                with st.popover(
                    f"{simb} Plan de contingencia",
                    use_container_width=True,
                ):
                    st.markdown(f"**Plan — {regla['nombre']}**")
                    for paso in regla["plan"]:
                        st.markdown(f"- {paso}")

    # ---- Heatmaps de tensión por mes×sucursal ----
    st.markdown("#### 🗺️ Mapa de tensión por mes y sucursal")
    tab1, tab2, tab3 = st.tabs(
        ["🔥 ROI Alimentos", "🥤 Mix Bebidas", "📉 Cumplimiento"]
    )
    with tab1:
        roi = _roi_alimentos_mensual(df, shock_marisco)
        if len(roi):
            st.plotly_chart(
                _heatmap(roi, f"ROI alimentos por mes·sucursal "
                              f"(shock marisco +{shock_marisco:.0%})",
                         UMBRAL_ROI, COLOR_SUCCESS, COLOR_CRITICAL),
                width="stretch",
            )
    with tab2:
        mix = _mix_bebidas_mensual(df, caida_bebidas)
        if len(mix):
            st.plotly_chart(
                _heatmap(mix, f"Mix bebidas por mes·sucursal "
                              f"(caída bebidas {caida_bebidas:.0%})",
                         UMBRAL_MIX, COLOR_SUCCESS, COLOR_CRITICAL),
                width="stretch",
            )
    with tab3:
        cum = _cumplimiento_mensual(df, presupuesto, caida_demanda)
        if len(cum):
            st.plotly_chart(
                _heatmap(cum, f"Cumplimiento presupuesto por mes·sucursal "
                              f"(demanda {caida_demanda:.0%}↓)",
                         UMBRAL_META, COLOR_SUCCESS, COLOR_CRITICAL),
                width="stretch",
            )

    # ---- Churn: clientes en riesgo ----
    st.markdown("#### 👥 Clientes Oro/VIP en riesgo de deserción")
    churn = _churn(clientes_crm, df, fecha_max)
    if churn.empty:
        st.success("Sin clientes Oro/VIP en riesgo para el corte actual.")
    else:
        top = churn.head(10).copy()
        top["nombre_cliente"] = top["nombre"]
        top["Nivel"] = top["nivel"]
        top["Sucursal"] = top["sucursal_frecuente"]
        top["Días sin visita"] = top["dias_sin_visita"].astype(int)
        top["Plan"] = "🎁 Sopa gratis + 2 bebidas marketing"
        st.dataframe(
            top[["nombre_cliente", "Nivel", "Sucursal", "Días sin visita", "Plan"]]
            .rename(columns={"nombre_cliente": "Cliente"}),
            width="stretch",
            hide_index=True,
        )
        if len(churn) > 10:
            st.caption(f"Mostrando 10 de {len(churn)} clientes en riesgo.")
