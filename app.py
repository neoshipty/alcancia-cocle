"""Aplicación educativa que transforma gastos hormiga en proyecciones de ahorro."""

# Permite usar anotaciones de tipos modernas en Python 3.10.
from __future__ import annotations

# Importa Any para describir diccionarios con valores de distintos tipos.
from typing import Any
# Importa utilidades estándar para conservar el historial entre ejecuciones.
from datetime import datetime
import json
from pathlib import Path

# Importa Plotly para crear el gráfico interactivo.
import plotly.graph_objects as go
# Importa Streamlit con el nombre corto st para construir la interfaz web.
import streamlit as st


# Configura el título de la pestaña, el icono y el ancho de la página web.
st.set_page_config(page_title="Alcancías en Coclé", layout="wide")

# Archivo local sencillo: se crea junto a la aplicación y no depende de servicios externos.
ARCHIVO_HISTORIAL = Path(__file__).with_name("historial_participantes.json")
ARCHIVO_METAS_PERSONALIZADAS = Path(__file__).with_name("metas_personalizadas.json")


def cargar_historial() -> list[dict[str, Any]]:
    """Lee el historial local; si no existe o está dañado, devuelve una lista vacía."""
    if not ARCHIVO_HISTORIAL.exists():
        return []
    try:
        with ARCHIVO_HISTORIAL.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos if isinstance(datos, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def guardar_historial(historial: list[dict[str, Any]]) -> None:
    """Guarda de forma legible los registros de participantes en un archivo JSON."""
    with ARCHIVO_HISTORIAL.open("w", encoding="utf-8") as archivo:
        json.dump(historial, archivo, ensure_ascii=False, indent=2)


def cargar_metas_personalizadas() -> list[dict[str, Any]]:
    """Lee las metas personalizadas válidas y crea su archivo local si hace falta."""
    if not ARCHIVO_METAS_PERSONALIZADAS.exists():
        guardar_metas_personalizadas([])
        return []
    try:
        with ARCHIVO_METAS_PERSONALIZADAS.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(datos, list):
        return []
    metas_validas = []
    for meta in datos:
        if not isinstance(meta, dict):
            continue
        nombre = str(meta.get("nombre", "")).strip()
        try:
            costo = float(meta.get("costo", 0))
        except (TypeError, ValueError):
            continue
        if nombre and costo > 0:
            metas_validas.append({"nombre": nombre, "costo": costo})
    return metas_validas


def guardar_metas_personalizadas(metas: list[dict[str, Any]]) -> None:
    """Guarda las metas creadas manualmente en un archivo JSON independiente."""
    with ARCHIVO_METAS_PERSONALIZADAS.open("w", encoding="utf-8") as archivo:
        json.dump(metas, archivo, ensure_ascii=False, indent=2)


def registrar_calculo(nombre: str, gastos: list[dict[str, Any]], tasa: float, gasto_mensual_total: float, ahorro_5: float, ahorro_10: float) -> None:
    """Añade al historial los datos principales de la simulación actual."""
    historial = cargar_historial()
    historial.append({
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "participante": nombre.strip() or "Participante sin nombre",
        "cantidad_gastos": len(gastos),
        "gastos": gastos,
        "tasa_anual": tasa,
        "gasto_mensual": gasto_mensual_total,
        "gasto_anual": gasto_mensual_total * MESES_POR_ANIO,
        "ahorro_potencial_5_anios": ahorro_5,
        "ahorro_potencial_10_anios": ahorro_10,
    })
    guardar_historial(historial)

# Guarda cuántos meses tiene un año para reutilizar el valor en las fórmulas.
MESES_POR_ANIO = 12
# Guarda los días del año para convertir un gasto diario al promedio mensual.
DIAS_POR_ANIO = 365
# Guarda las semanas del año para convertir un gasto semanal al promedio mensual.
SEMANAS_POR_ANIO = 52
# Define los plazos que se mostrarán en la tabla de proyecciones.
HORIZONTES = (1, 3, 5, 10)
# Define metas sugeridas y sus costos iniciales; el visitante puede modificar el costo.
METAS = {
    "Laptop": 850.00,
    "Motocicleta": 3500.00,
    "Primer año de universidad": 2500.00,
    "Abono inicial de una casa": 10000.00,
    "Terreno": 15000.00,
    "Fondo de emergencia": 3000.00,
}

# Paletas y acentos seleccionables desde la barra lateral.
PALETAS = {
    "Oscuro": {"fondo": "#0b1220", "superficie": "#152238", "lateral": "#101b2d", "borde": "#29405d", "texto": "#eaf2f7", "muted": "#a9bbca", "grafica": "plotly_dark"},
    "Claro": {"fondo": "#f6f8fc", "superficie": "#ffffff", "lateral": "#edf2f8", "borde": "#cbd5e1", "texto": "#152238", "muted": "#52657a", "grafica": "plotly_white"},
}
ACENTOS = {"Verde ahorro": "#35c98b", "Azul océano": "#5b8def", "Dorado": "#f4b942", "Violeta": "#ad7cff"}


def iniciar_apariencia() -> None:
    """Inicia las preferencias visuales que el visitante puede cambiar manualmente."""
    if "modo_visual" not in st.session_state:
        st.session_state.modo_visual = "Oscuro"
    if "acento_visual" not in st.session_state:
        st.session_state.acento_visual = "Verde ahorro"
    # Colores independientes para que la comparación de la gráfica sea configurable.
    if "color_gasto_grafica" not in st.session_state:
        st.session_state.color_gasto_grafica = "#ff8066"
    if "color_ahorro_grafica" not in st.session_state:
        st.session_state.color_ahorro_grafica = ACENTOS[st.session_state.acento_visual]


def aplicar_estilos(paleta: dict[str, str], acento: str) -> None:
    """Aplica colores CSS según el modo y acento elegidos en esta sesión."""
    estilos = """
    <style>
        :root { --fondo: FONDO; --superficie: SUPERFICIE; --lateral: LATERAL; --borde: BORDE; --texto: TEXTO; --muted: MUTED; --ahorro: ACENTO; --meta: #f4b942; --gasto: #ff8066; --info: #5b8def; }
        .stApp, [data-testid="stAppViewContainer"] { background: var(--fondo); color: var(--texto); }
        h1 { color: var(--ahorro); font-weight: 800; letter-spacing: -.5px; }
        h2, h3 { color: var(--texto); }
        [data-testid="stSidebar"], [data-testid="stSidebarContent"] { background: var(--lateral); }
        [data-testid="stSidebar"] h2 { color: var(--meta); }
        [data-testid="stMetric"] { background: var(--superficie); border: 1px solid var(--borde); border-radius: 14px; padding: 1rem; box-shadow: 0 6px 18px rgba(0, 0, 0, .12); }
        [data-testid="stMetricLabel"], [data-testid="stCaptionContainer"], .stCaption { color: var(--muted); }
        [data-testid="stMetricValue"] { color: var(--ahorro); }
        div.stButton > button, div.stFormSubmitButton > button { background: var(--ahorro); color: #07130e; border: 0; border-radius: 9px; font-weight: 700; transition: transform .15s ease, filter .15s ease; }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover { transform: translateY(-1px); filter: brightness(1.08); color: #07130e; }
        [data-testid="stDataFrame"] { border: 1px solid var(--borde); border-radius: 12px; overflow: hidden; }
        /* Se fuerzan los controles nativos para evitar campos negros al cambiar a modo claro. */
        [data-baseweb="input"], [data-baseweb="select"] > div, [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
            background-color: var(--superficie) !important; border-color: var(--borde) !important;
            color: var(--texto) !important; -webkit-text-fill-color: var(--texto) !important;
        }
        [data-baseweb="select"] *, [data-baseweb="input"] input, [data-baseweb="input"] svg,
        [data-testid="stNumberInput"] button, [data-testid="stTextInput"] input::placeholder {
            color: var(--texto) !important; fill: var(--texto) !important;
        }
        [data-baseweb="popover"], [role="listbox"], [role="option"] { background-color: var(--superficie) !important; color: var(--texto) !important; }
        [data-testid="stDataFrame"] [role="grid"] { background-color: var(--superficie) !important; color: var(--texto) !important; }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--borde); background: var(--superficie); border-radius: 14px; }
        /* El disparador se muestra en la cabecera, junto a Deploy, no dentro del contenido. */
        [data-testid="stColumn"]:has(#menu-apariencia-ancla) { position: fixed; top: 8px; right: 58px; z-index: 1000; width: 44px !important; min-width: 44px !important; }
        [data-testid="stColumn"]:has(#menu-apariencia-ancla) [data-testid="stMarkdownContainer"] { display: none; }
        [data-testid="stColumn"]:has(#menu-apariencia-ancla) button { min-height: 34px; padding: 0 .55rem; }
        [data-testid="stAlert"] { border-radius: 10px; }
        [data-testid="stInfo"] { border-left: 4px solid var(--info); }
        [data-testid="stSuccess"] { border-left: 4px solid var(--ahorro); }
        /* Tema de reto: solo modifica la presentación de los componentes existentes. */
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: var(--fondo); color: var(--texto);
            background-image: radial-gradient(circle at 8% 4%, rgba(91,141,239,.15) 0, transparent 22rem), radial-gradient(circle at 94% 18%, rgba(53,201,139,.10) 0, transparent 24rem);
        }
        [data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 1.8rem; }
        h1, h2, h3 { font-family: "Trebuchet MS", "Arial Rounded MT Bold", sans-serif; }
        h2 { font-size: 1.45rem !important; margin-top: 2.2rem !important; padding-left: .85rem; border-left: 5px solid var(--ahorro); }
        [data-testid="stSidebar"] { border-right: 1px solid var(--borde); }
        [data-testid="stMetric"] {
            position: relative; overflow: hidden; background: var(--superficie); border-radius: 18px; padding: 1.1rem; min-height: 126px;
            box-shadow: 0 10px 24px rgba(0, 0, 0, .16); transition: transform .18s ease, box-shadow .18s ease;
        }
        [data-testid="stMetric"]:before { content: "✦"; position: absolute; top: 5px; right: 12px; color: var(--meta); font-size: 1.15rem; opacity: .9; }
        [data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 15px 28px rgba(0, 0, 0, .23); }
        [data-testid="stMetricLabel"] { font-weight: 800; text-transform: uppercase; letter-spacing: .055em; font-size: .72rem; }
        [data-testid="stMetricValue"] { font-family: "Trebuchet MS", sans-serif; font-weight: 900; }
        div.stButton > button, div.stFormSubmitButton > button {
            min-height: 46px; background: linear-gradient(180deg, #71e5b2, var(--ahorro)); color: #07130e; border: 0; border-bottom: 4px solid rgba(0,0,0,.25);
            border-radius: 13px; font-family: "Trebuchet MS", sans-serif; font-weight: 900; box-shadow: 0 5px 0 rgba(0,0,0,.12), 0 9px 18px rgba(0,0,0,.14);
            transition: transform .15s ease, filter .15s ease, box-shadow .15s ease;
        }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover { transform: translateY(-2px); filter: brightness(1.08); color: #07130e; }
        div.stButton > button:active, div.stFormSubmitButton > button:active { transform: translateY(3px); border-bottom-width: 1px; box-shadow: 0 3px 0 rgba(0,0,0,.12); }
        [data-testid="stDataFrame"] { border-radius: 16px; box-shadow: 0 8px 20px rgba(0,0,0,.10); }
        [data-testid="stPlotlyChart"] { background: var(--superficie); border: 1px solid var(--borde); border-radius: 18px; padding: .5rem; box-shadow: 0 8px 20px rgba(0,0,0,.10); }
        [data-testid="stForm"] { background: rgba(255,255,255,.025); border: 1px solid var(--borde); border-radius: 18px; padding: 1.1rem 1rem .5rem; }
        .game-hero { position: relative; overflow: hidden; margin: 0 0 1.4rem; padding: clamp(1.35rem, 4vw, 2.5rem); border: 1px solid rgba(255,214,90,.48); border-radius: 24px; background: linear-gradient(125deg, #162852 0%, #273e82 52%, #167a65 100%); box-shadow: 0 16px 35px rgba(0,0,0,.26); color: #fff; }
        .game-hero:after { content: ""; position: absolute; width: 360px; height: 360px; border-radius: 50%; right: -110px; top: -190px; background: radial-gradient(circle, rgba(255,214,90,.32), transparent 65%); }
        .game-kicker { position: relative; z-index: 1; display: inline-block; padding: .34rem .7rem; border: 1px solid rgba(255,255,255,.32); border-radius: 999px; background: rgba(7,15,43,.30); color: #ffe387; font: 800 .75rem "Trebuchet MS", sans-serif; letter-spacing: .12em; }
        .game-title { position: relative; z-index: 1; margin: .55rem 0 .2rem; color: #fff; font: 900 clamp(1.85rem, 5vw, 3.2rem) "Trebuchet MS", sans-serif; line-height: 1.05; text-shadow: 0 3px 0 rgba(8,21,56,.5); }
        .game-copy { position: relative; z-index: 1; max-width: 680px; margin: .6rem 0 0; color: #eef6ff; font-size: 1.03rem; }
        .ant-mascot { position: absolute; z-index: 1; right: clamp(1rem, 7vw, 5rem); bottom: .4rem; font-size: clamp(4.6rem, 11vw, 8.5rem); filter: drop-shadow(0 8px 5px rgba(0,0,0,.28)); animation: ant-bounce 2.8s ease-in-out infinite; }
        .level-chip { position: relative; z-index: 1; display: inline-block; margin-top: 1.1rem; padding: .45rem .8rem; border-radius: 10px; background: #ffd65a; color: #152238; font: 900 .77rem "Trebuchet MS", sans-serif; letter-spacing: .04em; }
        @keyframes ant-bounce { 0%,100% { transform: translateY(0) rotate(-4deg); } 50% { transform: translateY(-8px) rotate(4deg); } }
        @media (max-width: 640px) { [data-testid="stMainBlockContainer"] { padding: 1rem .85rem 2.5rem; } .game-hero { padding-right: 5.4rem; } .ant-mascot { right: .45rem; font-size: 4.2rem; } [data-testid="stMetric"] { min-height: 105px; padding: .8rem; } h2 { font-size: 1.2rem !important; } }
        /* Correcciones puntuales para controles nativos que no heredan el tema del reto. */
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
        [data-testid="stSelectbox"] [data-baseweb="select"] input {
            background-color: var(--superficie) !important; color: var(--texto) !important;
            -webkit-text-fill-color: var(--texto) !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            border: 1px solid var(--borde) !important; border-radius: 12px !important;
            box-shadow: 0 3px 10px rgba(0,0,0,.12);
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
            border-color: var(--ahorro) !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
            border-color: var(--ahorro) !important; box-shadow: 0 0 0 2px rgba(53,201,139,.22) !important;
        }
        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {
            background: var(--superficie) !important; border: 1px solid var(--borde) !important;
            border-radius: 12px !important; box-shadow: 0 12px 28px rgba(0,0,0,.28) !important;
        }
        [role="option"], [data-baseweb="menu"] li, [data-baseweb="menu"] [role="menuitem"] {
            background: var(--superficie) !important; color: var(--texto) !important;
        }
        [role="option"]:hover, [role="option"][aria-selected="true"],
        [data-baseweb="menu"] li:hover, [data-baseweb="menu"] [role="menuitem"]:hover {
            background: rgba(53,201,139,.16) !important; color: var(--texto) !important;
        }
        [data-testid="stDataFrame"] button { color: var(--texto) !important; }
        [data-testid="stDataFrame"] button:hover { background: rgba(53,201,139,.14) !important; }
        AJUSTES_OSCURO
    </style>
    """
    reemplazos = {"FONDO": paleta["fondo"], "SUPERFICIE": paleta["superficie"], "LATERAL": paleta["lateral"], "BORDE": paleta["borde"], "TEXTO": paleta["texto"], "MUTED": paleta["muted"], "ACENTO": acento}
    for marcador, valor in reemplazos.items():
        estilos = estilos.replace(marcador, valor)
    # El modo claro conserva sus estilos nativos; estas correcciones se aplican solo al oscuro.
    ajustes_oscuro = """
        header[data-testid="stHeader"] { background: var(--fondo) !important; }
        header[data-testid="stHeader"] *, .stApp label, .stApp [data-testid="stWidgetLabel"] p { color: var(--texto) !important; }
        [data-testid="stNumberInput"] button { background: var(--superficie) !important; border-color: var(--borde) !important; color: var(--texto) !important; }
        [data-testid="stNumberInput"] button svg { fill: var(--texto) !important; }
        [data-testid="stNumberInput"] [data-baseweb="input"] { background: var(--superficie) !important; }
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: var(--texto) !important; }
        /* Streamlit aplica blanco en el contenedor interno del select; se cubren todos sus niveles. */
        [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div > div {
            background-color: var(--superficie) !important; color: var(--texto) !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] span,
        [data-testid="stSelectbox"] [data-baseweb="select"] svg { color: var(--texto) !important; fill: var(--texto) !important; }
        [data-baseweb="popover"] > div, [data-baseweb="popover"] [role="dialog"] { background-color: var(--superficie) !important; color: var(--texto) !important; }
    """ if paleta["fondo"] == "#0b1220" else ""
    estilos = estilos.replace("AJUSTES_OSCURO", ajustes_oscuro)
    st.markdown(estilos, unsafe_allow_html=True)


def color_transparente(color_hex: str, opacidad: float = 0.20) -> str:
    """Convierte un color hexadecimal a RGBA para rellenar el área de la gráfica."""
    rojo, verde, azul = (int(color_hex[posicion:posicion + 2], 16) for posicion in (1, 3, 5))
    return f"rgba({rojo}, {verde}, {azul}, {opacidad})"


iniciar_apariencia()
modo_visual = st.session_state.modo_visual
acento_actual = ACENTOS[st.session_state.acento_visual]
paleta_actual = PALETAS[modo_visual]
aplicar_estilos(paleta_actual, acento_actual)


# Recibe un número y devuelve el valor con símbolo B/., miles y dos decimales.
def formato_balboas(valor: float) -> str:
    """Da formato monetario uniforme para toda la aplicación."""
    # El formato , .2f agrega separador de miles y exactamente dos decimales.
    return f"B/. {valor:,.2f}"


# Convierte un gasto de cualquier frecuencia a su equivalente mensual.
def gasto_mensual(gasto: dict[str, Any]) -> float:
    """Convierte un gasto diario, semanal o mensual a su equivalente mensual."""
    # Extrae el monto del diccionario y lo convierte a número decimal.
    monto = float(gasto["monto"])
    # Extrae si el visitante indicó Diario, Semanal o Mensual.
    frecuencia = gasto["frecuencia"]
    # Si es diario, usa 365 días y los divide entre los 12 meses del año.
    if frecuencia == "Diario":
        return monto * DIAS_POR_ANIO / MESES_POR_ANIO
    # Si es semanal, usa las 52 semanas y las divide entre los 12 meses.
    if frecuencia == "Semanal":
        return monto * SEMANAS_POR_ANIO / MESES_POR_ANIO
    # Si ya es mensual, el monto ingresado no necesita conversión.
    return monto


# Calcula aportes, intereses y total para un aporte mensual y plazo determinados.
def proyeccion(aporte_mensual: float, tasa_anual: float, meses: int) -> tuple[float, float, float]:
    """Calcula aportes, intereses y total con depósitos al final de cada mes."""
    # Multiplica el aporte mensual por los meses para saber cuánto puso la persona.
    aportado = aporte_mensual * meses
    # Convierte la tasa anual porcentual, por ejemplo 4, a una tasa mensual decimal.
    tasa_mensual = tasa_anual / 100 / MESES_POR_ANIO
    # Evita dividir entre cero cuando la tasa seleccionada es 0 %.
    if tasa_mensual == 0:
        # Sin interés, el total equivale solamente a los aportes realizados.
        total = aportado
    else:
        # Aplica la fórmula del valor futuro de aportes mensuales con interés compuesto.
        total = aporte_mensual * (((1 + tasa_mensual) ** meses - 1) / tasa_mensual)
    # Devuelve una tupla: dinero aportado, intereses generados y total final.
    return aportado, total - aportado, total


# Busca en qué mes el ahorro proyectado alcanza o supera el costo de una meta.
def meses_para_meta(aporte_mensual: float, tasa_anual: float, meta: float) -> int | None:
    """Busca el primer mes que alcanza la meta; evita promesas de plazo infinito."""
    # Sin aporte o sin meta válida, no existe un plazo que se pueda calcular.
    if aporte_mensual <= 0 or meta <= 0:
        return None
    # Revisa mes a mes hasta un máximo de 100 años (1,200 meses).
    for meses in range(1, 1201):
        # Consulta el total, que es la tercera posición de la tupla de proyeccion.
        if proyeccion(aporte_mensual, tasa_anual, meses)[2] >= meta:
            # Devuelve el primer mes en el que se logró alcanzar la meta.
            return meses
    # Devuelve None si la meta no se alcanza ni siquiera dentro del límite establecido.
    return None


# Crea la lista de gastos de la sesión solo la primera vez que se abre la página.
def iniciar_estado() -> None:
    """Inicia una simulación vacía para que cada visitante ingrese sus datos."""
    # Comprueba si la variable gastos todavía no fue creada en la sesión de Streamlit.
    if "gastos" not in st.session_state:
        # Inicia una lista vacía: no se cargan gastos ficticios automáticamente.
        st.session_state.gastos = []


# Reemplaza los gastos por un único escenario de demostración rápida.
def reemplazar_por_simulacion(monto_diario: float) -> None:
    # Guarda en la sesión una lista con un gasto diario generado por el botón pulsado.
    st.session_state.gastos = [
        {"nombre": f"Ahorro diario de {formato_balboas(monto_diario)}", "monto": monto_diario, "frecuencia": "Diario"}
    ]


# Ejecuta la función antes de dibujar la página para garantizar que la lista existe.
iniciar_estado()

# Muestra la portada visual de la aplicación; no modifica los datos ni los cálculos.
st.markdown(
    """
    <section class="game-hero">
        <span class="game-kicker">🎮 MISIÓN EDUCATIVA · COCLÉ</span>
        <div class="ant-mascot">🐜💰</div>
        <div class="game-title">Gastos Hormiga:<br>El Reto del Ahorro</div>
        <p class="game-copy">Descubre cuánto dinero puedes acumular al convertir pequeños gastos en grandes metas.</p>
        <span class="level-chip">⭐ NIVEL 1 · DETECTA TUS GASTOS</span>
    </section>
    """,
    unsafe_allow_html=True,
)
# Advierte que la aplicación es educativa y no constituye asesoramiento financiero.
st.info("Estimación educativa: los resultados usan aportes mensuales e interés compuesto. No constituyen asesoramiento financiero.")

# Agrupa los controles de configuración dentro de la barra lateral izquierda.
with st.sidebar:
    # Escribe el encabezado de esa barra lateral.
    st.header("Configuración")
    # Crea el campo donde la persona selecciona la tasa anual de interés.
    tasa_anual = st.number_input("Tasa de interés anual (%)", min_value=0.0, max_value=30.0, value=4.0, step=0.25)
    # Explica que una tasa de cero permite observar el ahorro sin inversión.
    st.caption("Puedes usar 0 % para ver un ahorro sin inversión.")
    # Crea un botón para limpiar los gastos antes de atender a otro visitante.
    if st.button("Nueva demostración", use_container_width=True):
        # Reemplaza los gastos actuales por una lista vacía.
        st.session_state.gastos = []
        # Vuelve a ejecutar la app para que la pantalla se actualice inmediatamente.
        st.rerun()

# Inicia la primera sección de la aplicación.
st.header("🐜 NIVEL 1 · Tus gastos hormiga")
# Indica que deben usarse los gastos reales del visitante actual.
st.caption("Ingresa los gastos reales de la persona que está realizando la simulación.")
# Agrupa los campos de un gasto en un formulario para enviarlos con un solo botón.
with st.form("agregar_gasto", clear_on_submit=True):
    # Divide el formulario en cuatro columnas con proporciones de ancho diferentes.
    col_nombre, col_monto, col_frecuencia, col_boton = st.columns([3, 2, 2, 1])
    # Coloca el campo de nombre dentro de la primera columna.
    with col_nombre:
        # Permite escribir el nombre del gasto y muestra un ejemplo como guía.
        nombre = st.text_input("Nombre", placeholder="Ej.: Chicha")
    # Coloca el campo monetario dentro de la segunda columna.
    with col_monto:
        # Permite ingresar el precio; no acepta números menores que un centavo.
        monto = st.number_input("Precio (B/.)", min_value=0.01, value=1.00, step=0.25)
    # Coloca el selector de frecuencia dentro de la tercera columna.
    with col_frecuencia:
        # Permite escoger una de las tres frecuencias que reconoce la fórmula.
        frecuencia = st.selectbox("Frecuencia", ("Diario", "Semanal", "Mensual"))
    # Coloca el botón de envío dentro de la última columna.
    with col_boton:
        # Agrega un espacio vertical para alinear visualmente el botón con los campos.
        st.write("")
        # Guarda True en agregar cuando la persona envía el formulario.
        agregar = st.form_submit_button("+ Agregar gasto", use_container_width=True)

# Solo agrega un gasto cuando el formulario fue enviado.
if agregar:
    # Añade un diccionario con los datos del formulario; usa "Otro gasto" si no escribieron nombre.
    st.session_state.gastos.append({"nombre": nombre.strip() or "Otro gasto", "monto": monto, "frecuencia": frecuencia})
    # Recarga la página para mostrar el gasto recién agregado y recalcular resultados.
    st.rerun()

# Muestra un aviso cuando todavía no se han ingresado gastos.
if not st.session_state.gastos:
    st.warning("Aún no tienes gastos. Agrega uno o usa el simulador rápido.")
# Si sí hay gastos, muestra cada uno en una fila.
else:
    # enumerate entrega el número de fila y el diccionario de cada gasto.
    for indice, gasto in enumerate(st.session_state.gastos):
        # Crea columnas para el texto, el equivalente mensual y el botón Eliminar.
        col_texto, col_equivalente, col_eliminar = st.columns([5, 3, 1])
        # Muestra el nombre, precio y frecuencia originales del gasto.
        col_texto.write(f"**{gasto['nombre']}** · {formato_balboas(gasto['monto'])} · {gasto['frecuencia']}")
        # Muestra el valor mensual ya convertido mediante gasto_mensual.
        col_equivalente.caption(f"Equivale a {formato_balboas(gasto_mensual(gasto))}/mes")
        # Crea un botón único para eliminar este gasto específico.
        if col_eliminar.button("Eliminar", key=f"eliminar_{indice}"):
            # Quita de la lista el gasto que coincide con el índice de su fila.
            st.session_state.gastos.pop(indice)
            # Recarga para actualizar la lista y todos los cálculos.
            st.rerun()

# Suma los equivalentes mensuales de todos los gastos para obtener el aporte mensual potencial.
aporte_mensual = sum(gasto_mensual(gasto) for gasto in st.session_state.gastos)
# Convierte el aporte mensual a gasto anual para la tarjeta correspondiente.
gasto_anual = aporte_mensual * MESES_POR_ANIO
# Divide el gasto anual entre 365 para obtener el gasto diario promedio.
gasto_diario = gasto_anual / DIAS_POR_ANIO
# Calcula los tres resultados de la proyección a cinco años.
resultado_5 = proyeccion(aporte_mensual, tasa_anual, 5 * MESES_POR_ANIO)
# Calcula los tres resultados de la proyección a diez años.
resultado_10 = proyeccion(aporte_mensual, tasa_anual, 10 * MESES_POR_ANIO)

# Inicia la sección de resumen financiero.
st.header("🏆 RESULTADOS DEL RETO · Gastos y ahorro")
# Crea cuatro columnas iguales para las tarjetas principales.
tarjetas = st.columns(4)
# Muestra el gasto diario promedio en la primera tarjeta.
tarjetas[0].metric("Gasto diario aproximado", formato_balboas(gasto_diario))
# Muestra el gasto mensual en la segunda tarjeta.
tarjetas[1].metric("Gasto mensual", formato_balboas(aporte_mensual))
# Muestra el total con interés de la proyección a cinco años en la tercera tarjeta.
tarjetas[2].metric("Ahorro a 5 años", formato_balboas(resultado_5[2]))
# Muestra el total con interés de la proyección a diez años en la cuarta tarjeta.
tarjetas[3].metric("Ahorro a 10 años", formato_balboas(resultado_10[2]))

# Introduce la tabla que compara los cuatro horizontes de tiempo.
st.write("Si eliminas estos gastos y ahorras ese dinero, podrías acumular:")
# Prepara una lista vacía que contendrá cada fila de la tabla.
proyecciones = []
# Repite el cálculo para 1, 3, 5 y 10 años.
for anios in HORIZONTES:
    # Separa los valores devueltos por proyeccion en tres variables.
    aportado, intereses, total = proyeccion(aporte_mensual, tasa_anual, anios * MESES_POR_ANIO)
    # Agrega una fila con el plazo y los tres resultados convertidos a texto monetario.
    proyecciones.append({"Plazo": f"{anios} año" if anios == 1 else f"{anios} años", "Aportado": formato_balboas(aportado), "Intereses": formato_balboas(intereses), "Total acumulado": formato_balboas(total)})
# Muestra la lista de filas como una tabla sin el índice técnico de Python.
st.dataframe(proyecciones, hide_index=True, use_container_width=True)

# Inicia la sección dedicada a la visualización del crecimiento.
st.header("📊 TABLERO DE PROGRESO · Gasto vs. ahorro")
st.caption("La diferencia entre ambas líneas representa el beneficio de ahorrar e invertir en lugar de gastar.")
# Crea la lista de años del 0 al 10 para el eje horizontal del gráfico.
anios_grafico = list(range(0, 11))
# Compara lo gastado sin cambiar hábitos con el ahorro potencial que incluye intereses.
gastos_acumulados = [aporte_mensual * anio * MESES_POR_ANIO for anio in anios_grafico]
ahorros_potenciales = [proyeccion(aporte_mensual, tasa_anual, anio * MESES_POR_ANIO)[2] for anio in anios_grafico]
# Crea una figura Plotly todavía vacía.
figura = go.Figure()
# Añade la trayectoria del dinero que se seguiría gastando.
figura.add_trace(go.Scatter(x=anios_grafico, y=gastos_acumulados, mode="lines+markers", line={"width": 3, "color": st.session_state.color_gasto_grafica}, marker={"size": 8, "color": st.session_state.color_gasto_grafica}, name="Gasto acumulado", hovertemplate="Año %{x}<br>Gastado: B/. %{y:,.2f}<extra></extra>"))
# Añade el ahorro potencial y rellena el área para hacer más visible el beneficio.
figura.add_trace(go.Scatter(x=anios_grafico, y=ahorros_potenciales, mode="lines+markers", fill="tonexty", fillcolor=color_transparente(st.session_state.color_ahorro_grafica), line={"width": 4, "color": st.session_state.color_ahorro_grafica}, marker={"size": 8, "color": st.session_state.color_ahorro_grafica}, name="Ahorro potencial", hovertemplate="Año %{x}<br>Ahorro potencial: B/. %{y:,.2f}<extra></extra>"))
# Configura títulos, formato monetario, interacción al pasar el cursor y márgenes.
figura.update_layout(template=paleta_actual["grafica"], paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"family": "Trebuchet MS, sans-serif", "color": paleta_actual["texto"]}, xaxis_title="Años", yaxis_title="Dinero acumulado (B/.)", yaxis_tickprefix="B/. ", hovermode="x unified", legend={"orientation": "h", "y": 1.12}, margin={"l": 10, "r": 10, "t": 45, "b": 10})
# Inserta el gráfico interactivo en la aplicación y le permite ocupar todo el ancho.
st.plotly_chart(figura, use_container_width=True)

