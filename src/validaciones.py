# ============================================================
# VALIDACIONES — Proyecto "El Errante" (BI & Incentivos)
# QA de reglas de negocio · Fase 2 (CP2)
# ------------------------------------------------------------
# Verifica que los datos generados cumplen las especificaciones:
#   T1  Volúmenes de datos por tabla
#   T2  Crecimiento Año 2 = 1.5x (tolerancia ±5%)
#   T3  Estacionalidad (Ene/Feb -20% · Mar/Abr +40% · May/Dic picos)
#   T4  40% de tickets ligados a CRM
#   T5  Producto ancla: único, sin incentivo
#   T6  Variación de costos (±15% alimentos · ±2% bebidas · 0% ancla)
#   T7  Presupuesto: reales 5-10% abajo meses bajos, +12% Cuaresma
#   T8  Correlación ancla -> más bebidas (regla M3)
#   T9  Tiempos de mesa válidos (rotación M7)
#   T10 Churn: clientes Oro/VIP en riesgo (M8)
#   T11 Elasticidad-precio identificable (M9)
# Autor: Buffy | Generado: 2026-08-11 | Versión: 0.1.1
# Ejecución: python src/validaciones.py
# ============================================================

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    ANCLA_NOMBRE,
    COSTO_VARIACION_MAX,
    CRECIMIENTO_ANO2,
    CSV_DIM_CLIENTES_CRM,
    CSV_DIM_MESEROS,
    CSV_DIM_PRODUCTOS,
    CSV_DIM_SUCURSALES,
    CSV_FACT_COSTOS,
    CSV_FACT_ENCUESTAS,
    CSV_FACT_PRESUPUESTO,
    CSV_FACT_VENTAS,
    PCT_VENTAS_CRM,
    SUCURSALES,
)

# ------------------------------------------------------------
# Utilidades de reporte
# ------------------------------------------------------------
PASADAS = 0
FALLADAS = 0
DETALLES = []


def prueba(nombre: str, condicion: bool, detalle: str):
    """Registra el resultado de una prueba."""
    global PASADAS, FALLADAS
    if condicion:
        PASADAS += 1
        estado = "PASA"
    else:
        FALLADAS += 1
        estado = "FALLA"
    DETALLES.append(f"  [{estado}] {nombre}: {detalle}")
    print(f"  [{estado}] {nombre}: {detalle}")


def cargar_csv(ruta: Path, fechas: list[str] | None = None) -> pd.DataFrame:
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta} — ejecuta primero python src/data_factory.py")
    df = pd.read_csv(ruta)
    if fechas:
        for col in fechas:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
    return df


# ------------------------------------------------------------
# T1 · Volúmenes de datos
# ------------------------------------------------------------
def t1_volumenes(suc, mes, prod, cli, costos, pres, ventas, enc):
    esperado = {
        "sucursales": 3,
        "meseros": 48,
        "productos": 182,
        "clientes_crm": 400,
        "costos": 182 * 24,
        "presupuesto": 3 * 24,
    }
    real = {
        "sucursales": len(suc),
        "meseros": len(mes),
        "productos": len(prod),
        "clientes_crm": len(cli),
        "costos": len(costos),
        "presupuesto": len(pres),
    }
    for k, v in esperado.items():
        prueba(f"T1 volumen {k}", real[k] == v, f"{real[k]:,} (esperado {v:,})")

    # Meseros por sucursal (24/16/8)
    por_suc = mes["sucursal"].value_counts()
    for sid, info in SUCURSALES.items():
        prueba(
            f"T1 meseros en {sid}",
            por_suc.get(sid, 0) == info["meseros"],
            f"{por_suc.get(sid, 0)} (esperado {info['meseros']})",
        )

    # Alimentos 150 / Bebidas 32
    cat = prod["categoria"].value_counts()
    prueba("T1 alimentos=150", cat.get("Alimento", 0) == 150,
           f"{cat.get('Alimento', 0)}")
    prueba("T1 bebidas=32", cat.get("Bebida", 0) == 32, f"{cat.get('Bebida', 0)}")

    # Ventas y encuestas con datos
    prueba("T1 ventas no vacías", len(ventas) > 300_000, f"{len(ventas):,} líneas")
    prueba("T1 encuestas razonables", len(enc) > 10_000, f"{len(enc):,}")


