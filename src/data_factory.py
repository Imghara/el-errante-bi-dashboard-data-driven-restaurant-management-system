# ============================================================
# DATA_FACTORY — Proyecto "El Errante" (BI & Incentivos)
# Generador de datos sintéticos · Fase 1 (CP1)
# ------------------------------------------------------------
# Genera los 8 CSV del esquema en estrella (DOCUMENTO_MAESTRO §3):
#   dim_sucursales, dim_meseros, dim_productos, dim_clientes_crm,
#   fact_costos_mensuales, fact_presupuesto, fact_ventas,
#   fact_encuestas_satisfaccion
# ------------------------------------------------------------
# Reglas de negocio aplicadas (DOCUMENTO_MAESTRO §2.3):
#   • Año 2 = 1.5x Año 1 (crecimiento irregular, no lineal)
#   • Estacionalidad: Ene/Feb -20% · Sep/Oct baja · Mar/Abr +40%
#     (Cuaresma) · May (Día de las Madres) y Dic (fin de año) picos
#   • Costos de mariscos ±15% mensual (excepto producto ancla)
#   • Ancla (Sopa de Mariscos) ~25% del volumen de alimentos, sin incentivos
#   • 40% de tickets ligados al CRM (programa de lealtad)
#   • Presupuesto optimista: real 5-10% abajo en meses bajos, +12% en Cuaresma
#   • Mesas con ancla -> más líneas de bebidas (correlación M3)
#   • Elasticidad-precio simulada (M9): la demanda responde a experimentos de
#     precio por producto/mes (promos y menús de temporada, wobble mean-reverting
#     ~±4%) según coeficientes por regla de negocio: bebidas de marketing y ancla
#     INELÁSTICAS (-0.15 a -0.55), ceviches SENSIBLES (-1.5), resto -0.6 a -1.0
# Autor: Buffy | Generado: 2026-08-11 | Versión: 0.2.0 (M9 elasticidad)
# Ejecución: python src/data_factory.py
# ============================================================

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Asegurar importación de config.py desde src/
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
    DATA_DIR,
    PCT_VENTAS_CRM,
    SEED,
    SUCURSALES,
)

# ------------------------------------------------------------
# 1. CONSTANTES DE GENERACIÓN
# ------------------------------------------------------------
FECHA_INICIO = datetime(2024, 1, 1)   # Año 1
FECHA_FIN = datetime(2025, 12, 31)    # Año 2 (cierre del histórico)
NUM_CLIENTES_CRM = 400

# Probabilidades de deserción simulada por nivel (M8 · Churn Rate)
# Clientes "inactivos" dejan de visitar en una fecha determinada, creando
# el escenario real para el análisis de deserción de 45 días.
PROB_CHURN = {"Plata": 0.12, "Oro": 0.28, "VIP": 0.38}

# Factores estacionales mensuales (base promedio = 1.0)
SEASONAL = {
    1: 0.80, 2: 0.80, 3: 1.40, 4: 1.40,   # Ene/Feb cuesta · Mar/Abr Cuaresma
    5: 1.15, 6: 1.00, 7: 1.00, 8: 1.00,   # May Día de las Madres
    9: 0.85, 10: 0.85, 11: 1.00, 12: 1.25  # Sep/Oct baja · Dic fiestas
}

# Factores por día de la semana (lunes=0 ... domingo=6)
WEEKDAY = {0: 0.82, 1: 0.88, 2: 0.88, 3: 0.98, 4: 1.10, 5: 1.22, 6: 1.16}

# Tickets base por día (promedio anual, antes de factores)
BASE_TICKETS = {"S1": 90, "S2": 58, "S3": 32}

# Probabilidad de que un ticket incluya el ancla (=> ~25% del volumen de alimentos)
PROB_ANCLA = 0.50

# Peso de bebidas por tipo (por sucursal): Refresco, Agua, Cerveza
PESO_BEBIDAS = {
    "S1": {"Refresco": 0.35, "Agua": 0.30, "Cerveza": 0.35},   # flujo corporativo
    "S2": {"Refresco": 0.50, "Agua": 0.30, "Cerveza": 0.20},   # público familiar
    "S3": {"Refresco": 0.25, "Agua": 0.25, "Cerveza": 0.50},   # cerca del proveedor
}

# ------------------------------------------------------------
# 1b. ELASTICIDAD-PRECIO SIMULADA (M9 · Matriz de Elasticidad)
# ------------------------------------------------------------
# La demanda responde al precio en la FRECUENCIA DE PEDIDO (no en la cantidad
# de línea):  peso_demanda = peso_base * (1 + wobble) ** elasticidad
#   • wobble = experimento de precio por producto/mes (promos regionales, menús
#     de temporada), autorregresivo (un experimento dura ~4 meses) y
#     MEAN-REVERTING → no rompe el crecimiento 1.5x ni la estacionalidad (CP2)
#   • Aplicar la respuesta al peso de muestreo (probabilidad de pedir el
#     producto) evita la cuantización de la cantidad y da una señal continua
#   • Coeficientes por regla de negocio (DOCUMENTO_MAESTRO §6 · M9):
#       - Ancla (Sopa de Mariscos): INELÁSTICA (-0.15) — los clientes vienen por ella
#       - Bebidas de marketing (aguas naturales, micheladas/preparados): -0.30
#       - Cervezas: -0.45 · Refrescos: -0.55 (hábito arraigado)
#       - Ceviches: -1.50 (altamente sensibles, especificación M9)
#       - Premium: -0.60 · Temporada: -1.00 · Familiar: -0.80 · Resto: -0.90
ELAST_WOBBLE_PERSIST = 0.65   # persistencia del experimento de precio (AR1)
ELAST_WOBBLE_SD = 0.032       # sd del shock mensual (sd efectiva ~4.2%)
NUM_MESES = 24                # meses del histórico (2024-01 .. 2025-12)


