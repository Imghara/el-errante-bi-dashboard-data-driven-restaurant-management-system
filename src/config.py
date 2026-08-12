# ============================================================
# CONFIG — Proyecto "El Errante" (BI & Incentivos)
# Fuente única de constantes: rutas, semillas, paleta, reglas.
# Ver DOCUMENTO_MAESTRO.md §5 (diseño) y §3 (modelo de datos).
# Generado: 2026-08-11 | Versión: 0.1.0 (Fase 0)
# ============================================================

from pathlib import Path

# ------------------------------------------------------------
# 1. RUTAS DEL PROYECTO
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
APP_DIR = PROJECT_ROOT / "app"

# ------------------------------------------------------------
# 2. REPRODUCIBILIDAD
# ------------------------------------------------------------
SEED = 42  # Semilla fija: la generación de datos es reproducible

# ------------------------------------------------------------
# 3. SISTEMA DE DISEÑO — Paleta "Océano & Arena" (DOCUMENTO_MAESTRO §5)
# ------------------------------------------------------------
COLOR_PRIMARY      = "#0B2545"  # Azul Océano Profundo (fondo)
COLOR_PRIMARY_LIGHT= "#13315C"  # Azul Marino (superficies)
COLOR_SUCCESS      = "#1BA39C"  # Turquesa Oleaje (metas cumplidas)
COLOR_WARNING      = "#F5A623"  # Ámbar Arena (vigilar)
COLOR_CRITICAL     = "#E74C3C"  # Coral Emergencia (alertas críticas)
COLOR_TEXT         = "#F8FAFC"  # Perla (texto)
COLOR_TEXT_DARK    = "#1E293B"  # Grafito
COLOR_TEXT_MUTED   = "#94A3B8"  # Plata (texto secundario)

# ------------------------------------------------------------
# 4. REGLAS DE NEGOCIO (DOCUMENTO_MAESTRO §2.3 y §6)
# ------------------------------------------------------------
# Umbrales del sistema de alertas (M5)
UMBRAL_ROI_CRITICO          = 0.45   # ROI promedio < 45% -> ALERTA ROJA
UMBRAL_CUMPLIMIENTO_CRITICO = 0.90   # % de meta < 90% -> ALERTA ROJA
UMBRAL_MIX_BEBIDAS          = 0.30   # Mix bebidas < 30% -> ALERTA ROJA
UMBRAL_CHURN_DIAS           = 45     # VIP/Oro sin visita en 45 días -> riesgo
UMBRAL_SERVICIO_SALUDABLE   = 3.5    # Calificación < 3.5 -> bandera amarilla

# Crecimiento y estacionalidad del generador (F1)
CRECIMIENTO_ANO2 = 1.5          # Año 2 factura 1.5x el Año 1 (irregular)
COSTO_VARIACION_MAX = 0.15      # Variación ±15% del costo de mariscos
PCT_VENTAS_CRM = 0.40           # 40% de tickets ligados al CRM

# Producto ancla (sin incentivo)
ANCLA_NOMBRE = "Sopa de Mariscos"

# ------------------------------------------------------------
# 5. ESTRUCTURA DE LAS SUCURSALES
# ------------------------------------------------------------
SUCURSALES = {
    "S1": {"entidad": "Nuevo León",   "ciudad": "Monterrey",       "meseros": 24, "perfil": "insignia"},
    "S2": {"entidad": "Coahuila",     "ciudad": "Saltillo/Torreón", "meseros": 16, "perfil": "familiar"},
    "S3": {"entidad": "Tamaulipas",   "ciudad": "Tampico/Reynosa",  "meseros": 8,  "perfil": "costera"},
}

# ------------------------------------------------------------
# 6. ARCHIVOS DE DATOS (esquema en estrella, DOCUMENTO_MAESTRO §3)
# ------------------------------------------------------------
CSV_DIM_SUCURSALES     = DATA_DIR / "dim_sucursales.csv"
CSV_DIM_MESEROS        = DATA_DIR / "dim_meseros.csv"
CSV_DIM_PRODUCTOS      = DATA_DIR / "dim_productos.csv"
CSV_DIM_CLIENTES_CRM   = DATA_DIR / "dim_clientes_crm.csv"
CSV_FACT_COSTOS        = DATA_DIR / "fact_costos_mensuales.csv"
CSV_FACT_PRESUPUESTO   = DATA_DIR / "fact_presupuesto.csv"
CSV_FACT_VENTAS        = DATA_DIR / "fact_ventas.csv"
CSV_FACT_ENCUESTAS     = DATA_DIR / "fact_encuestas_satisfaccion.csv"

ALL_CSV = [
    CSV_DIM_SUCURSALES,
    CSV_DIM_MESEROS,
    CSV_DIM_PRODUCTOS,
    CSV_DIM_CLIENTES_CRM,
    CSV_FACT_COSTOS,
    CSV_FACT_PRESUPUESTO,
    CSV_FACT_VENTAS,
    CSV_FACT_ENCUESTAS,
]