# Inicia la sección de metas de ahorro.
st.header("🎯 TU META · ¿Qué podrías lograr?")
# Combina las metas sugeridas con las creadas y guardadas por los visitantes.
metas_personalizadas = cargar_metas_personalizadas()
metas_disponibles = dict(METAS)
for meta_personalizada in metas_personalizadas:
    metas_disponibles[meta_personalizada["nombre"]] = meta_personalizada["costo"]
# La selección de una meta recién creada se aplica antes de crear el selectbox.
meta_pendiente = st.session_state.pop("meta_seleccionada_pendiente", None)
if meta_pendiente in metas_disponibles:
    st.session_state.meta_seleccionada = meta_pendiente
# Conserva el costo escrito manualmente hasta que se cambie la meta seleccionada.
if "meta_seleccionada" not in st.session_state or st.session_state.meta_seleccionada not in metas_disponibles:
    st.session_state.meta_seleccionada = next(iter(metas_disponibles))
if st.session_state.get("meta_costo_origen") != st.session_state.meta_seleccionada:
    st.session_state.costo_meta_input = float(metas_disponibles[st.session_state.meta_seleccionada])
    st.session_state.meta_costo_origen = st.session_state.meta_seleccionada
# Crea dos columnas: una para escoger la meta y otra para definir su costo.
col_meta, col_costo = st.columns(2)
# Coloca el selector de metas dentro de la primera columna.
with col_meta:
    # Muestra tanto las metas predefinidas como las personalizadas guardadas.
    nombre_meta = st.selectbox("Selecciona una meta", list(metas_disponibles), key="meta_seleccionada")