def elasticidad_producto(nombre: str, categoria: str, sub: str, etiquetas: str) -> float:
    """Coeficiente de elasticidad-precio SIMULADO (negativo: al subir el precio
    cae la demanda). Reglas de negocio documentadas en DOCUMENTO_MAESTRO §6 · M9."""
    # Etiquetas vacías ("") se leen como NaN desde CSV; normalizar a str
    etiquetas = etiquetas if isinstance(etiquetas, str) else ""
    if sub == "Ancla":
        return -0.15                       # ancla: los clientes vienen por ella
    if categoria == "Bebida":
        if "vistoso" in etiquetas or "preparado" in etiquetas:
            return -0.30                   # bebidas de marketing: marca fuerte
        if sub == "Cerveza":
            return -0.45                   # cervezas: hábito arraigado
        return -0.55                       # refrescos: consumo habitual
    if "Ceviche" in nombre:
        return -1.50                       # altamente sensibles (especificación)
    if "premium" in etiquetas:
        return -0.60                       # segmento premium: menos sensibles
    if "temporada" in etiquetas:
        return -1.00
    if "familiar" in etiquetas:
        return -0.80
    return -0.90


def gen_experimentos_precio(
    rng: np.random.Generator, productos: pd.DataFrame
) -> np.ndarray:
    """Matriz (n_productos, NUM_MESES) de experimentos de precio.

    Wobble autorregresivo mean-reverting: un 'experimento' (promo o menú de
    temporada) dura varios meses y se revierte, de modo que el nivel de precio
    promedio de cada año no cambia (CP2 intacto). El ancla tiene un wobble
    ligeramente mayor (su precio se mueve con el mercado del marisco).
    """
    n = len(productos)
    es_ancla = productos["es_ancla"].to_numpy()
    W = np.zeros((n, NUM_MESES))
    for p in range(n):
        sd = ELAST_WOBBLE_SD * (1.6 if es_ancla[p] else 1.0)
        w = 0.0
        for m in range(NUM_MESES):
            w = ELAST_WOBBLE_PERSIST * w + rng.normal(0, sd)
            W[p, m] = w
    return W

# ------------------------------------------------------------
# 2. NOMBRES (MEXICANOS REALISTAS)
# ------------------------------------------------------------
NOMBRES = [
    "José", "Juan", "María", "Guadalupe", "Pedro", "Miguel", "Ana", "Luis",
    "Carlos", "Jesús", "Francisco", "Jorge", "Rosa", "Sandra", "Verónica",
    "Fernando", "Alejandro", "Ricardo", "Mónica", "Patricia", "Eduardo",
    "Manuel", "Raúl", "Teresa", "Gabriela", "Sergio", "Alberto", "Laura",
    "Arturo", "Daniel", "Claudia", "Mariana", "Óscar", "Héctor", "Diana",
    "Iván", "César", "Brenda", "Norma", "Mario", "Rubén", "Silvia", "Antonio",
    "Roberto", "Karla", "Elisa", "Rogelio", "Armando",
]
APELLIDOS = [
    "Hernández", "García", "Martínez", "López", "González", "Rodríguez",
    "Pérez", "Sánchez", "Ramírez", "Flores", "Torres", "Rivera", "Morales",
    "Vázquez", "Cruz", "Ortiz", "Gutiérrez", "Chávez", "Ramos", "Mendoza",
    "Aguilar", "Castro", "Reyes", "Medina", "Silva", "Fuentes", "Salinas",
    "Garza", "Cantú", "Treviño", "Cavazos", "Zúñiga",
]

