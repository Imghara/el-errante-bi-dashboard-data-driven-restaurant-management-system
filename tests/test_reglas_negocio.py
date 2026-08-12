# ============================================================
# TEST_REGLAS_NEGOCIO — Proyecto "El Errante" (BI & Incentivos)
# Reglas de negocio del histórico simulado (CP6 · Fase 6).
# Portadas a pytest desde src/validaciones.py (T1-T11):
#   T1  Volúmenes de datos por tabla
#   T2  Crecimiento Año 2 = 1.5x (tolerancia ±5%)
#   T3  Estacionalidad (Ene/Feb -20% · Mar/Abr +40% · Sep/Oct baja · Dic pico)
#   T4  40% de tickets ligados a CRM
#   T5  Producto ancla: único, sin incentivo
#   T6  Variación de costos (±15% alimentos · ±2% bebidas · 0% ancla)
#   T7  Presupuesto: reales 5-10% abajo meses bajos, +12% Cuaresma
#   T8  Correlación ancla -> más bebidas (regla M3)
#   T9  Tiempos de mesa válidos (rotación M7)
#   T10 Churn: clientes Oro/VIP en riesgo (M8)# T11 Elasticidad-precio identificable (M9)
#
# NOTA: la lógica espeja src/validaciones.py (QA de CP2). Si cambia una regla
# del generador, actualizar AMBOS sitios para evitar derivación.
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import pytest

from config import (
    ANCLA_NOMBRE,
    COSTO_VARIACION_MAX,
    CRECIMIENTO_ANO2,
    PCT_VENTAS_CRM,
    SUCURSALES,
)


# ------------------------------------------------------------
# T1 · Volúmenes de datos
# ------------------------------------------------------------
def test_t1_volumenes_dimensiones(sucursales, meseros, productos, clientes_crm):
    assert len(sucursales) == 3
    assert len(meseros) == 48
    assert len(productos) == 182
    assert len(clientes_crm) == 400


def test_t1_meseros_por_sucursal(meseros):
    por_suc = meseros["sucursal"].value_counts()
    for sid, info in SUCURSALES.items():
        assert por_suc.get(sid, 0) == info["meseros"], f"{sid}: {info['meseros']}"


def test_t1_categorias_menu(productos):
    cat = productos["categoria"].value_counts()
    assert cat.get("Alimento", 0) == 150
    assert cat.get("Bebida", 0) == 32


def test_t1_volumenes_hechos(costos, presupuesto, ventas, encuestas):
    assert len(costos) == 182 * 24
    assert len(presupuesto) == 3 * 24
    assert len(ventas) > 300_000
    assert len(encuestas) > 10_000


# ------------------------------------------------------------
# T2 · Crecimiento Año 2 = 1.5x (irregular)
# ------------------------------------------------------------
def test_t2_crecimiento_ano2(ventas_con_monto):
    anual = ventas_con_monto.groupby(ventas_con_monto["fecha_hora"].dt.year)["monto"].sum()
    assert {2024, 2025} <= set(anual.index)
    ratio = anual[2025] / anual[2024]
    assert abs(ratio - CRECIMIENTO_ANO2) <= CRECIMIENTO_ANO2 * 0.05, f"{ratio:.2f}x"


# ------------------------------------------------------------
# T3 · Estacionalidad mensual (año base 2024)
# ------------------------------------------------------------
def test_t3_estacionalidad(ventas_con_monto):
    v = ventas_con_monto.copy()
    v["mes"] = v["fecha_hora"].dt.month
    base24 = v[v["fecha_hora"].dt.year == 2024]
    prom = base24.groupby("mes")["monto"].sum().mean()
    mensual = base24.groupby("mes")["monto"].sum() / prom

    # Ene/Feb ~20% abajo (factor 0.8)
    assert 0.65 <= mensual.loc[[1, 2]].mean() <= 0.92
    # Mar/Abr +40% (factor 1.4) — Cuaresma
    assert 1.15 <= mensual.loc[[3, 4]].mean() <= 1.55
    # Sep/Oct temporada baja (< 1.0)
    assert mensual.loc[[9, 10]].mean() < 1.0
    # Dic pico de fin de año
    assert mensual.loc[12] > 1.05


