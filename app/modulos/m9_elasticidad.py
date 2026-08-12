# ============================================================
# M9 · MATRIZ DE ELASTICIDAD DE PRECIOS — "El Errante"
# Pestaña 9 del dashboard (DOCUMENTO_MAESTRO §6 · M9)
# ------------------------------------------------------------
# Poder científico para ajustar el menú: el gerente identifica qué
# productos toleran subidas de precio (INELÁSTICOS: bebidas de marketing,
# ancla) y cuáles son sensibles (ELÁSTICOS: ceviches y variantes).
#   • Scatter interactivo: volumen de venta vs precio (182 productos)
#   • Elasticidad log-log por SUBCATEGORÍA con efectos fijos de producto
#     y de mes (quita tamaño del producto + estacionalidad/crecimiento/
#     inflación comunes) — pooling porque a nivel producto individual el
#     ruido mensual domina la señal (decisión documentada en el maestro)
#   • Simulador de re-precio: ingreso proyectado = ingreso × (1+Δp)^(1+e)
#   • Plan de precios sugerido: subir inelásticos, mantener intermedios,
#     bajar elásticos para acelerar volumen
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from styles import COLOR_CRITICAL, COLOR_SUCCESS, COLOR_WARNING, header
from utils import fmt_money

# Umbrales de clasificación (valor absoluto de la elasticidad)
INELASTICO_MAX = 0.5     # |e| < 0.5  -> subir precio sin perder demanda
ELASTICO_MIN = 1.0       # |e| > 1.0  -> altamente sensible al precio
MIN_MESES = 6            # mínimo de meses para estimar elasticidad


def _template() -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F8FAFC"),
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor="#13315C", font_color="#F8FAFC"),
        legend=dict(orientation="h", y=1.12, x=0),
    )


COLOR_CLASE = {
    "Inelástico": COLOR_SUCCESS,
    "Intermedio": COLOR_WARNING,
    "Elástico": COLOR_CRITICAL,
    "Sin datos": "#94A3B8",  # defensivo: subcategoría sin estimación
}


# ------------------------------------------------------------
# Estimación de elasticidad
# ------------------------------------------------------------
def _precio_volumen(df: pd.DataFrame) -> pd.DataFrame:
    """Agregación producto × mes: precio medio, volumen e ingreso."""
    v = df.copy()
    v["mes"] = v["fecha_hora"].dt.to_period("M")
    return v.groupby(["id_producto", "mes"]).agg(
        precio=("precio_unitario_aplicado", "mean"),
        volumen=("cantidad", "sum"),
        ingreso=("monto", "sum"),
    ).reset_index()


def _elasticidades(pv: pd.DataFrame, productos: pd.DataFrame) -> pd.DataFrame:
    """Elasticidad log-log por subcategoría con efectos fijos (producto + mes).

    Modelo:  log(volumen) ~ log(precio) + efecto_producto + efecto_mes
    Los efectos fijos eliminan el tamaño del producto y la estacionalidad /
    crecimiento / inflación comunes; la pendiente queda identificada por los
    experimentos de precio internos a cada producto (promos, menús de temporada).
    Se estima AGRUPADO por subcategoría porque a nivel producto individual el
    ruido mensual domina la señal (decisión documentada en el maestro §6 · M9).
    Nota: el demeaning secuencial (mes → producto) es exacto en paneles
    balanceados (todos los productos venden todos los meses del rango, que es
    el caso del histórico completo); con rangos filtrados es aproximado.
    """
    p = pv.copy()
    p["lp"] = np.log(p["precio"])
    p["lq"] = np.log(p["volumen"])
    p["lp_m"] = p["lp"] - p.groupby("mes")["lp"].transform("mean")
    p["lq_m"] = p["lq"] - p.groupby("mes")["lq"].transform("mean")
    p["lp_pm"] = p["lp_m"] - p.groupby("id_producto")["lp_m"].transform("mean")
    p["lq_pm"] = p["lq_m"] - p.groupby("id_producto")["lq_m"].transform("mean")
    p = p.merge(productos[["id_producto", "subcategoria"]], on="id_producto")

    def pendiente_pool(g: pd.DataFrame) -> float:
        num = float((g["lp_pm"] * g["lq_pm"]).sum())
        den = float((g["lp_pm"] ** 2).sum())
        return num / den if den > 0 else np.nan

    est = p.groupby("subcategoria").apply(
        pendiente_pool, include_groups=False
    ).dropna()
    return est.rename("elasticidad").reset_index()