# ------------------------------------------------------------
# 3. MENÚ — 182 PRODUCTOS
# Formato: (nombre, precio, subcategoria, ratio_costo, etiquetas)
#   ratio_costo = costo_elaboracion / precio_venta (base)
#   ROI base = (1 - ratio) / ratio ->  bebidas muy superiores (motor de margen)
# ------------------------------------------------------------
MENU_ALIMENTOS = [
    # --- ANCLA (1) ---
    ("Sopa de Mariscos", 195, "Ancla", 0.58, "ancla,familiar"),
    # --- CEVICHES (24) ---
    ("Ceviche de Camarón", 165, "Principal", 0.62, "fresco"),
    ("Ceviche Mixto", 185, "Principal", 0.62, "fresco"),
    ("Ceviche de Pescado", 155, "Principal", 0.62, "fresco"),
    ("Ceviche Verde", 175, "Variante", 0.60, "fresco"),
    ("Ceviche de Pulpo", 210, "Principal", 0.62, "premium"),
    ("Ceviche de Sierra", 170, "Principal", 0.62, "fresco"),
    ("Ceviche de Atún", 178, "Principal", 0.62, "fresco"),
    ("Ceviche Tostada", 145, "Variante", 0.60, "fresco"),
    ("Ceviche Tatemado", 180, "Variante", 0.60, "temporada"),
    ("Ceviche de Callo de Hacha", 220, "Principal", 0.62, "premium"),
    ("Ceviche de Camarón Gigante", 240, "Variante", 0.60, "premium"),
    ("Ceviche de Jaiba", 168, "Principal", 0.62, "fresco"),
    ("Ceviche de Caracol", 190, "Principal", 0.62, "fresco"),
    ("Ceviche Sinaloense", 195, "Principal", 0.62, "temporada"),
    ("Ceviche de Mero", 200, "Principal", 0.62, "fresco"),
    ("Ceviche de Huachinango", 205, "Principal", 0.62, "premium"),
    ("Ceviche de Camarón al Coco", 195, "Variante", 0.60, "vistoso"),
    ("Ceviche de Pescado Tostada", 150, "Variante", 0.60, "fresco"),
    ("Ceviche de Pulpo al Cilantro", 215, "Variante", 0.60, "premium"),
    ("Ceviche de Camarón y Pulpo", 225, "Principal", 0.62, "premium"),
    ("Ceviche de Atún Aleta Amarilla", 235, "Principal", 0.62, "premium"),
    ("Ceviche de Ostión", 175, "Principal", 0.62, "fresco"),
    ("Ceviche de Camarón al Mango", 185, "Variante", 0.60, "vistoso,temporada"),
    ("Ceviche de Huachinango Tostada", 155, "Variante", 0.60, "fresco"),
    # --- FILETES (26) ---
    ("Filete de Pescado Empanizado", 185, "Principal", 0.66, "familiar"),
    ("Filete a la Plancha", 190, "Principal", 0.66, "familiar"),
    ("Filete al Mojo de Ajo", 200, "Principal", 0.66, "familiar"),
    ("Filete Relleno de Camarón", 245, "Principal", 0.66, "premium"),
    ("Filete Veracruzano", 210, "Principal", 0.66, "temporada"),
    ("Filete al Pastor de Marisco", 195, "Variante", 0.64, "temporada"),
    ("Filete al Achiote", 205, "Principal", 0.66, "familiar"),
    ("Filete en Salsa de Mango", 215, "Variante", 0.64, "vistoso"),
    ("Filete de Mero a la Plancha", 225, "Principal", 0.66, "premium"),
    ("Filete de Huachinango", 235, "Principal", 0.66, "premium"),
    ("Filete al Chipotle", 208, "Principal", 0.66, "familiar"),
    ("Filete de Robalo", 230, "Principal", 0.66, "premium"),
    ("Filete Dorado al Limón", 198, "Principal", 0.66, "familiar"),
    ("Filete de Sierra", 212, "Principal", 0.66, "fresco"),
    ("Filete con Camarones", 250, "Principal", 0.66, "premium"),
    ("Filete de Pescado al Coco", 220, "Variante", 0.64, "vistoso"),
    ("Filete a la Diabla", 205, "Principal", 0.66, "familiar"),
    ("Filete de Cazón", 190, "Principal", 0.66, "familiar"),
    ("Filete de Liza", 175, "Principal", 0.66, "fresco"),
    ("Filete de Corvina", 240, "Principal", 0.66, "premium"),
    ("Filete Empanizado con Papas", 192, "Principal", 0.66, "familiar"),
    ("Filete al Ajillo", 198, "Principal", 0.66, "familiar"),
    ("Filete en Salsa Verde", 195, "Principal", 0.66, "familiar"),
    ("Filete en Salsa de Camarón", 255, "Principal", 0.66, "premium"),
    ("Filete de Mero al Mojo", 228, "Principal", 0.66, "premium"),
    ("Filete de Huachinango Relleno", 265, "Variante", 0.64, "premium"),
    # --- AGUACHILES (20) ---
    ("Aguachile Verde", 150, "Variante", 0.58, "temporada"),
    ("Aguachile Negro", 165, "Variante", 0.58, "vistoso,temporada"),
    ("Aguachile Rojo", 155, "Variante", 0.58, "temporada"),
    ("Aguachile Mixto", 175, "Variante", 0.58, "temporada"),
    ("Aguachile de Pulpo", 185, "Variante", 0.58, "premium,temporada"),
    ("Aguachile de Camarón", 160, "Variante", 0.58, "temporada"),
    ("Aguachile Familiar", 320, "Variante", 0.58, "familiar,temporada"),
    ("Aguachile de Sierra", 170, "Variante", 0.58, "temporada"),
    ("Aguachile de Atún", 180, "Variante", 0.58, "temporada"),
    ("Aguachile Tatemado", 165, "Variante", 0.58, "temporada"),
    ("Aguachile de Callo de Hacha", 200, "Variante", 0.58, "premium,temporada"),
    ("Aguachile de Jaiba", 155, "Variante", 0.58, "temporada"),
    ("Aguachile Verde con Mango", 168, "Variante", 0.58, "vistoso,temporada"),
    ("Aguachile de Camarón Gigante", 195, "Variante", 0.58, "premium,temporada"),
    ("Aguachile de Pescado", 145, "Variante", 0.58, "temporada"),
    ("Aguachile de Ostión", 190, "Variante", 0.58, "temporada"),
    ("Aguachile con Chiles Toreados", 158, "Variante", 0.58, "temporada"),
    ("Aguachile de Pulpo Verde", 190, "Variante", 0.58, "premium,temporada"),
    ("Aguachile de Camarón al Coco", 175, "Variante", 0.58, "vistoso,temporada"),
    ("Aguachile Sinaloense", 172, "Variante", 0.58, "temporada"),
    # --- TACOS (30) ---
    ("Tacos de Pescado", 65, "Principal", 0.64, "familiar"),
    ("Tacos de Camarón", 75, "Principal", 0.64, "familiar"),
    ("Tacos de Marlin", 70, "Principal", 0.64, "familiar"),
    ("Tacos Gobernador", 85, "Principal", 0.64, "familiar"),
    ("Tacos de Pulpo", 90, "Principal", 0.64, "premium"),
    ("Tacos de Jaiba", 80, "Principal", 0.64, "familiar"),
    ("Tacos de Atún", 88, "Principal", 0.64, "familiar"),
    ("Tacos de Chicharrón de Pescado", 68, "Principal", 0.64, "familiar"),
    ("Tacos de Camarón al Coco", 82, "Variante", 0.62, "vistoso"),
    ("Tacos de Sierra", 72, "Principal", 0.64, "familiar"),
    ("Tacos de Mero", 86, "Principal", 0.64, "familiar"),
    ("Tacos de Huachinango", 92, "Principal", 0.64, "premium"),
    ("Tacos de Langosta", 145, "Principal", 0.64, "premium"),
    ("Tacos de Caracol", 84, "Principal", 0.64, "familiar"),
    ("Tacos de Callo de Hacha", 95, "Principal", 0.64, "premium"),
    ("Tacos de Pescado Empanizado", 70, "Principal", 0.64, "familiar"),
    ("Tacos de Marlin Ahumado", 78, "Principal", 0.64, "familiar"),
    ("Tacos de Camarón Empanizado", 80, "Principal", 0.64, "familiar"),
    ("Tacos de Pulpo a las Brasas", 95, "Principal", 0.64, "premium"),
    ("Tacos de Jaiba al Mojo", 85, "Principal", 0.64, "familiar"),
    ("Tacos de Ostión", 88, "Principal", 0.64, "familiar"),
    ("Tacos de Camarón al Mojo de Ajo", 84, "Principal", 0.64, "familiar"),
    ("Tacos de Atún Tatemado", 90, "Variante", 0.62, "temporada"),
    ("Tacos de Mero a la Plancha", 88, "Principal", 0.64, "familiar"),
    ("Tacos de Sierra Zarandeada", 78, "Variante", 0.62, "temporada"),
    ("Tacos de Huachinango a la Veracruzana", 96, "Principal", 0.64, "premium"),
    ("Tacos de Camarón Gigante", 110, "Variante", 0.62, "premium"),
    ("Tacos de Pulpo al Ajillo", 92, "Principal", 0.64, "premium"),
    ("Tacos de Jaiba Empanizada", 82, "Principal", 0.64, "familiar"),
    ("Tacos de Marlin a la Brasa", 76, "Principal", 0.64, "familiar"),
    # --- OTROS PRINCIPALES (49) ---
    ("Camarones a la Diabla", 210, "Principal", 0.62, "familiar"),
    ("Camarones al Ajillo", 205, "Principal", 0.62, "familiar"),
    ("Camarones Empanizados", 195, "Principal", 0.62, "familiar"),
    ("Camarones al Coco", 225, "Principal", 0.62, "vistoso"),
    ("Camarones Rellenos", 235, "Principal", 0.62, "premium"),
    ("Camarones a la Plancha", 195, "Principal", 0.62, "familiar"),
    ("Camarones al Mojo de Ajo", 208, "Principal", 0.62, "familiar"),
    ("Camarones en Salsa de Mango", 220, "Variante", 0.60, "vistoso"),
    ("Camarones al Chipotle", 215, "Principal", 0.62, "familiar"),
    ("Coctel de Camarón", 155, "Principal", 0.60, "familiar"),
    ("Coctel de Pulpo", 190, "Principal", 0.60, "premium"),
    ("Coctel de Ostiones", 175, "Principal", 0.60, "familiar"),
    ("Coctel Vuelve a la Vida", 185, "Principal", 0.60, "vistoso"),
    ("Caldo de Camarón", 165, "Principal", 0.60, "familiar"),
    ("Caldo de Pescado", 155, "Principal", 0.60, "familiar"),
    ("Caldo de Mariscos", 210, "Principal", 0.60, "familiar"),
    ("Paella de Mariscos", 280, "Principal", 0.60, "premium"),
    ("Arroz a la Marinera", 175, "Principal", 0.60, "familiar"),
    ("Mariscada", 290, "Principal", 0.60, "premium"),
    ("Surtido de Mariscos", 300, "Principal", 0.60, "premium"),
    ("Pescado Zarandeado", 310, "Principal", 0.60, "premium,temporada"),
    ("Mojarra Frita", 165, "Principal", 0.60, "familiar"),
    ("Huachinango a la Veracruzana", 245, "Principal", 0.60, "premium"),
    ("Huachinango Entero Frito", 230, "Principal", 0.60, "premium"),
    ("Pulpo a las Brasas", 240, "Principal", 0.60, "premium"),
    ("Pulpo al Ajillo", 220, "Principal", 0.60, "premium"),
    ("Calamar Frito", 165, "Principal", 0.60, "familiar"),
    ("Calamares Rellenos", 210, "Principal", 0.60, "premium"),
    ("Ostiones al Natural", 160, "Principal", 0.58, "familiar"),
    ("Ostiones a la Parmesana", 185, "Variante", 0.58, "familiar"),
    ("Almejas al Natural", 150, "Principal", 0.58, "familiar"),
    ("Almejas a la Mantequilla", 175, "Variante", 0.58, "familiar"),
    ("Almejas al Vapor", 160, "Principal", 0.58, "familiar"),
    ("Botana de Mariscos", 185, "Principal", 0.58, "familiar"),
    ("Chicharrón de Pescado", 135, "Principal", 0.58, "familiar"),
    ("Tostadas de Marisco", 125, "Principal", 0.58, "familiar"),
    ("Tostadas de Camarón", 120, "Principal", 0.58, "familiar"),
    ("Tostadas de Ceviche", 130, "Variante", 0.58, "familiar"),
    ("Enchiladas de Marisco", 145, "Principal", 0.58, "familiar"),
    ("Enchiladas de Camarón", 140, "Principal", 0.58, "familiar"),
    ("Torta de Pescado", 110, "Principal", 0.58, "familiar"),
    ("Torta de Camarón", 125, "Principal", 0.58, "familiar"),
    ("Quesadilla de Mariscos", 130, "Principal", 0.58, "familiar"),
    ("Hamburguesa de Pescado", 115, "Principal", 0.58, "familiar"),
    ("Hamburguesa de Camarón", 135, "Principal", 0.58, "familiar"),
    ("Ensalada de Mariscos", 165, "Principal", 0.58, "familiar"),
    ("Ensalada César con Camarón", 145, "Principal", 0.58, "familiar"),
    ("Camarones a la Parrilla", 230, "Principal", 0.60, "premium"),
    ("Langostinos a la Plancha", 260, "Principal", 0.60, "premium"),
]

