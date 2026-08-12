# ============================================================
# GENERADOR DEL PDF — Manual de usuario "El Errante" (APA 7.ª)
# ------------------------------------------------------------
# Construye MANUAL_DE_USUARIO.pdf bajo las normas APA vigentes:
#   • Portada, resumen, tabla de contenido y cuerpo del manual
#   • Times New Roman 12, doble espacio, margenes de 1 pulgada
#   • Numero de pagina arriba a la derecha (todas las paginas)
#   • Leyenda vertical al margen izquierdo (proyecto)
#   • Figuras numeradas (Figura N) con nota, tablas estilo APA
#   • UNA SOLA TINTA: texto y figuras en negro/gris
# Uso: python scripts/generar_manual_pdf.py
# (requiere haber ejecutado antes scripts/figuras_vintage.py)
# Autor: Buffy | Fase: pre-F7 (2026-08-12)
# ============================================================

import sys
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "scripts" / "figuras"
PDF_PATH = ROOT / "MANUAL_DE_USUARIO.pdf"

LEYENDA = (
    "EL ERRANTE · BI E INCENTIVOS · Manual de usuario — Restaurante de mariscos: "
    "Nuevo Leon, Coahuila y Tamaulipas — Historico simulado 2024-2025 (semilla 42) — "
    "Documento complementario del DOCUMENTO_MAESTRO.md"
)

PAGE_W, PAGE_H = LETTER
FRAME = Frame(inch, inch, PAGE_W - 2 * inch, PAGE_H - 2 * inch, id="main")

# ------------------------------------------------------------
# Estilos APA 7.ª
# ------------------------------------------------------------
NORMAL = ParagraphStyle(
    "NORMAL", fontName="Times-Roman", fontSize=12, leading=24,
    alignment=TA_JUSTIFY, firstLineIndent=0.5 * inch,
)
NO_INDENT = ParagraphStyle(
    "NO_INDENT", fontName="Times-Roman", fontSize=12, leading=24,
    alignment=TA_JUSTIFY, firstLineIndent=0,
)
H1 = ParagraphStyle(
    "H1", fontName="Times-Bold", fontSize=12, leading=24,
    alignment=TA_CENTER, spaceBefore=12, spaceAfter=6, keepWithNext=1,
)
H2 = ParagraphStyle(
    "H2", fontName="Times-Bold", fontSize=12, leading=24,
    alignment=TA_LEFT, spaceBefore=10, spaceAfter=2, keepWithNext=1,
)
H3 = ParagraphStyle(
    "H3", fontName="Times-BoldItalic", fontSize=12, leading=24,
    alignment=TA_LEFT, spaceBefore=8, spaceAfter=2, keepWithNext=1,
)
CAP_NUM = ParagraphStyle(
    "CAP_NUM", fontName="Times-Bold", fontSize=11, leading=14,
    alignment=TA_LEFT, spaceBefore=14,
)
CAP_TIT = ParagraphStyle(
    "CAP_TIT", fontName="Times-Italic", fontSize=11, leading=14,
    alignment=TA_LEFT, spaceAfter=6,
)
CAP_NOTA = ParagraphStyle(
    "CAP_NOTA", fontName="Times-Roman", fontSize=10, leading=13,
    alignment=TA_LEFT, spaceBefore=4, spaceAfter=14,
)
REF = ParagraphStyle(
    "REF", fontName="Times-Roman", fontSize=12, leading=24,
    leftIndent=0.5 * inch, firstLineIndent=-0.5 * inch, alignment=TA_LEFT,
)
TOC0 = ParagraphStyle(
    "TOC0", fontName="Times-Bold", fontSize=12, leading=24, leftIndent=0,
)
TOC1 = ParagraphStyle(
    "TOC1", fontName="Times-Roman", fontSize=12, leading=24,
    leftIndent=0.3 * inch,
)
PORTADA = ParagraphStyle(
    "PORTADA", fontName="Times-Roman", fontSize=12, leading=24,
    alignment=TA_CENTER,
)
PORTADA_TIT = ParagraphStyle(
    "PORTADA_TIT", fontName="Times-Bold", fontSize=12, leading=24,
    alignment=TA_CENTER,
)

STORY = []


def p(text, style=NORMAL):
    STORY.append(Paragraph(text, style))


def h1(text):
    STORY.append(Paragraph(text, H1))


def h2(text):
    STORY.append(Paragraph(text, H2))


def h3(text):
    STORY.append(Paragraph(text, H3))


def figura(num, archivo, titulo, nota, width=5.9 * inch):
    ruta = FIG / archivo
    w, h = PILImage.open(ruta).size
    fig_w = width
    fig_h = fig_w * h / w
    if fig_h > 5.1 * inch:
        fig_h = 5.1 * inch
        fig_w = fig_h * w / h
    STORY.append(Paragraph(f"<b>Figura {num}</b>", CAP_NUM))
    STORY.append(Paragraph(f"<i>{titulo}</i>", CAP_TIT))
    STORY.append(Image(str(ruta), width=fig_w, height=fig_h))
    STORY.append(Paragraph(f"<i>Nota.</i> {nota}", CAP_NOTA))


def tabla(num, titulo, data, widths, nota, font=9.5):
    STORY.append(Paragraph(f"<b>Tabla {num}</b>", CAP_NUM))
    STORY.append(Paragraph(f"<i>{titulo}</i>", CAP_TIT))
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), font),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), font + 0.5),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 1.2, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    STORY.append(t)
    if nota:
        STORY.append(Paragraph(f"<i>Nota.</i> {nota}", CAP_NOTA))


# ------------------------------------------------------------
# Plantillas de pagina (numero de pagina + leyenda al margen)
# ------------------------------------------------------------
def on_portada(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 12)
    canvas.drawRightString(PAGE_W - inch, PAGE_H - inch + 6, str(doc.page))
    canvas.restoreState()