# Coloca el campo de costo dentro de la segunda columna.
with col_costo:
    # Permite modificar el costo inicial asociado a la meta seleccionada.
    costo_meta = st.number_input("Costo estimado de la meta (B/.)", min_value=1.0, step=100.0, key="costo_meta_input")

# Permite añadir una meta sin alterar las metas predefinidas ni el cálculo actual.
with st.expander("➕ Agregar nueva meta"):
    with st.form("agregar_meta_personalizada", clear_on_submit=True):
        col_nombre_meta, col_valor_meta, col_guardar_meta = st.columns([3, 2, 1])
        with col_nombre_meta:
            nueva_meta_nombre = st.text_input("Nombre de la meta", placeholder="Ej.: PlayStation 5")
        with col_valor_meta:
            nueva_meta_costo = st.number_input("Costo de la meta (B/.)", min_value=0.01, value=1.00, step=10.0)
        with col_guardar_meta:
            st.write("")
            agregar_meta = st.form_submit_button("Agregar nueva meta", use_container_width=True)

if agregar_meta:
    nombre_limpio = nueva_meta_nombre.strip()
    nombres_existentes = {nombre.casefold() for nombre in metas_disponibles}
    if not nombre_limpio:
        st.warning("Escribe un nombre para la nueva meta.")
    elif nueva_meta_costo <= 0:
        st.warning("El costo de la meta debe ser mayor que B/. 0.00.")
    elif nombre_limpio.casefold() in nombres_existentes:
        st.warning("Ya existe una meta con ese nombre.")
    else:
        metas_personalizadas.append({"nombre": nombre_limpio, "costo": float(nueva_meta_costo)})
        guardar_metas_personalizadas(metas_personalizadas)
        st.session_state.meta_seleccionada_pendiente = nombre_limpio
        st.rerun()