MENU_BEBIDAS = [
    # --- REFRESCOS (10) ---
    ("Coca-Cola 600ml", 38, "Refresco", 0.48, ""),
    ("Coca-Cola Zero 600ml", 38, "Refresco", 0.48, ""),
    ("Sprite 600ml", 36, "Refresco", 0.48, ""),
    ("Fanta Naranja 600ml", 36, "Refresco", 0.48, ""),
    ("Fanta Uva 600ml", 36, "Refresco", 0.48, ""),
    ("Sidral Mundet 600ml", 36, "Refresco", 0.48, ""),
    ("Manzanita Sol 600ml", 35, "Refresco", 0.48, ""),
    ("Fresca 600ml", 35, "Refresco", 0.48, ""),
    ("Dr Pepper 600ml", 38, "Refresco", 0.48, ""),
    ("Big Cola 600ml", 34, "Refresco", 0.48, ""),
    # --- AGUAS NATURALES (7) — margen altísimo, marketing visual ---
    ("Agua de Jamaica", 48, "Agua", 0.22, "vistoso"),
    ("Agua de Horchata", 48, "Agua", 0.22, "vistoso"),
    ("Agua de Tamarindo", 48, "Agua", 0.22, "vistoso"),
    ("Agua de Limón con Chía", 52, "Agua", 0.22, "vistoso"),
    ("Agua de Pepino", 55, "Agua", 0.22, "vistoso"),
    ("Agua de Sandía", 55, "Agua", 0.22, "vistoso"),
    ("Agua de Coco Natural", 75, "Agua", 0.22, "vistoso,premium"),
    # --- CERVEZAS (15) ---
    ("Cerveza Carta Blanca", 48, "Cerveza", 0.55, ""),
    ("Cerveza Sol", 48, "Cerveza", 0.55, ""),
    ("Cerveza Victoria", 50, "Cerveza", 0.55, ""),
    ("Cerveza Corona Extra", 52, "Cerveza", 0.55, ""),
    ("Cerveza Modelo Especial", 52, "Cerveza", 0.55, ""),
    ("Cerveza Indio", 50, "Cerveza", 0.55, ""),
    ("Cerveza XX Lager", 50, "Cerveza", 0.55, ""),
    ("Cerveza Bohemia", 58, "Cerveza", 0.48, "artesanal"),
    ("Cerveza Pacífico", 58, "Cerveza", 0.48, "artesanal"),
    ("Cerveza Dos Equis Ámbar", 58, "Cerveza", 0.48, "artesanal"),
    ("Michelada Clásica", 85, "Cerveza", 0.32, "vistoso,preparado"),
    ("Michelada de Camarón", 120, "Cerveza", 0.32, "vistoso,preparado,premium"),
    ("Michelada Piñada", 95, "Cerveza", 0.32, "vistoso,preparado"),
    ("Coctel de Cerveza Cantina", 110, "Cerveza", 0.32, "vistoso,preparado,premium"),
    ("Torito de Cerveza", 95, "Cerveza", 0.32, "vistoso,preparado"),
]


