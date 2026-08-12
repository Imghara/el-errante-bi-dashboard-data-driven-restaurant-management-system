# ============================================================
# FORECAST — Proyecto "El Errante" (BI & Incentivos)
# Modelo de pronóstico de ventas e inventario (Fase 5 · M6)
# ------------------------------------------------------------
# Modelo: regresión estacional ligera con GradientBoosting sobre
# la serie SEMANAL de ventas por sucursal (features: semana del
# año, año y sucursal).
#
# Decisión documentada (validada con backtest):
#   • Serie diaria + features de mes/día de semana → MAPE ~52%
#     (el ruido diario domina; std diario ≈ 35% de la media).
#   • Serie semanal + semana del año (sin tendencia ni mes) → MAPE
#     ~20% por fila semanal y supera a la referencia ingenua (~42%):
#     la estacionalidad anual es la señal dominante (Cuaresma +40%,
#     Ene/Feb −20%, picos de mayo y diciembre).
# Se reporta además el MAPE de una referencia ingenua (persistencia)
# para dar contexto al error del modelo.
# Salidas:
#   • Pronóstico semanal a N semanas con banda de confianza
#   • Backtest de las últimas N semanas (MAPE) + referencia ingenua
#   • Conversión a insumos: kg de marisco (Sopa Ancla ≈ 0.35 kg/
#     porción) y cajas de cerveza (24 uds/caja)
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.2.0
# ============================================================

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

# ------------------------------------------------------------
# Constantes de conversión a insumos (DOCUMENTO_MAESTRO §6 · M6)
# ------------------------------------------------------------
KG_MARISCO_POR_SOPA = 0.35   # kg de marisco por porción de Sopa Ancla
CERVEZAS_POR_CAJA = 24       # unidades de cerveza por caja
PRECIO_MARISCO_KG = 240.0    # $ por kg al mayorista (costa de Tamaulipas)

HORIZONTE_DEFAULT_SEMANAS = 4


# ------------------------------------------------------------
# Serie semanal por sucursal
# ------------------------------------------------------------
def serie_semanal(df: pd.DataFrame) -> pd.DataFrame:
    """Ventas semanales (ISO) por sucursal a partir de fact_ventas."""
    df = df.copy()
    df["dia"] = pd.to_datetime(df["fecha_hora"]).dt.normalize()
    diaria = (
        df.groupby(["dia", "id_sucursal"])["monto"]
        .sum()
        .rename("ventas")
        .reset_index()
    )
    iso = pd.to_datetime(diaria["dia"]).dt.isocalendar()
    diaria["inicio_sem"] = pd.to_datetime(
        iso["year"].astype(str) + "-W" + iso["week"].astype(str) + "-1",
        format="%G-W%V-%u",
    )
    semanal = (
        diaria.groupby(["inicio_sem", "id_sucursal"])["ventas"]
        .sum()
        .reset_index()
        .sort_values(["inicio_sem", "id_sucursal"])
    )
    return semanal


# Códigos de sucursal FIJOS (la codificación por orden de aparición
# rompería el modelo si un subconjunto llegara en distinto orden).
SUCURSAL_CODES = {"S1": 0.0, "S2": 1.0, "S3": 2.0}


# ------------------------------------------------------------
# Ingeniería de features
# ------------------------------------------------------------
def _features(serie: pd.DataFrame) -> pd.DataFrame:
    """Features estacionales sobre la serie semanal.

    - semana_ano: 1-53 (captura Cuaresma, picos de mayo/dic, cuesta de enero)
    - ano: 2024/2025 (crecimiento anual 1.5× no lineal: el año captura el
      salto entre temporadas)
    - sucursal: 0-2 con mapa FIJO (efecto fijo por entidad)

    Validado con backtest: añadir tendencia/mes degradaba el MAPE porque la
    tendencia lineal compite con el crecimiento irregular 1.5× y el mes es
    redundante con la semana del año.
    """
    d = pd.to_datetime(serie["inicio_sem"])
    iso = d.dt.isocalendar()
    return pd.DataFrame({
        "semana_ano": iso["week"].astype(float),
        "ano": iso["year"].astype(float),
        "sucursal": serie["id_sucursal"].map(SUCURSAL_CODES).astype(float),
    })


# ------------------------------------------------------------
# Backtest
# ------------------------------------------------------------
def _backtest(serie: pd.DataFrame, semanas: int, seed: int) -> tuple:
    """Re-entrena sin las últimas N semanas y mide el MAPE semanal.

    Devuelve (mape_modelo, mape_referencia). La referencia ingenua es
    la persistencia: repetir el promedio de las 4 semanas previas por
    sucursal (contexto del error).
    """
    corte = serie["inicio_sem"].max() - pd.Timedelta(weeks=semanas)
    train = serie[serie["inicio_sem"] <= corte]
    test = serie[serie["inicio_sem"] > corte]
    if len(train) < 12 or len(test) < 1:
        return float("nan"), float("nan")

    bt = GradientBoostingRegressor(
        n_estimators=400, learning_rate=0.05, max_depth=4, random_state=seed,
    )
    bt.fit(_features(train), train["ventas"])
    pred_modelo = bt.predict(_features(test))
    real = np.maximum(test["ventas"].astype(float).values, 1.0)
    mape_modelo = float(np.mean(np.abs((real - pred_modelo) / real)))

    # Referencia ingenua: promedio de las 4 semanas previas por sucursal
    ref = train[train["inicio_sem"] > corte - pd.Timedelta(weeks=4)]
    nivel = ref.groupby("id_sucursal")["ventas"].mean()
    pred_ref = np.maximum(test["id_sucursal"].map(nivel).values, 1.0)
    mape_ref = float(np.mean(np.abs((real - pred_ref) / real)))

    return mape_modelo, mape_ref


