# ============================================================
# TEST_UTILS — Proyecto "El Errante" (BI & Incentivos)
# Pruebas de los helpers de formato y métricas (app/utils.py)
#   • fmt_money / fmt_pct (formato de KPIs)
#   • kpi_delta (delta vs periodo anterior)
#   • periodo_anterior (rango equivalente previo)
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import pandas as pd
import pytest

from utils import fmt_money, fmt_pct, kpi_delta, periodo_anterior


# ------------------------------------------------------------
# Formato
# ------------------------------------------------------------
def test_fmt_money():
    assert fmt_money(1234567.89) == "$1,234,568"
    assert fmt_money(0) == "$0"
    assert fmt_money(-500) == "$-500"


def test_fmt_pct():
    assert fmt_pct(0.456) == "45.6%"
    assert fmt_pct(1.0) == "100.0%"
    assert fmt_pct(0) == "0.0%"


# ------------------------------------------------------------
# kpi_delta
# ------------------------------------------------------------
def test_kpi_delta_positivo():
    texto, positivo = kpi_delta(120.0, 100.0)
    assert texto == "+20.0%"
    assert positivo is True


def test_kpi_delta_negativo():
    texto, positivo = kpi_delta(80.0, 100.0)
    assert texto == "-20.0%"
    assert positivo is False


def test_kpi_delta_sin_anterior():
    # No hay base de comparación -> delta vacío y considerado positivo
    texto, positivo = kpi_delta(100.0, 0.0)
    assert texto == ""
    assert positivo is True


def test_kpi_delta_anterior_none():
    texto, positivo = kpi_delta(100.0, None)
    assert texto == ""
    assert positivo is True


# ------------------------------------------------------------
# periodo_anterior
# ------------------------------------------------------------
def test_periodo_anterior():
    f_min = pd.Timestamp("2024-02-01")
    f_max = pd.Timestamp("2024-02-28")
    ant_min, ant_max = periodo_anterior(pd.DataFrame(), f_min, f_max)
    assert ant_min == pd.Timestamp("2024-01-05")
    assert ant_max == pd.Timestamp("2024-01-31")


def test_periodo_anterior_un_dia():
    f = pd.Timestamp("2024-03-15")
    ant_min, ant_max = periodo_anterior(pd.DataFrame(), f, f)
    # Duración 0: el rango anterior queda justo antes del día seleccionado
    assert ant_min == f
    assert ant_max == f - pd.Timedelta(days=1)
