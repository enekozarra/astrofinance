import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import math
import os
import base64
from PIL import Image
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Astro Finance Tool",
    page_icon="🔮",
    layout="wide"
)

def get_base64(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_base64("assets/background.png")

page_bg = f"""
<style>

.stApp {{
    background-image:
        linear-gradient(
            rgba(0,0,0,0.50),
            rgba(0,0,0,0.50)
        ),
        url("data:image/png;base64,{img}");

    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

[data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
}}

[data-testid="stToolbar"] {{
    right: 2rem;
}}

.main {{
    background: rgba(0,0,0,0.30);
    backdrop-filter: blur(6px);
    border-radius: 20px;
}}

section[data-testid="stSidebar"] {{
    background: rgba(0,0,0,0.45);
}}

</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

st.markdown("""
<style>

/* SOLO CARDS DE PLANETAS */

div[class*="st-key-planet_card_"] {
    background: #050a14 !important;
    border-radius: 22px !important;
    border: 1px solid rgba(255,215,100,0.22) !important;
    box-shadow:
        0 0 28px rgba(255,215,100,0.08),
        inset 0 0 16px rgba(255,255,255,0.02) !important;
    padding: 16px !important;
    overflow: hidden !important;
    color: white !important;
}

/* CARDS CONJUNCIONES */

div[class*="st-key-conj_card_"] {
    background: rgba(5,10,20,0.88) !important;
    border-radius: 22px !important;
    border: 1px solid rgba(255,215,100,0.18) !important;
    padding: 22px !important;
    backdrop-filter: blur(10px);
    box-shadow:
        0 0 28px rgba(255,215,100,0.06),
        inset 0 0 16px rgba(255,255,255,0.02) !important;
}

</style>
""", unsafe_allow_html=True)

swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANETAS = {
    "☉ Sol": swe.SUN,
    "☽ Luna": swe.MOON,
    "♂ Marte": swe.MARS,
    "☿ Mercurio": swe.MERCURY,
    "♃ Júpiter": swe.JUPITER,
    "♀ Venus": swe.VENUS,
    "♄ Saturno": swe.SATURN,
    "☊ Rahu": swe.MEAN_NODE,
}

MACRO_PLANETAS = [
    "♄ Saturno",
    "☊ Rahu",
    "☋ Ketu",
    "♃ Júpiter",
    "♂ Marte"
]

BASE_MACRO = {
    "♄ Saturno": 1.00,
    "☊ Rahu": 0.88,
    "☋ Ketu": 0.85,
    "♃ Júpiter": 0.96,
    "♂ Marte": 0.70,
}

AVG_SPEED = {
    "♄ Saturno": 0.033,
    "♃ Júpiter": 0.083,
    "♂ Marte": 0.52,
    "☊ Rahu": 0.052,
    "☋ Ketu": 0.052,
}

MACRO_RELEVANTES = [
    "♄ Saturno",
    "♃ Júpiter",
    "☊ Rahu",
    "☋ Ketu",
    "♂ Marte"
]

SIGNOS = [
    "Aries","Tauro","Géminis","Cáncer","Leo","Virgo",
    "Libra","Escorpio","Sagitario","Capricornio",
    "Acuario","Piscis"
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini",
    "Mrigashira","Ardra","Punarvasu","Pushya",
    "Ashlesha","Magha","Purva Phalguni",
    "Uttara Phalguni","Hasta","Chitra",
    "Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha",
    "Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada",
    "Revati"
]

DIAS_ES = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

REGENTE_DIA = {
    0: "☽ Luna",      # Lunes
    1: "♂ Marte",     # Martes
    2: "☿ Mercurio",  # Miércoles
    3: "♃ Júpiter",   # Jueves
    4: "♀ Venus",     # Viernes
    5: "♄ Saturno",   # Sábado
    6: "☉ Sol"        # Domingo
}

def jd(fecha):
    return swe.julday(fecha.year, fecha.month, fecha.day, 13.5)

# @st.cache_data
def obtener_posiciones(fecha):
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    j = jd(fecha)

    longitudes = {}
    filas = []

    for nombre, pid in PLANETAS.items():
        data = swe.calc_ut(j, pid, flags)[0]
        lon = data[0] % 360
        speed = data[3]

        longitudes[nombre] = lon

        filas.append({
            "Planeta": nombre,
            "Longitud": round(lon, 4),
            "Signo": SIGNOS[int(lon // 30)],
            "Grado": round(lon % 30, 2),
            "Velocidad": round(speed, 5),
            "Retrógrado": speed < 0
        })

    ketu = (longitudes["☊ Rahu"] + 180) % 360

    rahu_speed = [
        x["Velocidad"]
        for x in filas
        if x["Planeta"] == "☊ Rahu"
    ][0]

    filas.append({
        "Planeta": "☋ Ketu",
        "Longitud": round(ketu, 4),
        "Signo": SIGNOS[int(ketu // 30)],
        "Grado": round(ketu % 30, 2),
        "Velocidad": rahu_speed,
        "Retrógrado": rahu_speed < 0
    })

    return pd.DataFrame(filas)

# @st.cache_data
def obtener_luna(fecha):
    flags = swe.FLG_SIDEREAL
    j = jd(fecha)

    sol = swe.calc_ut(j, swe.SUN, flags)[0][0] % 360
    luna = swe.calc_ut(j, swe.MOON, flags)[0][0] % 360

    diff = (luna - sol) % 360

    nak_num = int(luna / (360 / 27))
    nak = NAKSHATRAS[nak_num]

    tithi = int(diff / 12)

    if tithi == 0:
        fase = "Luna nueva"
    elif 1 <= tithi <= 6:
        fase = "Creciente"
    elif tithi == 7:
        fase = "Cuarto creciente"
    elif 8 <= tithi <= 13:
        fase = "Creciente avanzada"
    elif tithi == 14 or tithi == 15:
        fase = "Luna llena"
    elif 16 <= tithi <= 21:
        fase = "Menguante"
    elif tithi == 22:
        fase = "Cuarto menguante"
    else:
        fase = "Menguante"

    return fase, nak

def signo_planeta(planeta, fecha):
    df = obtener_posiciones(fecha)
    lon = float(df[df["Planeta"] == planeta]["Longitud"].iloc[0])
    return int(lon // 30)

def longitud_planeta(planeta, fecha):
    df = obtener_posiciones(fecha)
    return float(df[df["Planeta"] == planeta]["Longitud"].iloc[0])

def velocidad_planeta(planeta, fecha):
    df = obtener_posiciones(fecha)
    return float(df[df["Planeta"] == planeta]["Velocidad"].iloc[0])

def buscar_entrada_signo(planeta, fecha):
    signo_actual = signo_planeta(planeta, fecha)
    f = fecha

    for _ in range(3000):
        prev = f - timedelta(days=1)

        if signo_planeta(planeta, prev) != signo_actual:
            return f

        f = prev

    return fecha

def buscar_salida_signo(planeta, fecha):
    signo_actual = signo_planeta(planeta, fecha)
    f = fecha

    for _ in range(3000):
        nxt = f + timedelta(days=1)

        if signo_planeta(planeta, nxt) != signo_actual:
            return nxt

        f = nxt

    return fecha

def buscar_pico_signo(planeta, entrada, salida):
    signo = signo_planeta(planeta, entrada)
    objetivo = signo * 30 + 15

    mejor_fecha = entrada
    mejor_dist = 999
    dias = max((salida - entrada).days, 1)

    for i in range(dias + 1):
        f = entrada + timedelta(days=i)
        lon = longitud_planeta(planeta, f)

        d = abs(lon - objetivo)
        d = min(d, 360 - d)

        if d < mejor_dist:
            mejor_dist = d
            mejor_fecha = f

    return mejor_fecha

def gauss_phase(fecha, entrada, pico, salida):
    if fecha < entrada or fecha > salida:
        return 0.0

    total = max((salida - entrada).days, 1)

    x = (fecha - entrada).days / total
    peak_x = (pico - entrada).days / total

    sigma = 0.23

    return math.exp(-((x - peak_x) ** 2) / (2 * sigma ** 2))

def speed_weight(planeta, speed):
    avg = AVG_SPEED.get(planeta, 0.05)
    ratio = abs(speed) / avg if avg else 1

    if ratio < 0.15:
        return 1.35
    elif ratio < 0.50:
        return 1.15
    elif ratio < 1.25:
        return 1.00

    return 0.80

def retro_weight(planeta, speed, retro):
    avg = AVG_SPEED.get(planeta, 0.05)

    station = max(0, 1 - min(abs(speed) / avg, 1))

    w = 1.0

    if retro:

        if planeta in ["☊ Rahu", "☋ Ketu"]:
            w *= 1.0

        elif planeta == "♄ Saturno":
            w *= 0.82

        elif planeta == "♃ Júpiter":
            w *= 0.90

        elif planeta == "♂ Marte":
            w *= 0.88

        elif planeta == "☿ Mercurio":
            w *= 0.94

        elif planeta == "♀ Venus":
            w *= 0.96

    w *= 1 + 0.35 * station

    return w

def buscar_movimientos(planeta, fecha):
    eventos = []

    inicio = fecha - timedelta(days=400)
    fin = fecha + timedelta(days=400)

    prev_speed = velocidad_planeta(planeta, inicio)
    prev_retro = prev_speed < 0

    f = inicio

    while f <= fin:
        speed = velocidad_planeta(planeta, f)
        retro = speed < 0

        if retro != prev_retro:
            eventos.append({
                "fecha": f,
                "tipo": "Retrógrado" if retro else "Directo"
            })

        prev_retro = retro
        f += timedelta(days=1)

    return eventos

# @st.cache_data
def datos_macro(fecha):
    df = obtener_posiciones(fecha)

    filas = []

    for planeta in MACRO_PLANETAS:
        base = df[df["Planeta"] == planeta].iloc[0]

        entrada = buscar_entrada_signo(planeta, fecha)
        salida = buscar_salida_signo(planeta, fecha)
        pico = buscar_pico_signo(planeta, entrada, salida)

        phase = gauss_phase(fecha, entrada, pico, salida)

        speed = float(base["Velocidad"])
        retro = bool(base["Retrógrado"])

        raw = (
            BASE_MACRO[planeta]
            * phase
            * speed_weight(planeta, speed)
            * retro_weight(planeta, speed, retro)
        )

        filas.append({
            "Planeta": planeta,
            "PesoRaw": raw,
            "Peso": 0,
            "Influencia": round(phase * 100, 1),
            "Estado": "Subiendo" if fecha < pico else "Bajando",
            "Entrada": entrada,
            "Pico": pico,
            "Salida": salida,
            "Signo": base["Signo"],
            "Grado": base["Grado"],
            "Velocidad": speed,
            "Retrógrado": retro,
            "Movimientos": buscar_movimientos(planeta, fecha)
        })

    total = sum(x["PesoRaw"] for x in filas)

    for x in filas:
        x["Peso"] = round((x["PesoRaw"] / total) * 100, 1) if total else 0

    return pd.DataFrame(filas).sort_values("Peso", ascending=False)

def calcular_bias_mercado(
    dia,
    macro,
    fase,
    nak,
    market_regime,
    score,
    nombre
):

    top1 = macro.iloc[0]["Planeta"]
    top2 = macro.iloc[1]["Planeta"]
    top3 = macro.iloc[2]["Planeta"]

    bias = "Neutral"

    # -------------------------
    # PLANETAS ALCISTAS
    # -------------------------

    alcistas = [
        "♃ Júpiter",
        "♀ Venus",
        "☉ Sol"
    ]

    # -------------------------
    # PLANETAS BAJISTAS
    # -------------------------

    bajistas = [
        "♄ Saturno",
        "☋ Ketu"
    ]

    # -------------------------
    # VOLÁTILES
    # -------------------------

    volatilidad = [
        "☊ Rahu",
        "♂ Marte"
    ]

    for p in [top1, top2, top3]:

        if p in alcistas:
            score += 2

        elif p in bajistas:
            score -= 2

        elif p in volatilidad:
            score -= 1

    # -------------------------
    # REGENTE DEL DÍA
    # -------------------------

    regente = REGENTE_DIA[dia.weekday()]

    if regente == top1:
        score += 3

    elif regente in [top2, top3]:
        score += 1

    # Afinidad especial

    if regente == "♀ Venus":
        score += 1

    if regente == "♃ Júpiter":
        score += 1

    if regente == "♄ Saturno":
        score -= 1

    if regente == "♂ Marte":
        score -= 1

    # -------------------------
    # FASE LUNAR
    # -------------------------

    if fase in [
        "Creciente",
        "Creciente avanzada",
        "Luna llena"
    ]:
        score += 1

    elif fase in [
        "Menguante",
        "Luna nueva"
    ]:
        score -= 1

    # -------------------------
    # NAKSHATRAS
    # -------------------------

    buenos = [
        "Rohini",
        "Pushya",
        "Revati",
        "Ashwini",
        "Uttara Bhadrapada",
        "Shravana",
        "Hasta"
    ]

    malos = [
        "Ardra",
        "Ashlesha",
        "Mula",
        "Jyeshtha",
        "Purva Bhadrapada",
        "Bharani"
    ]

    if nak in buenos:
        score += 2

    elif nak in malos:
        score -= 2

    # -------------------------
    # RESULTADO FINAL
    # -------------------------

    if score >= 80:

        if market_regime == "Bull":
            return "🚀 Momentum alcista"

        return "🟢 Alcista"

    elif score >= 65:

        if "Rahu" in nombre:
            return "⚡ Especulativo alcista"

        return "🟡 Ligeramente alcista"

    elif score <= 40:

        if market_regime == "Bear":
            return "🔻 Presión bajista"

        return "🔴 Bajista"

    elif score <= 55:
        return "🟠 Volátil / indeciso"

    return "⚪ Neutral"

def grafico_gauss(fecha_actual, entrada, pico, salida, titulo):
    fechas = []
    valores = []

    dias = max((salida - entrada).days, 1)

    for i in range(dias + 1):
        f = entrada + timedelta(days=i)
        fechas.append(f)
        valores.append(gauss_phase(f, entrada, pico, salida))

    actual = gauss_phase(fecha_actual, entrada, pico, salida)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=fechas,
        y=valores,
        mode="lines",
        fill="tozeroy"
    ))

    fig.add_trace(go.Scatter(
        x=[fecha_actual],
        y=[actual],
        mode="markers+text",
        text=["AHORA"],
        textposition="top center"
    ))

    fig.update_layout(
        title=titulo,
        template="plotly_dark",
        height=260,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig

# @st.cache_data
def calcular_conjunciones(fecha, orbe=12):

    df = obtener_posiciones(fecha)

    planetas = df[
        ["Planeta", "Longitud", "Signo", "Grado", "Retrógrado"]
    ].to_dict("records")

    conjunciones = []

    PESO_PLANETAS = {
        "♄ Saturno": 34,
        "☊ Rahu": 34,
        "☋ Ketu": 30,
        "♃ Júpiter": 26,
        "♂ Marte": 22,
        "☉ Sol": 18,
        "☿ Mercurio": 14,
        "♀ Venus": 16,
        "☽ Luna": 14,
    }

    PLANETAS_MACRO = [
        "♄ Saturno",
        "♃ Júpiter",
        "☊ Rahu",
        "☋ Ketu",
        "♂ Marte",
        "☉ Sol"
    ]

    PLANETAS_RAPIDOS = [
        "☿ Mercurio",
        "♀ Venus",
        "☽ Luna"
    ]

    ORBES = {
        "☉ Sol": 10,
        "☽ Luna": 10,
        "☿ Mercurio": 8,
        "♀ Venus": 8,
        "♂ Marte": 8,
        "♃ Júpiter": 9,
        "♄ Saturno": 10,
        "☊ Rahu": 11,
        "☋ Ketu": 11,
    }

    # =========================================================
    # CONJUNCIONES BASE
    # =========================================================

    for i in range(len(planetas)):

        for j in range(i + 1, len(planetas)):

            p1 = planetas[i]
            p2 = planetas[j]


            diff = abs(
                p1["Longitud"] - p2["Longitud"]
            )

            diff = min(diff, 360 - diff)

            orbe_actual = min(
                (
                    ORBES[p1["Planeta"]] +
                    ORBES[p2["Planeta"]]
                ) / 2,
                orbe
            )

            if diff > orbe_actual:
                continue

            precision = 1 - (diff / orbe_actual)

            angular_score = (precision ** 2) * 60

            peso1 = PESO_PLANETAS.get(p1["Planeta"], 5)
            peso2 = PESO_PLANETAS.get(p2["Planeta"], 5)

            score = angular_score + peso1 + peso2

            # =====================================================
            # CERCANÍA EXTREMA
            # =====================================================

            if diff <= 1:
                score += 25

            elif diff <= 3:
                score += 12

            # =====================================================
            # RETRÓGRADOS
            # =====================================================

            if p1["Retrógrado"]:
                score += 10

            if p2["Retrógrado"]:
                score += 10

            # =====================================================
            # LENTOS MACRO
            # =====================================================

            lentos_count = sum(
                1 for p in [p1["Planeta"], p2["Planeta"]]
                if p in PLANETAS_MACRO
            )

            if lentos_count == 2:
                score += 18

            # =====================================================
            # MISMO SIGNO
            # =====================================================

            mismo_signo = p1["Signo"] == p2["Signo"]

            if mismo_signo:
                score += 12

            else:
                if diff <= 3:
                    score += 6
                elif diff <= orbe_actual:
                    score -= 2
                else:
                    score -= 10

            # =====================================================
            # AMPLIFICADORES INTELIGENTES
            # =====================================================

            pares = [p1["Planeta"], p2["Planeta"]]

            # Mercurio amplifica narrativa
            if (
                "☿ Mercurio" in pares
                and any(
                    p in pares for p in
                    ["☉ Sol", "♄ Saturno", "☊ Rahu", "♂ Marte"]
                )
            ):
                score += 16

            # Luna con Rahu → euforia / FOMO

            if (
                "☽ Luna" in pares
                and "☊ Rahu" in pares
            ):
                score += 18

            # Luna con Marte → volatilidad emocional

            if (
                "☽ Luna" in pares
                and "♂ Marte" in pares
            ):
                score += 16

            # Luna con Saturno → presión emocional

            if (
                "☽ Luna" in pares
                and "♄ Saturno" in pares
            ):
                score += 10

            # Venus solo importa con macro
            if (
                "♀ Venus" in pares
                and any(
                    p in pares for p in
                    ["♃ Júpiter", "♄ Saturno", "☊ Rahu"]
                )
            ):
                score += 10

            # =====================================================
            # THRESHOLD DINÁMICO
            # =====================================================

            threshold = 34

            if lentos_count == 2:
                threshold = 48

            elif (
                p1["Planeta"] in PLANETAS_RAPIDOS
                and p2["Planeta"] in PLANETAS_RAPIDOS
            ):
                threshold = 20

            if any(p in PLANETAS_MACRO for p in pares):
                threshold = 40

            if score < threshold:
                continue

            # =====================================================
            # INTENSIDAD
            # =====================================================

            if score >= 90:
                intensidad = "Extrema"

            elif score >= 70:
                intensidad = "Alta"

            elif score >= 50:
                intensidad = "Media"

            else:
                intensidad = "Baja"

            # =====================================================
            # NATURALEZA
            # =====================================================

            contractivos = [
                "♄ Saturno",
                "☋ Ketu"
            ]

            expansivos = [
                "♃ Júpiter",
                "♀ Venus"
            ]

            tipo_score = 0

            for p in pares:

                if p in contractivos:
                    tipo_score -= 1

                if p in expansivos:
                    tipo_score += 1

            if tipo_score <= -1:
                naturaleza = "Contractiva"

            elif tipo_score >= 1:
                naturaleza = "Expansiva"

            else:
                naturaleza = "Mixta"

            # =====================================================
            # VOLATILIDAD
            # =====================================================

            if (
                "♂ Marte" in pares
                or "☊ Rahu" in pares
            ):
                volatilidad = "Alta"

            elif "☽ Luna" in pares:
                volatilidad = "Media-Alta"

            else:
                volatilidad = "Media"

            # =====================================================
            # DURACIÓN
            # =====================================================

            if lentos_count == 2:
                duracion = "Largo plazo"

            elif lentos_count == 1:
                duracion = "Medio plazo"

            else:
                duracion = "Corto plazo"

            conjunciones.append({

                "Planeta 1": p1["Planeta"],
                "Planeta 2": p2["Planeta"],

                "Retro1": p1["Retrógrado"],
                "Retro2": p2["Retrógrado"],

                "Orbe": round(diff, 2),

                "Score": round(score, 1),

                "Intensidad": intensidad,

                "Naturaleza": naturaleza,

                "Volatilidad": volatilidad,

                "Duración": duracion,

                "Signo": (
                    p1["Signo"]
                    if mismo_signo
                    else "Entre signos"
                )
            })

    # =========================================================
    # DETECCIÓN DE STELLIUMS
    # =========================================================

    stelliums = []

    usados = set()

    for p in planetas:

        grupo = []

        for q in planetas:

            diff = abs(
                p["Longitud"] - q["Longitud"]
            )

            diff = min(diff, 360 - diff)

            if diff <= 8:
                grupo.append(q["Planeta"])

        grupo = sorted(set(grupo))

        if len(grupo) >= 3:

            clave = tuple(grupo)

            if clave not in usados:

                usados.add(clave)

                stelliums.append({
                    "tipo": "Stellium",
                    "planetas": grupo
                })

    if len(conjunciones) == 0:
        return pd.DataFrame(), stelliums

    return (
        pd.DataFrame(conjunciones)
        .sort_values("Score", ascending=False),
        stelliums
    )

st.markdown("""
<h1 style="
    color:white;
    font-size:58px;
    margin-bottom:0;
">
    Astro Finance Tool
</h1>

<p style="
    color:#cccccc;
    font-size:18px;
    margin-top:-10px;
">
    Swiss Ephemeris · Sidéreo Lahiri
</p>
""", unsafe_allow_html=True)

col_fecha, _ = st.columns([1, 20])

with col_fecha:
    fecha = st.date_input(
    "Selecciona fecha",
    datetime.utcnow(),
    format="DD/MM/YYYY"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Dashboard",
    "Macro",
    "Calendario Lunar",
    "Conjunciones",
    "Forecast Semanal"
    
])

with tab1:

    df = obtener_posiciones(fecha)

    st.subheader("Posiciones planetarias")

    st.dataframe(
        df,
        use_container_width=True
    )

with tab2:

    macro = datos_macro(fecha)

    cols = st.columns(len(macro))

    for i, (_, row) in enumerate(macro.iterrows()):

        with cols[i]:

            with st.container(border=True, key=f"planet_card_{i}"):

                nombre_limpio = (
                    row["Planeta"]
                    .replace("♄ ", "")
                    .replace("☊ ", "")
                    .replace("☋ ", "")
                    .replace("♃ ", "")
                    .replace("♂ ", "")
                    .lower()
                )

                posibles = [
                    f"assets/{nombre_limpio}.png",
                    f"assets/{nombre_limpio}.jpg",
                    f"assets/{nombre_limpio}.webp",
                    "assets/jupiter.png" if "Júpiter" in row["Planeta"] else "",
                ]

                imagen = next(
                    (p for p in posibles if p and os.path.exists(p)),
                    None
                )

                if imagen:
                    st.image(imagen, width=150)

                st.markdown(f"## {row['Planeta']}")

                st.progress(row["Peso"] / 100)

                st.metric(
                    "Peso Macro",
                    f"{row['Peso']}%"
                )

                estado_color = "#00ff99" if row["Estado"] == "Subiendo" else "#ff5555"

                st.markdown(
                    f"""
                    <div style="
                        font-size:18px;
                        margin-bottom:8px;
                        color:white;
                    ">
                        Estado:
                        <span style="
                            color:{estado_color};
                            font-weight:700;
                        ">
                            {row['Estado']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                

                if row["Retrógrado"]:
                    st.markdown("""
                    <div style="
                        background: rgba(255,0,0,0.18);
                        border: 1px solid rgba(255,80,80,0.35);
                        color: #ff6b6b;
                        padding: 12px;
                        border-radius: 12px;
                        font-weight: 600;
                        text-align: center;
                    ">
                    🔴 Retrógrado
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="
                        background: rgba(0,255,120,0.12);
                        border: 1px solid rgba(0,255,120,0.25);
                        color: #00ff99;
                        padding: 12px;
                        border-radius: 12px;
                        font-weight: 600;
                        text-align: center;
                    ">
                    🟢 Directo
                    </div>
                    """, unsafe_allow_html=True)

                fig = grafico_gauss(
                    fecha,
                    row["Entrada"],
                    row["Pico"],
                    row["Salida"],
 		    f"{row['Planeta']} en {row['Signo']}"
                )

                st.plotly_chart(
                    fig,
                    width="stretch"
                )

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.markdown(
                        f"""
                        <div style="
                            text-align:center;
                            color:#7CFFB2;
                            font-size:14px;
                            margin-top:-10px;
                        ">
                            🟢 Entrada<br>
                            <b>{row['Entrada'].strftime('%d-%m-%Y')}</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col_b:
                    st.markdown(
                        f"""
                        <div style="
                            text-align:center;
                            color:#FFB347;
                            font-size:14px;
                            margin-top:-10px;
                        ">
                            🔥 Pico<br>
                            <b>{row['Pico'].strftime('%d-%m-%Y')}</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col_c:
                    st.markdown(
                        f"""
                        <div style="
                            text-align:center;
                            color:#B0B0B0;
                            font-size:14px;
                            margin-top:-10px;
                        ">
                            ⚫ Salida<br>
                            <b>{row['Salida'].strftime('%d-%m-%Y')}</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )



                st.markdown(
                    "<div style='height:28px'></div>",
                    unsafe_allow_html=True
                )

                movimientos_futuros = [
                    m for m in row["Movimientos"]
                    if m["fecha"] >= fecha
                ]

                if movimientos_futuros:

                    st.markdown("""
                    <div style="
                        color:white;
                        font-size:18px;
                        font-weight:700;
                        margin-bottom:14px;
                    ">
                        Movimientos futuros:
                    </div>
                    """, unsafe_allow_html=True)

                    for mov in movimientos_futuros:

                        if mov["tipo"] == "Retrógrado":
                            color = "#ff4d4d"
                            texto = "Retrógrado"
                            icono = "↩"
                        else:
                            color = "#00ff99"
                            texto = "Directo"
                            icono = "↪"

                        st.markdown(
                            f"""
                            <div style="
                                margin-bottom:10px;
                                color:white;
                                font-size:16px;
                            ">
                                {icono}
                                <span style="
                                    color:{color};
                                    font-weight:800;
                                ">
                                    {texto}
                                </span>
                                <span style="color:white;">
                                    → {mov['fecha'].strftime('%d-%m-%Y')}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    st.divider()

    st.subheader("Dominancia Macro")

    st.dataframe(
        macro[[
            "Planeta",
            "Peso",
            "Influencia",
            "Estado",
            "Entrada",
            "Pico",
            "Salida",
            "Signo",
            "Grado",
            "Velocidad",
            "Retrógrado"
        ]],
        width="stretch"
    )

with tab3:

    
    ICONOS_FASE = {
        "Luna nueva": "🌑",
        "Creciente": "🌒",
        "Cuarto creciente": "🌓",
        "Creciente avanzada": "🌔",
        "Luna llena": "🌕",
        "Menguante": "🌖",
        "Cuarto menguante": "🌗",
    }

    año = fecha.year
    mes = fecha.month

    inicio = datetime(año, mes, 1)
    primer_dia_semana = inicio.weekday()

    if mes == 12:
        fin = datetime(año + 1, 1, 1)
    else:
        fin = datetime(año, mes + 1, 1)

    dias_semana = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

    dias_html = ""

    f = inicio


    # ESPACIOS VACÍOS INICIALES

    for _ in range(primer_dia_semana):

        dias_html += """
        <div style="
            background:transparent;
            border-radius:16px;
            min-height:110px;
        ">
        </div>
        """

    while f < fin:

        fase, nak = obtener_luna(f)

        icono = ICONOS_FASE.get(fase, "🌙")

        buenos = [
            "Rohini","Punarvasu","Pushya","Hasta",
            "Uttara Phalguni","Anuradha","Shravana",
            "Uttara Ashadha","Uttara Bhadrapada",
            "Revati","Ashwini"
        ]

        malos = [
            "Ardra","Ashlesha","Jyeshtha",
            "Mula","Purva Bhadrapada","Bharani"
        ]

        if nak in buenos:
            color = "#0f9d58"

        elif nak in malos:
            color = "#d93025"

        else:
            color = "#c58b00"

        dias_html += f"""
        <div style="
            background:{color};
            border-radius:16px;
            padding:10px;
            min-height:110px;
            color:white;
            box-shadow:0 0 12px rgba(0,0,0,0.35);
            border:1px solid rgba(255,255,255,0.08);
        ">

            <div style="
                font-size:14px;
                opacity:0.9;
                margin-bottom:8px;
                font-weight:700;
            ">
                {f.day}
            </div>

            <div style="
                display:flex;
                align-items:center;
                gap:8px;
                margin-bottom:8px;
            ">

                <div style="
                    font-size:26px;
                ">
                    {icono}
                </div>

                <div style="
                    font-size:11px;
                    color:white;
                    font-weight:700;
                    opacity:0.92;
                    line-height:1.1;
                ">
                    {fase}
                </div>

            </div>

            <div style="
                font-size:13px;
                font-weight:700;
                line-height:1.25;
            ">
                {nak}
            </div>

        </div>
        """

        f += timedelta(days=1)

    semana_html = ""

    for d in dias_semana:

        semana_html += f"""
        <div style="
            text-align:center;
            color:#cccccc;
            font-weight:700;
            padding:10px 0;
            font-size:15px;
        ">
            {d}
        </div>
        """

    html = f"""
    <html>
    <body style="
        margin:0;
        padding:0;
        background:transparent;
        font-family:sans-serif;
    ">

    <div style="
        background:rgba(5,10,20,0.82);
        padding:28px;
        border-radius:24px;
        border:1px solid rgba(255,215,100,0.15);
        max-width:1600px;
        margin:auto;
    ">

        <div style="
            color:white;
            font-size:30px;
            font-weight:800;
            margin-bottom:24px;
        ">
            🌙 Calendario Lunar · {mes}/{año}
        </div>

        <div style="
            display:grid;
            grid-template-columns:repeat(7, 1fr);
            gap:12px;
        ">
            {semana_html}
            {dias_html}
        </div>

    </div>

    </body>
    </html>
    """

    left_space, center, right_space = st.columns([0.2, 1, 0.2])

    with center:

        components.html(
            html,
            height=900,
            scrolling=True
        )

    left_space, center, right_space = st.columns([0.2, 1, 0.2])

    with center:

        st.markdown("""
        <div style="
            color:white;
            font-size:30px;
            font-weight:800;
            margin-top:30px;
            margin-bottom:18px;
            text-align:center;
        ">
            Guía rápida de Nakshatras
        </div>
        """, unsafe_allow_html=True)

        REGENTES_NAKSHATRA = {

    "Rohini": "Luna",
    "Punarvasu": "Júpiter",
    "Pushya": "Saturno",
    "Hasta": "Luna",
    "Uttara Phalguni": "Sol",
    "Anuradha": "Saturno",
    "Shravana": "Luna",
    "Uttara Ashadha": "Sol",
    "Uttara Bhadrapada": "Saturno",
    "Revati": "Mercurio",
    "Ashwini": "Ketu",

    "Mrigashira": "Marte",
    "Krittika": "Sol",
    "Swati": "Rahu",
    "Chitra": "Marte",
    "Vishakha": "Júpiter",
    "Purva Ashadha": "Venus",
    "Dhanishta": "Marte",
    "Shatabhisha": "Rahu",
    "Magha": "Ketu",
    "Purva Phalguni": "Venus",

    "Ardra": "Rahu",
    "Ashlesha": "Mercurio",
    "Jyeshtha": "Mercurio",
    "Mula": "Ketu",
    "Bharani": "Venus",
    "Purva Bhadrapada": "Júpiter",
}

    GUIA = [
        ("🟢", "Rohini", "Crecimiento", "Breakouts que funcionan"),
        ("🟢", "Punarvasu", "Recuperación", "Confirmaciones / rebotes"),
        ("🟢", "Pushya", "Expansión estable", "Mejor para añadir fuerte"),
        ("🟢", "Hasta", "Control", "Entradas limpias"),
        ("🟢", "Uttara Phalguni", "Consolidación", "Continuación tendencia"),
        ("🟢", "Anuradha", "Cooperación", "Subidas ordenadas"),
        ("🟢", "Shravana", "Estructura", "Movimientos consistentes"),
        ("🟢", "Uttara Ashadha", "Victoria", "Tendencias fuertes"),
        ("🟢", "Uttara Bhadrapada", "Estabilidad", "Mantener posiciones"),
        ("🟢", "Revati", "Fluidez", "Final de tendencias limpias"),
        ("🟢", "Ashwini", "Inicio rápido", "Entradas veloces"),

        ("🟡", "Mrigashira", "Búsqueda", "Breakouts dudosos"),
        ("🟡", "Krittika", "Corte / decisón", "Rupturas, necesita confirmación"),
        ("🟡", "Swati", "Independencia", "Volátil pero tradeable"),
        ("🟡", "Chitra", "Diseño", "Movimientos técnicos"),
        ("🟡", "Vishakha", "Objetivo", "Puede acelerar"),
        ("🟡", "Purva Ashadha", "Impulso", "Puede fallar"),
        ("🟡", "Dhanishta", "Ritmo", "Momentum irregular"),
        ("🟡", "Shatabhisha", "Corrección", "Reversals posibles"),
        ("🟡", "Magha", "Autoridad", "Movimientos bruscos"),
        ("🟡", "Purva Phalguni", "Relajación", "Poco follow-through"),

        ("🔴", "Ardra", "Tormenta", "Volatilidad / fake breakouts"),
        ("🔴", "Ashlesha", "Confusión", "Manipulación"),
        ("🔴", "Jyeshtha", "Presión", "Movimientos erráticos"),
        ("🔴", "Mula", "Destrucción", "Caídas fuertes"),
        ("🔴", "Bharani", "Presión", "Evitar entradas"),
        ("🔴", "Purva Bhadrapada", "Extremos", "Movimientos bruscos"),
    ]

    html_guia = f"""
    <div style="
        background:linear-gradient(
            135deg,
            rgba(8,15,28,0.96),
            rgba(15,25,45,0.92)
        );
        border-radius:22px;
        padding:14px;
        border:1px solid rgba(255,215,100,0.12);
        backdrop-filter:blur(10px);
        box-shadow:0 0 24px rgba(255,215,100,0.08);
        max-width:1200px;
        margin:auto;
    ">

    <table style="
        width:100%;
        border-collapse:collapse;
        color:white;
        font-size:16px;
    ">

    <tr style="
        background:rgba(255,215,100,0.12);
    ">
        <th style="padding:10px;text-align:left;">Tipo</th>
        <th style="padding:10px;text-align:left;">Nakshatra</th>
        <th style="padding:10px;text-align:left;">Regente</th>
        <th style="padding:10px;text-align:left;">Energía</th>
        <th style="padding:10px;text-align:left;">Uso en trading</th>
    </tr>
    """

    for tipo, nak, energia, uso in GUIA:

        regente = REGENTES_NAKSHATRA.get(nak, "-")

        color = "#0f9d58"

        if tipo == "🟡":
            color = "#c58b00"

        elif tipo == "🔴":
            color = "#d93025"

        html_guia += f"""
        <tr style="
            border-bottom:1px solid rgba(255,255,255,0.06);
        ">
            <td style="
                padding:10px;
                color:{color};
                font-size:18px;
            ">
                {tipo}
            </td>

            <td style="
                padding:10px;
                font-weight:700;
                color:white;
            ">
                {nak}
            </td>

            <td style="
                padding:10px;
                color:#ffd166;
                font-weight:700;
            ">
                {regente}
            </td>

            <td style="
                padding:10px;
                color:#cccccc;
            ">
                {energia}
            </td>

            <td style="
                padding:10px;
                color:#eeeeee;
            ">
                {uso}
            </td>
        </tr>
        """

    html_guia += """
    </table>
    </div>
    """

    left_space, center, right_space = st.columns([0.55, 1, 0.55])

    with center:

        components.html(
            html_guia,
            height=1400,
            scrolling=False
        )

with tab4:

    st.subheader("☌ Conjunciones Planetarias")

    orbe = st.slider(
        "Orbe de conjunción",
        min_value=1,
        max_value=20,
        value=15
    )

    conj, stelliums = calcular_conjunciones(fecha, orbe)

    if conj.empty:

        st.info("No hay conjunciones relevantes para esta fecha.")

    else:
        if stelliums:

            st.markdown("""
            <div style="
                text-align:center;
                color:white;
                font-size:40px;
                font-weight:800;
                margin-top:20px;
                margin-bottom:18px;
            ">
                ✨ Stelliums detectados
            </div>
            """, unsafe_allow_html=True)

            for s in stelliums:

                left_space, center, right_space = st.columns([0.9, 0.6, 0.9])

                with center:

                    st.markdown(f"""
                    <div style="
                        background:rgba(20,60,120,0.45);
                        border:1px solid rgba(120,180,255,0.18);
                        border-radius:14px;
                        padding:14px;
                        text-align:center;
                        color:#7ec8ff;
                        font-size:24px;
                        font-weight:800;
                        margin-bottom:24px;
                    ">
                        {' · '.join(s['planetas'])}
                    </div>
                    """, unsafe_allow_html=True)

        left, mid, right = st.columns([0.25, 1, 0.25])

        with mid:
            cols = st.columns(2, gap="small")

            for i, (_, row) in enumerate(conj.iterrows()):

                with cols[i % 2]:

                    with st.container(key=f"conj_card_{i}"):

                        p1 = row["Planeta 1"]
                        p2 = row["Planeta 2"]

                        archivo1 = (
                            p1.split(" ", 1)[1]
                            .lower()
                            .replace("ú", "u")
                        )

                        archivo2 = (
                            p2.split(" ", 1)[1]
                            .lower()
                            .replace("ú", "u")
                        )

                        img1 = f"assets/{archivo1}.png"
                        img2 = f"assets/{archivo2}.png"

                        col1, col2, col3 = st.columns([1, 0.18, 1])

                    # ---------------- LEFT ----------------

                    with col1:

                        if os.path.exists(img1):
                            st.image(img1, width=140)

                        st.markdown(f"## {p1}")

                        if row["Retro1"]:
                            st.error("🔴 Retrógrado")
                        else:
                            st.success("🟢 Directo")

                        st.write(f"**Orbe:** {row['Orbe']}°")
                        st.write(f"**Signo:** {row['Signo']}")

                        if row["Intensidad"] == "Extrema":
                            intensidad_color = "🔴"

                        elif row["Intensidad"] == "Alta":
                            intensidad_color = "🟠"

                        elif row["Intensidad"] == "Media":
                            intensidad_color = "🟡"

                        else:
                            intensidad_color = "⚪"

                        st.info(f"""
                        {intensidad_color} Intensidad: {row['Intensidad']}

                        ⚡ Score Macro: {row['Score']}

                        🌊 Naturaleza: {row['Naturaleza']}

                        📈 Volatilidad: {row['Volatilidad']}

                        🕰 Duración: {row['Duración']}
                        """)

                    # ---------------- CENTER ----------------

                    with col2:

                        st.markdown(
                            """
                            <div style="
                                text-align:center;
                                font-size:60px;
                                margin-top:60px;
                                color:#ffd166;
                            ">
                                ☌
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # ---------------- RIGHT ----------------

                    with col3:

                        if os.path.exists(img2):
                            st.image(img2, width=140)

                        st.markdown(f"## {p2}")

                        if row["Retro2"]:
                            st.error("🔴 Retrógrado")
                        else:
                            st.success("🟢 Directo")

    st.divider()

    st.subheader("🜂 Rueda Zodiacal")

    df_zodiaco = obtener_posiciones(fecha)

    fig = go.Figure()

    fig.add_shape(
        type="circle",
        x0=-1,
        y0=-1,
        x1=1,
        y1=1,
        fillcolor="rgba(5,10,20,0.88)",
        line=dict(
            color="rgba(255,215,100,0.20)",
            width=2
        ),
        layer="below"
    )

    # CÍRCULOS
    for r in [0.55, 0.75]:
        fig.add_shape(
            type="circle",
            x0=-r,
            y0=-r,
            x1=r,
            y1=r,
            line=dict(color="rgba(255,215,100,0.22)", width=1),
            fillcolor="rgba(0,0,0,0)"
        )

    # DIVISIONES DE SIGNOS
    for i in range(12):
        ang = math.radians(90 - i * 30)

        fig.add_shape(
            type="line",
            x0=0,
            y0=0,
            x1=math.cos(ang),
            y1=math.sin(ang),
            line=dict(color="rgba(255,255,255,0.12)", width=1)
        )

    # SIGNOS
    signos_simbolos = [
        "♈ Aries", "♉ Tauro", "♊ Géminis", "♋ Cáncer",
        "♌ Leo", "♍ Virgo", "♎ Libra", "♏ Escorpio",
        "♐ Sagitario", "♑ Capricornio", "♒ Acuario", "♓ Piscis"
    ]

    for i, signo in enumerate(signos_simbolos):
        ang = math.radians(90 - i * 30 - 15)

        fig.add_annotation(
            x=0.93 * math.cos(ang),
            y=0.93 * math.sin(ang),
            text=signo,
            showarrow=False,
            font=dict(size=14, color="#ffdf80")
        )

    # PLANETAS CON IMÁGENES
    mapa_imgs = {
        "☉ Sol": "assets/sol.png",
        "☽ Luna": "assets/luna.png",
        "♂ Marte": "assets/marte.png",
        "☿ Mercurio": "assets/mercurio.png",
        "♃ Júpiter": "assets/jupiter.png",
        "♀ Venus": "assets/venus.png",
        "♄ Saturno": "assets/saturno.png",
        "☊ Rahu": "assets/rahu.png",
        "☋ Ketu": "assets/ketu.png",
    }

    for idx, (_, row) in enumerate(df_zodiaco.iterrows()):

        planeta = row["Planeta"]
        lon = row["Longitud"]

        ang = math.radians(90 - lon)

        radio = 0.66 + (idx % 3) * 0.045

        x = radio * math.cos(ang)
        y = radio * math.sin(ang)

        ruta = mapa_imgs.get(planeta)

        if ruta and os.path.exists(ruta):

            fig.add_layout_image(
                dict(
                    source=f"data:image/png;base64,{get_base64(ruta)}",
                    x=x,
                    y=y,
                    xref="x",
                    yref="y",
                    sizex=0.18,
                    sizey=0.18,
                    xanchor="center",
                    yanchor="middle",
                    layer="above"
                )
            )

        estado = "℞" if row["Retrógrado"] else "•"

        color_estado = "#ff4d4d" if row["Retrógrado"] else "#00ff99"

        texto_planeta = (
            f"{planeta}<br>"
            f"<span style='color:#ffd166;font-size:11px'>"
            f"{row['Signo']} {row['Grado']}°"
            f"</span><br>"
            f"<span style='color:{color_estado};font-size:10px'>"
            f"{estado} {'Retrógrado' if row['Retrógrado'] else 'Directo'}"
            f"</span>"
        )

        fig.add_annotation(
            x=x,
            y=y - 0.12,
            text=texto_planeta,
            showarrow=False,
            align="center",
            font=dict(size=12, color="white")
        )

    fig.update_layout(
        height=720,
        template="plotly_dark",
        dragmode="pan",
        uirevision=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(
            visible=False,
            range=[-1.15, 1.15],
            scaleanchor="y"
        ),
        yaxis=dict(
            visible=False,
            range=[-1.15, 1.15]
        ),
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "modeBarButtonsToRemove": [
                "select2d",
                "lasso2d"
            ]
        }
    )

    MARKET_REGIMES = [
    "Bull",
    "Bear",
    "Sideways",
    "Volatile"
]

with tab5:

    st.markdown("""
    <div style="
        text-align:center;
        color:white;
        font-size:42px;
        font-weight:800;
        margin-bottom:30px;
    ">
        Forecast Semanal
    </div>
    """, unsafe_allow_html=True)

    market_regime = st.selectbox(
        "Fase de mercado",
        MARKET_REGIMES,
        index=0
    )

    cards_html = ""

    for i in range(7):

        dia = fecha + timedelta(days=i)

        weekend = dia.weekday() >= 5

        macro = datos_macro(dia)
        top = macro.iloc[0]

        signo = top["Signo"]

        fase, nak = obtener_luna(dia)
        conj_dia, _ = calcular_conjunciones(dia, 8)

        BUENOS = [
            "Rohini","Punarvasu","Pushya","Hasta",
            "Uttara Phalguni","Anuradha","Shravana",
            "Uttara Ashadha","Uttara Bhadrapada",
            "Revati","Ashwini"
        ]

        MALOS = [
            "Ardra","Ashlesha","Jyeshtha",
            "Mula","Bharani","Purva Bhadrapada"
        ]

        if nak in BUENOS:
            nak_color = "#57ff8a"

        elif nak in MALOS:
            nak_color = "#ff5c5c"

        else:
            nak_color = "#ffd166"

        retro_bonus = 0
        dignidad_bonus = 0
        direction_score = 0
        volatility_score = 0
        speculative_score = 0

        # ==================================================
        # LUNA
        # ==================================================

        if fase in ["Creciente", "Creciente avanzada"]:
            direction_score += 12

        elif fase in ["Menguante", "Luna nueva"]:
            direction_score -= 10

        elif fase == "Luna llena":
            volatility_score += 16

        elif fase == "Cuarto creciente":
            volatility_score += 8

        elif fase == "Cuarto menguante":
            volatility_score += 10

        # ==================================================
        # NAKSHATRAS
        # ==================================================

        NAK_EXPANSIVOS = [
            "Rohini",
            "Pushya",
            "Hasta",
            "Revati",
            "Uttara Phalguni"
        ]

        NAK_VOLATILES = [
            "Ashlesha",
            "Ardra",
            "Mula",
            "Purva Bhadrapada",
            "Shatabhisha"
        ]

        NAK_CONTRACTIVOS = [
            "Bharani",
            "Jyeshtha",
            "Magha"
        ]

        if nak in NAK_EXPANSIVOS:
            direction_score += 14

        if nak in NAK_VOLATILES:
            volatility_score += 20
            speculative_score += 12

        if nak in NAK_CONTRACTIVOS:
            direction_score -= 12

        # ==================================================
        # DÍA SEMANAL
        # ==================================================

        weekday = dia.weekday()

        # Martes → Marte

        if weekday == 1:
            volatility_score += 10

        # Jueves → Júpiter

        elif weekday == 3:
            direction_score += 8

        # Sábado → Saturno

        elif weekday == 5:
            direction_score -= 8

        # ==================================================
        # RETRÓGRADOS SECUNDARIOS
        # ==================================================

        # ==================================================
        # MERCURIO
        # ==================================================

        if weekday == 2:
            speculative_score += 4

        # ==================================================
        # VENUS
        # ==================================================

        if weekday == 4:
            direction_score += 3
            volatility_score -= 2

        for _, p in macro.iterrows():

            planeta = p["Planeta"]

            if not p["Retrógrado"]:
                continue

            if "Saturno" in planeta:
                direction_score -= 12

            elif "Júpiter" in planeta:
                direction_score -= 6

            elif "Marte" in planeta:
                volatility_score += 14

            elif "Mercurio" in planeta:
                speculative_score += 10

        EXALTACIONES = {
            "Sol": "Aries",
            "Luna": "Tauro",
            "Marte": "Capricornio",
            "Mercurio": "Virgo",
            "Júpiter": "Cáncer",
            "Venus": "Piscis",
            "Saturno": "Libra",
        }

        DEBILITADOS = {
            "Sol": "Libra",
            "Luna": "Escorpio",
            "Marte": "Cáncer",
            "Mercurio": "Piscis",
            "Júpiter": "Capricornio",
            "Venus": "Virgo",
            "Saturno": "Aries",
        }

        nombre = top["Planeta"]
        planeta_limpio = nombre.split(" ", 1)[1]

        if top["Retrógrado"] and planeta_limpio not in ["Rahu", "Ketu"]:

            if "Saturno" in nombre:
                retro_bonus -= 12

            elif "Júpiter" in nombre:
                retro_bonus -= 10

            elif "Mercurio" in nombre:
                retro_bonus -= 8

            elif "Venus" in nombre:
                retro_bonus -= 6

            elif "Marte" in nombre:
                retro_bonus -= 7

        if (
            planeta_limpio in EXALTACIONES
            and signo == EXALTACIONES[planeta_limpio]
        ):
            dignidad_bonus += 12

        elif (
            planeta_limpio in DEBILITADOS
            and signo == DEBILITADOS[planeta_limpio]
        ):
            dignidad_bonus -= 12

        conj_bonus = 0

        for _, c in conj_dia.iterrows():    

            score_conj = c["Score"]

            if c["Naturaleza"] == "Expansiva":
                conj_bonus += score_conj * 0.12
                
            elif c["Naturaleza"] == "Contractiva":
                conj_bonus -= score_conj * 0.10

            else:
                conj_bonus += score_conj * 0.04

        conj_bonus = max(min(conj_bonus, 18), -18)

        for _, c in conj_dia.iterrows():

            pares = [
                c["Planeta 1"],
                c["Planeta 2"]
            ]

            macro_planetas = macro.head(5)["Planeta"].tolist()

            if not any(p in pares for p in macro_planetas):
                continue

            fuerza = c["Score"] / 45

            # RAHU

            if "☊ Rahu" in pares:
                speculative_score += 30 * fuerza
                volatility_score += 18 * fuerza

            # MARTE

            if "♂ Marte" in pares:
                volatility_score += 22 * fuerza

            # SATURNO

            if "♄ Saturno" in pares:
                direction_score -= 14 * fuerza

            # JÚPITER

            if "♃ Júpiter" in pares:
                direction_score += 16 * fuerza

            # NATURALEZA

            if c["Naturaleza"] == "Contractiva":
                direction_score -= 12 * fuerza

            elif c["Naturaleza"] == "Expansiva":
                direction_score += 12 * fuerza


        regime_bonus = 0

        if "Rahu" in nombre:

            speculative_score += 14
            volatility_score += 10

            if market_regime == "Bull":
                regime_bonus += 10

            elif market_regime == "Bear":
                regime_bonus -= 12

            elif market_regime == "Sideways":
                regime_bonus += 2

            elif market_regime == "Volatile":
                regime_bonus += 6


        elif "Júpiter" in nombre:

            direction_score += 24

            if market_regime == "Bull":
                regime_bonus += 8

            elif market_regime == "Bear":
                regime_bonus -= 4


        elif "Saturno" in nombre:

            direction_score -= 26

            if market_regime == "Bear":
                regime_bonus -= 10

            elif market_regime == "Bull":
                regime_bonus -= 3


        elif "Marte" in nombre:

            volatility_score += 14

            if market_regime == "Bull":
                regime_bonus += 5

            elif market_regime == "Bear":
                regime_bonus -= 8

        direction_score = max(min(direction_score, 100), -100)

        volatility_score = max(min(volatility_score, 100), 0)

        speculative_score = max(min(speculative_score, 100), 0)

        score = round(
            top["Peso"] +
            top["Influencia"] * 0.35 +
            retro_bonus +
            conj_bonus +
            dignidad_bonus +
            regime_bonus +

            (direction_score * 0.42) -

            (volatility_score * 0.08) +

            (speculative_score * 0.02)
        )
        
        bias_market = calcular_bias_mercado(
            dia,
            macro,
            fase,
            nak,
            market_regime,
            score,
            nombre
        )

        if score >= 75:
            bias = "🔥 Expansivo"

        elif score >= 55:
            bias = "⚡ Volátil"

        else:
            bias = "🧊 Contractivo"

        glow = (
            "0 0 24px rgba(180,120,255,0.16)"
            if weekend
            else "0 0 24px rgba(255,215,100,0.10)"
        )

        fondo = (
            "rgba(35,25,60,0.92)"
            if weekend
            else "rgba(5,10,20,0.92)"
        )

        card_html = f"""
        <div style="
            flex:1;
            background:{fondo};
            border-radius:20px;
            padding:18px 14px;
            border:1px solid rgba(255,215,100,0.22);
            box-shadow:{glow};
            min-height:420px;
            text-align:center;
            backdrop-filter:blur(10px);
        ">

            <!-- DÍA -->
            <div style="
                color:white;
                font-size:15px;
                font-weight:800;
                letter-spacing:1px;
                margin-bottom:4px;
            ">
                {dia.strftime('%A').upper()}
            </div>

            <div style="
                color:#cccccc;
                font-size:13px;
                margin-bottom:24px;
            ">
                {dia.strftime('%d/%m')}
            </div>

            <!-- PLANETA -->
            <div style="
                font-size:62px;
                margin-bottom:10px;
                color:#ffd166;
            ">
                {top["Planeta"].split()[0]}
            </div>

            <!-- DOMINANTE -->
            <div style="
                color:#bbbbbb;
                font-size:14px;
                margin-bottom:4px;
            ">
                Dominante
            </div>

            <div style="
                color:white;
                font-size:30px;
                font-weight:800;
                margin-bottom:18px;
            ">
                {top["Planeta"].split(" ",1)[1]}
            </div>

            <!-- SECUNDARIOS -->
            <div style="
                color:#bbbbbb;
                font-size:15px;
                line-height:1.6;
                margin-bottom:18px;
            ">
                {macro.iloc[1]["Planeta"]}<br>
                {macro.iloc[2]["Planeta"]}
            </div>

            <!-- LUNA -->
            <div style="
                margin-bottom:18px;
                padding:12px;
                border-radius:14px;
                background:rgba(255,255,255,0.04);
            ">

                <div style="
                    color:#ffd166;
                    font-size:14px;
                    font-weight:700;
                    margin-bottom:6px;
                ">
                    🌙 {fase}
                </div>

                <div style="
                    color:{nak_color};
                    font-size:14px;
                    font-weight:700;
                ">
                    {nak}
                </div>
            </div>
            
            <!-- SCORE -->
            <div style="
                color:#57ff8a;
                font-size:58px;
                font-weight:900;
                line-height:1;
                margin-bottom:14px;
            ">
                {score}
            </div>
            
            <!-- SCORES -->

            <div style="
                margin-bottom:18px;
                text-align:center;
                padding:12px;
                border-radius:14px;
                background:rgba(255,255,255,0.04);
                line-height:1.9;
                color:white;
                font-size:16px;
                font-weight:700;
            ">

                <div>
                    📈 Dirección:
                    <span style="
                        color:{
                            '#57ff8a' if direction_score > 20
                            else '#ff5c5c' if direction_score < -20
                            else '#ffd166'
                        };
                        font-weight:900;
                        text-shadow:0 0 8px rgba(255,255,255,0.18);
                    ">
                        {int(direction_score)}
                    </span>
                </div>

                <div>
                    ⚡ Volatilidad:
                    <span style="
                        color:#ffb347;
                        font-weight:900;
                        text-shadow:0 0 8px rgba(255,255,255,0.18);
                    ">
                        {int(volatility_score)}
                    </span>
                </div>

                <div>
                    🧠 Especulación:
                    <span style="
                        color:#c77dff;
                        font-weight:900;
                        text-shadow:0 0 8px rgba(255,255,255,0.18);
                    ">
                        {int(speculative_score)}
                    </span>
                </div>

            </div>
            
            <!-- BIAS -->
            <div style="
                color:#ffd166;
                font-size:18px;
                font-weight:700;
                margin-bottom:8px;
            ">
                {bias}
            </div>

            <div style="
                color:white;
                font-size:15px;
                font-weight:700;
            ">
                {bias_market}
            </div>

        </div>
        """

        cards_html += card_html

    components.html(
        f"""
        <div style="
            display:flex;
            gap:18px;
        ">
            {cards_html}
        </div>
        """,
        height=700
    )