def on_cuerpo(canvas, doc):
    canvas.saveState()
    # APA: numero de pagina arriba a la derecha
    canvas.setFont("Times-Roman", 12)
    canvas.drawRightString(PAGE_W - inch, PAGE_H - inch + 6, str(doc.page))
    # Leyenda vertical al margen izquierdo (relacionada con el proyecto)
    canvas.setFont("Times-Roman", 6.8)
    canvas.setFillColor(colors.HexColor("#5a5a5a"))
    canvas.translate(0.30 * inch, 1.1 * inch)
    canvas.rotate(90)
    canvas.drawString(0, 0, LEYENDA)
    canvas.restoreState()


class ManualDoc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            st = flowable.style.name
            txt = flowable.getPlainText()
            if st == "H1" and txt not in ("Resumen", "Tabla de contenido"):
                self.notify("TOCEntry", (0, txt, self.page))
            elif st == "H2":
                self.notify("TOCEntry", (1, txt, self.page))


# ============================================================
# CONTENIDO
# ============================================================
def portada():
    STORY.append(NextPageTemplate("cuerpo"))
    STORY.append(Spacer(1, 2.2 * inch))
    p("El Errante: Manual de Usuario del Panel de Control de "
      "Business Intelligence e Incentivos para Restaurante Multisucursal",
      PORTADA_TIT)
    STORY.append(Spacer(1, 0.4 * inch))
    p("gluevanos", PORTADA)
    p("Proyecto de Portafolio Profesional: BI e Incentivos", PORTADA)
    p("Analisis de Datos y Visualizacion", PORTADA)
    p("Buffy (asistente de inteligencia artificial)", PORTADA)
    p("12 de agosto de 2026", PORTADA)
    STORY.append(PageBreak())


def resumen():
    h1("Resumen")
    p("Este manual describe el funcionamiento del panel de control El Errante, "
      "un sistema de Business Intelligence para el gerente general de un "
      "restaurante de mariscos con tres sucursales en el noreste de Mexico "
      "(Monterrey, Saltillo y Tampico). El documento explica, en primer lugar, "
      "como iniciar la aplicacion y navegar por sus filtros globales. En "
      "segundo lugar, define el glosario de conceptos y formulas que utiliza "
      "el sistema, entre ellos el retorno sobre la inversion (ROI), el mix de "
      "bebidas, la elasticidad de precios y el churn. En tercer lugar, detalla "
      "el modelo de datos de esquema en estrella del que nace cada indicador. "
      "A continuacion presenta los diez modulos del panel, cada uno con su "
      "pregunta de negocio, sus elementos en pantalla y una figura elaborada "
      "con datos reales del historico. Finalmente, explica la clasificacion de "
      "clientes en los niveles Plata, Oro y VIP, el momento en que se aplican "
      "las encuestas a los meseros, las preguntas que responde el CRM y una "
      "nota tecnica sobre la naturaleza simulada de los datos. Todas las "
      "figuras del manual se presentan en una sola tinta con un estilo de "
      "dibujo a mano para facilitar su impresion rapida.", NO_INDENT)
    STORY.append(Spacer(1, 0.15 * inch))
    p("<i>Palabras clave:</i> business intelligence, incentivos, deserción de "
      "clientes, elasticidad de precios, pronóstico de ventas, auditoría de "
      "servicio", REF)
    STORY.append(PageBreak())


def indice():
    h1("Tabla de contenido")
    toc = TableOfContents()
    toc.levelStyles = [TOC0, TOC1]
    STORY.append(toc)
    STORY.append(PageBreak())


def seccion1():
    h1("Introducción")
    h2("Qué es el sistema")
    p("El Errante es el panel de control de Business Intelligence del gerente "
      "general de un restaurante de mariscos con tres sucursales en el noreste "
      "de México: S1 Monterrey (Nuevo León), S2 Saltillo y Torreón (Coahuila) y "
      "S3 Tampico y Reynosa (Tamaulipas). No es un tablero de ventas estático: "
      "es un entorno de prescripción estratégica que combina analítica "
      "descriptiva (qué ocurrió), analítica predictiva (qué viene) y analítica "
      "prescriptiva (qué hacer), con planes de contingencia, incentivos para el "
      "personal y recomendaciones de precios.")
    p("El sistema opera con 48 meseros, un menú de 182 productos y un programa "
      "de lealtad de aproximadamente 400 clientes, sobre un histórico de dos "
      "años (2024-2025) con más de 700 000 líneas de venta. Todos los "
      "indicadores, gráficos y alertas que se describen en este manual "
      "provienen de ese histórico y de las reglas de negocio documentadas en el "
      "Documento Maestro del proyecto.")
    h2("Cómo ejecutar el panel")
    p("1. Crear el entorno virtual e instalar las dependencias: "
      "<i>python -m venv .venv</i> y <i>pip install -r requirements.txt</i>.")
    p("2. Iniciar la aplicación: <i>streamlit run app/app.py</i>.")
    p("3. Abrir en el navegador la dirección <i>http://localhost:8501</i>.")
    p("El despliegue en la nube utiliza el mismo archivo <i>app/app.py</i>.")
    h2("Navegación y filtros globales")
    p("Toda la operación se realiza desde la barra lateral izquierda, que "
      "contiene dos bloques: el selector de módulos (las diez pestañas del "
      "sistema, M1 a M10) y los filtros globales (rango de fechas y "
      "sucursales). La regla de oro de uso es fijar primero el periodo y las "
      "sucursales que se desean analizar y después navegar entre módulos: "
      "todos los gráficos e indicadores se recalculan automáticamente al mover "
      "cualquier filtro.")
    p("El rango de fechas recorta el análisis al periodo seleccionado, con un "
      "máximo de 01-ene-2024 a 31-dic-2025, y los indicadores comparan contra "
      "el periodo anterior de igual duración (delta). El filtro de sucursales "
      "activa o desactiva cada plaza y debe quedar al menos una activa. Para "
      "ver la fotografía completa del negocio se recomienda dejar el rango "
      "completo y las tres sucursales; para investigar un problema puntual, por "
      "ejemplo la cuesta de enero, se recomienda recortar al rango del "
      "problema.")
    h2("Semántica de estados")
    p("El sistema mantiene una semántica de colores consistente en toda la "
      "aplicación. En la impresión en una sola tinta, el lector debe "
      "interpretarla por el estado señalado en cada indicador: saludable, "
      "vigilar o crítico. La Tabla 1 resume su significado.")
    tabla(1, "Semántica de estados del sistema",
          [["Estado", "Significado", "Ejemplo"],
           ["Saludable", "El indicador cumple la meta, sin riesgo",
            "ROI mayor o igual a 45%; cumplimiento mayor o igual a 100%"],
           ["Vigilar", "Cerca del umbral, requiere atención",
            "Cumplimiento entre 90% y 95%; calificación menor a 3.5"],
           ["Crítico", "Umbral cruzado, requiere acción inmediata",
            "ROI menor a 45%; cumplimiento menor a 90%; churn activo"]],
          [1.3 * inch, 2.55 * inch, 2.65 * inch],
          "Elaboración propia a partir de la especificación del proyecto "
          "(DOCUMENTO_MAESTRO, sección 6). Los colores de la aplicación "
          "(turquesa, ámbar y coral) se muestran en pantalla.")