# ------------------------------------------------------------
# T2 · Crecimiento Año 2 = 1.5x
# ------------------------------------------------------------
def t2_crecimiento(ventas):
    v = ventas.copy()
    v["monto"] = v["precio_unitario_aplicado"] * v["cantidad"]
    anual = v.groupby(v["fecha_hora"].dt.year)["monto"].sum()
    if 2024 not in anual.index or 2025 not in anual.index:
        prueba("T2 crecimiento", False, "faltan años completos")
        return
    ratio = anual[2025] / anual[2024]
    tol = 0.05
    ok = abs(ratio - CRECIMIENTO_ANO2) <= CRECIMIENTO_ANO2 * tol
    prueba("T2 crecimiento Año2/Año1", ok,
           f"{ratio:.2f}x (meta {CRECIMIENTO_ANO2}x ±{tol:.0%}) — 2024: ${anual[2024]:,.0f}, 2025: ${anual[2025]:,.0f}")


# ------------------------------------------------------------
# T3 · Estacionalidad mensual
# ------------------------------------------------------------
def t3_estacionalidad(ventas):
    v = ventas.copy()
    v["monto"] = v["precio_unitario_aplicado"] * v["cantidad"]
    v["mes"] = v["fecha_hora"].dt.month
    # Promedio mensual 2024 (año base sin crecimiento)
    base24 = v[v["fecha_hora"].dt.year == 2024]
    prom = base24.groupby("mes")["monto"].sum().mean()  # promedio del mes

    mensual = base24.groupby("mes")["monto"].sum() / prom

    # Ene/Feb deben estar ~20% abajo (factor 0.8)
    ene_feb = mensual.loc[[1, 2]].mean()
    prueba("T3 Ene/Feb -20%", 0.65 <= ene_feb <= 0.92,
           f"factor {ene_feb:.2f} (esperado ~0.80)")

    # Mar/Abr +40% (factor 1.4)
    mar_abr = mensual.loc[[3, 4]].mean()
    prueba("T3 Mar/Abr +40%", 1.15 <= mar_abr <= 1.55,
           f"factor {mar_abr:.2f} (esperado ~1.40)")

    # Sep/Oct bajos (< 1.0)
    sep_oct = mensual.loc[[9, 10]].mean()
    prueba("T3 Sep/Oct bajos", sep_oct < 1.0,
           f"factor {sep_oct:.2f} (esperado <1.0)")

    # Dic pico
    dic = mensual.loc[12]
    prueba("T3 Dic pico", dic > 1.05, f"factor {dic:.2f} (esperado >1.05)")


# ------------------------------------------------------------
# T4 · 40% de tickets ligados a CRM
# ------------------------------------------------------------
def t4_crm(ventas):
    pct = ventas["id_cliente_crm"].notna().mean()
    prueba("T4 tickets con CRM", abs(pct - PCT_VENTAS_CRM) <= 0.02,
           f"{pct:.1%} (meta {PCT_VENTAS_CRM:.0%})")


# ------------------------------------------------------------
# T5 · Producto ancla
# ------------------------------------------------------------
def t5_ancla(prod):
    anclas = prod[prod["es_ancla"]]
    prueba("T5 exactamente 1 ancla", len(anclas) == 1,
           f"{len(anclas)} registros")
    if len(anclas) == 1:
        ancla = anclas.iloc[0]
        prueba("T5 ancla es Sopa de Mariscos",
               ancla["nombre_producto"] == ANCLA_NOMBRE,
               ancla["nombre_producto"])
        prueba("T5 ancla sin incentivo", ancla["es_incentivable"] == False,
               f"es_incentivable={ancla['es_incentivable']}")
        prueba("T5 ancla en categoría Alimento",
               ancla["categoria"] == "Alimento", ancla["categoria"])