# Calcula cuántos meses se necesitan para alcanzar la meta con el ahorro actual.
plazo_meta = meses_para_meta(aporte_mensual, tasa_anual, costo_meta)
# Si no se puede calcular el plazo, informa cómo resolverlo.
if plazo_meta is None:
    st.warning("Agrega un gasto o aumenta tu ahorro mensual para calcular el plazo de esta meta.")
# Si existe plazo, convierte el número total de meses en años y meses restantes.
else:
    # divmod divide por 12 y devuelve el cociente y el residuo al mismo tiempo.
    anios_meta, meses_restantes = divmod(plazo_meta, MESES_POR_ANIO)
    # Construye el texto adecuado según si el plazo incluye años o solo meses.
    texto_plazo = f"{anios_meta} años y {meses_restantes} meses" if anios_meta else f"{meses_restantes} meses"
    # Muestra el resultado de la meta destacado en color de éxito.
    st.success(f"Con tu ahorro actual podrías alcanzar **{nombre_meta}** aproximadamente en **{texto_plazo}**.")

# Inicia la sección que compara gastar hoy con ahorrar e invertir.
st.header("✨ BONUS DEL RETO · Costo de oportunidad")
# Calcula cuánto dinero se gastaría en cinco años sin ahorrar ni generar intereses.
gasto_sin_ahorrar = aporte_mensual * 5 * MESES_POR_ANIO
# Calcula el interés potencial como la diferencia entre total proyectado y aportes.
beneficio = resultado_5[2] - gasto_sin_ahorrar
# Crea tres columnas para mostrar la comparación.
col_a, col_b, col_c = st.columns(3)
# Muestra el dinero que se habría gastado durante cinco años.
col_a.metric("Gastarías en 5 años", formato_balboas(gasto_sin_ahorrar))
# Muestra el dinero que podría acumularse al ahorrar e invertir ese mismo aporte.
col_b.metric("Podrías acumular", formato_balboas(resultado_5[2]))
# Muestra la ganancia adicional atribuible al interés compuesto.
col_c.metric("Beneficio potencial", formato_balboas(beneficio))
# Indica cuál fue la tasa usada para calcular la diferencia.
st.caption(f"La diferencia es el interés potencial al ahorrar con una tasa anual de {tasa_anual:.2f} %.")