def seccion2():
    h1("Glosario de conceptos y fórmulas")
    p("El manual emplea los siguientes conceptos. Sus fórmulas y umbrales son "
      "los mismos que calcula la aplicación; los umbrales de alerta alimentan "
      "el Centro de Alertas (M5).")
    tabla(2, "Conceptos, fórmulas y umbrales del sistema",
          [["Concepto", "Definición", "Fórmula", "Umbral de alerta"],
           ["ROI promedio", "Margen de ganancia sobre el costo de elaboración",
            "(Precio de venta - Costo) / Costo", "Menor a 45% en alimentos"],
           ["Ticket promedio", "Gasto promedio por mesa o ticket",
            "Ventas / Número de tickets", "—"],
           ["Mix de bebidas", "Participación de bebidas en el ticket",
            "Ingresos por bebidas / Total del ticket", "Menor a 30%"],
           ["% de cumplimiento", "Qué tanto se cumplió la meta de ventas",
            "Ventas reales / Meta de ventas", "Menor a 90%"],
           ["Comisión", "Incentivo al mesero por línea vendida",
            "Utilidad x Tasa x Multiplicador", "—"],
           ["Elasticidad precio", "Sensibilidad de la demanda al precio",
            "Cambio % del volumen / Cambio % del precio (log-log)",
            "|e| mayor a 1.0 = elástico"],
           ["Churn / deserción", "Cliente de alto valor que deja de visitar",
            "Días desde su última visita", "Mayor a 45 días (Oro/VIP)"],
           ["Tiempo de ocupación", "Minutos que una mesa permanece ocupada",
            "Hora de cierre - Hora de apertura", "—"],
           ["Eficiencia de mesa", "Ingreso generado por minuto de mesa",
            "Ticket / Tiempo de ocupación", "—"],
           ["MAPE", "Error del pronóstico; menor es mejor",
            "Media de |Real - Predicción| / Real",
            "Comparación vs referencia ingenua"],
           ["Salud del incentivo", "Comisiones vs calidad de servicio",
            "Calificación media por mesero",
            "Menor a 3.5; con comisión alta = crítico"]],
          [1.15 * inch, 1.85 * inch, 2.1 * inch, 1.4 * inch],
          "Elaboración propia. El símbolo — indica que el concepto no tiene "
          "umbral de alerta propio.", font=8.8)


def seccion3():
    h1("Modelo de datos")
    p("El sistema utiliza un esquema en estrella: una gran tabla de hechos "
      "(fact_ventas) rodeada de tablas de dimensiones y de hechos auxiliares. "
      "Todo lo que se observa en el panel se calcula a partir de los ocho "
      "archivos CSV que resume la Tabla 3. La Figura 1 muestra el esquema: la "
      "tabla de hechos central y las siete tablas que la rodean.")
    tabla(3, "Archivos del modelo de datos y su uso",
          [["Archivo", "Contenido", "Uso"],
           ["dim_sucursales.csv", "Las 3 sucursales: nombre, ciudad, entidad, "
            "número de meseros y coordenadas", "Mapa (M1) y filtro"],
           ["dim_meseros.csv", "Los 48 meseros: nombre, sucursal y fecha de "
            "ingreso", "M2, M7 y M10"],
           ["dim_productos.csv", "Los 182 productos: categoría, subcategoría, "
            "precio, costo, es_ancla, es_incentivable", "ROI, incentivos, M9"],
           ["dim_clientes_crm.csv", "~400 clientes del programa de lealtad: "
            "nivel, frecuencia, sucursal, canal", "M3, M5 y M8"],
           ["fact_ventas.csv", "Más de 700 000 líneas de tickets: fecha, "
            "sucursal, mesero, producto, precio, mesa", "Base de todos"],
           ["fact_costos_mensuales.csv", "Costo de elaboración por producto y "
            "mes (fluctúa ±15%)", "ROI (M1) y comisiones (M2)"],
           ["fact_presupuesto.csv", "Meta de ventas mensual por sucursal",
            "Cumplimiento (M4) y M5"],
           ["fact_encuestas_satisfaccion.csv", "Encuestas ligadas a ticket: "
            "calificación 1-5, comentario, sentimiento", "M10 y M5"]],
          [1.75 * inch, 3.0 * inch, 1.75 * inch],
          "Elaboración propia. El esquema en estrella centraliza la tabla de "
          "hechos y las dimensiones que la describen.", font=9.0)
    figura(1, "fig_estrella.png",
           "Esquema en estrella del modelo de datos de El Errante",
           "Elaboración propia con base en la especificación del modelo de "
           "datos del Documento Maestro, sección 3. La tabla de hechos "
           "fact_ventas se une con las siete tablas circundantes.",
           width=4.9 * inch)
    p("El flujo de datos dentro de la aplicación es el siguiente: fact_ventas "
      "se cruza con fact_costos_mensuales por producto y mes para obtener el "
      "ROI de cada línea; se agrega por mes y sucursal y se compara con "
      "fact_presupuesto para obtener el porcentaje de cumplimiento; las "
      "columnas de apertura y cierre de mesa alimentan el análisis de rotación "
      "(M7). La tabla de clientes se cruza con el 40% de los tickets ligados "
      "al programa para calcular la última visita y la deserción (M3, M5 y "
      "M8). Las encuestas se cruzan con los tickets para calificar al mesero "
      "(M5 y M10). La serie semanal alimenta el modelo de pronóstico (M6) y la "
      "relación precio-volumen mensual estima la elasticidad (M9).")