# ------------------------------------------------------------
# T6 · Variación de costos mensuales
# ------------------------------------------------------------
def t6_costos(costos, prod):
    # Variación por producto: costo del mes vs costo_base (en dim_productos)
    df = costos.merge(
        prod[["id_producto", "categoria", "es_ancla", "costo_base"]], on="id_producto"
    )
    df["var"] = df["costo_elaboracion"] / df["costo_base"] - 1

    # Alimentos (no ancla): |var| <= 15%
    alimentos = df[(df["categoria"] == "Alimento") & (~df["es_ancla"])]
    max_ali = alimentos["var"].abs().max()
    prueba("T6 alimentos ±15%", max_ali <= COSTO_VARIACION_MAX + 0.005,
           f"máx |var| = {max_ali:.1%} (límite {COSTO_VARIACION_MAX:.0%})")

    # Bebidas: |var| <= 3% (generador usa ±2%)
    bebidas = df[df["categoria"] == "Bebida"]
    max_beb = bebidas["var"].abs().max()
    prueba("T6 bebidas ±2%", max_beb <= 0.03,
           f"máx |var| = {max_beb:.1%} (límite 3%)")

    # Ancla: var = 0
    ancla_var = df[df["es_ancla"]]["var"]
    prueba("T6 ancla sin variación", (ancla_var.abs() < 0.001).all(),
           f"máx |var| = {ancla_var.abs().max():.4%}")


# ------------------------------------------------------------
# T7 · Presupuesto vs real
# ------------------------------------------------------------
def t7_presupuesto(pres, ventas):
    v = ventas.copy()
    v["mes_ano"] = v["fecha_hora"].dt.strftime("%Y-%m")
    v["monto"] = v["precio_unitario_aplicado"] * v["cantidad"]
    real = v.groupby(["mes_ano", "id_sucursal"])["monto"].sum().rename("real_ventas").reset_index()
    df = pres.merge(real, on=["mes_ano", "id_sucursal"])
    df["cumplimiento"] = df["real_ventas"] / df["meta_ventas"]

    meses_bajos = df["mes_ano"].isin(
        {"2024-01", "2024-02", "2024-09", "2024-10", "2025-01", "2025-02", "2025-09", "2025-10"}
    )
    meses_cuaresma = df["mes_ano"].isin({"2024-03", "2024-04", "2025-03", "2025-04"})

    bajos = df[meses_bajos]["cumplimiento"]
    prueba("T7 meses bajos 5-10% abajo",
           0.85 <= bajos.mean() <= 0.95,
           f"cumplimiento promedio {bajos.mean():.1%} (esperado ~92.5%)")

    cuaresma = df[meses_cuaresma]["cumplimiento"]
    prueba("T7 Cuaresma +12%",
           1.05 <= cuaresma.mean() <= 1.20,
           f"cumplimiento promedio {cuaresma.mean():.1%} (esperado ~112%)")

    resto = df[~meses_bajos & ~meses_cuaresma]["cumplimiento"]
    prueba("T7 meses normales ~100%",
           0.93 <= resto.mean() <= 1.07,
           f"cumplimiento promedio {resto.mean():.1%}")