# ------------------------------------------------------------
# T4 · 40% de tickets ligados al CRM
# ------------------------------------------------------------
def test_t4_pct_crm(ventas):
    pct = ventas["id_cliente_crm"].notna().mean()
    assert abs(pct - PCT_VENTAS_CRM) <= 0.02, f"{pct:.1%}"


# ------------------------------------------------------------
# T5 · Producto ancla (sin incentivo)
# ------------------------------------------------------------
def test_t5_unica_ancla(productos):
    anclas = productos[productos["es_ancla"]]
    assert len(anclas) == 1


def test_t5_ancla_sopa_sin_incentivo(productos):
    ancla = productos[productos["es_ancla"]].iloc[0]
    assert ancla["nombre_producto"] == ANCLA_NOMBRE
    assert not ancla["es_incentivable"]  # np.bool_ del CSV es falsy
    assert ancla["categoria"] == "Alimento"


# ------------------------------------------------------------
# T6 · Variación de costos mensuales
# ------------------------------------------------------------
def test_t6_variacion_costos(costos, productos):
    df = costos.merge(
        productos[["id_producto", "categoria", "es_ancla", "costo_base"]],
        on="id_producto",
    )
    df["var"] = df["costo_elaboracion"] / df["costo_base"] - 1

    alimentos = df[(df["categoria"] == "Alimento") & (~df["es_ancla"])]
    assert alimentos["var"].abs().max() <= COSTO_VARIACION_MAX + 0.005

    bebidas = df[df["categoria"] == "Bebida"]
    assert bebidas["var"].abs().max() <= 0.03

    ancla_var = df[df["es_ancla"]]["var"]
    assert (ancla_var.abs() < 0.001).all()


# ------------------------------------------------------------
# T7 · Presupuesto vs real
# ------------------------------------------------------------
def test_t7_presupuesto_vs_real(presupuesto, ventas_con_monto):
    v = ventas_con_monto.copy()
    v["mes_ano"] = v["fecha_hora"].dt.strftime("%Y-%m")
    real = v.groupby(["mes_ano", "id_sucursal"])["monto"].sum().rename("real_ventas").reset_index()
    df = presupuesto.merge(real, on=["mes_ano", "id_sucursal"])
    df["cumplimiento"] = df["real_ventas"] / df["meta_ventas"]

    meses_bajos = df["mes_ano"].isin(
        {"2024-01", "2024-02", "2024-09", "2024-10", "2025-01", "2025-02", "2025-09", "2025-10"}
    )
    meses_cuaresma = df["mes_ano"].isin({"2024-03", "2024-04", "2025-03", "2025-04"})

    assert 0.85 <= df[meses_bajos]["cumplimiento"].mean() <= 0.95
    assert 1.05 <= df[meses_cuaresma]["cumplimiento"].mean() <= 1.20
    assert 0.93 <= df[~meses_bajos & ~meses_cuaresma]["cumplimiento"].mean() <= 1.07