def seccion4():
    h1("Los indicadores (KPIs)")
    p("Los indicadores son la primera lectura de cada módulo. Se presentan en "
      "tarjetas con el valor del periodo y el cambio porcentual (delta) "
      "respecto del periodo anterior de igual duración. La Figura 2 muestra "
      "los cuatro indicadores globales del Consolidado Financiero (M1) "
      "calculados con el histórico completo: ventas totales, ticket promedio, "
      "ROI promedio y mix de bebidas.")
    figura(2, "fig_kpis.png",
           "Indicadores globales del Consolidado Financiero (M1)",
           "Elaboración propia con datos de fact_ventas 2024-2025. Ventas "
           "totales del periodo, ticket promedio por mesa, ROI promedio sobre "
           "el costo de elaboración y participación de bebidas en el ticket.",
           width=5.7 * inch)
    p("Dos precisiones útiles. Primero, el delta aparece vacío cuando el "
      "periodo anterior cae antes del inicio de los datos (01-ene-2024), lo "
      "cual es un comportamiento esperado. Segundo, los indicadores de ROI y "
      "de mix de bebidas se marcan como críticos cuando cruzan sus umbrales "
      "(45% y 30%, respectivamente).")


def seccion5():
    h1("Los diez módulos, paso a paso")
    p("Los diez módulos responden, en orden, las preguntas de negocio del "
      "gerente. Para cada uno se describe la pregunta que responde, los "
      "elementos en pantalla y la figura correspondiente, elaborada con datos "
      "reales del histórico.")

    h2("M1 · Consolidado Financiero y ROI")
    p("Este módulo responde la pregunta: ¿cómo va el negocio en general y "
      "dónde se gana o se pierde? Presenta los cuatro indicadores globales, un "
      "mapa geográfico de las sucursales (el tamaño de cada burbuja es la "
      "venta del periodo), un resumen por sucursal, la evolución diaria de "
      "ventas con zoom, el cumplimiento mensual del presupuesto y el ROI "
      "mensual de la categoría Alimentos.")
    p("La Figura 3 muestra la estacionalidad del histórico: los valles de "
      "enero y febrero (cuesta de enero) y de septiembre y octubre, frente a "
      "los picos de marzo y abril (Cuaresma), mayo y diciembre. La Figura 4 "
      "presenta el mapa de sucursales con su participación en ventas; S1 "
      "Monterrey concentra la mayor plaza.")
    figura(3, "fig_m1_ventas.png",
           "Evolución mensual de ventas 2024-2025 (M1)",
           "Elaboración propia con datos de fact_ventas. Se aprecian los "
           "valles de enero y septiembre-octubre y los picos de Cuaresma, mayo "
           "y diciembre.", width=5.9 * inch)
    figura(4, "fig_m1_mapa.png",
           "Mapa geográfico de las sucursales con ventas del periodo (M1)",
           "Elaboración propia con datos de dim_sucursales y fact_ventas. El "
           "tamaño de cada punto es proporcional a la venta del periodo; S1 "
           "Monterrey concentra la mayor plaza.", width=5.3 * inch)

    h2("M2 · Programa de Incentivos")
    p("Este módulo responde: ¿cuánto cuesta motivar a los meseros y quién "
      "rinde más? Un simulador permite ajustar la comisión sobre la utilidad "
      "(0% a 15%, con 5% por defecto) y el multiplicador para bebidas y "
      "variantes de alto ROI (1.0 a 3.0 veces, con 1.5 por defecto). El módulo "
      "calcula las comisiones del periodo, el porcentaje de utilidad destinado "
      "a incentivos, el mesero número uno, la proyección de ingreso extra y el "
      "ranking de los 48 meseros.")
    p("Una regla de negocio central: la Sopa de Mariscos, producto ancla, no "
      "genera incentivos (es_incentivable es falso). El ancla atrae tráfico; "
      "el incentivo debe empujar las bebidas y variantes de alto ROI, que son "
      "el motor del margen. La Figura 5 muestra los diez meseros con mayor "
      "comisión con la política estándar.")
    figura(5, "fig_m2_leaderboard.png",
           "Top 10 de meseros por comisión con la política 5% y 1.5 veces (M2)",
           "Elaboración propia con datos de fact_ventas, fact_costos_mensuales "
           "y dim_meseros. El cálculo excluye la Sopa de Mariscos por ser el "
           "producto ancla.", width=5.9 * inch)

    h2("M3 · CRM y Marketing")
    p("Este módulo responde: ¿qué tan saludable está la base de clientes y el "
      "ancla realmente arrastra venta de bebidas? Presenta el padrón del "
      "programa, los clientes activos en el periodo, los Oro/VIP en riesgo de "
      "deserción, el embudo de clientes, la distribución por sucursal y nivel "
      "y la correlación entre el ancla y las bebidas.")
    p("La Figura 6 confirma la regla del negocio: las mesas que ordenan la "
      "Sopa de Mariscos consumen en promedio 2.95 variedades de bebidas, "
      "frente a 1.54 en las mesas sin ancla, y la mayoría de las mesas con "
      "ancla supera las dos variedades. La Figura 7 muestra el embudo: del "
      "padrón de clientes registrados se pasa a los activos en el periodo y de "
      "estos a los Oro/VIP activos, el grupo de mayor valor.")
    figura(6, "fig_m3_ancla.png",
           "Correlación entre la Sopa Ancla y las bebidas por mesa (M3)",
           "Elaboración propia con datos de fact_ventas. Las mesas con ancla "
           "ordenan en promedio 2.95 variedades de bebidas frente a 1.54 de "
           "las mesas sin ancla.", width=5.4 * inch)
    figura(7, "fig_m3_embudo.png",
           "Embudo de clientes del programa de lealtad (M3)",
           "Elaboración propia con datos de dim_clientes_crm y fact_ventas. "
           "De los clientes registrados, se identifican los activos en el "
           "periodo y, entre ellos, los Oro/VIP activos.", width=4.6 * inch)

    h2("M4 · Presupuesto de Ventas vs Real")
    p("Este módulo responde: ¿estamos cumpliendo la meta financiera de cada "
      "sucursal? Incluye un medidor por sucursal, barras mensuales de real "
      "contra meta, la serie de cumplimiento con su banda de vigilancia (90% "
      "a 95%) y el detalle mensual con estado semántico.")
    p("La Figura 8 presenta el cumplimiento mensual consolidado. Los meses de "
      "enero, febrero, septiembre y octubre quedan por debajo de la meta (5% "
      "a 10% abajo), mientras que la Cuaresma supera la meta en cerca de 12%. "
      "Este comportamiento es intencional: es el escenario que la gerencia "
      "debe gestionar, no un error del sistema.")
    figura(8, "fig_m4_cumplimiento.png",
           "Cumplimiento mensual de la meta de ventas (M4)",
           "Elaboración propia con datos de fact_ventas y fact_presupuesto. "
           "La línea punteada indica la meta (100%) y la línea de puntos el "
           "umbral de alerta (90%).", width=5.9 * inch)

    h2("M5 · Centro de Alertas (sistema experto)")
    p("El Centro de Alertas es el sistema experto del panel. Responde: ¿qué "
      "está mal ahora y qué hacemos al respecto? Incluye un simulador de "
      "estrés (alza del marisco, caída de bebidas y caída de demanda), cuatro "
      "indicadores, tarjetas con el estado de las cinco reglas, planes de "
      "contingencia, mapas de tensión por mes y sucursal y la tabla de "
      "clientes en riesgo.")
    p("Las cinco reglas del sistema experto son: ROI en peligro (ROI de "
      "alimentos menor a 45%), caída de meta (cumplimiento menor a 90%), mix "
      "de bebidas (menor a 30%), deserción (Oro/VIP sin compra en 45 días) y "
      "salud del incentivo (top vendedores de bebidas con calificación menor a "
      "3.5). La Figura 9 muestra el mapa de tensión de cumplimiento por mes y "
      "sucursal: las celdas oscuras marcan los cruces de umbral que activan "
      "los planes de contingencia.")
    figura(9, "fig_m5_tension.png",
           "Mapa de tensión: cumplimiento de meta por mes y sucursal (M5)",
           "Elaboración propia con datos de fact_ventas y fact_presupuesto. "
           "Las celdas más oscuras indican los meses con mayor riesgo de "
           "incumplimiento.", width=5.9 * inch)

    h2("M6 · Pronóstico de Ventas e Inventario")
    p("Este módulo responde: ¿cuánto marisco y cerveza compro para las "
      "próximas semanas? El horizonte es configurable (dos a ocho semanas, con "
      "cuatro por defecto). El modelo es un GradientBoosting sobre la serie "
      "semanal por sucursal, con semana del año, año y sucursal como "
      "características; en el backtest alcanza un MAPE de 30.9% frente a 45.2% "
      "de la referencia ingenua.")
    p("La Figura 10 muestra las últimas semanas del histórico y el pronóstico "
      "a cuatro semanas con su banda de confianza de 80%. El módulo convierte "
      "el pronóstico en insumos: cada porción de Sopa Ancla consume "
      "aproximadamente 0.35 kilogramos de marisco y cada caja de cerveza "
      "contiene 24 unidades; con el precio mayorista de 240 pesos por "
      "kilogramo se calcula la conveniencia de la compra anticipada.")
    figura(10, "fig_m6_forecast.png",
           "Pronóstico semanal de ventas a cuatro semanas con banda de "
           "confianza (M6)",
           "Elaboración propia con el modelo de pronóstico del proyecto "
           "(models/forecast.py). La banda sombreada corresponde al intervalo "
           "de confianza de 80% en escala logarítmica.", width=5.9 * inch)

    h2("M7 · Rotación de Mesas y Eficiencia del Servicio")
    p("Este módulo responde: ¿cuánto tiempo permanece cada mesa y quién la "
      "aprovecha bien? Presenta el tiempo medio de ocupación (aproximadamente "
      "77 minutos), el ticket promedio, la eficiencia en pesos por minuto, el "
      "diagrama de dispersión de meseros, el histograma por sucursal y el "
      "análisis por hora del día y día de semana.")
    p("La Figura 11 muestra la distribución del tiempo de ocupación por "
      "sucursal. Un matiz importante: la menor eficiencia en horas pico es "
      "señal de servicio ágil, no de baja calidad, porque las mesas rotan más "
      "rápido (75 frente a 82 minutos).")
    figura(11, "fig_m7_ocupacion.png",
           "Distribución del tiempo de ocupación de mesa por sucursal (M7)",
           "Elaboración propia con datos de fact_ventas. La línea punteada "
           "indica la media de aproximadamente 77 minutos.", width=5.9 * inch)

    h2("M8 · Análisis de Deserción de Clientes (churn)")
    p("Este módulo responde: ¿a qué clientes valiosos estamos perdiendo y "
      "cuánto dinero nos cuesta? La fecha de corte (por defecto 31-dic-2025) y "
      "el umbral de churn (30 a 120 días, con 45 por defecto) son parámetros "
      "expuestos de forma auditable. El módulo presenta los indicadores de "
      "riesgo, el histograma de días sin visita, la evolución mensual del "
      "churn y la tabla de reactivación.")
    p("La Figura 12 muestra la distribución de días sin visita de los clientes "
      "Oro y VIP. Con el umbral de 45 días, 58 clientes de alto valor (35.8%) "
      "están en riesgo, lo que representa aproximadamente 1.05 millones de "
      "pesos de valor anual en riesgo. Retener a un cliente cuesta una "
      "fracción de lo que cuesta atraer uno nuevo.")
    figura(12, "fig_m8_churn.png",
           "Días sin visita de los clientes Oro y VIP y umbral de churn (M8)",
           "Elaboración propia con datos de dim_clientes_crm y fact_ventas al "
           "corte 31-dic-2025. La barra de la derecha agrupa a los clientes "
           "sin visita registrada en el periodo.", width=5.9 * inch)

    h2("M9 · Matriz de Elasticidad de Precios")
    p("Este módulo responde: ¿a qué productos les subo el precio sin perder "
      "clientes? La elasticidad se estima por subcategoría con un modelo "
      "log-log con efectos fijos de producto y mes, lo que elimina el tamaño "
      "del producto y la estacionalidad. Con los datos del histórico, la "
      "elasticidad media del menú es de -0.58: 33 productos son inelásticos "
      "(valor absoluto menor a 0.5), 41 son elásticos (mayor a 1.0) y el resto "
      "es intermedio.")
    p("La Figura 13 ordena las subcategorías de la más elástica a la más "
      "inelástica. Los ceviches y las variantes (alrededor de -1.5) no deben "
      "tocarse; el ancla es prácticamente inelástica (-0.07) y las bebidas "
      "oscilan entre -0.2 y -0.4. El simulador de re-precio aplica la regla "
      "económica ingreso proyectado = ingreso actual por (1 + cambio de "
      "precio) elevado a (1 + elasticidad); el plan sugerido es subir 5% a los "
      "inelásticos y bajar 3% a los elásticos.")
    figura(13, "fig_m9_elasticidad.png",
           "Elasticidad estimada por subcategoría de producto (M9)",
           "Elaboración propia con el modelo log-log con efectos fijos de "
           "producto y mes. Las barras más oscuras son las subcategorías "
           "elásticas, las más claras las inelásticas.", width=5.9 * inch)

    h2("M10 · Auditoría de Incentivos (anti-fraude)")
    p("Este módulo responde: ¿el mesero que más comisiones gana lo hace con "
      "buen servicio o presionando al cliente? Contrasta las comisiones "
      "calculadas con la política estándar (5% y 1.5 veces) contra la "
      "calificación media de las encuestas ligadas a sus tickets. Un mesero es "
      "crítico (venta impositiva) cuando su calificación es menor a 3.5 y su "
      "comisión es mayor o igual a la mediana del periodo.")
    p("La Figura 14 muestra el diagrama de dispersión de comisión contra "
      "calificación; el cuadro sombreado es la zona de venta impositiva. Con "
      "los datos del histórico, 19 meseros quedan bajo el umbral de servicio y "
      "6 son críticos; el caso de Tamaulipas (cuatro de ocho críticos en S3) "
      "queda detectado por el sistema.")
    figura(14, "fig_m10_auditoria.png",
           "Comisión ganada contra calificación media del servicio (M10)",
           "Elaboración propia con el motor de comisiones del proyecto y las "
           "encuestas de fact_encuestas_satisfaccion. Los puntos oscuros son "
           "los meseros en zona de venta impositiva.", width=5.9 * inch)


