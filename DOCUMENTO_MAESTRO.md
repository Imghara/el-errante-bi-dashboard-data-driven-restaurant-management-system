# 📘 DOCUMENTO MAESTRO — PROYECTO "EL ERRANTE"

> **Sistema Inteligente de Optimización de Margen, CRM, Incentivos y Business Intelligence para Restaurantes Multisucursal**

---

## 🗂️ 0. Identidad del Documento

| Campo | Valor |
|---|---|
| **Nombre del proyecto** | El Errante — BI & Incentivos |
| **Versión del documento** | 1.0.0 |
| **Fecha de creación** | 11 de agosto de 2026 |
| **Última actualización** | 12 de agosto de 2026 |
| **Estado general** | 🟡 EN PLANEACIÓN — Fase 0 |
| **Propietario** | Gerente General (usuario del dashboard) |
| **Objetivo superior** | Portafolio profesional de Business Intelligence para ofertar en vacantes |
| **Uso** | Local + Nube gratuita (Streamlit Community Cloud) |
| **Documento fuente** | `El Errante.txt` (especificación original) |
| **Nomenclatura de archivos** | `snake_case` para código y datos · `MAYÚSCULAS` para documentación raíz · prefijos `dim_` / `fact_` para datos |

> ⚠️ **REGLAS DE ORO DEL PROYECTO**
> 1. Todo cambio relevante se registra en la [Sección 14 — Bitácora](#-14-bitácora-de-sesiones-y-puntos-de-guardado).
> 2. Nunca se edita la especificación original (`El Errante.txt`); este documento es la fuente de verdad.
> 3. Cada archivo creado debe estar identificado con un encabezado de comentario (autor, propósito, fecha).
> 4. Antes de cada checkpoint (CP) se ejecuta la validación definida en la [Sección 10](#-10-ruta-de-desarrollo-paso-a-paso-con-puntos-de-revisión).

---

## 🎯 1. Resumen Ejecutivo

**"El Errante"** es un ecosistema de Business Intelligence que transforma la analítica descriptiva tradicional en un **entorno de prescripción estratégica**. Al integrar módulos de predicción de demanda (Forecasting), alertas de deserción en el CRM (Churn) y auditoría del comportamiento del personal, la herramienta se convierte en el **copiloto definitivo del Gerente General**, asegurando la escalabilidad del negocio en Nuevo León, Coahuila y Tamaulipas al blindar el margen operativo frente a las irregularidades del mercado de mariscos.

### 1.1 Los 3 pilares para el portafolio (talking points de entrevista)

1. **Enfoque de Ciencia de Datos Aplicada** — *"No es un tablero de ventas estático; es un software de simulación que ayuda a un Gerente General a tomar decisiones de inventario perecedero basándose en el margen real del platillo."*
2. **Modelado de Datos Avanzado** — Esquema en estrella (`fact_ventas` rodeado de dimensiones como CRM y Productos) controlado por Python.
3. **Lógica de Negocio Compleja** — Crecimiento irregular del 1.5×, estacionalidad del precio mayorista de mariscos (±15%), y exclusión del producto ancla del sistema de incentivos.

### 1.2 Entregables finales

| # | Entregable | Descripción |
|---|---|---|
| E1 | **Datos sintéticos** | 8 archivos CSV interconectados (dimensiones + hechos) con 2 años de historial realista |
| E2 | **Dashboard Streamlit** | Aplicación multi-pestaña con 10 módulos de BI y sistema de alertas experto |
| E3 | **Documentación** | Documento maestro (este), README de portafolio y guía de despliegue |
| E4 | **Despliegue** | Repositorio en GitHub + app pública en Streamlit Community Cloud |

---

## 🏢 2. Comprensión del Negocio

### 2.1 Distribución geográfica y recursos humanos

| Sucursal | Entidad | Ciudad(es) | Meseros | % Personal | Perfil de mercado |
|---|---|---|---|---|---|
| **S1** | Nuevo León | Monterrey | 24 | 50% | Sucursal insignia, alto volumen de mesas y flujo corporativo |
| **S2** | Coahuila | Saltillo / Torreón | 16 | 33.3% | Público marcadamente familiar |
| **S3** | Tamaulipas | Tampico / Reynosa | 8 | 16.7% | La más pequeña; estratégica por cercanía al proveedor de costa |
| **TOTAL** | 3 entidades | — | **48** | 100% | — |

### 2.2 Arquitectura del menú (182 productos)

| Categoría | Cantidad | Detalle |
|---|---|---|
| **Alimentos** | 150 | **1 Producto Ancla** (Sopa de Mariscos — especialidad de la casa, ~25% del volumen de alimentos, precio accesible, **sin incentivo**) + **149** platillos principales y variantes (ceviches, filetes, aguachiles, tacos) |
| **Bebidas** | 32 | Refrescos (10), Aguas Naturales (7), Cervezas (15: nacionales, artesanales, preparados/micheladas) |

> 💡 **Concepto clave**: Las **bebidas son el motor del margen** (bajo costo de producción, alta percepción de valor por marketing visual). El producto **ancla atrae tráfico** pero no genera incentivos.

### 2.3 Comportamiento de ventas (reglas del histórico)

| Regla | Especificación |
|---|---|
| **Crecimiento anual** | Año 2 factura **1.5×** el Año 1, de forma **irregular** (no lineal) |
| **Cuesta de enero** | Ene + Feb: −20% vs promedio general; los meseros rara vez alcanzan KPIs |
| **Temporada baja** | Sep + Oct: caída por regreso a clases |
| **Cuaresma (pico)** | Mar + Abr: **+40%** sobre el promedio (máxima venta para restaurante de mariscos) |
| **Picos masivos** | May (Día de las Madres) y Dic (fin de año) |
| **Costo mayorista** | Costos de insumos de platillos principales (**excepto la sopa ancla**) fluctúan **±15%** mes a mes (vedas, clima marítimo) → obliga al gerente a mover incentivos para proteger el ROI |

---

## 🧩 3. Modelo de Datos — Esquema en Estrella

### 3.1 Diagrama conceptual

```
                        ┌─────────────────────┐
                        │  dim_sucursales     │  ← (S1/S2/S3, ciudad, entidad, lat/lon)
                        └─────────┬───────────┘
                        ┌─────────┴───────────┐
                        │  dim_meseros        │  ← 48 meseros
                        └─────────┬───────────┘
┌──────────────────┐    ┌─────────┴───────────┐    ┌─────────────────────┐
│ dim_productos    │────│  fact_ventas        │────│ dim_clientes_crm    │
│ (182 productos)  │    │  (ticket + línea)   │    │ (Plata/Oro/VIP)     │
└──────────────────┘    └─────────┬───────────┘    └─────────────────────┘
                        ┌─────────┴───────────┐
                        │  fact_costos_mens   │  ← costo ±15% por producto/mes
                        └─────────────────────┘
┌──────────────────┐    ┌─────────────────────┐
│ fact_presupuesto │    │ fact_encuestas_sat  │  ← encuestas ligadas a ticket
└──────────────────┘    └─────────────────────┘
```

### 3.2 Diccionario de datos (8 tablas)

> ⚠️ **Nota de mejora sobre la especificación**: el documento original define 6 tablas. Se agregan **2 tablas de soporte** (`dim_sucursales` y `fact_encuestas_satisfaccion`) requeridas por los módulos de mapa geográfico y auditoría de incentivos. Los IDs originales se respetan.

#### 📄 `dim_sucursales.csv` *(nueva — soporte mapa geográfico)*
| Campo | Tipo | Descripción |
|---|---|---|
| id_sucursal | str | S1, S2, S3 |
| nombre | str | Ej. "El Errante Monterrey" |
| ciudad | str | Monterrey / Saltillo / Tampico |
| entidad | str | Nuevo León / Coahuila / Tamaulipas |
| num_meseros | int | 24 / 16 / 8 |
| lat, lon | float | Coordenadas para el mapa geográfico |
| descripcion | str | Perfil de mercado |

#### 📄 `dim_meseros.csv` — **48 registros**
| Campo | Tipo | Descripción |
|---|---|---|
| id_mesero | int | 1–48 |
| nombre | str | Nombre y apellido (respetando límite por sucursal) |
| sucursal | str | NL / Coahuila / Tamaulipas |
| fecha_ingreso | date | Antigüedad para análisis de rendimiento |
| activo | bool | True |

#### 📄 `dim_productos.csv` — **182 registros**
| Campo | Tipo | Descripción |
|---|---|---|
| id_producto | int | 1–182 |
| nombre_producto | str | Ej. "Aguachile Verde" |
| categoria | str | Alimento / Bebida |
| subcategoria | str | Ancla, Principal, Variante, Refresco, Agua, Cerveza |
| etiquetas | str | marketing, vistoso, temporada, familiar (para análisis) |
| precio_venta | float | Precio al público |
| costo_base | float | Costo base de referencia (pre-variación) |
| es_ancla | bool | True solo para Sopa de Mariscos |
| es_incentivable | bool | False solo para el ancla |

#### 📄 `dim_clientes_crm.csv` — clientes del programa de lealtad
| Campo | Tipo | Descripción |
|---|---|---|
| id_cliente | int | |
| nombre | str | |
| nivel | str | Plata / Oro / VIP |
| frecuencia_visitas_mensual | float | Meta de frecuencia del cliente |
| sucursal_frecuente | str | S1/S2/S3 |
| fecha_alta | date | |
| canal_alta | str | restaurante / campaña / referencia |

#### 📄 `fact_costos_mensuales.csv` — cruce producto × mes
| Campo | Tipo | Descripción |
|---|---|---|
| id_producto | int | FK → dim_productos |
| mes_ano | str | AAAAMM (24 meses) |
| costo_elaboracion | float | Costo con variación **±15%** (excepto ancla) |

#### 📄 `fact_presupuesto.csv` *(sexta tabla de la especificación)*
| Campo | Tipo | Descripción |
|---|---|---|
| mes_ano | str | AAAAMM |
| id_sucursal | str | S1/S2/S3 |
| meta_ventas | float | Meta en $ (ligeramente **optimista**) |
| meta_roi_promedio | float | Meta de ROI (%) |
| meta_venta_bebidas | float | Meta en $ del rubro bebidas |
| meta_ticket_promedio | float | Meta de ticket por mesa |

#### 📄 `fact_ventas.csv` — registro transaccional (la tabla más grande)
| Campo | Tipo | Descripción |
|---|---|---|
| id_ticket | int | Ticket (puede tener varias líneas) |
| fecha_hora | datetime | Marca de tiempo de la venta |
| id_sucursal | str | S1/S2/S3 |
| id_mesero | int | FK → dim_meseros |
| id_producto | int | FK → dim_productos |
| cantidad | int | Unidades vendidas |
| id_cliente_crm | int \| null | **40%** de los tickets ligados a CRM (programa de lealtad) |
| hora_apertura_mesa | datetime | *Nuevo:* apertura de mesa |
| hora_cierre_mesa | datetime | *Nuevo:* cierre de mesa (para rotación) |
| precio_unitario_aplicado | float | *Nuevo:* precio pagado (incluye inflación suave ~4% anual, base para M9 elasticidad) |
| metodo_pago | str | Efectivo / Tarjeta / Transferencia |

> ℹ️ La calificación de servicio vive en `fact_encuestas_satisfaccion` (no se duplica en ventas).

#### 📄 `fact_encuestas_satisfaccion.csv` *(nueva — auditoría de incentivos)*
| Campo | Tipo | Descripción |
|---|---|---|
| id_encuesta | int | |
| id_ticket | int | FK → fact_ventas |
| id_mesero | int | |
| calificacion_servicio | int | 1–5 |
| comentario | str | Texto opcional |
| sentimiento | str | positivo / neutro / negativo (etiqueta) |

### 3.3 Volumen estimado de datos

| Tabla | Registros estimados |
|---|---|
| dim_sucursales | 3 |
| dim_meseros | 48 |
| dim_productos | 182 |
| dim_clientes_crm | ~400 (Plata 60% / Oro 30% / VIP 10%) |
| fact_costos_mensuales | 182 × 24 = **4,368** |
| fact_presupuesto | 3 × 24 = **72** |
| fact_ventas (líneas) | ~**450,000 – 650,000** (2 años, 3 sucursales, tickets diarios) |
| fact_encuestas_satisfaccion | ~40% de los tickets |

---

## 🏗️ 4. Stack Tecnológico

| Capa | Tecnología | Versión mínima | Justificación |
|---|---|---|---|
| Lenguaje | Python | 3.10+ | Estándar en BI/Data Science |
| Datos | pandas + numpy | 2.x / 1.26 | Manipulación y generación de datos |
| Dashboard | **Streamlit** | 1.36+ | Gratuito, reactivo, ideal para portafolio |
| Gráficos | **Plotly** | 5.x | Interactivos (zoom, hover, filtros) |
| ML (forecast) | scikit-learn (+ statsmodels opcional) | 1.4+ | Regresión estacional ligera, sin dependencias pesadas |
| Calidad | pytest (opcional) | 8.x | Validación de reglas de negocio |
| Versionado | Git + GitHub | — | Publicación del portafolio |
| Nube | Streamlit Community Cloud | — | Despliegue gratuito |

> 🔧 **Decisión técnica (forecasting)**: se usará un modelo de **regresión estacional ligero** (features: mes, tendencia, día de semana, efectos de sucursal) en scikit-learn. Se evalúa SARIMA (statsmodels) como comparativo. Esto evita la dependencia pesada de Prophet y funciona bien en la nube gratuita.

---

## 🎨 5. Sistema de Diseño (UI/UX)

> Requisito del proyecto: manejo **profesional de colores, gráficos y relaciones**, práctico, moderno y apto para trabajo diario.

### 5.1 Paleta oficial — "Océano & Arena"

| Rol | Color | Hex | Uso |
|---|---|---|---|
| 🟦 Primario | Azul Océano Profundo | `#0B2545` | Fondo principal, barras laterales, encabezados |
| 🟦 Primario claro | Azul Marino | `#13315C` | Superficies secundarias |
| 🟩 Acento positivo | Turquesa Oleaje | `#1BA39C` | Metas cumplidas, crecimiento, éxito |
| 🟨 Acento cálido | Ámbar Arena | `#F5A623` | Advertencias, incentivos, alertas medias |
| 🟥 Acento crítico | Coral Emergencia | `#E74C3C` | Alertas críticas (ROI, deserción, incumplimiento) |
| ⬜ Neutro claro | Perla | `#F8FAFC` | Fondos de tarjetas en modo claro |
| ⬛ Neutro oscuro | Grafito | `#1E293B` | Texto principal |
| 🩶 Neutro medio | Plata | `#94A3B8` | Texto secundario, bordes |

### 5.2 Semántica de estados (consistente en TODA la app)

| Estado | Color | Ejemplo de uso |
|---|---|---|
| ✅ Saludable | Turquesa `#1BA39C` | KPI ≥ meta, ROI sano, mesero sin banderas |
| ⚠️ Vigilar | Ámbar `#F5A623` | 90–95% de cumplimiento, salud del incentivo en duda |
| 🚨 Crítico | Coral `#E74C3C` | ROI < 45%, cumplimiento < 90%, churn activo |

### 5.3 Tipografía e interacción

- **Fuentes**: `Inter` (datos y UI) + `Poppins` (títulos) — cargadas desde Google Fonts.
- **Tarjetas KPI**: `st.metric` con delta (+12% vs mes anterior), colores semánticos.
- **Micro-interacciones**: hover en gráficos Plotly (información de contexto), tooltips, botones de estrategia en alertas.
- **Modo oscuro** predeterminado (estética BI premium), con tema configurado en `.streamlit/config.toml`.

### 5.4 Mapa de la aplicación (navegación)

```
El Errante BI — Sidebar
├── 🏠 Resumen Ejecutivo (landing con KPIs globales)
├── 💰 01 · Consolidado Financiero & ROI
├── 🥇 02 · Programa de Incentivos
├── 👥 03 · CRM & Marketing
├── 🎯 04 · Presupuesto vs Real
├── 🚨 05 · Centro de Alertas (Sistema Experto)
├── 🔮 06 · Pronóstico (Forecasting)
├── ⏱️ 07 · Rotación de Mesas & Servicio
├── 💎 08 · Inteligencia de Menú (Elasticidad)
└── 🕵️ 09 · Auditoría de Incentivos (Anti-fraude)
```

---

## 🧠 6. Especificación Funcional de Módulos

### M1 · Consolidado Financiero y ROI
- Mapa geográfico dinámico de las 3 sucursales + tarjetas KPI (`st.metric`).
- Serie temporal con zoom y filtro de rango de fechas; visualizar meses de incumplimiento vs Cuaresma.
- **ROI** calculado dinámicamente: `ROI = (Precio_Venta − Costo_Elaboración) / Costo_Elaboración`.

### M2 · Programa de Incentivos
- **Slider de comisión** (`st.slider`): simular comisión en variantes de platillos con mejor ROI → proyección de ingreso extra.
- **Leaderboard de 48 meseros** (filtrable por sucursal) que **excluye la Sopa Ancla** del cálculo.
- Ranking de venta de bebidas vistosas y platillos de temporada.

### M3 · CRM & Marketing
- **Embudo** de clientes VIP activos por sucursal (NL vs Tamaulipas vs Coahuila).
- **Análisis de correlación**: mesas que consumen Sopa Ancla → ordenan >2 variedades de cervezas/aguas preparadas (salvando el margen del ticket familiar).

### M4 · Presupuesto de Ventas vs Real
- Presupuesto anual desglosado mensual, absorbe estacionalidad.
- **% Cumplimiento (Pipeline/Gauge)**: ej. NL presupuestó $1,000,000 en Enero, vendió $920,000 → **92%** → enciende alarmas.
- Regla de generación: reales quedan 5–10% abajo en Ene/Feb/Sep/Oct y **12% arriba** en Cuaresma.

### M5 · Sistema de Alertas y Planes de Contingencia (Sistema Experto)
| 🚨 Alerta | Condición de activación | Plan de contingencia (ventana emergente) |
|---|---|---|
| **ROI en Peligro** | ROI promedio **de la categoría platillos/mariscos** del mes < **45%** (por alza de marisco mayorista) | 1. Incentivo meseros al **8%** solo en Aguas Naturales y Cervezas Artesanales. 2. Ajuste temporal de porciones en variantes secundarias **sin tocar el ancla**. |

> 🔧 **Decisión de diseño (documentada)**: el umbral del 45% se aplica al ROI de la categoría **Alimentos** (platillos/mariscos), que es la afectada directamente por el precio del marisco mayorista. El ROI de bebidas se mantiene alto por diseño (motor de margen), de modo que la alerta refleja fielmente la lógica de negocio: cuando sube el costo del marisco, el margen de los platillos se comprime y dispara el plan de contingencia.
| **Caída de Meta Ventas** | Cumplimiento presupuesto mensual acumulado < **90%** | 1. Campaña CRM: cupones de bebidas vistosas a VIP/Oro (reactivar martes/miércoles). 2. Concurso "Mesero Estrella": bono en efectivo al que eleve su ticket promedio 15%. |
| **Desviación Mix Bebidas** | Proporción de ingresos por bebidas < **30%** del ticket | 1. Ofrecer "Bebida de Temporada Vistosa" antes de tomar la orden de la Sopa. 2. Neuromarketing visual: mantelería/pantallas con coctelería de la casa. |
| **Riesgo de Deserción (Churn)** | Cliente VIP/Oro sin compra en **45 días** | Botón: "Enviar incentivo personalizado de Sopa de Mariscos gratis con 2 bebidas de marketing". |
| **Salud del Incentivo** | Mesero top en bebidas con calificación de servicio < 3.5 | Bandera amarilla: crecimiento no sano, supervisar venta impositiva. |

> Implementación: evaluación reactiva por periodo con Python condicional; icono rojo/ámbar parpadeante + modal con plan de estrategia al hacer clic.

### M6 · Pronóstico de Ventas e Inventario (Forecasting)
- Modelo de series temporales (regresión estacional ligera) sobre los 2 años históricos.
- **Predicción 4 semanas**: kilos de marisco y cajas de cerveza necesarios.
- Tabla de conversión a insumos (ej. Sopa de Mariscos ≈ 0.35 kg marisco/porción; cerveza 24 uds/caja).
- Impacto: compra anticipada con mayoristas en Tamaulipas para congelar precio bajo (protege ROI de raíz).

### M7 · Rotación de Mesas y Eficiencia del Servicio
- Columnas `Hora_Apertura_Mesa` / `Hora_Cierre_Mesa` → **Tiempo de Ocupación Promedio**.
- Cruce con rendimiento de meseros: detectar si un ticket alto = "secuestro de mesa" vs eficiencia real (bebidas vistosas rápidas, liberación de mesa en horas pico).

### M8 · Análisis de Deserción de Clientes (Churn Rate)
- Días desde la última visita por cliente.
- **Fecha de referencia**: como el histórico simulado es 2024–2025, el cálculo de churn usa como referencia la **última fecha del dataset** (31-dic-2025), no la fecha real del sistema. El dashboard expondrá este parámetro para que sea auditable.
- VIP/Oro sin visita en 45 días → etiqueta **"Riesgo de Deserción"** → alerta con botón de reactivación.
- Contexto de negocio: cuesta 5× más atraer cliente nuevo en Coahuila que retener a un VIP en NL.

### M9 · Matriz de Elasticidad de Precios
- **Scatter Plot interactivo**: Volumen de Venta vs Precio de Venta (150 platillos + variantes).
- Identificar **inelásticos** (sube $10, venden igual — ej. bebidas de marketing) vs **sensibles** (ceviche → desplome).
- Poder científico para ajustar precios por entidad federativa.

### M10 · Auditoría de Calidad del Programa de Incentivos (Anti-fraude)
- **Indicador de Salud del Incentivo**: comisiones ganadas vs calificación del servicio (encuestas ligadas al ticket).
- Detecta "canibalización"/venta impositiva (ej. mesero #1 en Tamaulipas con quejas de servicio impositivo → bandera amarilla).

---

## 📐 7. Arquitectura de Archivos y Nomenclatura

```
Errante/  (raíz del proyecto)
│
├── DOCUMENTO_MAESTRO.md          ← ESTE DOCUMENTO (fuente de verdad + bitácora)
├── El Errante.txt                ← especificación original (NO EDITAR)
├── README.md                     ← portafolio / landing para GitHub (Fase 7)
├── requirements.txt              ← dependencias
├── .gitignore
├── .streamlit/
│   └── config.toml               ← tema visual oficial
│
├── data/
│   ├── dim_sucursales.csv
│   ├── dim_meseros.csv
│   ├── dim_productos.csv
│   ├── dim_clientes_crm.csv
│   ├── fact_costos_mensuales.csv
│   ├── fact_presupuesto.csv
│   ├── fact_ventas.csv
│   └── fact_encuestas_satisfaccion.csv
│
├── src/                          ← código de datos
│   ├── config.py                 ← constantes centrales (rutas, semillas, paleta)
│   ├── data_factory.py           ← generador de datos sintéticos (Fase 1)
│   └── validaciones.py           ← QA de reglas de negocio (Fase 2)
│
├── app/                          ← dashboard Streamlit
│   ├── app.py                    ← entrada / navegación
│   ├── styles.py                 ← CSS y tema
│   ├── utils.py                  ← helpers (carga de datos, métricas, alertas)
│   ├── modulos/
│   │   ├── m1_consolidado.py
│   │   ├── m2_incentivos.py
│   │   ├── m3_crm.py
│   │   ├── m4_presupuesto.py
│   │   ├── m5_alertas.py
│   │   ├── m6_forecast.py
│   │   ├── m7_rotacion.py
│   │   ├── m8_churn.py
│   │   ├── m9_elasticidad.py
│   │   └── m10_auditoria.py
│   └── assets/
│       └── logo.png
│
├── models/
│   └── forecast.py               ← modelo de pronóstico (Fase 5)
│
├── scripts/                      ← generación del manual PDF (pre-F7)
│   ├── figuras_vintage.py        ← 16 figuras monocromas "dibujo a mano"
│   ├── generar_manual_pdf.py     ← MANUAL_DE_USUARIO.pdf (APA 7.ª)
│   └── figuras/                  ← PNGs generados por el script
│
└── tests/
    ├── conftest.py               ← fixtures compartidas (pytest)
    ├── test_reglas_negocio.py    ← T1-T11 portadas de validaciones.py
    ├── test_forecast.py          ← modelo de pronóstico
    ├── test_utils.py             ← helpers de formato
    ├── test_incentivos.py        ← motor M2
    └── test_app_smoke.py         ← E2E AppTest (marcado e2e)
```

### 7.1 Convenciones de identificación de archivos

- **Código**: `snake_case.py`, con docstring inicial: `# ============================================` + propósito, autor, fecha, versión.
- **Datos**: prefijos `dim_` (dimensiones) y `fact_` (hechos), minúsculas.
- **Docs**: `MAYÚSCULAS.md` en raíz; versionados en `CHANGELOG` (sección 14 del maestro).
- **Módulos del dashboard**: `m<N>_<nombre>.py` para trazabilidad con la especificación.
- **Semilla aleatoria fija** (p. ej. `SEED = 42`) para que la generación de datos sea **reproducible**.

---

## 🗺️ 8. Ruta de Desarrollo Paso a Paso con Puntos de Revisión

> Cada fase termina en un **Checkpoint (CP)** con criterios de aceptación verificables. Si el CP no se cumple, se corrige antes de avanzar.

| Fase | Descripción | Entregables | Criterios de aceptación (Checkpoint) |
|---|---|---|---|
| **F0** · Fundaciones | Estructura de carpetas, `requirements.txt`, `.gitignore`, `.streamlit/config.toml`, entorno virtual | Skeleton del repo listo | `python -c "import pandas, numpy, streamlit, plotly, sklearn"` OK |
| **F1** · Data Factory | `src/config.py` + `src/data_factory.py` generan los **8 CSV** | Todos los CSV en `data/` | **CP1**: CSV existen, volúmenes ≈ tabla 3.3, sin valores nulos críticos |
| **F2** · QA de Negocio | `src/validaciones.py` verifica reglas algorítmicas | Reporte de validación | **CP2**: Año 2 ≈ 1.5× Año 1 (±5%), estacionalidad ±, 40% CRM, ancla sin incentivo, costos ±15% |
| **F3** · Núcleo del Dashboard | `app.py`, tema, M1 (Consolidado), M2 (Incentivos), M3 (CRM) | 3 módulos funcionales | **CP3**: app corre local, filtros redibujan gráficos, mapa + KPIs OK |
| **F4** · BI Avanzado I | M4 (Presupuesto vs Real), M5 (Alertas/experto) | Gauge de cumplimiento + centro de alertas | **CP4**: alertas se activan/desactivan según umbrales (45/90/30%) |
| **F5** · BI Avanzado II | M6 (Forecast), M7 (Rotación), M8 (Churn), M9 (Elasticidad), M10 (Auditoría) | 5 módulos + `models/forecast.py` | **CP5**: pronóstico 4 semanas genera insumos; churn 45 días detecta clientes; scatter de elasticidad OK |
| **F6** · QA Visual y Pruebas | Pruebas de reglas (`tests/`), pulido UI/UX, responsive, estado vacío | Tests verdes + UI final | **CP6**: `pytest` pasa; navegación completa sin errores en consola |
| **F7** · Publicación | Repositorio GitHub (con `data/` incluida), README de portafolio, despliegue Streamlit Community Cloud | Repo público + app desplegada | **CP7**: app en línea; clics en filtros redibujan todos los gráficos en tiempo real |

### 8.1 Carga de trabajo estimada (sesiones de trabajo)

| Fase | Sesiones estimadas | Notas |
|---|---|---|
| F0 | 1 | Incluye instalación de entorno |
| F1 | 2 | El generador es el corazón del realismo |
| F2 | 1 | Validaciones automatizadas |
| F3 | 2–3 | Mayor esfuerzo de UI |
| F4 | 1–2 | Lógica experta de alertas |
| F5 | 2–3 | ML + 5 módulos |
| F6 | 1–2 | Pulido + pruebas |
| F7 | 1 | GitHub + nube |

---

## 🧪 9. Plan de Pruebas y Validación

| # | Prueba | Método | Fase |
|---|---|---|---|
| T1 | Volúmenes de datos | Conteo de filas por CSV | F1 |
| T2 | Crecimiento 1.5× Año 2 | Comparar facturación anual agregada | F2 |
| T3 | Estacionalidad (−20%, +40%, picos) | Ratios mensuales vs promedio | F2 |
| T4 | 40% de tickets con CRM | % de nulos en `id_cliente_crm` ≈ 60% | F2 |
| T5 | Ancla sin incentivos | Verificar `es_incentivable=False` en cálculo de comisiones | F2 |
| T6 | Variación de costos ±15% | Desviación mensual vs costo base | F2 |
| T7 | Presupuesto: reales 5–10% abajo / 12% arriba | Ratios de cumplimiento por mes | F4 |
| T8 | Alertas por umbral | Simular escenarios (ROI 44% → alerta ON) | F4 |
| T9 | Churn 45 días | Clientes con última visita > 45 días | F5 |
| T10 | E2E en navegador | Clics en filtros redibujan gráficos sin errores de consola | F6–F7 |

---

## 🚀 10. Despliegue

### 10.1 GitHub
1. Repositorio `el-errante-bi` (público), estructura de la sección 7.
2. Incluir los CSV en `data/` (como pide la especificación).
3. `README.md` con: pitch de los 3 pilares, capturas del dashboard, stack, instrucciones de ejecución local.

### 10.2 Streamlit Community Cloud (gratuito)
1. Cuenta vinculada a GitHub.
2. Conectar repositorio → `app/app.py` como archivo principal.
3. `requirements.txt` con versiones fijas.
4. Prueba interactiva: filtros de fecha deben redibujar todos los gráficos en tiempo real.

### 10.3 Ejecución local
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python src/data_factory.py      # genera los CSV (si no existen)
streamlit run app/app.py
```

---

## 📊 11. KPI Maestros del Dashboard

| KPI | Fórmula | Umbral de alerta |
|---|---|---|
| **ROI promedio** | `(PV − CE) / CE` | < 45% 🚨 |
| **% Cumplimiento presupuesto** | `Ventas_Reales / Meta_Ventas` | < 90% 🚨 |
| **Mix de bebidas** | `Ingresos_Bebidas / Ticket_Total` | < 30% 🚨 |
| Ticket promedio | Ventas / Nº tickets | — |
| Tiempo de ocupación de mesa | `Cierre − Apertura` | — |
| Churn rate | Clientes en riesgo / Clientes activos | 45 días sin visita |
| Salud del incentivo | Comisiones vs calificación servicio | < 3.5 ⚠️ |

---

## 🔖 12. Guion de Presentación del Portafolio (Elevator Pitch)

> *"Este ecosistema de BI para 'El Errante' transforma la analítica descriptiva tradicional en un Entorno de Prescripción Estratégica. Al integrar módulos de Predicción de Demanda (Forecasting), Alertas de Deserción en el CRM (Churn) y Auditoría del Comportamiento del Personal, la herramienta se convierte en el copiloto definitivo del Gerente General, asegurando la escalabilidad del negocio en Nuevo León, Coahuila y Tamaulipas al blindar el margen operativo frente a las irregularidades del mercado de mariscos."*

**Puntos de demostración en entrevista:**
1. Abrir pestaña **Alertas** → mostrar cómo el ROI < 45% dispara el plan de contingencia.
2. Subir el **slider de comisiones** en Incentivos → ver proyección de ingreso extra.
3. Mostrar el **pronóstico de 4 semanas** en kilos de marisco → decisión de compra anticipada.
4. Mostrar el **churn** → botón de reactivación de cliente VIP.

---

## 📝 13. Bitácora de Sesiones y Puntos de Guardado

> **Cómo usar**: al inicio de cada sesión, lee el último punto de guardado (estado más reciente con ✅). Al finalizar, agrega una fila nueva. Si el trabajo se interrumpe, el "punto de guardado" permite retomar exactamente donde quedó.

### Estado de fases

| Fase | Estado | Checkpoint |
|---|---|---|
| F0 · Fundaciones | ✅ Completada | — |
| F1 · Data Factory | ✅ Completada | **CP1 APROBADO** (8 CSV, 708,114 líneas de ventas) |
| F2 · QA de Negocio | ✅ Completada | **CP2 APROBADO** (33/33 pruebas) |
| F3 · Núcleo Dashboard | ✅ Completada | **CP3 APROBADO** (app en vivo, M1 verificado en navegador) |
| F4 · BI Avanzado I | ✅ Completada | **CP4 APROBADO** (gauge cumplimiento + sistema experto de alertas) |
| F5 · BI Avanzado II | ✅ Completada | **CP5 APROBADO** (forecast + churn + elasticidad + auditoría anti-fraude) |
| F6 · QA Visual | ✅ Completada | **CP6 APROBADO** (pytest 41/41 · navegador 10/10 sin errores) |
| F7 · Publicación | ✅ Completada | **CP7 APROBADO** (app en línea + navegación verificada en la nube) |

### Registro de sesiones

| # | Fecha | Sesión | Qué se hizo | Estado | Siguiente paso |
|---|---|---|---|---|---|
| 1 | 2026-08-11 | Planeación | Revisión de especificación, verificación de entorno, creación del Documento Maestro | ✅ Completada | **F0**: instalar Git y dependencias, verificar Python |
| 2 | 2026-08-11 | F0 parcial | Esqueleto F0 creado: `requirements.txt`, `.gitignore`, `.streamlit/config.toml` (tema oficial), `src/config.py` (constantes centrales) | ✅ Completada | F1: validar generador |
| 3 | 2026-08-11 | F0-F2 completadas | Git 2.55.0 instalado, Python 3.11.9 verificado, `.venv` creado con pandas 2.3.3/streamlit 1.61.1/plotly 6.9.0/sklearn 1.9.0. `data_factory.py` ejecutado → 8 CSV (708,114 líneas de ventas). `validaciones.py` creado y ejecutado → **CP2 33/33 aprobado** | ✅ Completada | **F3**: app Streamlit (núcleo M1/M2/M3) |
| 4 | 2026-08-12 | Manual de usuario | Revisión integral del proyecto (10 módulos, generador, forecast, datos verificados en vivo). Creación de `MANUAL_DE_USUARIO.md`: guía de uso, origen de datos por elemento, clasificación de clientes, momento de las encuestas a meseros y preguntas de negocio del CRM | ✅ Completada | **F6**: QA visual + pruebas automatizadas |
| 5 | 2026-08-12 | F6 QA Visual | `tests/` pytest (41 pruebas), fix de guarda M6 (90 días: timestamps→días), pulido UI (estado vacío global + footer), verificación navegador 10/10 módulos sin errores de consola | ✅ Completada | **F7**: Publicación (git init, README, GitHub, Cloud) |
| 6 | 2026-08-12 | Manual PDF profesional | `MANUAL_DE_USUARIO.pdf` (28 páginas) bajo normas **APA 7.ª** y **una sola tinta**: portada APA (autor gluevanos, instructor Buffy/IA), resumen, índice con números de página, 16 figuras monocromas estilo dibujo a mano con datos reales, 6 tablas, número de página y leyenda vertical al margen. Scripts: `figuras_vintage.py` + `generar_manual_pdf.py` | ✅ Completada | **F7**: Publicación (git init, README, GitHub, Cloud) |
| 7 | 2026-08-12 | F7 GitHub + Cloud | `git init -b main`, identidad gluevanos, README + 3 capturas reales (Playwright), repo creado por el usuario, **push exitoso** (1aa6b93, licencia MIT), **despliegue en Streamlit Community Cloud** (`app/app.py`) → app en línea verificada (M1/M3/M9 + footer, 0 errores de app) | ✅ Completada | Proyecto publicado — CP7 APROBADO |

### 🟢 PUNTO DE GUARDADO ACTUAL

```
📌 Sesión 17 — 2026-08-12 — F7 COMPLETADA → CP7 APROBADO · PROYECTO EN LÍNEA 🎉
   Estado del proyecto:
     ✅ F0-F7 COMPLETAS (CP1 a CP7 aprobados) — módulos M1 a M10 operativos
     ✅ Repositorio público: https://github.com/Imghara/
        el-errante-bi-dashboard-data-driven-restaurant-management-system
        (licencia MIT, README de portafolio + capturas reales del dashboard)
     ✅ App desplegada: https://bi-dashboard-data-driven-restaurant-management-
        system.streamlit.app/ — verificada en la nube con navegación de módulos
        (M1 KPIs+mapa · M3 CRM · M9 elasticidad · footer OK · 0 errores de app)
     ✅ MANUAL_DE_USUARIO.pdf (APA 7.ª, 28 páginas, una tinta) + tests 41/41
     ✅ README actualizado con la URL real de la demo
   El proyecto está PUBLICADO. Opcionales a futuro: Git LFS para data/ (82 MB),
   subdominio personalizado, más capturas al README.
```

### Historial de versiones del documento maestro

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0.0 | 2026-08-11 | Creación del documento maestro con especificación completa, modelo de datos, sistema de diseño, ruta de desarrollo con checkpoints y bitácora |
| 1.0.1 | 2026-08-11 | Registro de sesión 2 y avance parcial de F0 (esqueleto de archivos) |
| 1.1.0 | 2026-08-11 | F1 redactada (data_factory v0.1.1); decisiones documentadas: ROI de alerta sobre categoría Alimentos, fecha de referencia de churn, columna `precio_unitario_aplicado`, volumen estimado de ventas actualizado |
| 1.2.0 | 2026-08-11 | **CP1 y CP2 aprobados**: entorno listo (Git/Python/.venv), 8 CSV generados (708,114 líneas de ventas), 33/33 validaciones de negocio. Entorno virtual con pandas 2.x (estabilidad BI). Sesión 3 registrada |
| 1.2.1 | 2026-08-11 | Revisión de código: limpieza en `validaciones.py` (import numpy sin uso, merge simplificado en T6, groupby optimizado en T8) y `data_factory.py` (rama inalcanzable eliminada). Re-ejecución: generador OK y CP2 33/33 |
| 1.3.0 | 2026-08-12 | **F3 completada (CP3)**: app Streamlit con tema Océano & Arena (`app/styles.py`), carga cacheada (`app/utils.py`), M1 Consolidado Financiero y ROI (4 KPIs, mapa geo, serie temporal con zoom, cumplimiento presupuesto, ROI mensual con umbral 45%), sidebar con navegación y filtros globales. Verificada con AppTest (0 errores, filtros interactivos) y browser-use en vivo. Corrección de imports sin prefijo de paquete (conflicto app.py/app) y limpieza por revisión |
| 1.3.1 | 2026-08-12 | **M2 Programa de Incentivos completado**: simulador de comisiones (sliders tasa 0-15% y multiplicador alto-ROI 1.0-3.0x), leaderboard de 48 meseros excluyendo el ancla, rankings de bebidas vistosas y platillos de temporada, y proyección de ingreso extra con modelo de elasticidad (incluye costo sobre ventas existentes). Verificado: AppTest 0 errores (slider 5→10% duplica comisiones), navegador en vivo OK. Revisión aplicada: parámetros muertos eliminados, modelo de proyección corregido |
| 1.4.0 | 2026-08-12 | **M3 CRM & Marketing completado**: embudo de clientes por nivel, clientes activos por sucursal y nivel, correlación ancla→bebidas (regla M3: 2.95 vs 1.54 variedades), churn 45 días con plan de reactivación. **Mejora al generador**: deserción simulada de clientes (`fecha_salida`) para dar realismo al churn (58/162 Oro/VIP en riesgo, 36%). Nueva validación T10. CP2: 34/34. Revisión aplicada: NaN de churn (fillna 9999), lambda sin efecto eliminada, renombrado `fecha_ultima_visita`→`fecha_salida`, parseo de fechas en utils |
| 1.5.0 | 2026-08-12 | **M4 Presupuesto vs Real completado** (`app/modulos/m4_presupuesto.py`): 3 gauges de cumplimiento por sucursal, barras mensuales real vs meta, serie de cumplimiento con banda de vigilancia y umbral crítico, tabla detalle con estados semánticos. **Decisión documentada**: umbrales alineados con §5.2 (✅≥100% · ⚠️90-99.9% · 🚨<90%); inicialmente se propuso 95% único, pero contradecía la regla M5 (<90%) → se separaron `UMBRAL_CRITICO=0.90` y `UMBRAL_VIGILANCIA=0.95`. Revisión aplicada: merge `how='left'` desde presupuesto (mes sin ventas = 0% → 🚨), `PALETA_SUCURSAL.get()` con fallback, KPI honesto "Meses bajo meta" (47/72). Verificado: AppTest 0 errores (filtros fecha/sucursal) + navegador en vivo |
| 1.6.0 | 2026-08-12 | **M5 Sistema de Alertas completado — F4 TERMINADA (CP4)**: `app/modulos/m5_alertas.py` (sistema experto). 5 reglas del documento evaluadas reactivamente con planes de contingencia en `st.popover` (ROI alimentos <45%, cumplimiento <90%, mix bebidas <30%, churn Oro/VIP >45 días, salud del incentivo calif <3.5). **Simulador de escenarios de estrés**: sliders de alza de marisco (0-25%), caída de bebidas (0-10%) y caída de demanda (0-10%) — con datos base se activan 2 reglas (churn 58 clientes, 7/10 top meseros con bandera) y con shocks máximos las 5 (AppTest 2→3→4→5). Heatmaps de tensión por mes·sucursal (ROI/mix/cumplimiento). Revisión aplicada: encuestas cruzadas con tickets del periodo filtrado (R5 respeta filtros), colorscale monotónico en heatmaps, churn con NaN→9999 (consistente con M3), imports muertos eliminados |
| 1.7.0 | 2026-08-12 | **M6 Pronóstico e Inventario completado** (`models/forecast.py` + `app/modulos/m6_forecast.py`): GradientBoosting sobre serie **semanal** con features semana_del_año/año/sucursal en escala log1p, pronóstico 2-8 semanas con banda de confianza 80%. **Decisión documentada (backtest)**: la serie diaria daba MAPE ~52% (ruido diario) y la semanal ~20.6%, duplicando en precisión a la referencia ingenua de persistencia (~41.9%). Conversión a insumos: kg de marisco (Sopa Ancla 0.35 kg/porción) y cajas de cerveza (24 uds/caja) con ratios por sucursal; tabla de compra semanal e impacto de compra anticipada (ahorro del +15% por congelar precio). Revisión aplicada: códigos de sucursal fijos (cat.codes frágil), guarda de división por cero en MAPE, parámetro muerto y docstrings corregidos, peso muerto del caché eliminado |
| 1.8.0 | 2026-08-12 | **M7 Rotación de Mesas completado** (`app/modulos/m7_rotacion.py`): tiempo de ocupación medio 77 min (p10 49, p90 114) derivado de apertura→cierre de mesa; eficiencia de mesa $/min por mesero (rango 8.5-10.7, mediana 8.8) con scatter ticket vs tiempo y bandera de **secuestro potencial** (ticket alto + eficiencia baja); histograma por sucursal, tiempo por hora (las mesas rotan más rápido en pico: 75 vs 82 min), ticket/tiempo por día de semana y tabla de rendimiento. **Insight de negocio**: la eficiencia baja en horas pico es señal de servicio ágil, no de baja calidad. Revisión aplicada: hover del scatter con customdata (mostraba píxeles de marker.size), np.where redundante simplificado, pd.to_datetime duplicado eliminado (708k filas), parámetro `sucursales` usado para nombres de entidad |
| 1.9.0 | 2026-08-12 | **M8 Análisis de Deserción de Clientes completado** (`app/modulos/m8_churn.py`): churn rate de clientes Oro/VIP con **fecha de corte configurable** (auditable, default = última fecha del dataset 31-dic-2025 según decisión §6 M8) y umbral 30-120 días. Al corte por defecto: 58/162 Oro/VIP en riesgo (35.8%) = **$1.05M de valor anual en riesgo**; el corte y el umbral interactivos mueven el resultado (corte jun-2025 → 55/34.0%; umbral 90 → 46/28.4%). Componentes: KPIs (registrados, en riesgo, tasa, valor en riesgo), histograma de días sin visita con línea de umbral, evolución mensual del churn rate, barras por nivel (Plata/Oro/VIP) y tabla de reactivación (Sopa de Mariscos gratis + 2 bebidas de marketing). Revisión aplicada: guarda anti-NaN en fecha_alta→valor_anual, fillna en total/riesgo del reindex, etiqueta "999+" para clientes sin visita jamás registrada. Verificado: AppTest 0 errores (4 escenarios) + navegador en vivo (corte 58→55) |
| 1.10.0 | 2026-08-12 | **M9 Matriz de Elasticidad completado** (`app/modulos/m9_elasticidad.py`) con **mejora al generador** (`src/data_factory.py` v0.2.0): experimentos de precio por producto/mes (wobble AR1 mean-reverting ~±4%, promos/menús de temporada) y demanda que responde en la **frecuencia de pedido** (pesos de muestreo, evita cuantización) con coeficientes por regla de negocio (ancla -0.15, bebidas de marketing -0.30, cervezas -0.45, refrescos -0.55, ceviches -1.50, premium -0.60, temporada -1.00, familiar -0.80). Elasticidad estimada log-log **por subcategoría con efectos fijos de producto y mes** (pooling: a nivel producto el ruido mensual domina la señal — decisión documentada; demeaning secuencial exacto en panel balanceado). **Laboratorio**: correlación 0.989 simulada vs estimada (Ancla -0.07, Agua -0.19, Cerveza -0.31, Refresco -0.39, Principal -0.89, Variante -1.15). Módulo: scatter volumen vs precio de los 182 productos con clasificación semántica, KPIs (33 inelásticos / 41 elásticos, elasticidad media -0.58), simulador de re-precio (-10% a +15%: ingreso′ = ingreso×(1+Δp)^(1+e); +5% → +$2.5M) y **plan fijo** +5% inelásticos / -3% elásticos. Nueva validación **T11** (respuesta negativa al precio en todas las subcategorías + dispersión) → **CP2 36/36**. Nota: la regeneración subió el MAPE de M6 a 30.9% (ref. 45.2%, el modelo sigue ganando ~1.5×) por el ruido de los experimentos de precio. Revisión aplicada: import sin uso eliminado, plan fijo independiente del slider, color defensivo "Sin datos", KPI e_media con máscara |
| 1.16.0 | 2026-08-12 | **F7 Publicación completada — CP7 APROBADO**: repositorio público en GitHub (Imghara/el-errante-bi-dashboard-data-driven-restaurant-management-system, licencia MIT, commit `1aa6b93` con integración del commit inicial de GitHub) y **app desplegada en Streamlit Community Cloud**: https://bi-dashboard-data-driven-restaurant-management-system.streamlit.app/ — verificación en navegador de la app EN LÍNEA: M1 (KPIs + mapa geográfico), M3 (CRM), M9 (elasticidad) y pie de página correctos, sin errores de aplicación (404 benigno de favicon). README actualizado con la URL real de la demo |
| 1.15.0 | 2026-08-12 | **F7 Publicación — preparación completada**: `git init -b main` con identidad gluevanos/ghara@outlook.com; `README.md` de portafolio (3 pilares, 10 módulos, stack, inicio rápido, pruebas 41/41, documentación) con **3 capturas reales del dashboard** tomadas con Playwright (M1 Consolidado, M6 Pronóstico, M10 Auditoría) en `assets/` + script reproducible `scripts/capturas_dashboard.py` (espera el encabezado del módulo para evitar falsos positivos); commit inicial `c0d5dd4` (64 archivos, `data/` incluida — fact_ventas 82 MB —, repo comprimido 15 MB). Pendiente: crear repositorio `el-errante-bi` en GitHub y push; despliegue en Streamlit Community Cloud |
| 1.14.0 | 2026-08-12 | **Manual de usuario profesional en PDF (pre-F7)** (`MANUAL_DE_USUARIO.pdf`, 28 páginas) bajo **normas APA 7.ª** (Times 12, doble espacio, márgenes 1", portada, resumen, índice, figuras/tablas numeradas, referencias) y **una sola tinta** para impresión rápida. Nuevos scripts reproducibles: `scripts/figuras_vintage.py` — 16 figuras monocromas con estética de dibujo a mano (efecto boceto matplotlib + serif + tramas) calculadas con los datos reales del dashboard (KPIs, esquema en estrella, ventas mensuales, mapa de sucursales, leaderboard M2, ancla→bebidas, embudo, cumplimiento, mapa de tensión M5, pronóstico con banda, ocupación, churn, elasticidad, auditoría, niveles de cliente y encuestas) — y `scripts/generar_manual_pdf.py` — reportlab 5: portada APA (autor gluevanos, instructor Buffy/IA), resumen con palabras clave, índice con números de página, 6 tablas estilo APA, referencias APA 7 y apéndice A; número de página arriba a la derecha en todas las páginas y **leyenda vertical al margen izquierdo** con la identidad del proyecto. Dependencias adicionales solo para documentos: `reportlab`, `matplotlib`. **QA verificado**: 16/16 imágenes incrustadas · 0.0000% de píxeles de color (una sola tinta) · sin glifos rotos · 28 páginas |
| 1.13.0 | 2026-08-12 | **F6 QA Visual completada — CP6 APROBADO**: `tests/` con pytest (41 pruebas) — T1-T11 portadas de `validaciones.py`, unitarios de forecast (serie semanal, features, entrenamiento, insumos), utils e incentivos, y smoke E2E de los 10 módulos con AppTest (marcados `e2e`, skip limpio sin datos). **Bug corregido en M6**: la guarda de 90 días usaba `fecha_hora.nunique()` (timestamps por minuto) y nunca se disparaba → ahora cuenta días con `dt.normalize()`. Pulido UI/UX: guarda global de estado vacío en `app.py` + pie de página con estilo `.errante-footer`. **CP6 verificado**: pytest 41/41 · navegación 10/10 módulos en navegador con 0 errores de consola · footer presente |
| 1.12.0 | 2026-08-12 | **Manual de usuario creado (pre-F6)** (`MANUAL_DE_USUARIO.md`): guía completa del dashboard — elementos por módulo y su origen de datos, semántica de colores, clasificación de clientes (Plata 60%/Oro 30%/VIP 10%; frecuencia 1-2/2-4/4-8 visitas; canales restaurante/campaña/referencia), encuestas a meseros (momento: al cierre de la cuenta en tickets CRM ~40%; calificación 1-5 con comentario y sentimiento; uso en M10/M5), y las 9 preguntas de negocio del CRM con su ubicación en pantalla. Registrada en bitácora (sesión 14) |
| 1.11.0 | 2026-08-12 | **M10 Auditoría de Calidad del Programa de Incentivos completado — F5 TERMINADA (CP5)** (`app/modulos/m10_auditoria.py`): contrasta las **comisiones** (motor `_calc_incentivos` de M2 reutilizado, política 5%/1.5×) con la **calificación del servicio** de las encuestas ligadas a ticket (respeta filtros globales). Estados: ✅ Saludable (calif ≥ 3.5) · ⚠️ Vigilar (calif < 3.5) · 🚨 **Crítico** (calif < 3.5 Y comisión ≥ mediana = **venta impositiva**). Resultados: 60% de salud del incentivo, 19 meseros bajo el umbral, **6 críticos** con expanders de plan de acción (reducir multiplicador de bebidas, rotar mesas, coaching) — el caso Tamaulipas de la especificación (top en bebidas con quejas de "servicio impositivo") queda detectado (4/8 críticos en S3). Scatter comisión vs calificación con **zona roja** de riesgo, barras por sucursal, histograma de calificaciones, expediente completo de 48 meseros. Revisión aplicada: guarda `comision > 0` en estado crítico (evita mediana 0), guarda sin-encuestas (info + return), denominador de salud = meseros con encuestas, `PALETA_SUCURSAL` importada de M2 (sin duplicar). Verificado: AppTest 0 errores (base, solo S2/S3, rango corto) + navegador 4/4. **Con esto F5 (M6-M10) queda completa: CP5 APROBADO** |

---

*Documento generado y mantenido como fuente de verdad del proyecto "El Errante". Ante cualquier discrepancia con `El Errante.txt`, este documento prevalece y la discrepancia se registra en la bitácora.*