def _clasificar(e: float) -> str:
    if e is None or pd.isna(e):
        return "Sin datos"
    ab = abs(e)
    if ab < INELASTICO_MAX:
        return "Inelástico"
    if ab < ELASTICO_MIN:
        return "Intermedio"
    return "Elástico"


def _resumen(pv: pd.DataFrame, productos: pd.DataFrame, est_sub: pd.DataFrame) -> pd.DataFrame:
    """Resumen por producto: precio, volumen mensual, ingreso, elasticidad
    (heredada de su subcategoría) y clasificación."""
    agg = pv.groupby("id_producto").agg(
        precio=("precio", "mean"),
        volumen=("volumen", "sum"),
        ingreso=("ingreso", "sum"),
        meses=("mes", "count"),
    ).reset_index()
    r = agg.merge(
        productos[
            ["id_producto", "nombre_producto", "categoria", "subcategoria", "es_ancla"]
        ],
        on="id_producto",
    )
    r = r.merge(est_sub, on="subcategoria", how="left")
    r["clasificacion"] = r["elasticidad"].map(_clasificar)
    r["vol_mensual"] = r["volumen"] / r["meses"].clip(lower=1)
    return r


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------
def _scatter(r: pd.DataFrame) -> go.Figure:
    """Scatter volumen mensual vs precio (especificación M9)."""
    r = r.copy()
    r["marca"] = np.where(r["es_ancla"], "Ancla ★", "Producto")
    fig = px.scatter(
        r,
        x="precio",
        y="vol_mensual",
        color="clasificacion",
        size="ingreso",
        symbol="marca",
        custom_data=["nombre_producto", "subcategoria", "elasticidad", "clasificacion"],
        color_discrete_map=COLOR_CLASE,
        symbol_map={"Producto": "circle", "Ancla ★": "star"},
        log_x=True,
        log_y=True,
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]} · %{customdata[3]}<br>"
            "Precio: $%{x:,.0f} · Volumen/mes: %{y:,.0f} uds<br>"
            "Elasticidad: %{customdata[2]:.2f}<extra></extra>"
        ),
        marker=dict(opacity=0.85, line=dict(width=1, color="#0B2545")),
    )
    fig.update_layout(
        **_template(), height=430,
        xaxis=dict(title="Precio promedio ($, escala log)", type="log"),
        yaxis=dict(title="Volumen mensual (uds, escala log)", type="log"),
        title=dict(text="Curva de demanda del menú: volumen vs precio por producto",
                   font=dict(size=14)),
    )
    return fig


def _barras_subcategoria(est_sub: pd.DataFrame) -> go.Figure:
    """Elasticidad estimada por subcategoría (de más elástica a más inelástica)."""
    d = est_sub.copy()
    d = d.sort_values("elasticidad")
    d["clasificacion"] = d["elasticidad"].map(_clasificar)
    colores = d["clasificacion"].map(COLOR_CLASE)
    fig = go.Figure(go.Bar(
        x=d["elasticidad"],
        y=d["subcategoria"],
        orientation="h",
        marker_color=colores,
        customdata=d[["clasificacion"]],
        hovertemplate="%{y}: %{x:.2f} (%{customdata[0]})<extra></extra>",
    ))
    fig.add_vline(
        x=-1, line_dash="dash", line_color="#94A3B8",
        annotation_text="Elasticidad unitaria (e=-1)",
        annotation_font_color="#94A3B8",
    )
    fig.update_layout(
        **_template(), height=360,
        xaxis=dict(title="Elasticidad estimada (negativa: sube precio → cae demanda)"),
        yaxis=dict(title=""),
        title=dict(text="Elasticidad por subcategoría (efectos fijos producto + mes)",
                   font=dict(size=14)),
    )
    return fig


def _simular(r: pd.DataFrame, delta_pct: float) -> pd.DataFrame:
    """Ingreso proyectado ante un cambio de precio global Δp:
       precio' = precio·(1+Δp) · volumen' = volumen·(1+Δp)^e
       ingreso' = ingreso·(1+Δp)^(1+e)   (regla económica estándar)."""
    dp = delta_pct / 100.0
    s = r.copy()
    s["e"] = s["elasticidad"].fillna(-0.9)  # sin datos -> sensibilidad conservadora
    s["factor_ingreso"] = (1 + dp) ** (1 + s["e"])
    s["ingreso_proy"] = s["ingreso"] * s["factor_ingreso"]
    s["delta_ingreso"] = s["ingreso_proy"] - s["ingreso"]
    return s