# Inicia la sección de botones para una demostración rápida durante la feria.
st.header("⚡ MODO RÁPIDO · Simulador")
# Explica que estos botones son una ayuda opcional para el expositor.
st.write("Úsalo durante la exposición para cargar un ejemplo instantáneo.")
# Crea cuatro columnas para distribuir los cuatro botones por igual.
botones = st.columns(4)
# Recorre cada columna junto con los montos diarios disponibles.
for columna, monto_rapido in zip(botones, (0.50, 1.00, 2.00, 5.00)):
    # Crea un botón dentro de la columna actual y espera que sea pulsado.
    if columna.button(f"Ahorrar {formato_balboas(monto_rapido)} al día", use_container_width=True):
        # Carga el escenario correspondiente al monto elegido.
        reemplazar_por_simulacion(monto_rapido)
        # Recarga para recalcular y mostrar inmediatamente todos los resultados.
        st.rerun()


# Permite registrar la simulación actual sin interrumpir el uso de la calculadora.
st.header("📝 REGISTRO DE JUGADORES")
st.caption("Al finalizar una simulación, guárdala para incluirla en el historial y las estadísticas del proyecto.")
with st.form("guardar_participante", clear_on_submit=True):
    participante = st.text_input("Nombre o identificador del participante", placeholder="Ej.: María G.")
    guardar_calculo = st.form_submit_button("Guardar cálculo en el historial", use_container_width=True)

