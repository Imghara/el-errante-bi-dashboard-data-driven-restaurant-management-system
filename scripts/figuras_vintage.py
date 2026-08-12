# ============================================================
# FIGURAS VINTAGE — Manual de usuario "El Errante" (PDF · APA)
# ------------------------------------------------------------
# Genera las figuras del manual en UNA SOLA TINTA con estética
# de dibujo a mano (efecto boceto de matplotlib + serif + tramas
# de impresión), calculadas con los DATOS REALES del dashboard.
# Salida: scripts/figuras/*.png (blanco y negro, 200 dpi)
# Uso: python scripts/figuras_vintage.py
# Autor: Buffy | Fase: pre-F7 (2026-08-12)
# ============================================================

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon, Rectangle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from config import (  # noqa: E402
    CSV_DIM_CLIENTES_CRM,
    CSV_DIM_MESEROS,
    CSV_DIM_PRODUCTOS,
    CSV_DIM_SUCURSALES,
    CSV_FACT_COSTOS,
    CSV_FACT_ENCUESTAS,
    CSV_FACT_PRESUPUESTO,
    CSV_FACT_VENTAS,
)

OUT = ROOT / "scripts" / "figuras"
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Estética "vintage": boceto a mano + serif + tinta negra
# ------------------------------------------------------------
np.random.seed(42)
plt.xkcd(scale=0.85, length=90, randomness=2)
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10.5,
    "axes.edgecolor": "#111111",
    "axes.labelcolor": "#111111",
    "xtick.color": "#111111",
    "ytick.color": "#111111",
    "text.color": "#111111",
    "axes.titlecolor": "#111111",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

GRAF = ["#111111", "#4d4d4d", "#808080", "#b3b3b3", "#d9d9d9"]
HATCH = ["///", "xxx", "...", "\\\\\\"]


