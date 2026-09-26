# Contexto del proyecto

Este documento registra el estado técnico vigente de **Alcancías en Coclé**. Debe actualizarse cuando cambien la funcionalidad, la persistencia o la presentación de la aplicación.

## Producto

**Alcancías en Coclé – Gastos Hormiga: El Reto del Ahorro** es una aplicación educativa para actividades escolares y ferias. Muestra cómo pequeños gastos frecuentes pueden convertirse en ahorro e inversión a través del tiempo. Sus resultados son estimaciones educativas y no constituyen asesoramiento financiero.

## Tecnología y decisiones vigentes

| Área | Decisión |
| --- | --- |
| Lenguaje | Python 3.10 o superior |
| Interfaz | Streamlit |
| Gráficas | Plotly |
| Persistencia | JSON locales para historial (`historial_participantes.json`) y metas (`metas_personalizadas.json`) |
| Tema | Oscuro, nativo de Streamlit y complementado con CSS en `app.py` |
| Moneda | Balboa panameño (`B/.`) |
| Frecuencias | Diario, semanal y mensual |

No se usa un framework adicional ni JavaScript independiente. El CSS se inyecta con `aplicar_estilos()` y `.streamlit/config.toml` define el tema de componentes nativos que Streamlit dibuja internamente.

## Diseño visual actual

La interfaz usa una apariencia de videojuego educativo moderno:

- Portada “**Gastos Hormiga: El Reto del Ahorro**” con mascota 🐜💰 y animación suave.
- Fondo oscuro, paneles redondeados, sombras y detalles verde/turquesa.
- Tarjetas métricas estilo recompensa, botones grandes y encabezados de nivel/logro.
- Gráfica Plotly adaptada al tema: coral para gasto y verde/turquesa para ahorro.
- Diseño responsivo para computadora y celular.

### Elementos visuales que deben preservarse

- Fondo general, portada, tarjetas, botones, títulos, distribución y gráficas actuales.
- Selector **Frecuencia**, incluidas las opciones Diario, Semanal y Mensual.
- Sección **🎯 TU META · ¿Qué podrías lograr?**: selector de meta, costo estimado y mensaje de resultado.
- Tarjetas superiores del **🏅 SALÓN DE LOGROS · Historial y estadísticas**.

### Tablas nativas de Streamlit

Las tablas de proyección e historial usan `st.dataframe`. Su cuadrícula se dibuja internamente con un lienzo, por lo que no se deben aplicar estilos CSS directamente a `canvas`, `.dvn-stack` o `.dvn-scroller`: esas reglas pueden impedir que se visualice el contenido del grid.

El fondo oscuro, contraste, bordes y encabezados de las tablas se definen principalmente en `.streamlit/config.toml`:

```toml
[theme]
base = "dark"
primaryColor = "#35c98b"
backgroundColor = "#0b1220"
secondaryBackgroundColor = "#152238"
textColor = "#eaf2f7"
borderColor = "#29405d"
dataframeBorderColor = "#29405d"
dataframeHeaderBackgroundColor = "#1d3150"
```

Después de modificar `config.toml`, reinicia Streamlit.

## Funcionalidad implementada

- Ingreso, visualización y eliminación de gastos diarios, semanales o mensuales.
- Simulación inicial vacía y simulador rápido con B/. 0.50, 1.00, 2.00 y 5.00 diarios.
- Resumen de gasto diario, gasto mensual y ahorro proyectado a 5 y 10 años.
- Tabla de proyección a 1, 3, 5 y 10 años: aportado, intereses y total acumulado.
- Gráfica interactiva de gasto acumulado frente a ahorro potencial durante 10 años.
- Metas predefinidas y metas personalizadas persistentes, con plazo aproximado para alcanzarlas.
- Comparación de costo de oportunidad a cinco años.
- Registro explícito de participantes, historial persistente y estadísticas agregadas.

## Persistencia e historial

Al pulsar **“Guardar cálculo en el historial”**, se registra localmente en `historial_participantes.json`:

- Fecha y nombre o identificador.
- Cantidad y detalle de gastos.
- Tasa anual usada.
- Gasto mensual y anual.
- Ahorro potencial a 5 y 10 años.

No hay cuentas, autenticación ni almacenamiento remoto. Para actividades públicas se recomienda usar identificadores anónimos.

## Metas personalizadas

El selector de metas combina las sugeridas en `METAS` con las almacenadas en `metas_personalizadas.json`. Las metas predefinidas nunca se reemplazan ni eliminan.

Desde **“➕ Agregar nueva meta”** se puede guardar una meta con solo dos datos:

- Nombre de la meta.
- Costo en B/.

Cada registro personalizado se guarda como `{"nombre": "...", "costo": ...}`. El archivo se crea automáticamente si no existe; si está ausente, dañado o contiene registros inválidos, la aplicación continúa sin interrumpirse. No se permiten nombres vacíos, costos menores o iguales a cero ni nombres duplicados sin distinguir mayúsculas/minúsculas.

Al seleccionar una meta predefinida o personalizada, el campo de costo recupera su valor guardado. El tiempo se calcula con la función existente `meses_para_meta()`; no se añade una fórmula financiera nueva.

## Arquitectura

```text
.
├── app.py                         # Streamlit, cálculos, historial, CSS y gráfica Plotly
├── historial_participantes.json   # Registros locales de participantes
├── metas_personalizadas.json      # Nombre y costo de metas creadas manualmente
├── .streamlit/
│   └── config.toml                # Tema oscuro y tablas nativas
├── requirements.txt               # Dependencias
├── Context.md                     # Este documento
├── Ejecucion.md                   # Instrucciones de arranque
└── Prompt.md                      # Requerimientos originales
```

`app.py` conserva esta secuencia: configuración y persistencia; funciones de cálculo; estado de sesión; calculadora, resultados, tablas, gráfica, metas y simulador; finalmente registro, historial y estadísticas.

## Fórmulas

- Conversión mensual: diario × 365/12, semanal × 52/12 o mensual × 1.
- Aporte mensual: equivalente mensual de los gastos que se dejan de realizar.
- Valor futuro con aportes al final de cada mes:

```text
VF = aporte_mensual × (((1 + tasa_mensual)^meses - 1) / tasa_mensual)
```

- Con tasa de 0 %, el total es `aporte_mensual × meses`.
- Interés ganado = total acumulado − aportes realizados.

Las fórmulas, funciones, datos guardados y lógica existente no deben modificarse durante ajustes visuales.

## Validación y estado

- [x] Sintaxis de `app.py` validada con `python -m py_compile app.py`.
- [x] Arranque de Streamlit y respuesta HTTP local verificados.
- [x] Tema oscuro cargado desde `.streamlit/config.toml`.
- [x] Persistencia JSON e indicadores del historial conservados.
- [x] Metas personalizadas persistentes con validación de nombre, costo y duplicados.
- [x] Datos de proyección e historial confirmados antes de renderizar sus tablas.
- [ ] Realizar una revisión visual manual en computadora y celular antes de la actividad.
- [ ] Validar ejemplos, tasas y metas con el equipo responsable.

## Ejecución

Desde PowerShell, en la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Si el entorno virtual aún no existe:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

La aplicación queda disponible normalmente en `http://localhost:8501`.