# ------------------------------------------------------------
# 4. GENERADORES DE DIMENSIONES
# ------------------------------------------------------------
def gen_sucursales() -> pd.DataFrame:
    """dim_sucursales: 3 sucursales con coordenadas para el mapa."""
    datos = []
    coords = {
        "S1": (25.6866, -100.3161),   # Monterrey, NL
        "S2": (25.4232, -100.9992),   # Saltillo, Coahuila
        "S3": (22.2553, -97.8686),    # Tampico, Tamaulipas (cerca del proveedor)
    }
    for sid, info in SUCURSALES.items():
        lat, lon = coords[sid]
        datos.append({
            "id_sucursal": sid,
            "nombre": f"El Errante {info['ciudad']}",
            "ciudad": info["ciudad"],
            "entidad": info["entidad"],
            "num_meseros": info["meseros"],
            "lat": lat,
            "lon": lon,
            "perfil": info["perfil"],
        })
    return pd.DataFrame(datos)


def gen_meseros(rng: np.random.Generator) -> pd.DataFrame:
    """dim_meseros: 48 meseros respetando límites por sucursal (24/16/8)."""
    pool = [f"{n} {a}" for n in NOMBRES for a in APELLIDOS]
    filas = []
    for sid, info in SUCURSALES.items():
        nombres = rng.choice(pool, size=info["meseros"], replace=False)
        for nombre in nombres:
            filas.append({
                "id_mesero": len(filas) + 1,
                "nombre": nombre,
                "sucursal": sid,
                "fecha_ingreso": pd.Timestamp(FECHA_INICIO) - pd.Timedelta(
                    days=int(rng.integers(30, 700))
                ),
                "activo": True,
            })
    return pd.DataFrame(filas)


def gen_productos() -> pd.DataFrame:
    """dim_productos: 182 productos (150 alimentos + 32 bebidas)."""
    filas = []
    for nombre, precio, sub, ratio, tags in MENU_ALIMENTOS + MENU_BEBIDAS:
        filas.append({
            "id_producto": len(filas) + 1,
            "nombre_producto": nombre,
            "categoria": "Alimento" if sub in ("Ancla", "Principal", "Variante") else "Bebida",
            "subcategoria": sub,
            "etiquetas": tags,
            "precio_venta": precio,
            "costo_base": round(precio * ratio, 2),
            "es_ancla": nombre == ANCLA_NOMBRE,
            "es_incentivable": nombre != ANCLA_NOMBRE,
        })
    df = pd.DataFrame(filas)
    assert len(df) == 182, f"Esperado 182 productos, generados {len(df)}"
    assert df["es_ancla"].sum() == 1, "Debe existir exactamente 1 producto ancla"
    return df