def seccion6():
    h1("Clasificación de clientes: Plata, Oro y VIP")
    p("El programa de lealtad clasifica a los clientes en tres niveles. La "
      "distribución la reflejan los datos históricos: Plata (60%, "
      "aproximadamente 240 clientes, con 1 a 2 visitas esperadas al mes), Oro "
      "(30%, aproximadamente 120 clientes, con 2 a 4 visitas) y VIP (10%, "
      "aproximadamente 40 clientes, con 4 a 8 visitas). El nivel define la "
      "frecuencia de visita esperada: cuanto más alto, más consumo esperado y "
      "más caro es perderlo. La Tabla 4 resume la clasificación y la Figura 15 "
      "muestra la distribución por nivel.")
    tabla(4, "Clasificación de clientes del programa de lealtad",
          [["Nivel", "Proporción", "Clientes (sobre 400)", "Frecuencia esperada"],
           ["Plata", "60%", "~240", "1 a 2 visitas al mes"],
           ["Oro", "30%", "~120", "2 a 4 visitas al mes"],
           ["VIP", "10%", "~40", "4 a 8 visitas al mes"]],
          [0.9 * inch, 1.1 * inch, 2.1 * inch, 2.4 * inch],
          "Elaboración propia con base en la regla de clasificación del "
          "Documento Maestro, sección 6. La frecuencia esperada es el "
          "parámetro que usa el análisis de deserción.")
    figura(15, "fig_clientes_niveles.png",
           "Distribución de clientes por nivel del programa (Plata, Oro y VIP)",
           "Elaboración propia con datos de dim_clientes_crm. Las proporciones "
           "corresponden a 60%, 30% y 10% del padrón.",
           width=5.0 * inch)
    p("De cada cliente se registra además la sucursal frecuente, la fecha de "
      "alta, el canal de alta (restaurante 60%, campaña 25% o referencia 15%) "
      "y, para los clientes con deserción simulada, la fecha de salida. La "
      "deserción se calcula solo sobre Oro y VIP: un cliente de alto valor sin "
      "compra en más de 45 días entra en riesgo. Los clientes Plata no activan "
      "la alerta porque su pérdida es menos costosa. El valor anual en riesgo "
      "se estima como el gasto total entre los años desde el alta.")
    p("Nota de transparencia: la deserción está simulada por nivel, con "
      "probabilidades de 12%, 28% y 38% para Plata, Oro y VIP "
      "respectivamente. Es el mecanismo que crea el escenario realista de "
      "churn que se observa en el panel.")