# ------------------------------------------------------------
# T8 · Correlación ancla -> más bebidas (regla M3)
# ------------------------------------------------------------
def t8_correlacion_ancla(ventas, prod):
    ancla_id = prod.loc[prod["es_ancla"], "id_producto"].iloc[0]
    # Tickets que incluyen el ancla
    tickets_ancla = set(ventas[ventas["id_producto"] == ancla_id]["id_ticket"].unique())
    ventas["es_ancla_ticket"] = ventas["id_ticket"].isin(tickets_ancla)

    bebidas_ids = set(prod[prod["categoria"] == "Bebida"]["id_producto"].unique())
    ventas["es_bebida"] = ventas["id_producto"].isin(bebidas_ids)

    por_ticket = ventas.groupby("id_ticket").agg(
        num_bebidas=("es_bebida", "sum"),
        con_ancla=("es_ancla_ticket", "first"),
    ).reset_index()
    con_ancla = por_ticket[por_ticket["con_ancla"]]["num_bebidas"]
    sin_ancla = por_ticket[~por_ticket["con_ancla"]]["num_bebidas"]

    prom_con = con_ancla.mean()
    prom_sin = sin_ancla.mean()
    prueba("T8 mesas con ancla piden más bebidas",
           prom_con > prom_sin * 1.3,
           f"con ancla {prom_con:.2f} bebidas vs sin ancla {prom_sin:.2f}")


# ------------------------------------------------------------
# T9 · Tiempos de mesa válidos (rotación M7)
# ------------------------------------------------------------
def t9_tiempos_mesa(ventas):
    tickets = ventas.drop_duplicates("id_ticket")[
        ["id_ticket", "hora_apertura_mesa", "hora_cierre_mesa"]
    ]
    tickets["duracion_min"] = (
        pd.to_datetime(tickets["hora_cierre_mesa"]) - pd.to_datetime(tickets["hora_apertura_mesa"])
    ).dt.total_seconds() / 60

    prueba("T9 duraciones positivas", (tickets["duracion_min"] > 0).all(),
           f"mín {tickets['duracion_min'].min():.0f} min")
    prueba("T9 duraciones razonables (<4h)",
           tickets["duracion_min"].max() <= 240,
           f"máx {tickets['duracion_min'].max():.0f} min")
    prueba("T9 promedio 45-120 min",
           45 <= tickets["duracion_min"].mean() <= 120,
           f"promedio {tickets['duracion_min'].mean():.0f} min")


# ------------------------------------------------------------
# T10 · Churn: clientes VIP/Oro sin visita en los últimos 45 días (M8)
# ------------------------------------------------------------
def t10_churn(cli, ventas):
    """Debe existir una población de clientes Oro/VIP en riesgo de deserción
    (>45 días sin visita al cierre del histórico) para que el módulo M8
    tenga datos que analizar."""
    cli_uo = cli[cli["nivel"].isin(["Oro", "VIP"])]
    v = ventas[ventas["id_cliente_crm"].notna()]
    ultima = v.groupby("id_cliente_crm")["fecha_hora"].max()
    ref = ventas["fecha_hora"].max()
    dias = (ref - ultima).dt.days
    en_riesgo = cli_uo["id_cliente"].isin(dias[dias > 45].index).sum()
    prueba(
        "T10 clientes Oro/VIP en riesgo (>45d)",
        5 <= en_riesgo <= len(cli_uo) * 0.6,
        f"{en_riesgo} de {len(cli_uo)} Oro/VIP (corte: {ref:%Y-%m-%d})",
    )