def gen_clientes_crm(rng: np.random.Generator) -> pd.DataFrame:
    """dim_clientes_crm: ~400 clientes (Plata 60% / Oro 30% / VIP 10%)."""
    pool = [f"{n} {a}" for n in NOMBRES for a in APELLIDOS]
    niveles = rng.choice(
        ["Plata", "Oro", "VIP"], size=NUM_CLIENTES_CRM, p=[0.60, 0.30, 0.10]
    )
    sucursales = rng.choice(list(SUCURSALES.keys()), size=NUM_CLIENTES_CRM)
    canales = rng.choice(
        ["restaurante", "campaña", "referencia"],
        size=NUM_CLIENTES_CRM, p=[0.60, 0.25, 0.15],
    )
    frec = {"Plata": (1, 2), "Oro": (2, 4), "VIP": (4, 8)}
    filas = []
    for i in range(NUM_CLIENTES_CRM):
        f_min, f_max = frec[niveles[i]]
        # Deserción simulada: si el cliente "abandona", se define la fecha de su
        # última visita plausible (entre mediados de 2024 y mediados de 2025).
        fecha_salida = None
        if rng.random() < PROB_CHURN[niveles[i]]:
            fecha_salida = pd.Timestamp(FECHA_INICIO) + pd.Timedelta(
                days=int(rng.integers(150, 540))
            )
        filas.append({
            "id_cliente": i + 1,
            "nombre": pool[i],
            "nivel": niveles[i],
            "frecuencia_visitas_mensual": round(rng.uniform(f_min, f_max), 1),
            "sucursal_frecuente": sucursales[i],
            "fecha_alta": pd.Timestamp(FECHA_INICIO) - pd.Timedelta(days=int(rng.integers(0, 400))),
            "canal_alta": canales[i],
            "fecha_salida": fecha_salida,  # NaN = cliente activo (M8 churn)
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------------
# 5. FACTORES TEMPORALES
# ------------------------------------------------------------
def crecimiento_mensual(rng: np.random.Generator) -> np.ndarray:
    """Factores del Año 2 (Año 1 = 1.0). Promedio = 1.5x pero irregular."""
    brutos = rng.uniform(0.93, 1.07, 12)
    return brutos / brutos.mean() * CRECIMIENTO_ANO2


def factor_estacional(mes: int) -> float:
    return SEASONAL[mes]


def factor_inflacion(indices: np.ndarray) -> np.ndarray:
    """Inflación acumulada (~4% anual) para variación suave de precios (M9)."""
    return 1.0 + 0.0035 * indices


def gen_calidad_meseros(rng: np.random.Generator, meseros: pd.DataFrame):
    """Calidad de servicio base por mesero + 4 'vendedores agresivos' (M10)."""
    calidad = pd.Series(
        rng.uniform(3.6, 4.9, len(meseros)), index=meseros["id_mesero"].values
    )
    agresivos = rng.choice(meseros["id_mesero"].values, size=4, replace=False)
    calidad.loc[agresivos] = rng.uniform(2.6, 3.3, 4)
    return calidad, agresivos


# ------------------------------------------------------------
# 6. GENERADOR DE VENTAS (fact_ventas)
# ------------------------------------------------------------
def gen_ventas(
    rng: np.random.Generator,
    meseros: pd.DataFrame,
    productos: pd.DataFrame,
    clientes: pd.DataFrame,
    agresivos: np.ndarray,
) -> pd.DataFrame:
    """fact_ventas: registro transaccional diario de 2 años (reglas §2.3)."""
    fecha_ancla = int(productos.loc[productos["es_ancla"], "id_producto"].iloc[0])

    # Pools de productos
    no_ancla = productos[~productos["es_ancla"]]
    pool_alimentos = no_ancla[no_ancla["categoria"] == "Alimento"]["id_producto"].values
    pool_bebidas = {
        tipo: productos[productos["subcategoria"] == tipo]["id_producto"].values
        for tipo in ("Refresco", "Agua", "Cerveza")
    }

    # Peso de popularidad por producto (variabilidad -> M9)
    peso_alimentos = rng.uniform(0.6, 1.6, len(pool_alimentos))
    peso_alimentos /= peso_alimentos.sum()
    peso_bebidas = {}
    for tipo, ids in pool_bebidas.items():
        w = rng.uniform(0.6, 1.6, len(ids))
        peso_bebidas[tipo] = w / w.sum()

    metodos = rng.choice(
        ["Efectivo", "Tarjeta", "Transferencia"], size=10000, p=[0.45, 0.40, 0.15]
    )
    # Clientes por sucursal con su fecha de salida (NaN = activo, M8 churn)
    clientes_por_suc = {
        sid: clientes[clientes["sucursal_frecuente"] == sid][
            ["id_cliente", "fecha_salida"]
        ]
        for sid in SUCURSALES
    }

    # M9: elasticidad simulada y experimentos de precio por producto/mes
    W = gen_experimentos_precio(rng, productos)   # (182, 24)
    E = np.array([
        elasticidad_producto(
            r["nombre_producto"], r["categoria"], r["subcategoria"], r["etiquetas"]
        )
        for _, r in productos.iterrows()
    ])                                            # (182,)

    crecimiento = crecimiento_mensual(rng)
    dias = pd.date_range(FECHA_INICIO, FECHA_FIN, freq="D")

    chunks_cabeceras = []
    chunks_lineas = []
    ticket_global = 0

    for fecha in dias:
        mes = fecha.month
        crec = crecimiento[mes - 1] if fecha.year == 2025 else 1.0
        dow = fecha.weekday()

        for sid in SUCURSALES:
            base = BASE_TICKETS[sid]
            # S2 (familiar): leve refuerzo en fines de semana
            extra_s2 = 1.08 if (sid == "S2" and dow >= 5) else 1.0
            esperado = (
                base * factor_estacional(mes) * crec * WEEKDAY[dow]
                * extra_s2 * rng.normal(1.0, 0.08)
            )
            n = max(5, int(rng.poisson(esperado)))

            # ---- Cabeceras ----
            ticket_global += n
            ids_ticket = ticket_global - n + np.arange(n)
            meseros_suc = meseros[meseros["sucursal"] == sid]["id_mesero"].values
            ids_mesero = rng.choice(meseros_suc, size=n)

            es_comida = rng.random(n) < 0.45
            min_apertura = 12 * 60 + np.where(es_comida, 0, 360) + np.where(
                es_comida, rng.integers(0, 241, n), rng.integers(0, 271, n)
            )
            duracion = np.where(
                es_comida, rng.integers(40, 81, n), rng.integers(55, 131, n)
            )
            min_cierre = np.minimum(min_apertura + duracion, 23 * 60 + 50)
            hora_apertura = fecha + pd.to_timedelta(min_apertura, unit="m")
            hora_cierre = fecha + pd.to_timedelta(min_cierre, unit="m")

            # ---- Composición de líneas ----
            food_lines = rng.integers(1, 4, n)                      # 1-3 alimentos
            con_ancla = rng.random(n) < PROB_ANCLA
            # Correlación M3: mesas con ancla -> 2-4 bebidas; resto 0-2
            drink_lines = np.where(
                con_ancla,
                rng.integers(2, 5, n),
                rng.integers(0, 3, n),
            )
            push = np.isin(ids_mesero, agresivos)
            drink_lines = drink_lines + push.astype(int)

            # ---- Expandir a líneas ----
            idx_food = np.repeat(np.arange(n), food_lines)
            idx_drink = np.repeat(np.arange(n), drink_lines)
            n_drinks = len(idx_drink)

            # M9: índice de mes del experimento de precio (2024-01 -> 0)
            m_idx = (fecha.year - 2024) * 12 + mes - 1

            # Productos alimentos: la 1ª línea de cada ticket con ancla = ancla
            prods_food = np.empty(len(idx_food), dtype=int)
            pos_primera = np.concatenate([[0], np.cumsum(food_lines[:-1])]).astype(np.int64)
            pos_ancla = pos_primera[con_ancla]
            prods_food[pos_ancla] = fecha_ancla
            resto = np.ones(len(idx_food), dtype=bool)
            resto[pos_ancla] = False
            if int(resto.sum()) > 0:
                peso_dia = peso_alimentos * (
                    1 + W[pool_alimentos - 1, m_idx]
                ) ** E[pool_alimentos - 1]
                peso_dia = peso_dia / peso_dia.sum()
                prods_food[resto] = rng.choice(
                    pool_alimentos, size=int(resto.sum()), p=peso_dia
                )

            # Productos bebidas (mezcla por tipo según sucursal)
            prods_drink = np.empty(n_drinks, dtype=int)
            if n_drinks > 0:
                tipos = rng.choice(
                    list(pool_bebidas.keys()),
                    size=n_drinks, p=list(PESO_BEBIDAS[sid].values()),
                )
                for tipo in np.unique(tipos):
                    mask = tipos == tipo
                    ids_tipo = pool_bebidas[tipo]
                    peso_dia = peso_bebidas[tipo] * (
                        1 + W[ids_tipo - 1, m_idx]
                    ) ** E[ids_tipo - 1]
                    peso_dia = peso_dia / peso_dia.sum()
                    prods_drink[mask] = rng.choice(
                        ids_tipo, size=int(mask.sum()), p=peso_dia
                    )

            cant_food = rng.choice([1, 1, 1, 2], size=len(idx_food))
            cant_drink = rng.integers(1, 4, size=n_drinks)

            # Clientes CRM (40% de tickets): solo clientes aún activos en esa fecha
            tiene_cliente = rng.random(n) < PCT_VENTAS_CRM
            cli_suc = clientes_por_suc[sid]
            # Clientes activos: sin fecha de salida o con salida posterior al día
            activos = cli_suc[cli_suc["fecha_salida"].fillna(fecha) >= fecha]
            pool_suc = activos["id_cliente"].values
            ids_cliente = np.full(n, None, dtype=object)
            n_cli = int(tiene_cliente.sum())
            if n_cli > 0 and len(pool_suc) > 0:
                ids_cliente[tiene_cliente] = rng.choice(pool_suc, size=n_cli)

            # ---- Ensamblar ----
            chunks_cabeceras.append(pd.DataFrame({
                "id_ticket": ids_ticket,
                "fecha_hora": hora_apertura,
                "id_sucursal": sid,
                "id_mesero": ids_mesero,
                "id_cliente_crm": pd.array(ids_cliente, dtype="Int64"),
                "hora_apertura_mesa": hora_apertura,
                "hora_cierre_mesa": hora_cierre,
                "metodo_pago": metodos[rng.integers(0, 10000, n)],
            }))
            chunks_lineas.append(pd.DataFrame({
                "id_ticket": ids_ticket[idx_food],
                "id_producto": prods_food,
                "cantidad": cant_food,
            }))
            if n_drinks > 0:
                chunks_lineas.append(pd.DataFrame({
                    "id_ticket": ids_ticket[idx_drink],
                    "id_producto": prods_drink,
                    "cantidad": cant_drink,
                }))

    df_tickets = pd.concat(chunks_cabeceras, ignore_index=True)
    df_lineas = pd.concat(chunks_lineas, ignore_index=True)
    df = df_tickets.merge(df_lineas, on="id_ticket", how="left")
    df = df.merge(
        productos[["id_producto", "precio_venta", "categoria", "subcategoria", "es_ancla"]],
        on="id_producto",
    )
    # Precio aplicado por fila (inflación acumulada + experimento M9 del producto/mes)
    indice = (df["fecha_hora"].dt.year - 2024) * 12 + df["fecha_hora"].dt.month - 1
    wob = W[df["id_producto"].to_numpy() - 1, indice.to_numpy()]
    df["precio_unitario_aplicado"] = (
        df["precio_venta"] * factor_inflacion(indice.to_numpy()) * (1 + wob)
    ).round(2)
    return df.sort_values(["id_ticket", "id_producto"]).reset_index(drop=True)


# ------------------------------------------------------------
# 7. GENERADOR DE COSTOS MENSUALES (fact_costos_mensuales)
# ------------------------------------------------------------
def gen_costos(rng: np.random.Generator, productos: pd.DataFrame) -> pd.DataFrame:
    """fact_costos_mensuales: costo ±15% mensual en alimentos (excepto ancla),
    ±2% en bebidas, 0% en el ancla."""
    meses = pd.period_range("2024-01", "2025-12", freq="M")
    filas = []
    for _, prod in productos.iterrows():
        for mes in meses:
            if prod["es_ancla"]:
                var = 0.0
            elif prod["categoria"] == "Alimento":
                var = rng.uniform(-COSTO_VARIACION_MAX, COSTO_VARIACION_MAX)
            else:
                var = rng.uniform(-0.02, 0.02)
            filas.append({
                "id_producto": prod["id_producto"],
                "mes_ano": mes.strftime("%Y-%m"),
                "costo_elaboracion": round(prod["costo_base"] * (1 + var), 2),
            })
    return pd.DataFrame(filas)


# ------------------------------------------------------------
# 8. GENERADOR DE PRESUPUESTO (fact_presupuesto)
# ------------------------------------------------------------
def gen_presupuesto(rng: np.random.Generator, ventas: pd.DataFrame) -> pd.DataFrame:
    """fact_presupuesto: meta optimista. Reales 5-10% abajo en meses bajos
    (Ene/Feb/Sep/Oct) y +12% arriba en Cuaresma (Mar/Abr)."""
    v = ventas.copy()
    v["mes_ano"] = v["fecha_hora"].dt.strftime("%Y-%m")
    v["monto"] = v["precio_unitario_aplicado"] * v["cantidad"]

    agg = v.groupby(["mes_ano", "id_sucursal"]).agg(
        real_ventas=("monto", "sum"),
        num_tickets=("id_ticket", "nunique"),
    )

    meses_bajos = {"2024-01", "2024-02", "2024-09", "2024-10",
                   "2025-01", "2025-02", "2025-09", "2025-10"}
    meses_cuaresma = {"2024-03", "2024-04", "2025-03", "2025-04"}

    filas = []
    for (mes_ano, sid), r in agg.iterrows():
        if mes_ano in meses_bajos:
            objetivo_cumplimiento = 0.925   # reales ~7.5% abajo del presupuesto
        elif mes_ano in meses_cuaresma:
            objetivo_cumplimiento = 1.12    # reales 12% arriba
        else:
            objetivo_cumplimiento = 1.0
        objetivo = r["real_ventas"] / objetivo_cumplimiento * rng.uniform(0.98, 1.02)
        filas.append({
            "mes_ano": mes_ano,
            "id_sucursal": sid,
            "meta_ventas": round(objetivo, 2),
            "meta_roi_promedio": 0.60,
            "meta_venta_bebidas": round(objetivo * 0.33, 2),
            "meta_ticket_promedio": round(
                r["real_ventas"] / r["num_tickets"] * 1.05, 2
            ),
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------------
# 9. GENERADOR DE ENCUESTAS (fact_encuestas_satisfaccion)
# ------------------------------------------------------------
def gen_encuestas(
    rng: np.random.Generator,
    ventas: pd.DataFrame,
    calidad_mesero: pd.Series,
) -> pd.DataFrame:
    """fact_encuestas: calificación ligada a tickets con cliente CRM (~40%)."""
    con_cliente = ventas[ventas["id_cliente_crm"].notna()]
    tickets_unicos = con_cliente.drop_duplicates("id_ticket")

    # Vectorizado: calidad base del mesero + ruido gaussiano
    meseros_arr = tickets_unicos["id_mesero"].to_numpy()
    calidad_arr = calidad_mesero.reindex(meseros_arr).to_numpy()
    ruido = rng.normal(0, 0.35, size=len(meseros_arr))
    calificacion = np.clip(np.round(calidad_arr + ruido, 1), 1, 5).astype(int)

    sentimiento = np.where(calificacion >= 4, "positivo",
                           np.where(calificacion == 3, "neutro", "negativo"))
    comentarios = {
        1: "Servicio impositivo, me presionaron para pedir más",
        2: "La atención no fue agradable",
        3: "Servicio regular",
        4: "Buen servicio, todo rico",
        5: "Excelente atención, volveré",
    }
    comentario = np.array([comentarios[c] for c in calificacion])

    return pd.DataFrame({
        "id_encuesta": np.arange(1, len(tickets_unicos) + 1),
        "id_ticket": tickets_unicos["id_ticket"].values,
        "id_mesero": tickets_unicos["id_mesero"].values,
        "calificacion_servicio": calificacion,
        "comentario": comentario,
        "sentimiento": sentimiento,
    })


# ------------------------------------------------------------
# 10. ORQUESTADOR PRINCIPAL
# ------------------------------------------------------------
def main():
    # Compatibilidad con consolas Windows (códec cp1252 no soporta emojis/✓)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    rng = np.random.default_rng(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("== Generando dimensiones ==")
    sucursales = gen_sucursales()
    meseros = gen_meseros(rng)
    productos = gen_productos()
    clientes = gen_clientes_crm(rng)
    calidad_mesero, agresivos = gen_calidad_meseros(rng, meseros)

    print("== Generando fact_ventas (puede tardar unos segundos) ==")
    ventas = gen_ventas(rng, meseros, productos, clientes, agresivos)

    print("== Generando costos, presupuesto y encuestas ==")
    costos = gen_costos(rng, productos)
    presupuesto = gen_presupuesto(rng, ventas)
    encuestas = gen_encuestas(rng, ventas, calidad_mesero)

    # --- Guardar todos los CSV ---
    rutas = {
        CSV_DIM_SUCURSALES: sucursales,
        CSV_DIM_MESEROS: meseros,
        CSV_DIM_PRODUCTOS: productos,
        CSV_DIM_CLIENTES_CRM: clientes,
        CSV_FACT_COSTOS: costos,
        CSV_FACT_PRESUPUESTO: presupuesto,
        CSV_FACT_VENTAS: ventas,
        CSV_FACT_ENCUESTAS: encuestas,
    }
    for ruta, df in rutas.items():
        df.to_csv(ruta, index=False)
        print(f"  [OK] {ruta.name}: {len(df):,} filas")

    # --- Resumen de negocio (pre-CP2) ---
    print("\n== Resumen de negocio ==")
    v = ventas.copy()
    v["monto"] = v["precio_unitario_aplicado"] * v["cantidad"]
    fact_anual = v.groupby(v["fecha_hora"].dt.year)["monto"].sum()
    for anio in (2024, 2025):
        print(f"  Facturación {anio}: ${fact_anual.get(anio, 0):,.0f}")
    if 2024 in fact_anual.index and 2025 in fact_anual.index:
        ratio = fact_anual[2025] / fact_anual[2024]
        print(f"  Crecimiento Año2/Año1: {ratio:.2f}x (meta: {CRECIMIENTO_ANO2}x)")
    print(f"  % tickets con cliente CRM: {v['id_cliente_crm'].notna().mean():.1%} "
          f"(meta: {PCT_VENTAS_CRM:.0%})")
    print("\n✅ Data Factory completado. Ejecutar src/validaciones.py (CP1/CP2)")


if __name__ == "__main__":
    main()