def guardar(fig, nombre, w=6.5, h=None, dpi=200):
    fig.set_size_inches(w, h or w * 0.62)
    fig.savefig(OUT / nombre, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  ok {nombre}")


# ------------------------------------------------------------
# Carga de datos (misma semántica que app/utils.py)
# ------------------------------------------------------------
def cargar():
    v = pd.read_csv(CSV_FACT_VENTAS)
    for c in ("fecha_hora", "hora_apertura_mesa", "hora_cierre_mesa"):
        v[c] = pd.to_datetime(v[c])
    v["monto"] = v["precio_unitario_aplicado"] * v["cantidad"]
    v["mes_ano"] = v["fecha_hora"].dt.strftime("%Y-%m")
    costos = pd.read_csv(CSV_FACT_COSTOS)
    v = v.merge(costos, on=["id_producto", "mes_ano"], how="left")
    v["roi"] = (v["precio_unitario_aplicado"] - v["costo_elaboracion"]) / v[
        "costo_elaboracion"
    ]
    v["costo_total"] = v["costo_elaboracion"] * v["cantidad"]
    suc = pd.read_csv(CSV_DIM_SUCURSALES)
    mes = pd.read_csv(CSV_DIM_MESEROS)
    pro = pd.read_csv(CSV_DIM_PRODUCTOS)
    cli = pd.read_csv(CSV_DIM_CLIENTES_CRM)
    pre = pd.read_csv(CSV_FACT_PRESUPUESTO)
    enc = pd.read_csv(CSV_FACT_ENCUESTAS)
    return v, suc, mes, pro, cli, pre, enc


V, SUC, MES, PRO, CLI, PRE, ENC = cargar()


def _sin_spines(ax, left=True, bottom=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if not left:
        ax.spines["left"].set_visible(False)
    if not bottom:
        ax.spines["bottom"].set_visible(False)


# ------------------------------------------------------------
# 1. Esquema en estrella (modelo de datos)
# ------------------------------------------------------------
def fig_estrella():
    fig, ax = plt.subplots()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.add_patch(Rectangle(
        (3.1, 3.6), 3.8, 2.8, fill=True, facecolor="#e8e8e8",
        edgecolor="#111", lw=1.6,
    ))
    ax.text(5.0, 5.55, "fact_ventas", ha="center", fontsize=13, fontweight="bold")
    ax.text(5.0, 4.65, "tabla de hechos\n~706 000 líneas de tickets", ha="center", fontsize=8.5)
    dims = [
        (1.4, 8.6, "dim_sucursales\n3 sucursales"),
        (4.6, 9.35, "dim_meseros\n48 meseros"),
        (8.6, 8.4, "dim_productos\n182 productos"),
        (8.8, 2.0, "dim_clientes_crm\n~400 clientes"),
        (4.6, 0.65, "fact_costos_mensuales\ncosto por producto y mes"),
        (1.3, 2.1, "fact_presupuesto\nmeta mensual por sucursal"),
        (6.9, 5.6, "fact_encuestas\ncalificacion 1 a 5"),
    ]
    for x, y, label in dims:
        ax.add_patch(Rectangle(
            (x - 1.6, y - 0.55), 3.2, 1.1, fill=False, edgecolor="#111", lw=1.15,
        ))
        ax.text(x, y, label, ha="center", va="center", fontsize=7.6)
        ax.annotate(
            "", xy=(5.0, 5.0), xytext=(x, y),
            arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.0),
        )
    guardar(fig, "fig_estrella.png", w=6.4, h=6.4)


# ------------------------------------------------------------
# 2. Indicadores (KPIs) del Consolidado Financiero
# ------------------------------------------------------------
def fig_kpis():
    ventas = V["monto"].sum()
    tickets = V["id_ticket"].nunique()
    tp = ventas / tickets
    costo = V["costo_total"].sum()
    roi = (ventas - costo) / costo
    mix = V.loc[V["categoria"] == "Bebida", "monto"].sum() / ventas
    cards = [
        ("VENTAS TOTALES", f"${ventas:,.0f}"),
        ("TICKET PROMEDIO", f"${tp:,.0f}"),
        ("ROI PROMEDIO", f"{roi:.1%}"),
        ("MIX DE BEBIDAS", f"{mix:.1%}"),
    ]
    fig, ax = plt.subplots()
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    for i, (lab, val) in enumerate(cards):
        x0 = 0.35 + i * 2.45
        ax.add_patch(Rectangle(
            (x0, 1.15), 2.25, 3.15, fill=True, facecolor="#f4f4f4",
            edgecolor="#111", lw=1.5,
        ))
        ax.text(x0 + 1.125, 3.6, lab, ha="center", fontsize=8.6)
        ax.text(x0 + 1.125, 2.35, val, ha="center", fontsize=15.5, fontweight="bold")
    ax.text(5, 0.45, "Periodo completo 2024-2025 · tres sucursales (M1)",
            ha="center", fontsize=8.4, style="italic")
    guardar(fig, "fig_kpis.png", w=6.6, h=3.4)


# ------------------------------------------------------------
# 3. M1 — Evolución mensual de ventas (estacionalidad)
# ------------------------------------------------------------
def fig_m1_ventas():
    mensual = V.groupby(V["fecha_hora"].dt.to_period("M"))["monto"].sum()
    x = [str(p) for p in mensual.index]
    vals = mensual.values
    fig, ax = plt.subplots()
    ax.plot(range(len(x)), vals, color="#111", lw=1.8, marker="o", ms=3.5)
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels([t[2:7] for t in x], rotation=45, ha="right", fontsize=7.5)
    ax.yaxis.set_major_formatter(lambda y, _: f"${y/1e6:.1f}M")
    ax.set_ylabel("Ventas mensuales ($)")
    _sin_spines(ax)
    ax.annotate(
        "Cuaresma +40%", xy=(14, vals[14]), xytext=(9.5, vals.max() * 0.92),
        fontsize=8.5, arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.0),
    )
    ax.annotate(
        "Cuesta de enero -20%", xy=(12, vals[12]), xytext=(2.5, vals.min() * 0.72),
        fontsize=8.5, arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.0),
    )
    guardar(fig, "fig_m1_ventas.png")