# ------------------------------------------------------------
# T11 · Elasticidad-precio identificable (M9)
# ------------------------------------------------------------
def t11_elasticidad(ventas, prod):
    """Con los experimentos de precio del generador (M9), el volumen mensual
    debe responder NEGATIVAMENTE al precio. Estimación AGRUPADA por
    subcategoría con efectos fijos de producto y de mes (dos vías):
    pendiente log-log < 0 en todas las subcategorías y con dispersión real
    (bebidas inelásticas vs ceviches sensibles, especificación M9)."""
    v = ventas.copy()
    v["mes"] = v["fecha_hora"].dt.to_period("M")
    pv = v.groupby(["id_producto", "mes"]).agg(
        precio=("precio_unitario_aplicado", "mean"),
        volumen=("cantidad", "sum"),
    ).reset_index()
    pv["lp"] = np.log(pv["precio"])
    pv["lq"] = np.log(pv["volumen"])
    # Efectos fijos: primero mes (estacionalidad/crecimiento/inflación comunes),
    # luego producto (tamaño) -> variación dentro de producto y de mes
    pv["lp_m"] = pv["lp"] - pv.groupby("mes")["lp"].transform("mean")
    pv["lq_m"] = pv["lq"] - pv.groupby("mes")["lq"].transform("mean")
    pv["lp_pm"] = pv["lp_m"] - pv.groupby("id_producto")["lp_m"].transform("mean")
    pv["lq_pm"] = pv["lq_m"] - pv.groupby("id_producto")["lq_m"].transform("mean")
    pv = pv.merge(prod[["id_producto", "subcategoria"]], on="id_producto")

    def pendiente_pool(g: pd.DataFrame) -> float:
        num = float((g["lp_pm"] * g["lq_pm"]).sum())
        den = float((g["lp_pm"] ** 2).sum())
        return num / den if den > 0 else np.nan

    pend = pv.groupby("subcategoria").apply(
        pendiente_pool, include_groups=False
    ).dropna()

    todas_neg = (pend < 0).all()
    prueba("T11 todas las subcategorías responden al precio", todas_neg,
           ", ".join(f"{k}: {v:.2f}" for k, v in pend.items()))
    dispersion = pend.max() - pend.min()
    prueba("T11 dispersión de elasticidad entre subcategorías", dispersion >= 0.4,
           f"rango {dispersion:.2f} (bebidas inelásticas vs ceviches sensibles)")


# ------------------------------------------------------------
# ORQUESTADOR
# ------------------------------------------------------------
def main():
    print("== Cargando CSV ==")
    suc = cargar_csv(CSV_DIM_SUCURSALES)
    mes = cargar_csv(CSV_DIM_MESEROS)
    prod = cargar_csv(CSV_DIM_PRODUCTOS)
    cli = cargar_csv(CSV_DIM_CLIENTES_CRM)
    costos = cargar_csv(CSV_FACT_COSTOS)
    pres = cargar_csv(CSV_FACT_PRESUPUESTO)
    ventas = cargar_csv(
        CSV_FACT_VENTAS,
        fechas=["fecha_hora", "hora_apertura_mesa", "hora_cierre_mesa"],
    )
    enc = cargar_csv(CSV_FACT_ENCUESTAS)

    print("\n== T1 · Volúmenes ==")
    t1_volumenes(suc, mes, prod, cli, costos, pres, ventas, enc)
    print("\n== T2 · Crecimiento 1.5x ==")
    t2_crecimiento(ventas)
    print("\n== T3 · Estacionalidad ==")
    t3_estacionalidad(ventas)
    print("\n== T4 · CRM 40% ==")
    t4_crm(ventas)
    print("\n== T5 · Producto ancla ==")
    t5_ancla(prod)
    print("\n== T6 · Variación de costos ==")
    t6_costos(costos, prod)
    print("\n== T7 · Presupuesto vs real ==")
    t7_presupuesto(pres, ventas)
    print("\n== T8 · Correlación ancla->bebidas ==")
    t8_correlacion_ancla(ventas, prod)
    print("\n== T9 · Tiempos de mesa ==")
    t9_tiempos_mesa(ventas)
    print("\n== T10 · Churn (M8) ==")
    t10_churn(cli, ventas)
    print("\n== T11 · Elasticidad (M9) ==")
    t11_elasticidad(ventas, prod)

    print(f"\n{'='*50}")
    print(f"RESULTADO CP2: {PASADAS} pruebas pasadas, {FALLADAS} falladas")
    if FALLADAS == 0:
        print("CP2 SUPERADO — los datos cumplen las reglas de negocio")
    else:
        print("CP2 NO SUPERADO — revisar las pruebas FALLA anteriores")
    print("=" * 50)
    return FALLADAS


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