def seccion7():
    h1("Encuestas y comentarios sobre los meseros")
    p("La encuesta de satisfacción registra tres datos por mesa atendida: "
      "calificación del servicio (1 a 5), comentario breve categorizado y "
      "sentimiento derivado (positivo, neutro o negativo). La encuesta se "
      "aplica al cierre de la experiencia, cuando el cliente registrado en el "
      "programa de lealtad paga su cuenta; por ello el momento es posterior a "
      "la cuenta, cuando el cliente ya vivió toda la interacción (toma de "
      "orden, servicio, bebidas y pago) y puede calificar la experiencia "
      "completa del mesero.")
    p("Solo se levantan encuestas sobre tickets de clientes del programa CRM, "
      "aproximadamente 40% de los tickets. Del ticket se conoce el mesero y la "
      "sucursal, lo que permite asignar la calificación. La Tabla 5 resume los "
      "comentarios canónicos y la Figura 16 la distribución de calificaciones "
      "del histórico.")
    tabla(5, "Comentarios canónicos de la encuesta de satisfacción",
          [["Calificación", "Comentario canónico", "Sentimiento"],
           ["1", "Servicio impositivo; me presionaron para pedir más",
            "Negativo"],
           ["2", "La atención no fue agradable", "Negativo"],
           ["3", "Servicio regular", "Neutro"],
           ["4", "Buen servicio, todo rico", "Positivo"],
           ["5", "Excelente atención, volveré", "Positivo"]],
          [1.1 * inch, 3.4 * inch, 2.0 * inch],
          "Elaboración propia con base en el diseño de la encuesta del "
          "Documento Maestro, sección 6.")
    figura(16, "fig_encuestas.png",
           "Distribución de calificaciones de las encuestas de servicio",
           "Elaboración propia con datos de fact_encuestas_satisfaccion. La "
           "línea punteada marca el umbral de servicio saludable (3.5).",
           width=5.6 * inch)
    p("La auditoría (M10) contrasta las comisiones contra las calificaciones y "
      "muestra textualmente el comentario negativo más frecuente de cada "
      "mesero; la alerta de salud del incentivo (M5) enciende una bandera "
      "amarilla si un top vendedor de bebidas tiene calificación menor a 3.5. "
      "Una bandera crítica se lee así: si un mesero cobra comisiones por "
      "encima de la mediana pero sus mesas reportan servicio impositivo, el "
      "sistema lo marca y sugiere reducir el multiplicador de bebidas, rotar "
      "sus mesas y acompañar con capacitación; es un crecimiento no sano, en "
      "el que la comisión crece a costa de la experiencia del cliente.")