# ------------------------------------------------------------
# Render del módulo
# ------------------------------------------------------------
def render(df, productos, sucursales_sel) -> None:
    header(
        "Matriz de Elasticidad de Precios",
        "El poder científico para ajustar el menú: identifica qué productos "
        "toleran subir de precio y cuáles se desploman si los tocas.",
    )

    df = df[df["id_sucursal"].isin(sucursales_sel)]
    if df.empty:
        st.info("Sin datos en el periodo y sucursales seleccionados.")
        return

    pv = _precio_volumen(df)
    n_meses = pv["mes"].nunique()
    if n_meses < MIN_MESES:
        st.warning(
            f"El rango seleccionado tiene {n_meses} meses. Se necesitan al menos "
            f"{MIN_MESES} meses con variación de precio para estimar la "
            f"elasticidad con efectos fijos."
        )
        return

    est_sub = _elasticidades(pv, productos)
    if est_sub.empty:
        st.info("No fue posible identificar elasticidad en el rango seleccionado.")
        return
    r = _resumen(pv, productos, est_sub)

    # ---- KPIs ----
    n_ali = int((r["categoria"] == "Alimento").sum())
    n_beb = int((r["categoria"] == "Bebida").sum())
    n_inel = int((r["clasificacion"] == "Inelástico").sum())
    n_elast = int((r["clasificacion"] == "Elástico").sum())
    mask_e = r["elasticidad"].notna()
    e_media = float(np.average(r.loc[mask_e, "elasticidad"], weights=r.loc[mask_e, "ingreso"]))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Productos analizados", f"{len(r)}",
        f"{n_ali} alimentos · {n_beb} bebidas",
        help="Los 182 productos del menú con su elasticidad estimada.",
    )
    k2.metric(
        "Elasticidad media del menú", f"{e_media:.2f}",
        "ponderada por ingreso",
        delta_color="inverse" if e_media < -1 else "normal",
        help="Media ponderada: menor a -1 indica un menú sensible al precio.",
    )
    k3.metric(
        "Inelásticos |e|<0.5", f"{n_inel}",
        "subir precio sin perder demanda",
        delta_color="normal",
        help="Bebidas y ancla: toleran subidas de precio. Motor de margen.",
    )
    k4.metric(
        "Elásticos |e|>1.0", f"{n_elast}",
        "sensibles: no tocar precio",
        delta_color="inverse",
        help="Ceviches y variantes: una subida desploma el volumen.",
    )

    # ---- Scatter (especificación M9) ----
    st.plotly_chart(_scatter(r), width="stretch")

    # ---- Elasticidad por subcategoría + insight ----
    c_bar, c_ctx = st.columns([1.1, 1])
    with c_bar:
        st.plotly_chart(_barras_subcategoria(est_sub), width="stretch")
    with c_ctx:
        st.markdown("#### 💡 Lectura de la matriz")
        orden = est_sub.sort_values("elasticidad", ascending=False)
        inel_nombres = " · ".join(
            f"{fila['subcategoria']} ({fila['elasticidad']:.2f})"
            for _, fila in orden[orden["elasticidad"] > -0.5].iterrows()
        )
        elast_nombres = " · ".join(
            f"{fila['subcategoria']} ({fila['elasticidad']:.2f})"
            for _, fila in orden[orden["elasticidad"] < -1.0].iterrows()
        )
        st.markdown(
            f"- **Inelásticas** ({inel_nombres}): subirles el precio apenas "
            f"reduce la demanda → **candidatas a subir** sin arriesgar el ticket."
        )
        st.markdown(
            f"- **Elásticas** ({elast_nombres}): una subida del 10% desploma "
            f"~10%+ del volumen → **no tocar** (o bajar para acelerar venta)."
        )
        st.markdown(
            "- La elasticidad se estima **por subcategoría con efectos fijos de "
            "producto y mes** (pooling). A nivel producto individual, el ruido "
            "mensual domina la señal — decisión documentada en el maestro §6 · M9."
        )
        st.caption(
            "El modelo usa los experimentos de precio del histórico 2024-2025 "
            "(promos regionales y menús de temporada ≈ ±4% mensual) para medir "
            "la respuesta real del cliente."
        )

    # ---- Simulador de re-precio ----
    st.markdown("#### 🎚️ Simulador de re-precio del menú")
    c_slider, c_act, c_proy, c_delta = st.columns([1.3, 1, 1, 1])
    delta_pct = c_slider.slider(
        "Cambio de precio global aplicado a todo el menú",
        -10, 15, 5, 1,
        help="El ingreso proyectado = ingreso × (1+Δp)^(1+e) por producto. "
             "Inelásticos ganan ingreso al subir; elásticos lo pierden.",
    )
    ing_actual = float(r["ingreso"].sum())
    sim = _simular(r, delta_pct)
    ing_proy = float(sim["ingreso_proy"].sum())
    delta = ing_proy - ing_actual
    c_act.metric("Ingreso actual", fmt_money(ing_actual),
                 help="Ingreso del periodo filtrado.")
    c_proy.metric("Ingreso proyectado", fmt_money(ing_proy),
                  help=f"Con {delta_pct:+d}% en todos los precios.")
    c_delta.metric(
        "Impacto", f"{delta:+,.0f}",
        f"{delta / ing_actual:+.1%}",
        delta_color="inverse" if delta < 0 else "normal",
        help="Δ ingreso del escenario simulado.",
    )

    col_gan, col_per = st.columns(2)
    top_gan = sim.nlargest(8, "delta_ingreso")
    top_per = sim.nsmallest(8, "delta_ingreso")
    with col_gan:
        st.markdown("##### 🟢 Productos que más ganan con el cambio")
        if top_gan["delta_ingreso"].max() <= 0:
            st.info("Ningún producto gana ingreso con este cambio (el menú es "
                    "elástico en general).")
        else:
            st.dataframe(
                top_gan[["nombre_producto", "subcategoria", "elasticidad",
                         "delta_ingreso"]]
                .assign(Producto=top_gan["nombre_producto"],
                        Subcategoría=top_gan["subcategoria"],
                        Elast=top_gan["elasticidad"].map(lambda x: f"{x:.2f}"),
                        **{"Δ ingreso": top_gan["delta_ingreso"].map(lambda x: f"${x:+,.0f}")})
                [["Producto", "Subcategoría", "Elast", "Δ ingreso"]],
                width="stretch", hide_index=True,
            )
    with col_per:
        st.markdown("##### 🔴 Productos que más pierden con el cambio")
        if top_per["delta_ingreso"].min() >= 0:
            st.info("Ningún producto pierde ingreso con este cambio.")
        else:
            st.dataframe(
                top_per[["nombre_producto", "subcategoria", "elasticidad",
                         "delta_ingreso"]]
                .assign(Producto=top_per["nombre_producto"],
                        Subcategoría=top_per["subcategoria"],
                        Elast=top_per["elasticidad"].map(lambda x: f"{x:.2f}"),
                        **{"Δ ingreso": top_per["delta_ingreso"].map(lambda x: f"${x:+,.0f}")})
                [["Producto", "Subcategoría", "Elast", "Δ ingreso"]],
                width="stretch", hide_index=True,
            )

    # ---- Plan de precios sugerido (Δp FIJO, independiente del slider) ----
    st.markdown("#### 📋 Plan de precios sugerido (basado en elasticidad)")
    plan = r.copy()
    plan["e"] = plan["elasticidad"].fillna(-0.9)
    plan["accion"] = np.select(
        [plan["e"] > -0.7, plan["e"] < -1.1],
        ["📈 Subir +5%", "📉 Bajar -3%"],
        default="➖ Mantener",
    )
    plan["delta_plan"] = np.select(
        [plan["e"] > -0.7, plan["e"] < -1.1],
        [0.05, -0.03],
        default=0.0,
    )
    plan["factor_ing"] = (1 + plan["delta_plan"]) ** (1 + plan["e"])
    plan["delta_ingreso"] = plan["ingreso"] * (plan["factor_ing"] - 1)
    resumen_plan = plan.groupby("accion").agg(
        n=("nombre_producto", "count"),
        delta=("delta_ingreso", "sum"),
    )
    subir, mantener, bajar = st.columns(3)
    for col, accion in ((subir, "📈 Subir +5%"), (mantener, "➖ Mantener"),
                        (bajar, "📉 Bajar -3%")):
        fila = resumen_plan.loc[accion] if accion in resumen_plan.index else None
        if fila is None:
            col.metric(accion, "0 productos", "—")
        else:
            col.metric(
                accion, f"{int(fila['n'])} productos",
                f"Δ {fila['delta']:+,.0f}",
                delta_color="normal" if accion.startswith("📈") else
                ("inverse" if accion.startswith("📉") else "off"),
                help="Impacto del plan fijo aplicado al grupo: +5% a inelásticos "
                     "(e>-0.7), -3% a elásticos (e<-1.1), sin tocar intermedios.",
            )
    st.caption(
        "Regla económica: subir precio aumenta ingreso si e > -1 (inelástico); "
        "bajar precio aumenta ingreso y volumen si e < -1 (elástico). "
        "Este plan es fijo (+5%/-3%) y no depende del slider del simulador."
    )