# ------------------------------------------------------------
# T8 · Correlación ancla -> más bebidas (regla M3)
# ------------------------------------------------------------
def test_t8_ancla_impulsa_bebidas(ventas_con_monto, productos):
    ancla_id = productos.loc[productos["es_ancla"], "id_producto"].iloc[0]
    tickets_ancla = set(ventas_con_monto[ventas_con_monto["id_producto"] == ancla_id]["id_ticket"])
    bebidas_ids = set(productos[productos["categoria"] == "Bebida"]["id_producto"])

    d = ventas_con_monto.copy()
    d["es_ancla_ticket"] = d["id_ticket"].isin(tickets_ancla)
    d["es_bebida"] = d["id_producto"].isin(bebidas_ids)
    por_ticket = d.groupby("id_ticket").agg(
        num_bebidas=("es_bebida", "sum"), con_ancla=("es_ancla_ticket", "first")
    ).reset_index()

    prom_con = por_ticket[por_ticket["con_ancla"]]["num_bebidas"].mean()
    prom_sin = por_ticket[~por_ticket["con_ancla"]]["num_bebidas"].mean()
    assert prom_con > prom_sin * 1.3, f"con ancla {prom_con:.2f} vs sin ancla {prom_sin:.2f}"


# ------------------------------------------------------------
# T9 · Tiempos de mesa válidos (rotación M7)
# ------------------------------------------------------------
def test_t9_tiempos_mesa(ventas):
    tickets = ventas.drop_duplicates("id_ticket")[
        ["id_ticket", "hora_apertura_mesa", "hora_cierre_mesa"]
    ]
    duracion = (
        tickets["hora_cierre_mesa"] - tickets["hora_apertura_mesa"]
    ).dt.total_seconds() / 60

    assert (duracion > 0).all()
    assert duracion.max() <= 240
    assert 45 <= duracion.mean() <= 120


# ------------------------------------------------------------
# T10 · Churn: clientes Oro/VIP en riesgo (M8)
# ------------------------------------------------------------
def test_t10_churn_oro_vip(clientes_crm, ventas):
    cli_uo = clientes_crm[clientes_crm["nivel"].isin(["Oro", "VIP"])]
    v = ventas[ventas["id_cliente_crm"].notna()]
    ultima = v.groupby("id_cliente_crm")["fecha_hora"].max()
    ref = ventas["fecha_hora"].max()
    dias = (ref - ultima).dt.days
    en_riesgo = cli_uo["id_cliente"].isin(dias[dias > 45].index).sum()
    assert 5 <= en_riesgo <= len(cli_uo) * 0.6, f"{en_riesgo} de {len(cli_uo)}"


# ------------------------------------------------------------
# T11 · Elasticidad-precio identificable (M9)
# ------------------------------------------------------------
def test_t11_elasticidad_responde_al_precio(ventas_con_monto, productos):
    """El volumen mensual responde negativamente al precio en todas las
    subcategorías (estimación log-log agrupada con efectos fijos)."""
    v = ventas_con_monto.copy()
    v["mes"] = v["fecha_hora"].dt.to_period("M")
    pv = v.groupby(["id_producto", "mes"]).agg(
        precio=("precio_unitario_aplicado", "mean"),
        volumen=("cantidad", "sum"),
    ).reset_index()
    pv["lp"] = np.log(pv["precio"])
    pv["lq"] = np.log(pv["volumen"])
    pv["lp_m"] = pv["lp"] - pv.groupby("mes")["lp"].transform("mean")
    pv["lq_m"] = pv["lq"] - pv.groupby("mes")["lq"].transform("mean")
    pv["lp_pm"] = pv["lp_m"] - pv.groupby("id_producto")["lp_m"].transform("mean")
    pv["lq_pm"] = pv["lq_m"] - pv.groupby("id_producto")["lq_m"].transform("mean")
    pv = pv.merge(productos[["id_producto", "subcategoria"]], on="id_producto")

    def pendiente_pool(g: pd.DataFrame) -> float:
        num = float((g["lp_pm"] * g["lq_pm"]).sum())
        den = float((g["lp_pm"] ** 2).sum())
        return num / den if den > 0 else np.nan

    pend = pv.groupby("subcategoria").apply(pendiente_pool, include_groups=False).dropna()
    assert not pend.empty
    assert (pend < 0).all(), pend.to_dict()
    assert pend.max() - pend.min() >= 0.4, f"rango {pend.max() - pend.min():.2f}"