def seccion8():
    h1("Preguntas de negocio que responde el CRM")
    p("El módulo CRM y sus extensiones responden nueve preguntas de negocio. "
      "La Tabla 6 indica dónde encontrar cada respuesta en pantalla.")
    tabla(6, "Preguntas de negocio del CRM y ubicación de la respuesta",
          [["N.º", "Pregunta de negocio", "Dónde verla"],
           ["1", "¿Cuántos clientes tiene el programa de lealtad?",
            "M3, indicador Clientes registrados"],
           ["2", "¿Cuántos están realmente activos en el periodo?",
            "M3, indicador Activos y embudo"],
           ["3", "¿Qué nivel predomina y en qué sucursal?",
            "M3, clientes por sucursal y nivel"],
           ["4", "¿La Sopa Ancla arrastra venta de bebidas?",
            "M3, correlación (2.95 vs 1.54 variedades)"],
           ["5", "¿Qué clientes de alto valor estamos perdiendo?",
            "M3 y M8, Oro/VIP sin visita en 45 días (58, 35.8%)"],
           ["6", "¿Cuánto dinero está en riesgo si no los retenemos?",
            "M8, valor anual en riesgo (1.05 millones)"],
           ["7", "¿El riesgo crece o decrece con el tiempo?",
            "M8, evolución mensual del churn rate"],
           ["8", "¿Los meseros top venden bien o venden por presión?",
            "M10, dispersión y banderas críticas"],
           ["9", "¿Qué opinan los clientes del servicio, literalmente?",
            "M10, comentario negativo más frecuente"]],
          [0.45 * inch, 3.35 * inch, 2.7 * inch],
          "Elaboración propia con base en los módulos M3, M5, M8 y M10.",
          font=9.2)


def seccion9():
    h1("Preguntas frecuentes")
    h3("¿Por qué el delta de un indicador aparece vacío?")
    p("El delta compara contra el periodo anterior de igual duración. Si el "
      "rango anterior cae antes del inicio de los datos (01-ene-2024), no hay "
      "comparativo; es un comportamiento esperado.")
    h3("¿Por qué el módulo de pronóstico no deja proyectar?")
    p("Necesita al menos 90 días de histórico dentro del filtro. Se debe "
      "ampliar el rango de fechas seleccionado.")
    h3("¿Por qué la elasticidad pide más meses?")
    p("La estimación necesita mínimo seis meses con variación de precio; con "
      "menos meses el modelo no tiene señal suficiente.")
    h3("¿Por qué la auditoría indica sin encuestas?")
    p("Solo se auditan meseros con encuestas ligadas a tickets del periodo "
      "filtrado. Si el rango se recortó demasiado, se debe ampliar. Las "
      "encuestas existen solo en aproximadamente 40% de los tickets, los del "
      "programa CRM.")
    h3("¿Qué significa 999+ en días sin visita?")
    p("Es un cliente del padrón sin ninguna visita registrada en el periodo; "
      "se considera en máximo abandono y, por tanto, en riesgo.")
    h3("¿Por qué la Sopa de Mariscos no genera incentivos?")
    p("Es el producto ancla: atrae tráfico familiar pero no genera incentivos "
      "por diseño. Es la regla de negocio del proyecto.")
    h3("¿Cómo regresar a los valores por defecto?")
    p("Se recarga la página (tecla R en el navegador) o se usa el ícono de "
      "recarga de Streamlit en la esquina superior derecha.")


