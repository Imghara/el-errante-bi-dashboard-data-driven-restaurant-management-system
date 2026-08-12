# ============================================================
# TEST_FORECAST — Proyecto "El Errante" (BI & Incentivos)
# Pruebas del modelo de pronóstico (models/forecast.py, Fase 5 · M6)
#   • Serie semanal agrega correctamente por semana ISO × sucursal
#   • Features: códigos de sucursal FIJOS y semana/año
#   • entrenar_y_pronosticar devuelve estructura esperada y valores >= 0
#   • Conversión a insumos (kg de marisco y cajas de cerveza)
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import numpy as np
import pandas as pd
import pytest

from models.forecast import (
    CERVEZAS_POR_CAJA,
    KG_MARISCO_POR_SOPA,
    SUCURSAL_CODES,
    _features,
    convertir_insumos,
    entrenar_y_pronosticar,
    serie_semanal,
)

RATIOS_EJEMPLO = {
    "mix_bebidas": {"S1": 0.35, "S2": 0.30, "S3": 0.50},
    "sopa_por_dolar_alimento": {"S1": 0.001, "S2": 0.001, "S3": 0.001},
    "cerveza_por_dolar_bebida": {"S1": 0.01, "S2": 0.01, "S3": 0.01},
}


# ------------------------------------------------------------
# Serie semanal
# ------------------------------------------------------------
def test_serie_semanal_agrupa_por_semana():
    fechas = pd.date_range("2024-01-01", "2024-01-14", freq="D")  # 2 semanas ISO
    df = pd.DataFrame({
        "fecha_hora": fechas.tolist() * 2,
        "id_sucursal": ["S1"] * 14 + ["S2"] * 14,
        "monto": [100.0] * 28,
    })
    sem = serie_semanal(df)
    # 2 semanas × 2 sucursales
    assert len(sem) == 4
    assert sem["id_sucursal"].nunique() == 2
    assert set(sem.columns) >= {"inicio_sem", "id_sucursal", "ventas"}
    # 7 días × $100 por semana
    assert (sem["ventas"] == 700.0).all()


def test_serie_semanal_vacia():
    df = pd.DataFrame(columns=["fecha_hora", "id_sucursal", "monto"])
    sem = serie_semanal(df)
    assert sem.empty


# ------------------------------------------------------------
# Features (códigos de sucursal fijos)
# ------------------------------------------------------------
def test_features_codigos_fijos():
    serie = pd.DataFrame({
        "inicio_sem": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-01"]),
        "id_sucursal": ["S1", "S2", "S3"],
    })
    f = _features(serie)
    assert f["sucursal"].tolist() == [SUCURSAL_CODES["S1"], SUCURSAL_CODES["S2"], SUCURSAL_CODES["S3"]]
    assert (f["semana_ano"] == 1.0).all()
    assert (f["ano"] == 2024.0).all()


def test_features_sin_sucursal_conocida():
    serie = pd.DataFrame({
        "inicio_sem": pd.to_datetime(["2024-01-01"]),
        "id_sucursal": ["SX"],
    })
    f = _features(serie)
    assert pd.isna(f["sucursal"].iloc[0])  # mapa fijo -> NaN para códigos desconocidos


# ------------------------------------------------------------
# Entrenamiento y pronóstico (serie sintética suficiente)
# ------------------------------------------------------------
def _serie_sintetica(semanas: int = 80) -> pd.DataFrame:
    """Serie semanal sintética con estacionalidad anual por sucursal."""
    fechas = pd.date_range("2024-01-01", periods=semanas, freq="W-MON")
    filas = []
    for d in fechas:
        for sid, base in (("S1", 500_000), ("S2", 300_000), ("S3", 150_000)):
            factor = 1.0 + 0.4 * np.sin(2 * np.pi * d.week / 52)
            filas.append({"inicio_sem": d, "id_sucursal": sid, "ventas": base * factor})
    return pd.DataFrame(filas)


def test_entrenar_y_pronosticar_estructura():
    serie = _serie_sintetica()
    res = entrenar_y_pronosticar(serie, semanas=4)
    pron = res["pronostico"]
    assert len(pron) == 4 * 3  # 4 semanas × 3 sucursales
    assert set(pron.columns) >= {"inicio_sem", "id_sucursal", "pronostico", "inferior", "superior"}
    assert (pron["pronostico"] >= 0).all()
    assert (pron["inferior"] <= pron["superior"]).all()
    assert not np.isnan(res["mape_backtest"])
    assert not np.isnan(res["mape_referencia"])


def test_entrenar_requiere_historia():
    # White-box: depende del umbral interno de _backtest (train < 12 semanas -> NaN).
    # Si ese mínimo cambia en models/forecast.py, ajustar también este test.
    serie = _serie_sintetica(semanas=6)  # insuficiente para backtest
    res = entrenar_y_pronosticar(serie, semanas=4)
    assert np.isnan(res["mape_backtest"])  # guarda: no hay suficiente historia


# ------------------------------------------------------------
# Conversión a insumos
# ------------------------------------------------------------
def test_convertir_insumos():
    pron = pd.DataFrame({
        "inicio_sem": pd.to_datetime(["2024-12-30"] * 3),
        "id_sucursal": ["S1", "S2", "S3"],
        "pronostico": [1_000_000.0, 1_000_000.0, 1_000_000.0],
        "inferior": [800_000.0] * 3,
        "superior": [1_200_000.0] * 3,
    })
    ins = convertir_insumos(pron, RATIOS_EJEMPLO)
    # S1: mix 35% bebidas → ventas_alimentos = 650k → porciones = 650k×0.001 = 650
    fila = ins[ins["id_sucursal"] == "S1"].iloc[0]
    assert fila["porciones_sopa"] == pytest.approx(650.0)
    assert fila["kg_marisco"] == pytest.approx(650.0 * KG_MARISCO_POR_SOPA)
    # Cerveza: ventas_bebidas = 350k → unidades = 3.5k → cajas = 3.5k / 24
    assert fila["cajas_cerveza"] == pytest.approx(350_000 * 0.01 / CERVEZAS_POR_CAJA)
    assert "Semana" in ins.columns


def test_convertir_insumos_ratios_faltantes():
    """Sucursal sin ratio definido cae al promedio de los ratios conocidos."""
    pron = pd.DataFrame({
        "inicio_sem": pd.to_datetime(["2024-12-30"]),
        "id_sucursal": ["SX"],
        "pronostico": [1_000_000.0],
        "inferior": [800_000.0],
        "superior": [1_200_000.0],
    })
    ins = convertir_insumos(pron, RATIOS_EJEMPLO)
    assert not ins["kg_marisco"].isna().any()
    assert not ins["cajas_cerveza"].isna().any()
