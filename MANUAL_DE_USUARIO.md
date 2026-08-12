# 📘 MANUAL DE USUARIO — DASHBOARD "EL ERRANTE" BI

> **Guía completa para operar el sistema**: qué muestra cada elemento, de dónde nace cada dato, cómo se clasifican los clientes, cuándo se recogen los comentarios sobre los meseros y qué preguntas de negocio responde el CRM.
>
> Proyecto: *El Errante — BI & Incentivos* (portafolio profesional)
> Documento complementario al [DOCUMENTO_MAESTRO.md](DOCUMENTO_MAESTRO.md) · Versión 1.0 · 12 de agosto de 2026

---

## 📑 Índice

1. [Empezar a usar el dashboard](#1-empezar-a-usar-el-dashboard)
2. [Filtros globales y semántica de colores](#2-filtros-globales-y-semántica-de-colores)
3. [Glosario de conceptos y fórmulas](#3-glosario-de-conceptos-y-fórmulas)
4. [De dónde nace cada dato (modelo de datos)](#4-de-dónde-nace-cada-dato-modelo-de-datos)
5. [Los 10 módulos, paso a paso](#5-los-10-módulos-paso-a-paso)
6. [Clasificación de clientes: Plata, Oro y VIP](#6-clasificación-de-clientes-plata-oro-y-vip)
7. [Encuestas y comentarios sobre los meseros](#7-encuestas-y-comentarios-sobre-los-meseros)
8. [Las preguntas de negocio que responde el CRM](#8-las-preguntas-de-negocio-que-responde-el-crm)
9. [Preguntas frecuentes](#9-preguntas-frecuentes)
10. [Nota técnica: los datos son una simulación](#10-nota-técnica-los-datos-son-una-simulación)

---

## 1. Empezar a usar el dashboard

### 1.1 Qué es este sistema

**El Errante BI** es el copiloto del Gerente General de un restaurante de mariscos con 3 sucursales en el noreste de México (Nuevo León, Coahuila y Tamaulipas). No es un tablero de ventas estático: es un **entorno de prescripción estratégica** que combina analítica descriptiva (qué pasó), predictiva (qué viene) y prescriptiva (qué hacer: planes de contingencia, incentivos, precios).

Opera con **48 meseros**, un menú de **182 productos** y un programa de lealtad de **~400 clientes**, sobre un histórico de **2 años (2024–2025)** con más de 700 mil líneas de venta.

### 1.2 Cómo ejecutarlo

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run app/app.py
```

Se abre en el navegador en `http://localhost:8501`. (El despliegue en Streamlit Community Cloud usa el mismo archivo `app/app.py`.)

### 1.3 Estructura de navegación

Todo se maneja desde la **barra lateral izquierda**:

| Bloque | Contenido |
|---|---|
| **🧭 Módulos** | Selector de las 10 pestañas del sistema (M1–M10) |
| **⚙️ Filtros globales** | Rango de fechas y sucursales — **afectan a todos los módulos** |

Regla de oro de uso: **primero fija el periodo y las sucursales que quieres analizar, y después navega entre módulos**. Todos los gráficos y KPIs se recalculan automáticamente al mover cualquier filtro.

---

## 2. Filtros globales y semántica de colores

### 2.1 Filtros globales

| Filtro | Qué hace | Detalle |
|---|---|---|
| **Rango de fechas** | Recorta el análisis al periodo seleccionado | El rango máximo es 01-ene-2024 → 31-dic-2025. Los KPIs comparan contra el periodo anterior de igual duración (delta). |
| **Sucursales** | Activa/desactiva sucursales (S1 · S2 · S3) | Muestra "S1 · Nuevo León", "S2 · Coahuila", "S3 · Tamaulipas". Debe quedar al menos una activa. |

> 💡 **Tip**: para ver la foto completa del negocio, deja el rango completo y las 3 sucursales. Para investigar un problema puntual (p. ej. la cuesta de enero), recorta al rango del problema.

### 2.2 Semántica de colores (consistente en TODA la app)

| Estado | Color | Significado | Ejemplo |
|---|---|---|---|
| ✅ **Saludable** | Turquesa `#1BA39C` | KPI cumple la meta, sin riesgo | ROI ≥ 45%, cumplimiento ≥ 100% |
| ⚠️ **Vigilar** | Ámbar `#F5A623` | Cerca del umbral, requiere atención | Cumplimiento 90–95%, calificación < 3.5 |
| 🚨 **Crítico** | Coral `#E74C3C` | Umbral cruzado, requiere acción inmediata | ROI < 45%, cumplimiento < 90%, churn activo |

---

## 3. Glosario de conceptos y fórmulas

| Concepto | Definición | Fórmula | Umbral de alerta |
|---|---|---|---|
| **ROI promedio** | Margen de ganancia sobre el costo de elaboración | `(Precio_Venta − Costo_Elaboración) / Costo_Elaboración` | < 45% (alimentos) 🚨 |
| **Ticket promedio** | Gasto promedio por mesa/ticket | `Ventas / Nº de tickets` | — |
| **Mix de bebidas** | Participación de bebidas en el ticket | `Ingresos_Bebidas / Ticket_Total` | < 30% 🚨 |
| **% Cumplimiento** | Qué tanto se cumplió la meta de ventas | `Ventas_Reales / Meta_Ventas` | < 90% 🚨 |
| **ROI de la línea** | Margen de cada línea de detalle | `(Precio_aplicado − Costo_del_mes) / Costo_del_mes` | — |
| **Comisión** | Incentivo al mesero por línea vendida | `Utilidad × tasa × multiplicador` | — |
| **Elasticidad precio** | Qué tan sensible es la demanda al precio | `Δ%Volumen / Δ%Precio` (log-log) | \|e\| > 1.0 = elástico |
| **Churn / deserción** | Cliente de alto valor que deja de visitar | Días desde su última visita | > 45 días (Oro/VIP) 🚨 |
| **Tiempo de ocupación** | Minutos que una mesa permanece ocupada | `Hora_cierre − Hora_apertura` | — |
| **Eficiencia de mesa** | Ingreso generado por minuto de mesa | `Ticket / Tiempo de ocupación` | — |
| **MAPE** | Error del pronóstico (menor = mejor) | `media(\|Real − Predicción\| / Real)` | contexto vs referencia ingenua |
| **Salud del incentivo** | Comisiones vs calidad de servicio | Calificación media por mesero | < 3.5 ⚠️ / + comisión alta 🚨 |

---

## 4. De dónde nace cada dato (modelo de datos)

El sistema usa un **esquema en estrella**: una gran tabla de hechos (`fact_ventas`) rodeada de dimensiones. Todo lo que ves en el dashboard se calcula a partir de estos 8 archivos:

| Archivo | Qué contiene | Se usa en… |
|---|---|---|
| `dim_sucursales.csv` | Las 3 sucursales: nombre, ciudad, entidad, nº de meseros, lat/lon | Mapa geográfico (M1), filtro de sucursales |
| `dim_meseros.csv` | Los 48 meseros: nombre, sucursal, fecha de ingreso | Leaderboards (M2), rotación (M7), auditoría (M10) |
| `dim_productos.csv` | Los 182 productos: categoría, subcategoría, precio, costo base, **es_ancla**, **es_incentivable** | Todo el cálculo de ROI, incentivos y elasticidad |
| `dim_clientes_crm.csv` | ~400 clientes del programa de lealtad: **nivel**, frecuencia, sucursal, canal de alta, fecha de salida | CRM (M3), churn (M8), alertas (M5) |
| `fact_ventas.csv` | ~700k líneas de tickets: fecha, sucursal, mesero, producto, cantidad, precio aplicado, **apertura/cierre de mesa**, cliente CRM | La base de todos los módulos |
| `fact_costos_mensuales.csv` | Costo de elaboración por producto y mes (fluctúa **±15%**) | ROI dinámico (M1) y comisiones (M2) |
| `fact_presupuesto.csv` | Meta de ventas mensual por sucursal (ligeramente optimista) | Cumplimiento (M4), alertas (M5) |
| `fact_encuestas_satisfaccion.csv` | Encuestas ligadas a ticket: calificación 1–5, comentario, sentimiento | Auditoría (M10), alertas (M5) |

**Flujo de datos dentro de la app:**

```
fact_ventas ─┬─ merge fact_costos_mensuales (por producto+mes) → ROI por línea
             ├─ groupby mes_ano × sucursal → reales vs presupuesto → % Cumplimiento
             └─ apertura/cierre de mesa → tiempo de ocupación → rotación (M7)
dim_clientes_crm + fact_ventas (40% de tickets) → última visita → churn (M3/M5/M8)
fact_encuestas + fact_ventas (por id_ticket) → calificación del mesero (M5/M10)
fact_ventas semanal → modelo GradientBoosting → pronóstico e insumos (M6)
fact_ventas + dim_productos (precio×volumen mensual) → elasticidad log-log (M9)
```

---

## 5. Los 10 módulos, paso a paso

> Para cada módulo: **pregunta de negocio** → **elementos en pantalla** → **cómo leerlos**.

---

### M1 · Consolidado Financiero y ROI

**Pregunta:** ¿Cómo va el negocio en general? ¿Dónde ganamos y dónde perdemos?

**Elementos:**

| Elemento | Qué muestra | Cómo leerlo |
|---|---|---|
| **4 KPIs** (Ventas, Ticket prom., ROI, Mix bebidas) | Resumen del periodo con delta vs periodo anterior | El ROI y el mix en rojo = umbral cruzado |
| **🗺️ Mapa geográfico** | 3 burbujas con tamaño = ventas del periodo | S1 (Monterrey) es la burbuja mayor |
| **📊 Resumen por sucursal** | Tabla con ventas, tickets, ticket prom., ROI, mix | Detecta sucursal más rentable vs más grande |
| **📈 Evolución diaria** | Serie de ventas diarias con zoom y selector de rango | Busca los valles (ene/feb, sep/oct) y picos (mar/abr Cuaresma, may, dic) |
| **🎯 Cumplimiento presupuesto** | Barras mensuales real/meta por sucursal | Línea punteada = umbral de alerta 90% |
| **💎 ROI mensual — Alimentos** | ROI de platillos/mariscos por mes, barras verdes/rojas | Barras rojas = meses donde se dispara la alerta M5 |

**Origen:** `fact_ventas` + `fact_costos_mensuales` (ROI) + `fact_presupuesto` (cumplimiento) + `dim_sucursales` (mapa).

**Lectura rápida de ejemplo:** "En Cuaresma (mar–abr) el ROI de alimentos se mantiene verde, pero en la cuesta de enero el cumplimiento cae a ~92% y el mix de bebidas baja — señal para activar campañas de bebidas."

---

### M2 · Programa de Incentivos

**Pregunta:** ¿Cuánto cuesta motivar a los meseros y quién rinde más?

**Elementos:**

| Elemento | Qué hace | Detalle |
|---|---|---|
| **🎚️ Slider "Comisión"** (0–15%) | % del margen que recibe el mesero | Default 5%. Todo el módulo se recalcula al moverlo |
| **🎚️ Slider "Multiplicador alto ROI"** (1.0–3.0×) | Refuerza incentivo en bebidas y variantes con ROI > 100% | Default 1.5× |
| **4 KPIs** | Comisiones del periodo, % utilidad a incentivos, mesero #1, proyección de ingreso extra | La proyección estima cuánto gana la sucursal estimulando venta de alto ROI |
| **🏆 Leaderboard** | Ranking de los 48 meseros por comisión (filtrado por sucursal) | **Excluye la Sopa de Mariscos (ancla)** por diseño |
| **🥤 Rankings especiales** | Top 5 en bebidas vistosas y platillos de temporada | Identifica a los "vendedores de margen" |

**Regla del negocio (importante):** la **Sopa de Mariscos no genera incentivos** (`es_incentivable = False`). El ancla atrae tráfico; el incentivo debe empujar bebidas y variantes de alto ROI, que son el motor del margen.

**Origen:** `fact_ventas` + `dim_productos` (subcategorías, etiquetas) + `fact_costos_mensuales` (utilidad real por línea) + `dim_meseros`.

**Probar en vivo:** sube la comisión de 5% → 10% y observa que las comisiones del leaderboard se duplican y la proyección de ingreso extra cambia.

---

### M3 · CRM & Marketing

**Pregunta:** ¿Qué tan saludable está nuestra base de clientes? ¿El ancla realmente arrastra venta de bebidas?

**Elementos:**

| Elemento | Qué muestra | Cómo leerlo |
|---|---|---|
| **4 KPIs** | Registrados, activos en el periodo, Oro/VIP en riesgo, tasa de deserción | El 3º y 4º se pintan en rojo si hay riesgo |
| **🔄 Embudo** | Registrados → Activos → Oro/VIP activos | Ver cuánto se "pierde" en cada paso |
| **📊 Barras por sucursal y nivel** | Clientes activos del programa por sucursal | S1 concentra más clientes (mayor plaza) |
| **🍤🍹 Correlación ancla→bebidas** | Variedades de bebida por mesa con/sin Sopa | Con ancla ≈ 2.95 variedades vs 1.54 sin ancla |
| **🚨 Tabla de churn** | Oro/VIP sin visita en 45 días + plan de reactivación | "Sopa gratis con 2 bebidas de marketing" |

**Origen:** `dim_clientes_crm` (padrón y niveles) + `fact_ventas` (visitas y consumo) + `dim_productos` (ancla/bebidas).

**Las conclusiones del CRM se obtienen cruzando estas preguntas** (ver sección 8).

---

### M4 · Presupuesto de Ventas vs Real

**Pregunta:** ¿Estamos cumpliendo la meta financiera de cada sucursal?

**Elementos:**

| Elemento | Qué muestra | Cómo leerlo |
|---|---|---|
| **4 KPIs** | Ventas reales, cumplimiento global, meses bajo meta, mejor mes | "Meses bajo meta" es el KPI más honesto del módulo |
| **🎯 Gauges** | Un medidor por sucursal (periodo acumulado) | Aguja en zona roja (<90%) = alerta M5 |
| **📊 Barras real vs meta** | Mensual por sucursal | Puntos punteados = meta; barras = real |
| **📈 Serie de cumplimiento** | % mensual con banda de vigilancia (90–95%) | Cae en la banda ámbar en ene/feb/sep/oct |
| **📋 Detalle mensual** | Tabla con estado semántico ✅/⚠️/🚨 | Filtra para ver qué mes/sucursal dispara |

**Regla de generación (por qué ves lo que ves):** los reales quedan **5–10% abajo** de la meta en Ene, Feb, Sep y Oct (meses bajos) y **12% arriba** en Cuaresma. Por eso los meses de incumplimiento son un comportamiento esperado y **no un error** — son el escenario que la gerencia debe gestionar.

**Origen:** `fact_presupuesto` (metas) + `fact_ventas` (reales).

---

### M5 · Centro de Alertas (Sistema Experto)

**Pregunta:** ¿Qué está mal AHORA y qué hacemos al respecto?

**Elementos:**

| Elemento | Qué hace |
|---|---|
| **🧪 Simulador de estrés** | 3 sliders: alza de marisco (0–25%), caída de bebidas (0–10%), caída de demanda (0–10%). Verás **cuándo se cruzaría cada umbral** y qué plan se activa |
| **4 KPIs** | Alertas activas, en vigilancia, reglas sanas, clientes en riesgo |
| **🧠 Tarjetas de reglas** | Las 5 reglas con su estado y "peor valor" |
| **🚨 Plan de contingencia** | Botón emergente con el plan de acción por regla |
| **🗺️ Mapas de tensión** | Heatmaps mes×sucursal de ROI, mix y cumplimiento |
| **👥 Tabla de churn** | Oro/VIP en riesgo con su plan de reactivación |

**Las 5 reglas del sistema experto:**

| Regla | Se activa cuando… | Plan de contingencia |
|---|---|---|
| 🔥 **ROI en Peligro** | ROI alimentos del mes < 45% | Incentivo al 8% en Aguas y Cervezas Artesanales; ajustar porciones sin tocar el ancla |
| 📉 **Caída de Meta** | Cumplimiento mensual < 90% | Cupones de bebidas vistosas a VIP/Oro; concurso "Mesero Estrella" |
| 🥤 **Mix Bebidas** | Mix de bebidas < 30% del ticket | Ofrecer "Bebida de Temporada" antes de la Sopa; neuromarketing visual |
| 👥 **Deserción** | Oro/VIP sin compra en 45 días | Sopa de Mariscos gratis + 2 bebidas de marketing |
| ⚠️ **Salud del Incentivo** | Top meseros en bebidas con calificación < 3.5 | Bandera amarilla: supervisar venta impositiva |

**Demo para entrevista:** con datos base se activan 2 reglas (churn + salud). Sube el alza de marisco a 25%, la caída de bebidas a 10% y la demanda a 10% → se activan las 5.

---

### M6 · Pronóstico de Ventas e Inventario

**Pregunta:** ¿Cuánto marisco y cerveza compro para las próximas semanas?

**Elementos:**

| Elemento | Qué muestra | Detalle |
|---|---|---|
| **🎚️ Horizonte** | 2–8 semanas (default 4) | El modelo entrena con el histórico hasta la última semana del filtro |
| **4 KPIs** | Ventas proyectadas, kg de marisco, cajas de cerveza, MAPE | MAPE ≈ 30.9% vs referencia ingenua 45.2% (el modelo gana ~1.5×) |
| **📈 Gráfico histórico + pronóstico** | Serie semanal por sucursal con banda de confianza 80% | Zona sombreada = rango probable |
| **🛒 Compra recomendada** | Tabla semanal: ventas, sopas, kg, cerveza, cajas | Conversión: Sopa ≈ **0.35 kg** de marisco; cerveza **24 uds/caja** |
| **⚓ Compra anticipada** | Costo de compra hoy vs ahorro si sube +15% | Precio mayorista $240/kg; congelar precio protege el ROI |

**Origen:** `fact_ventas` agregado por semana + modelo `models/forecast.py` (GradientBoosting con semana del año, año y sucursal).

**Uso real:** comprar anticipado en Tamaulipas (cerca del proveedor) antes de la subida estacional del marisco **evita disparar la alerta ROI del M5**.

---

### M7 · Rotación de Mesas y Eficiencia del Servicio

**Pregunta:** ¿Cuánto tiempo se queda cada mesa y quién la aprovecha bien?

**Elementos:**

| Elemento | Qué muestra | Lectura |
|---|---|---|
| **4 KPIs** | Tiempo de ocupación (≈77 min), ticket prom., eficiencia $/min, rotación estimada | p90 ≈ 114 min |
| **🎯 Scatter eficiencia** | Cada punto = mesero (ticket vs tiempo, color = $/min) | Arriba-izquierda = eficiente; arriba-derecha con $/min bajo = ⚠️ **secuestro potencial** |
| **📊 Histograma** | Distribución del tiempo por sucursal | Comparar curvas S1/S2/S3 |
| **🕐 Por hora del día** | Tiempo medio por hora (picos 13–15 y 20–22 sombreados) | Las mesas rotan más rápido en pico (75 vs 82 min) |
| **📅 Por día de semana** | Ticket y tiempo por día | Fin de semana = ticket mayor |
| **📋 Rendimiento por mesero** | Tabla con bandera ✅/⚠️ | "Secuestro potencial" = ticket alto + eficiencia baja |

**Origen:** columnas `hora_apertura_mesa` / `hora_cierre_mesa` de `fact_ventas` + `dim_meseros`.

**Insight de negocio:** la eficiencia baja en horas pico es **señal de servicio ágil**, no de baja calidad.

---

### M8 · Análisis de Deserción de Clientes (Churn)

**Pregunta:** ¿A qué clientes valiosos estamos perdiendo y cuánto dinero nos cuesta?

**Elementos:**

| Elemento | Qué hace | Detalle |
|---|---|---|
| **📅 Fecha de corte** | Configurable (default: 31-dic-2025) | **Auditable**: el parámetro se expone para reproducibilidad |
| **🎚️ Umbral de churn** | 30–120 días (default 45) | Al moverlo cambia todo el análisis |
| **4 KPIs** | Registrados, Oro/VIP en riesgo, tasa, **valor anual en riesgo** | Default: 58 Oro/VIP = 35.8% = **$1.05M en riesgo** |
| **📊 Histograma** | Días sin visita con línea del umbral | Clientes sin visita jamás registrada = "999+" |
| **📈 Evolución mensual** | Churn rate a lo largo del tiempo | Detecta cuándo empezó a subir el riesgo |
| **📊 Barras por nivel** | Total vs en riesgo por Plata/Oro/VIP | El riesgo se mide en Oro/VIP |
| **👥 Tabla de reactivación** | Clientes en riesgo por valor anual + plan | Sopa gratis + 2 bebidas de marketing |

**Contexto de negocio:** cuesta **5× más** atraer un cliente nuevo en Coahuila que retener a un VIP en Nuevo León.

---

### M9 · Matriz de Elasticidad de Precios

**Pregunta:** ¿A qué productos les subo el precio sin perder clientes?

**Elementos:**

| Elemento | Qué muestra | Lectura |
|---|---|---|
| **4 KPIs** | Productos analizados (182), elasticidad media, inelásticos (33), elásticos (41) | Media ≈ −0.58 |
| **📈 Scatter log-log** | Volumen mensual vs precio por producto, color = clasificación, estrella = ancla | Los inelásticos toleran subir precio |
| **📊 Elasticidad por subcategoría** | Barras ordenadas (de más elástica a más inelástica) | Ceviches ≈ −1.5 (¡no tocar!); ancla ≈ −0.07; bebidas ≈ −0.2 a −0.4 |
| **🎚️ Simulador de re-precio** | −10% a +15% en todo el menú | `Ingreso′ = Ingreso × (1+Δp)^(1+e)` |
| **📋 Plan de precios sugerido** | Fijo e independiente del slider: **+5% a inelásticos / −3% a elásticos** | Impacto total en $ |

**Cómo se estima:** regresión log-log **por subcategoría con efectos fijos de producto y mes** (elimina tamaño del producto, estacionalidad e inflación). Usa los experimentos de precio del histórico (promos y menús de temporada ≈ ±4% mensual) como señal.

**Clasificación:** **Inelástico** \|e\| < 0.5 (subir sin perder demanda) · **Intermedio** 0.5–1.0 · **Elástico** \|e\| > 1.0 (una subida desploma el volumen).

---

### M10 · Auditoría de Incentivos (Anti-fraude)

**Pregunta:** ¿El mesero que más comisiones gana lo hace con buen servicio o presionando al cliente?

**Elementos:**

| Elemento | Qué muestra | Lectura |
|---|---|---|
| **4 KPIs** | Meseros auditados, salud del incentivo (≈60%), en vigilancia, comentarios negativos | 19 meseros bajo el umbral; **6 críticos** |
| **📈 Scatter comisión vs calificación** | Cada punto = mesero; **zona roja** = venta impositiva | Cuadrante: comisión alta + calificación < 3.5 |
| **📊 Barras por sucursal** | Calificación media y % de meseros en riesgo | El caso Tamaulipas (4/8 críticos en S3) queda detectado |
| **📊 Histograma** | Distribución de calificaciones con línea en 3.5 | — |
| **🚨 Banderas críticas** | Expansores con el plan de acción por mesero | Reducir multiplicador, rotar mesas, coaching |
| **📋 Expediente de 48 meseros** | Tabla completa: comisión, mix, calif., encuestas, % negativos, comentario, estado | Filtrable y exportable |

**Cómo se define el estado:**

| Estado | Condición |
|---|---|
| ✅ Saludable | Calificación ≥ 3.5 |
| ⚠️ Vigilar | Calificación < 3.5 |
| 🚨 **Crítico (venta impositiva)** | Calificación < 3.5 **Y** comisión ≥ mediana (con comisión > 0) |

**Origen:** motor de comisiones de M2 (política 5% / 1.5×, sin el ancla) + `fact_encuestas_satisfaccion` cruzadas con los tickets del periodo.

---

## 6. Clasificación de clientes: Plata, Oro y VIP

### 6.1 Cómo se determina el nivel

El programa de lealtad asigna el nivel con la siguiente distribución (los datos históricos reflejan exactamente estos porcentajes):

| Nivel | Proporción | Clientes (sobre 400) | Frecuencia esperada de visita |
|---|---|---|---|
| 🥈 **Plata** | 60% | ~240 | 1–2 visitas/mes |
| 🥇 **Oro** | 30% | ~120 | 2–4 visitas/mes |
| 💎 **VIP** | 10% | ~40 | 4–8 visitas/mes |

El nivel define la **frecuencia de visita esperada** (`frecuencia_visitas_mensual`): cuanto más alto el nivel, más consumo esperado y más caro es perderlo.

### 6.2 Qué más se registra de cada cliente

| Campo | Significado |
|---|---|
| `sucursal_frecuente` | La sucursal donde el cliente concentra sus visitas (S1/S2/S3) |
| `fecha_alta` | Cuándo se registró en el programa |
| `canal_alta` | Cómo llegó: **restaurante** (60%), **campaña** (25%) o **referencia** (15%) |
| `fecha_salida` | Fecha de su última visita antes de "abandonar" (solo clientes con deserción simulada; vacío = activo) |

### 6.3 Cómo la usa el dashboard

- **El embudo (M3)** muestra cuántos registrados están activos y cuántos de alto valor siguen activos.
- **El churn (M3, M5, M8)** se calcula **solo sobre Oro y VIP**: un cliente de alto valor sin compra en **más de 45 días** entra en "Riesgo de Deserción". Los de nivel Plata no activan la alerta (su pérdida es menos costosa).
- **El valor anual en riesgo (M8)** estima el gasto anualizado de los clientes en riesgo: gasto total ÷ años desde el alta.

> ⚠️ **Nota de transparencia:** la deserción es **simulada por nivel** con probabilidades Plata 12% / Oro 28% / VIP 38%. Es el mecanismo que crea el escenario realista de churn que ves en el dashboard.

---

## 7. Encuestas y comentarios sobre los meseros

### 7.1 Qué se pregunta

La encuesta de satisfacción registra **3 datos** por mesa atendida:

1. **Calificación del servicio** (1–5)
2. **Comentario** (texto breve, categorizado)
3. **Sentimiento** derivado (positivo / neutro / negativo)

### 7.2 En qué momento de la interacción se realizan

> 🕐 **La encuesta se aplica al cierre de la experiencia**, cuando el cliente registrado en el programa de lealtad paga su cuenta.

El diseño es el siguiente:

- La encuesta **se liga al ticket** (`id_ticket`), y del ticket se conoce **qué mesero** atendió (`id_mesero`) y **qué sucursal**.
- Solo se levantan encuestas sobre tickets de **clientes del programa CRM (~40% de los tickets)** — es la forma de saber a quién preguntar.
- Por eso el momento es **posterior a la cuenta**: el cliente ya vivió toda la interacción (toma de orden, servicio, bebidas, pago) y puede calificar la experiencia completa del mesero.

### 7.3 Cómo se interpretan los comentarios

| Calificación | Comentario canónico | Sentimiento |
|---|---|---|
| 1 | "Servicio impositivo, me presionaron para pedir más" | 🔴 Negativo |
| 2 | "La atención no fue agradable" | 🔴 Negativo |
| 3 | "Servicio regular" | 🟡 Neutro |
| 4 | "Buen servicio, todo rico" | 🟢 Positivo |
| 5 | "Excelente atención, volveré" | 🟢 Positivo |

### 7.4 Dónde se ven y cómo se usan

| Módulo | Uso de las encuestas |
|---|---|
| **M10 · Auditoría** | Contraste comisiones vs calificación. Comentario negativo más frecuente por mesero, % negativos, y **venta impositiva** (calificación < 3.5 + comisión ≥ mediana). La crítica del cliente se muestra textualmente en el expediente. |
| **M5 · Alerta R5** | Si un mesero top en venta de bebidas tiene calificación < 3.5 → bandera amarilla "crecimiento no sano" |
| **M1/M3** | La distribución de calificaciones explica la salud del servicio por sucursal |

> 💡 **Cómo leer una bandera crítica (M10):** si un mesero cobra comisiones por encima de la mediana pero sus mesas reportan "Servicio impositivo, me presionaron para pedir más", el sistema lo marca 🚨 y sugiere: reducir el multiplicador de bebidas para ese mesero, rotar sus mesas y coaching 1:1 de servicio. Esto es **crecimiento NO sano**: la comisión crece a costa de la experiencia del cliente.

---

## 8. Las preguntas de negocio que responde el CRM

Estas son las preguntas que el módulo CRM (y sus extensiones M5/M8) responde, y **dónde encontrar la respuesta**:

| # | Pregunta de negocio | Dónde verla |
|---|---|---|
| 1 | ¿Cuántos clientes tiene el programa de lealtad? | M3 KPI "Clientes registrados" |
| 2 | ¿Cuántos están realmente activos en el periodo? | M3 KPI "Activos en el periodo" + embudo |
| 3 | ¿Qué nivel predomina y en qué sucursal? | M3 "Clientes activos por sucursal y nivel" |
| 4 | ¿La Sopa Ancla arrastra venta de bebidas? | M3 correlación ancla→bebidas (≈2.95 vs 1.54 variedades) |
| 5 | ¿Qué clientes de alto valor estamos perdiendo? | M3/M8: Oro/VIP sin visita en 45 días (58 clientes = 35.8%) |
| 6 | ¿Cuánto dinero está en riesgo si no los retenemos? | M8 KPI "Valor anual en riesgo" ($1.05M) |
| 7 | ¿El riesgo crece o decrece con el tiempo? | M8 "Evolución mensual del churn rate" |
| 8 | ¿Los meseros top venden bien o venden por presión? | M10 scatter comisión vs calificación + banderas críticas |
| 9 | ¿Qué opinan los clientes del servicio, literalmente? | M10 expediente: comentario negativo más frecuente por mesero |

---

## 9. Preguntas frecuentes

**¿Por qué el delta de un KPI aparece vacío?**
El delta compara contra el periodo anterior de igual duración. Si el rango anterior cae antes del inicio de los datos (01-ene-2024), no hay comparativo — es comportamiento esperado.

**¿Por qué M6 no me deja pronosticar?**
Necesita al menos 90 días de histórico dentro del filtro. Amplía el rango de fechas.

**¿Por qué M9 pide más meses?**
La elasticidad necesita mínimo 6 meses con variación de precio. Con menos meses el modelo no tiene señal.

**¿Por qué M10 dice "Sin encuestas"?**
Solo se auditan meseros con encuestas ligadas a tickets del periodo filtrado. Si recortaste mucho el rango, amplíalo. Recuerda que las encuestas existen solo en ~40% de los tickets (los del programa CRM).

**¿Qué significa "999+" en días sin visita?**
Cliente del padrón sin ninguna visita registrada en el periodo: se considera en máximo abandono (en riesgo).

**¿Por qué la Sopa de Mariscos no aparece en los incentivos?**
Es el producto **ancla**: atrae tráfico familiar pero no genera incentivos por diseño (`es_incentivable = False`). Es la regla de negocio del proyecto.

**¿Cómo puedo volver a los valores por defecto?**
Recarga la página (`R` en el navegador) o usa el ícono de recarga de Streamlit arriba a la derecha.

---

## 10. Nota técnica: los datos son una simulación

- Los 8 CSV son **datos sintéticos generados con Python** (`src/data_factory.py`) con semilla fija **`SEED = 42`**: el mismo script siempre produce los mismos datos (reproducibilidad total).
- El histórico simulado es **2024–2025**. Las reglas del negocio están "cocinadas" dentro del generador: crecimiento 1.5× del año 2 (irregular), estacionalidad (Cuaresma +40%, cuesta de enero −20%), costos de marisco ±15%, presupuesto optimista, correlación ancla→bebidas, elasticidad por subcategoría y deserción simulada por nivel.
- **Para regenerar los datos** (no recomendado a menos que quieras una nueva semilla):
  ```bash
  python src/data_factory.py      # regenera los 8 CSV
  python src/validaciones.py      # ejecuta el QA de negocio (36/36 pruebas)
  ```
- **Para este manual es útil saberlo:** lo que ves en pantalla es el resultado *intencional* de esas reglas — por eso los meses de incumplimiento, los 6 meseros críticos de M10 o los 58 clientes en riesgo de churn son "detectables": el sistema fue diseñado para que el análisis tenga historia que contar.

---

*Documento complementario del proyecto "El Errante". Para el detalle técnico (checkpoints, decisiones documentadas y bitácora), consulta el DOCUMENTO_MAESTRO.md.*