def seccion10():
    h1("Nota técnica: los datos son una simulación")
    p("Los ocho archivos CSV son datos sintéticos generados con Python "
      "(src/data_factory.py) con semilla fija 42: el mismo script produce "
      "siempre los mismos datos, con reproducibilidad total. El histórico "
      "simulado es 2024-2025 y las reglas de negocio están incorporadas en el "
      "generador: crecimiento de 1.5 veces en el segundo año, estacionalidad "
      "(Cuaresma +40%, cuesta de enero -20%), costos de marisco ±15%, "
      "presupuesto optimista, correlación ancla-bebidas, elasticidad por "
      "subcategoría y deserción simulada por nivel.")
    p("Para regenerar los datos, acción no recomendada a menos que se desee "
      "una nueva semilla, se ejecutan src/data_factory.py y src/validaciones.py, "
      "que verifica 36 pruebas de negocio. Para este manual es útil saberlo: "
      "lo que se observa en pantalla es el resultado intencional de esas "
      "reglas; por eso los meses de incumplimiento, los seis meseros críticos "
      "o los 58 clientes en riesgo son detectables: el sistema fue diseñado "
      "para que el análisis tenga historia que contar.")


def referencias():
    h1("Referencias")
    for r in [
        "American Psychological Association. (2020). <i>Publication manual of "
        "the American Psychological Association</i> (7.ª ed.). "
        "https://doi.org/10.1037/0000165-000",
        "gluevanos. (2026). <i>El Errante: documento maestro del proyecto</i> "
        "(versión 1.13.0). Proyecto de portafolio no publicado.",
        "Harris, C. R., Millman, K. J., van der Walt, S. J., Gommers, R., "
        "Virtanen, P., Cournapeau, D., et al. (2020). Array programming with "
        "NumPy. <i>Nature, 585</i>(7825), 357-362. "
        "https://doi.org/10.1038/s41586-020-2649-2",
        "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. "
        "<i>Computing in Science &amp; Engineering, 9</i>(3), 90-95. "
        "https://doi.org/10.1109/MCSE.2007.55",
        "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., "
        "Grisel, O., et al. (2011). Scikit-learn: Machine learning in Python. "
        "<i>Journal of Machine Learning Research, 12</i>, 2825-2830. "
        "https://www.jmlr.org/papers/v12/pedregosa11a.html",
        "Plotly Technologies Inc. (2024). <i>Plotly: The front-end for ML and "
        "data science models</i> (versión 6.9.0) [Software]. https://plotly.com",
        "ReportLab. (2025). <i>ReportLab: Open-source PDF library</i> "
        "(versión 5.0.0) [Software]. https://www.reportlab.com",
        "Snowflake Inc. (2025). <i>Streamlit: The fastest way to build and "
        "share data apps</i> (versión 1.61.1) [Software]. https://streamlit.io",
        "The pandas development team. (2024). <i>pandas: Python Data Analysis "
        "Library</i> (versión 2.3.3) [Software]. https://pandas.pydata.org",
    ]:
        p(r, REF)


def apendice():
    h1("Apéndice A: Instalación, pruebas y regeneración")
    h2("Instalación")
    p("1. Crear el entorno virtual: <i>python -m venv .venv</i>. 2. Activar el "
      "entorno (scripts/activate en Windows). 3. Instalar dependencias: "
      "<i>pip install -r requirements.txt</i>. 4. Iniciar la aplicación: "
      "<i>streamlit run app/app.py</i>. Se requiere Python 3.11 o superior y "
      "las librerías pandas, numpy, plotly, scikit-learn y streamlit.")
    h2("Pruebas automatizadas")
    p("El proyecto incluye una suite de 41 pruebas con pytest en la carpeta "
      "tests: 15 de reglas de negocio, 8 del modelo de pronóstico, 8 de "
      "utilidades, 6 del motor de incentivos y 4 pruebas de extremo a extremo "
      "de la aplicación. Se ejecutan con <i>python -m pytest</i>.")
    h2("Regeneración de datos y validación")
    p("La regeneración de los datos sintéticos se realiza con "
      "<i>python src/data_factory.py</i> y su validación con "
      "<i>python src/validaciones.py</i> (36 pruebas de negocio).")
    h2("Generación de este documento")
    p("Las figuras de este manual se generan con "
      "<i>python scripts/figuras_vintage.py</i> y el PDF con "
      "<i>python scripts/generar_manual_pdf.py</i>. Ambos scripts reproducen "
      "exactamente el documento entregado.")


def main():
    portada()
    resumen()
    indice()
    seccion1()
    seccion2()
    seccion3()
    seccion4()
    seccion5()
    seccion6()
    seccion7()
    seccion8()
    seccion9()
    seccion10()
    referencias()
    apendice()

    doc = ManualDoc(
        str(PDF_PATH), pagesize=LETTER,
        leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
        title="Manual de Usuario — El Errante BI",
        author="gluevanos",
    )
    doc.addPageTemplates([
        PageTemplate(id="portada", frames=[FRAME], onPage=on_portada),
        PageTemplate(id="cuerpo", frames=[FRAME], onPage=on_cuerpo),
    ])
    doc.multiBuild(STORY)
    print(f"PDF generado: {PDF_PATH}")


if __name__ == "__main__":
    main()