# ------------------------------------------------------------
# 4. M1 — Mapa de sucursales (tamaño = ventas del periodo)
# ------------------------------------------------------------
def fig_m1_mapa():
    agg = V.groupby("id_sucursal")["monto"].sum().rename("ventas")
    d = SUC.set_index("id_sucursal").join(agg)
    fig, ax = plt.subplots()
    for idx, r in d.iterrows():
        ax.add_patch(Ellipse(
            (r["lon"], r["lat"]), width=1.15, height=0.95, fill=True,
            facecolor="#e9e9e9", edgecolor="#111", lw=1.2,
        ))
        ax.scatter(r["lon"], r["lat"], s=r["ventas"] / 4e4, color="#111",
                   edgecolor="white", lw=0.8, zorder=3)
        ax.text(r["lon"], r["lat"] + 0.62,
                f"S{idx[-1]} · {r['ciudad']} ({r['entidad']})",
                ha="center", fontsize=8.2, fontweight="bold")
        ax.text(r["lon"], r["lat"] - 0.62,
                f"ventas ${r['ventas']/1e6:.1f}M",
                ha="center", fontsize=7.8, style="italic")
    ax.text(-96.7, 23.55, "Golfo de Mexico", ha="center", fontsize=9,
            style="italic", color="#555")
    ax.text(-96.7, 23.15, "~", ha="center", fontsize=12, color="#999")
    ax.set_xlim(-102.9, -95.9)
    ax.set_ylim(22.9, 27.2)
    ax.set_xticks([])
    ax.set_yticks([])
    _sin_spines(ax, left=False, bottom=False)
    guardar(fig, "fig_m1_mapa.png", w=6.4, h=4.5)


# ------------------------------------------------------------
# 5. M2 — Top 10 meseros por comisión (política 5% / 1.5x)
# ------------------------------------------------------------
def fig_m2_leaderboard():
    from modulos.m2_incentivos import _calc_incentivos

    d = _calc_incentivos(V, 0.05, 1.5)
    inc = d[d["comision_linea"] > 0]
    lb = (
        inc.groupby("id_mesero")["comision_linea"]
        .sum().reset_index()
        .merge(MES[["id_mesero", "nombre", "sucursal"]], on="id_mesero")
        .sort_values("comision_linea", ascending=False)
        .head(10)
    )
    lb = lb.iloc[::-1]
    fig, ax = plt.subplots()
    for i, (_, r) in enumerate(lb.iterrows()):
        h = HATCH[{"S1": 0, "S2": 1, "S3": 2}[r["sucursal"]]]
        ax.barh(i, r["comision_linea"], color="white", edgecolor="#111",
                lw=1.0, hatch=h)
        ax.text(r["comision_linea"], i, f"  ${r['comision_linea']:,.0f}",
                va="center", fontsize=8)
    ax.set_yticks(range(len(lb)))
    ax.set_yticklabels([f"{r['nombre']} ({r['sucursal']})" for _, r in lb.iterrows()],
                       fontsize=8)
    ax.set_xlabel("Comision ganada ($) · politica 5% + 1.5x alto ROI")
    ax.set_xlim(0, lb["comision_linea"].max() * 1.18)
    _sin_spines(ax, bottom=False)
    guardar(fig, "fig_m2_leaderboard.png")