# ------------------------------------------------------------
# Entrenamiento y pronóstico
# ------------------------------------------------------------
def entrenar_y_pronosticar(
    serie: pd.DataFrame,
    semanas: int = HORIZONTE_DEFAULT_SEMANAS,
    seed: int = 42,
) -> dict:
    """Entrena el modelo sobre la serie semanal y pronostica N semanas.

    Devuelve un dict con modelo, MAPEs de backtest, histórico semanal y
    pronóstico (con banda de confianza ±1.28σ en escala log).
    """
    serie = serie.sort_values(["inicio_sem", "id_sucursal"]).reset_index(drop=True)
    X = _features(serie)
    y = np.log1p(serie["ventas"].astype(float))

    modelo = GradientBoostingRegressor(
        n_estimators=400, learning_rate=0.05, max_depth=4, random_state=seed,
    )
    modelo.fit(X, y)

    # Residuos en escala log → banda de confianza (±1.28σ ≈ 80%)
    residuos = y - modelo.predict(X)
    sigma = float(np.std(residuos))

    mape_modelo, mape_ref = _backtest(serie, semanas, seed)

    # ---- Cuadrícula futura: N semanas × sucursales ----
    ultima = serie["inicio_sem"].max()
    suc_unicas = sorted(serie["id_sucursal"].unique())
    futuros = [ultima + pd.Timedelta(weeks=i + 1) for i in range(semanas)]
    cuadricula = pd.DataFrame(
        [(d, s) for d in futuros for s in suc_unicas],
        columns=["inicio_sem", "id_sucursal"],
    )
    log_pred = modelo.predict(_features(cuadricula))
    pred = np.expm1(log_pred)

    pronostico = cuadricula.copy()
    pronostico["pronostico"] = pred
    pronostico["inferior"] = np.expm1(log_pred - 1.28 * sigma)
    pronostico["superior"] = np.expm1(log_pred + 1.28 * sigma)
    pronostico["pronostico"] = pronostico["pronostico"].clip(lower=0)
    pronostico["inferior"] = pronostico["inferior"].clip(lower=0)

    return {
        "mape_backtest": mape_modelo,
        "mape_referencia": mape_ref,
        "historico": serie,
        "pronostico": pronostico,
    }


# ------------------------------------------------------------
# Conversión a insumos
# ------------------------------------------------------------
def convertir_insumos(pronostico: pd.DataFrame, ratios: dict) -> pd.DataFrame:
    """Convierte el pronóstico de $ en kg de marisco y cajas de cerveza.

    ratios: dict con las claves
      - mix_bebidas: {sucursal: fracción de ingresos por bebidas}
      - sopa_por_dolar_alimento: unidades de Sopa Ancla por $ de alimentos
      - cerveza_por_dolar_bebida: unidades de cerveza por $ de bebidas
    """
    p = pronostico.copy()
    p["pct_bebidas"] = p["id_sucursal"].map(ratios["mix_bebidas"]).fillna(0.33)
    p["ventas_alimentos"] = p["pronostico"] * (1 - p["pct_bebidas"])
    p["ventas_bebidas"] = p["pronostico"] * p["pct_bebidas"]
    # Ratios por sucursal → map + fillna con el promedio ponderado
    sopa_ratio = p["id_sucursal"].map(ratios["sopa_por_dolar_alimento"])
    sopa_ratio = sopa_ratio.fillna(
        np.mean(list(ratios["sopa_por_dolar_alimento"].values()))
    )
    cerveza_ratio = p["id_sucursal"].map(ratios["cerveza_por_dolar_bebida"])
    cerveza_ratio = cerveza_ratio.fillna(
        np.mean(list(ratios["cerveza_por_dolar_bebida"].values()))
    )
    p["porciones_sopa"] = p["ventas_alimentos"] * sopa_ratio
    p["kg_marisco"] = p["porciones_sopa"] * KG_MARISCO_POR_SOPA
    p["unidades_cerveza"] = p["ventas_bebidas"] * cerveza_ratio
    p["cajas_cerveza"] = p["unidades_cerveza"] / CERVEZAS_POR_CAJA

    p["Semana"] = p["inicio_sem"].dt.strftime("%d %b")
    return p.sort_values(["inicio_sem", "id_sucursal"])