if guardar_calculo:
    if aporte_mensual <= 0:
        st.warning("Agrega al menos un gasto antes de guardar el cálculo.")
    else:
        registrar_calculo(participante, st.session_state.gastos, tasa_anual, aporte_mensual, resultado_5[2], resultado_10[2])
        st.success("Cálculo guardado correctamente en el historial.")


# Sección independiente para revisar el historial persistente y sus indicadores.
st.header("🏅 SALÓN DE LOGROS · Historial y estadísticas")
historial = cargar_historial()
if not historial:
    st.info("Todavía no hay participantes registrados. Guarda un cálculo para comenzar el historial.")
else:
    total_participantes = len(historial)
    promedio_gasto = sum(float(registro.get("gasto_mensual", 0)) for registro in historial) / total_participantes
    promedio_ahorro = sum(float(registro.get("ahorro_potencial_5_anios", 0)) for registro in historial) / total_participantes
    total_gastos = sum(float(registro.get("gasto_anual", 0)) for registro in historial)

    estadisticas = st.columns(4)
    estadisticas[0].metric("Participantes registrados", total_participantes)
    estadisticas[1].metric("Promedio de gasto mensual", formato_balboas(promedio_gasto))
    estadisticas[2].metric("Promedio de ahorro potencial (5 años)", formato_balboas(promedio_ahorro))
    estadisticas[3].metric("Total de gastos anuales registrados", formato_balboas(total_gastos))

    # Presenta un resumen amigable; los detalles de los gastos originales siguen en el JSON local.
    filas_historial = [
        {
            "Fecha": registro.get("fecha", "—"),
            "Participante": registro.get("participante", "Sin nombre"),
            "Gastos ingresados": registro.get("cantidad_gastos", 0),
            "Gasto mensual": formato_balboas(float(registro.get("gasto_mensual", 0))),
            "Ahorro potencial a 5 años": formato_balboas(float(registro.get("ahorro_potencial_5_anios", 0))),
            "Ahorro potencial a 10 años": formato_balboas(float(registro.get("ahorro_potencial_10_anios", 0))),
        }
        for registro in reversed(historial)
    ]
    st.dataframe(filas_historial, hide_index=True, use_container_width=True)
    st.caption("Los registros se conservan localmente en historial_participantes.json, incluso al cerrar la aplicación.")