# ------------------------------------------------------------
# 6. M3 — Correlación ancla → bebidas
# ------------------------------------------------------------
def fig_m3_ancla():
    ancla_id = V.loc[V["es_ancla"], "id_producto"].iloc[0]
    tickets_ancla = set(V[V["id_producto"] == ancla_id]["id_ticket"])
    beb = V[V["categoria"] == "Bebida"]
    variedades = beb.groupby("id_ticket")["id_producto"].nunique().rename("v")
    res = variedades.reset_index()
    res["con_ancla"] = res["id_ticket"].isin(tickets_ancla)
    prom = res.groupby("con_ancla")["v"].mean()
    fig, ax = plt.subplots()
    x = [0, 1]
    b = ax.bar(x, [prom[False], prom[True]], width=0.55, color="white",
               edgecolor="#111", lw=1.1, hatch=[HATCH[1], HATCH[0]])
    ax.axhline(2, ls="--", color="#555", lw=1.1)
    ax.text(1.05, 2.06, "regla M3: >2 variedades", fontsize=8, style="italic")
    for xi, p in zip(x, [prom[False], prom[True]]):
        ax.text(xi, p + 0.06, f"{p:.2f}", ha="center", fontsize=9.5,
                fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(["Sin ancla", "Con ancla"], fontsize=9.5)
    ax.set_ylabel("Variedades de bebida por mesa")
    ax.set_ylim(0, prom.max() + 0.6)
    _sin_spines(ax, bottom=False)
    guardar(fig, "fig_m3_ancla.png")


# ------------------------------------------------------------
# 7. M3 — Embudo de clientes del programa
# ------------------------------------------------------------
def fig_m3_embudo():
    visitas = set(V[V["id_cliente_crm"].notna()]["id_cliente_crm"])
    registrados = len(CLI)
    activos = int(CLI["id_cliente"].isin(visitas).sum())
    ov = int(CLI[(CLI["nivel"].isin(["Oro", "VIP"])) &
                 (CLI["id_cliente"].isin(visitas))]["id_cliente"].nunique())
    etiquetas = [
        (f"Registrados: {registrados:,}", registrados),
        (f"Activos en el periodo: {activos:,}", activos),
        (f"Oro/VIP activos: {ov:,}", ov),
    ]
    fig, ax = plt.subplots()
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    wmax = 6.6
    for i, (lab, val) in enumerate(etiquetas):
        y = 5.0 - i * 1.75
        w = wmax * (val / registrados)
        ax.add_patch(Polygon(
            [(5 - w / 2, y), (5 + w / 2, y),
             (5 + w * 0.42, y - 1.15), (5 - w * 0.42, y - 1.15)],
            closed=True, fill=True, facecolor="#ececec", edgecolor="#111",
            lw=1.2, hatch=HATCH[i % 3],
        ))
        ax.text(5, y - 0.58, lab, ha="center", va="center", fontsize=9.5,
                fontweight="bold")
    guardar(fig, "fig_m3_embudo.png", w=6.0, h=4.6)


# ------------------------------------------------------------
# 8. M4 — Cumplimiento mensual real vs meta
# ------------------------------------------------------------
def fig_m4_cumplimiento():
    real = V.groupby("mes_ano")["monto"].sum()
    meta = PRE.groupby("mes_ano")["meta_ventas"].sum()
    comp = (real / meta).reindex(sorted(meta.index)).dropna()
    x = list(range(len(comp)))
    fig, ax = plt.subplots()
    ax.bar(x, comp.values, color="white", edgecolor="#111", lw=1.1, hatch="///")
    ax.axhline(1.0, ls="--", color="#111", lw=1.1)
    ax.text(0.2, 1.015, "meta (100%)", fontsize=8, style="italic")
    ax.axhline(0.90, ls=":", color="#555", lw=1.3)
    ax.text(0.2, 0.868, "umbral de alerta (90%)", fontsize=8, style="italic")
    ax.set_xticks(x)
    ax.set_xticklabels([str(p)[2:7] for p in comp.index], rotation=45,
                       ha="right", fontsize=7.5)
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_ylabel("Cumplimiento (real / meta)")
    ax.set_ylim(0.5, 1.15)
    _sin_spines(ax)
    guardar(fig, "fig_m4_cumplimiento.png")


# ------------------------------------------------------------
# 9. M5 — Mapa de tensión: cumplimiento mes × sucursal
# ------------------------------------------------------------
def fig_m5_tension():
    real = V.groupby(["mes_ano", "id_sucursal"])["monto"].sum().unstack()
    meta = PRE.pivot(index="mes_ano", columns="id_sucursal", values="meta_ventas")
    comp = (real / meta).reindex(sorted(real.index)).dropna()
    fig, ax = plt.subplots()
    im = ax.imshow(comp.values.T, cmap="Greys", vmin=0.7, vmax=1.2,
                   aspect="auto", interpolation="nearest")
    for i in range(comp.shape[0]):
        for j in range(comp.shape[1]):
            val = comp.values[i, j]
            ax.text(i, j, f"{val:.0%}", ha="center", va="center", fontsize=7.5,
                    color="#111" if val < 1.05 else "#555")
    ax.set_xticks(range(comp.shape[0]))
    ax.set_xticklabels([str(p)[2:7] for p in comp.index], rotation=45,
                       ha="right", fontsize=7.5)
    ax.set_yticks(range(len(comp.columns)))
    ax.set_yticklabels(comp.columns, fontsize=9)
    ax.set_ylabel("Sucursal")
    ax.set_title("Cumplimiento de meta por mes y sucursal (M5)",
                 fontsize=9.5, pad=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("Cumplimiento", fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    guardar(fig, "fig_m5_tension.png", w=6.4, h=4.2)


# ------------------------------------------------------------
# 10. M6 — Pronóstico semanal con banda de confianza
# ------------------------------------------------------------
def fig_m6_forecast():
    from models import forecast as fc

    serie = fc.serie_semanal(V)
    res = fc.entrenar_y_pronosticar(serie, semanas=4)
    hist = res["historico"].groupby("inicio_sem")["ventas"].sum()
    pron = (
        res["pronostico"]
        .groupby("inicio_sem")
        .agg(pron=("pronostico", "sum"), inf=("inferior", "sum"),
             sup=("superior", "sum"))
    )
    n = len(hist)
    x_hist = list(range(n - 26, n))
    x_fut = list(range(n, n + 4))
    fig, ax = plt.subplots()
    ax.plot(x_hist, hist.values[-26:], color="#111", lw=1.7,
            label="Historico semanal")
    ax.plot(x_fut, pron["pron"], color="#111", ls="--", lw=1.7,
            marker="o", ms=4.5, label="Pronostico 4 semanas")
    ax.fill_between(x_fut, pron["inf"], pron["sup"], color="#c9c9c9",
                    alpha=0.6, label="Banda de confianza 80%")
    ax.axvline(n - 0.5, ls=":", color="#555", lw=1.0)
    mape = res["mape_backtest"]
    ax.text(0.02, 0.9, f"MAPE backtest: {mape:.0%} (referencia ingenua ~45%)",
            transform=ax.transAxes, fontsize=8, style="italic")
    ax.yaxis.set_major_formatter(lambda y, _: f"${y/1e6:.1f}M")
    ax.set_ylabel("Ventas semanales ($)")
    all_x = x_hist + x_fut
    fechas = list(hist.index[-26:]) + list(pron.index)
    ax.set_xticks(all_x[::4])
    ax.set_xticklabels([f"{d:%d-%b}" for d in fechas[::4]], fontsize=7.5)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    _sin_spines(ax)
    guardar(fig, "fig_m6_forecast.png")


# ------------------------------------------------------------
# 11. M7 — Histograma de tiempo de ocupación por sucursal
# ------------------------------------------------------------
def fig_m7_ocupacion():
    dur = (V["hora_cierre_mesa"] - V["hora_apertura_mesa"]).dt.total_seconds() / 60
    V2 = V.assign(dur=dur)
    fig, ax = plt.subplots()
    for i, s in enumerate(["S1", "S2", "S3"]):
        ax.hist(V2.loc[V2["id_sucursal"] == s, "dur"], bins=36, range=(0, 180),
                histtype="stepfilled", alpha=0.5, color=GRAF[i + 1],
                edgecolor="#111", lw=0.7, hatch=HATCH[i], label=s)
    ax.axvline(77, ls="--", color="#111", lw=1.2)
    ax.text(80, ax.get_ylim()[1] * 0.95, "media ~77 min", fontsize=8,
            style="italic")
    ax.set_xlabel("Tiempo de ocupacion de la mesa (minutos)")
    ax.set_ylabel("Tickets")
    ax.legend(fontsize=8.5, frameon=False)
    _sin_spines(ax)
    guardar(fig, "fig_m7_ocupacion.png")


# ------------------------------------------------------------
# 12. M8 — Días sin visita de Oro/VIP y umbral de churn
# ------------------------------------------------------------
def fig_m8_churn():
    corte = V["fecha_hora"].max()
    con = V[V["id_cliente_crm"].notna()]
    ult = con.groupby("id_cliente_crm")["fecha_hora"].max().rename("ultima")
    cli = CLI.merge(ult, left_on="id_cliente", right_index=True, how="left")
    cli["dias"] = (corte - cli["ultima"]).dt.days.fillna(9999)
    ov = cli[cli["nivel"].isin(["Oro", "VIP"])].copy()
    n_riesgo = int((ov["dias"] > 45).sum())
    n_ov = len(ov)
    ov.loc[ov["dias"] > 400, "dias"] = 400
    fig, ax = plt.subplots()
    ax.hist(ov["dias"], bins=48, range=(0, 400), color="white",
            edgecolor="#111", lw=0.8, hatch="///")
    ax.axvline(45, ls="--", color="#111", lw=1.3)
    ax.text(48, ax.get_ylim()[1] * 0.96, "umbral de churn: 45 dias",
            fontsize=8, style="italic")
    ax.text(400 * 0.42, ax.get_ylim()[1] * 0.85,
            f"{n_riesgo} Oro/VIP en riesgo ({n_riesgo/n_ov:.0%})",
            fontsize=9, fontweight="bold")
    ax.set_xlabel("Dias sin visita (Oro y VIP; 400 = sin visita registrada)")
    ax.set_ylabel("Clientes")
    _sin_spines(ax)
    guardar(fig, "fig_m8_churn.png")


# ------------------------------------------------------------
# 13. M9 — Elasticidad por subcategoría
# ------------------------------------------------------------
def fig_m9_elasticidad():
    from modulos.m9_elasticidad import _elasticidades, _precio_volumen

    pv = _precio_volumen(V)
    est = _elasticidades(pv, PRO).sort_values("elasticidad")
    fig, ax = plt.subplots()
    for i, (_, r) in enumerate(est.iterrows()):
        ab = abs(r["elasticidad"])
        if ab >= 1.0:
            color, h = GRAF[0], HATCH[0]
        elif ab >= 0.5:
            color, h = GRAF[2], HATCH[1]
        else:
            color, h = GRAF[3], HATCH[2]
        ax.barh(i, r["elasticidad"], color=color, edgecolor="#111",
                lw=0.9, hatch=h)
        ax.text(r["elasticidad"], i, f"  {r['elasticidad']:.2f}",
                va="center", fontsize=8)
    ax.axvline(-1.0, ls="--", color="#111", lw=1.1)
    ax.text(-0.97, len(est) - 0.4, "elasticidad unitaria e = -1", fontsize=7.8,
            style="italic", rotation=90, va="bottom")
    ax.set_yticks(range(len(est)))
    ax.set_yticklabels(est["subcategoria"], fontsize=8)
    ax.set_xlabel("Elasticidad estimada (negativa: sube precio, cae demanda)")
    ax.invert_yaxis()
    _sin_spines(ax, bottom=False)
    guardar(fig, "fig_m9_elasticidad.png")


# ------------------------------------------------------------
# 14. M10 — Scatter comisión vs calificación (zona roja)
# ------------------------------------------------------------
def fig_m10_auditoria():
    from modulos.m2_incentivos import _calc_incentivos

    d = _calc_incentivos(V, 0.05, 1.5)
    inc = d[d["comision_linea"] > 0]
    agg = inc.groupby("id_mesero")["comision_linea"].sum()
    cal = ENC.groupby("id_mesero")["calificacion_servicio"].mean()
    aud = pd.DataFrame({"comision": agg, "calif": cal}).dropna()
    med = aud["comision"].median()
    y_max = aud["comision"].max() * 1.15
    fig, ax = plt.subplots()
    ax.add_patch(Rectangle(
        (1, med), 3.5 - 1, y_max - med, facecolor="#dddddd",
        edgecolor="#111", hatch="xxx", lw=0.8, alpha=0.55,
    ))
    ax.text(1.55, y_max * 0.96, "zona de venta impositiva", fontsize=8,
            style="italic", color="#111")
    ax.scatter(aud["calif"], aud["comision"], s=34, color="white",
               edgecolor="#111", lw=1.1, zorder=3)
    crit = aud[(aud["calif"] < 3.5) & (aud["comision"] >= med)]
    ax.scatter(crit["calif"], crit["comision"], s=48, color="#111",
               edgecolor="#111", zorder=4)
    ax.axvline(3.5, ls="--", color="#555", lw=1.1)
    ax.text(3.53, y_max * 0.06, "umbral de servicio 3.5", fontsize=8,
            style="italic")
    ax.axhline(med, ls=":", color="#555", lw=1.1)
    ax.text(0.85, med, f" mediana ${med:,.0f}", fontsize=8, style="italic",
            va="center")
    ax.set_xlabel("Calificacion media del servicio (1 a 5)")
    ax.set_ylabel("Comision ganada ($)")
    ax.set_xlim(0.8, 5.3)
    ax.set_ylim(0, y_max)
    _sin_spines(ax, bottom=False)
    guardar(fig, "fig_m10_auditoria.png")


# ------------------------------------------------------------
# 15. Clasificación de clientes por nivel
# ------------------------------------------------------------
def fig_clientes_niveles():
    counts = CLI["nivel"].value_counts().reindex(["Plata", "Oro", "VIP"])
    fig, ax = plt.subplots()
    for i, (nivel, n) in enumerate(counts.items()):
        ax.barh(i, n, color="white", edgecolor="#111", lw=1.1,
                hatch=HATCH[i % 3])
        ax.text(n, i, f"  {n}  ({n/len(CLI):.0%})", va="center", fontsize=9.5,
                fontweight="bold")
    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels(counts.index, fontsize=10)
    ax.set_xlabel("Clientes del programa de lealtad")
    ax.set_xlim(0, counts.max() * 1.35)
    ax.invert_yaxis()
    _sin_spines(ax, bottom=False)
    guardar(fig, "fig_clientes_niveles.png")


# ------------------------------------------------------------
# 16. Distribución de calificaciones de las encuestas
# ------------------------------------------------------------
def fig_encuestas():
    counts = ENC["calificacion_servicio"].value_counts().sort_index()
    fig, ax = plt.subplots()
    ax.bar(range(1, 6), counts.reindex(range(1, 6), fill_value=0).values,
           color="white", edgecolor="#111", lw=1.1, hatch="///")
    for x, n in counts.items():
        ax.text(x, n + 2500, f"{n:,}", ha="center", fontsize=8.5)
    ax.axvline(3.5, ls="--", color="#555", lw=1.1)
    ax.text(3.55, ax.get_ylim()[1] * 0.95, "umbral de servicio 3.5",
            fontsize=8, style="italic")
    ax.set_xticks(range(1, 6))
    ax.set_xlabel("Calificacion del servicio (1 a 5)")
    ax.set_ylabel("Encuestas")
    _sin_spines(ax)
    guardar(fig, "fig_encuestas.png")


if __name__ == "__main__":
    print("Generando figuras vintage (una tinta)...")
    fig_estrella()
    fig_kpis()
    fig_m1_ventas()
    fig_m1_mapa()
    fig_m2_leaderboard()
    fig_m3_ancla()
    fig_m3_embudo()
    fig_m4_cumplimiento()
    fig_m5_tension()
    fig_m6_forecast()
    fig_m7_ocupacion()
    fig_m8_churn()
    fig_m9_elasticidad()
    fig_m10_auditoria()
    fig_clientes_niveles()
    fig_encuestas()
    print("Listo. Figuras en:", OUT)
