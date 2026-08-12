# ============================================================
# TEST_INCENTIVOS — Proyecto "El Errante" (BI & Incentivos)
# Pruebas del motor de incentivos reutilizado por M2 y M10
# (app/modulos/m2_incentivos.py · _calc_incentivos)
# Reglas de negocio:
#   • El ancla (Sopa de Mariscos) NO genera comisión
#   • Bebidas y variantes con ROI > 100% reciben el multiplicador
#   • Utilidad = monto - costo_total
#   • Comisión = utilidad × tasa × multiplicador
# Autor: Buffy | Generado: 2026-08-12 | Versión: 0.1.0
# ============================================================

import pandas as pd
import pytest

from modulos.m2_incentivos import PALETA_SUCURSAL, _calc_incentivos

TASA = 0.05
MULT = 1.5


@pytest.fixture
def lineas() -> pd.DataFrame:
    """5 líneas de detalle que cubren todas las reglas del motor."""
    return pd.DataFrame([
        # id_mesero, id_producto, id_ticket, monto, costo_total, categoria, subcategoria, roi, es_ancla
        (1, 1, 10, 195.0, 113.1, "Alimento", "Ancla",     0.72, True),   # ancla -> sin comisión
        (1, 2, 10,  48.0,  26.4, "Bebida",  "Agua",       0.82, False),  # bebida -> multiplicador
        (2, 3, 11, 150.0,  87.0, "Alimento", "Variante",  1.20, False),  # variante ROI>1 -> multiplicador
        (2, 4, 11, 150.0,  93.0, "Alimento", "Variante",  0.61, False),  # variante ROI<1 -> sin multiplicador
        (3, 5, 12, 185.0, 114.7, "Alimento", "Principal", 0.61, False),  # principal -> sin multiplicador
    ], columns=[
        "id_mesero", "id_producto", "id_ticket", "monto", "costo_total",
        "categoria", "subcategoria", "roi", "es_ancla",
    ])


def test_utilidad(lineas):
    d = _calc_incentivos(lineas, TASA, MULT)
    assert (d["utilidad"] == d["monto"] - d["costo_total"]).all()


def test_ancla_sin_comision(lineas):
    d = _calc_incentivos(lineas, TASA, MULT)
    ancla = d[d["es_ancla"]].iloc[0]
    assert ancla["multiplicador"] == 1.0
    assert ancla["comision_linea"] == 0.0
    assert not ancla["_alto_roi"]  # np.bool_ de np.where es falsy


def test_bebidas_y_variantes_roi_alto_con_multiplicador(lineas):
    d = _calc_incentivos(lineas, TASA, MULT)
    bebida = d[(d["categoria"] == "Bebida")].iloc[0]
    assert bebida["multiplicador"] == MULT
    assert bebida["comision_linea"] == pytest.approx(bebida["utilidad"] * TASA * MULT)

    variante_alta = d[(d["subcategoria"] == "Variante") & (d["roi"] > 1.0)].iloc[0]
    assert variante_alta["multiplicador"] == MULT


def test_variante_roi_bajo_y_principal_sin_multiplicador(lineas):
    d = _calc_incentivos(lineas, TASA, MULT)
    variante_baja = d[(d["subcategoria"] == "Variante") & (d["roi"] < 1.0)].iloc[0]
    assert variante_baja["multiplicador"] == 1.0
    assert variante_baja["comision_linea"] == pytest.approx(variante_baja["utilidad"] * TASA)

    principal = d[d["subcategoria"] == "Principal"].iloc[0]
    assert principal["multiplicador"] == 1.0


def test_tasa_cero_no_genera_comision(lineas):
    d = _calc_incentivos(lineas, 0.0, MULT)
    assert (d["comision_linea"] == 0.0).all()


def test_paleta_cubre_las_3_sucursales():
    assert set(PALETA_SUCURSAL) == {"S1", "S2", "S3"}
