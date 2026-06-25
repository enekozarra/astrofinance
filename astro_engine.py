from datetime import datetime, timedelta
import itertools
import math
import pandas as pd
import swisseph as swe


swe.set_sid_mode(swe.SIDM_LAHIRI)


SIGNOS = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
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

def jd(fecha):
    return swe.julday(fecha.year, fecha.month, fecha.day, 13.5)


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

        nak_num = int(lon / (360 / 27))
        nak = NAKSHATRAS[nak_num]
        pada = nakshatra_pada(lon)

        filas.append({
            "Planeta": nombre,
            "Longitud": round(lon, 4),
            "Signo": SIGNOS[int(lon // 30)],
            "Nakshatra": nak,
            "Pada": pada,
            "Grado": round(lon % 30, 2),
            "Velocidad": round(speed, 5),
            "Retrógrado": speed < 0
        })

    ketu = (longitudes["☊ Rahu"] + 180) % 360
    rahu_speed = next(x["Velocidad"] for x in filas if x["Planeta"] == "☊ Rahu")


    nak_num = int(ketu / (360 / 27))
    nak = NAKSHATRAS[nak_num]
    pada = nakshatra_pada(ketu)
    
    filas.append({
        "Planeta": "☋ Ketu",
        "Longitud": round(ketu, 4),
        "Signo": SIGNOS[int(ketu // 30)],
        "Nakshatra": nak,
        "Pada": pada,
        "Grado": round(ketu % 30, 2),
        "Velocidad": rahu_speed,
        "Retrógrado": rahu_speed < 0
    })

    return pd.DataFrame(filas)


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

    return fase, nak, tithi

REGENTE_SIGNO = {
    "Aries": "♂ Marte",
    "Tauro": "♀ Venus",
    "Géminis": "☿ Mercurio",
    "Cáncer": "☽ Luna",
    "Leo": "☉ Sol",
    "Virgo": "☿ Mercurio",
    "Libra": "♀ Venus",
    "Escorpio": "♂ Marte",
    "Sagitario": "♃ Júpiter",
    "Capricornio": "♄ Saturno",
    "Acuario": "♄ Saturno",
    "Piscis": "♃ Júpiter",
}

EXALTACION = {
    "☉ Sol": "Aries",
    "☽ Luna": "Tauro",
    "♂ Marte": "Capricornio",
    "☿ Mercurio": "Virgo",
    "♃ Júpiter": "Cáncer",
    "♀ Venus": "Piscis",
    "♄ Saturno": "Libra",
}

DEBILIDAD = {
    "☉ Sol": "Libra",
    "☽ Luna": "Escorpio",
    "♂ Marte": "Cáncer",
    "☿ Mercurio": "Piscis",
    "♃ Júpiter": "Capricornio",
    "♀ Venus": "Virgo",
    "♄ Saturno": "Aries",
}

DOMICILIO = {
    "☉ Sol": ["Leo"],
    "☽ Luna": ["Cáncer"],
    "♂ Marte": ["Aries", "Escorpio"],
    "☿ Mercurio": ["Géminis", "Virgo"],
    "♃ Júpiter": ["Sagitario", "Piscis"],
    "♀ Venus": ["Tauro", "Libra"],
    "♄ Saturno": ["Capricornio", "Acuario"],
}


def dignidad_planeta(planeta, signo):
    if EXALTACION.get(planeta) == signo:
        return "exaltado", 1.30

    if DEBILIDAD.get(planeta) == signo:
        return "debilitado", 0.65

    if signo in DOMICILIO.get(planeta, []):
        return "domicilio", 1.15

    if REGENTE_SIGNO.get(signo) == planeta:
        return "regente", 1.15

    return "neutral", 1.00



def distancia_angular(a, b):
    diff = abs(a - b)
    return min(diff, 360 - diff)

ASPECTOS_VEDICOS = {
    "♂ Marte": [4, 7, 8],
    "♃ Júpiter": [5, 7, 9],
    "♄ Saturno": [3, 7, 10],
    "☊ Rahu": [5, 7, 9],
    "☋ Ketu": [5, 7, 9],
}


def distancia_signos(signo_origen, signo_destino):
    i = SIGNOS.index(signo_origen)
    j = SIGNOS.index(signo_destino)

    return ((j - i) % 12) + 1


def aspecto_vedico(p1, p2):
    planeta = p1["Planeta"]

    if planeta not in ASPECTOS_VEDICOS:
        return {
            "hay_aspecto": False,
            "tipo": None,
            "fuerza": 0,
        }

    distancia = distancia_signos(
        p1["Signo"],
        p2["Signo"]
    )

    if distancia not in ASPECTOS_VEDICOS[planeta]:
        return {
            "hay_aspecto": False,
            "tipo": None,
            "fuerza": 0,
        }

    fuerza = 0.30

    if distancia == 7:
        fuerza = 0.45

    if planeta in ["♃ Júpiter", "♄ Saturno"]:
        fuerza += 0.10

    if planeta in ["☊ Rahu", "☋ Ketu"]:
        fuerza += 0.05

    return {
        "hay_aspecto": True,
        "tipo": f"{planeta} aspecto {distancia}",
        "fuerza": round(fuerza, 2),
    }


def aspecto_entre_planetas(p1, p2):
    a1 = aspecto_vedico(p1, p2)
    a2 = aspecto_vedico(p2, p1)

    if a1["hay_aspecto"] and a2["hay_aspecto"]:
        return {
            "hay_aspecto": True,
            "tipo": f'{a1["tipo"]} / {a2["tipo"]}',
            "fuerza": round(a1["fuerza"] + a2["fuerza"], 2),
        }

    if a1["hay_aspecto"]:
        return a1

    if a2["hay_aspecto"]:
        return a2

    return {
        "hay_aspecto": False,
        "tipo": None,
        "fuerza": 0,
    }

COMBUSTION_ORBES = {
    "☽ Luna": 12,
    "♂ Marte": 17,
    "☿ Mercurio": 14,
    "♃ Júpiter": 11,
    "♀ Venus": 10,
    "♄ Saturno": 15,
}


def combustion_solar(p, posiciones):
    planeta = p["Planeta"]

    if planeta == "☉ Sol":
        return {
            "combusto": False,
            "distancia_sol": None,
            "factor": 1.0,
        }

    if planeta not in COMBUSTION_ORBES:
        return {
            "combusto": False,
            "distancia_sol": None,
            "factor": 1.0,
        }

    sol = posiciones[posiciones["Planeta"] == "☉ Sol"].iloc[0]
    distancia = distancia_angular(p["Longitud"], sol["Longitud"])
    orbe = COMBUSTION_ORBES[planeta]

    if distancia > orbe:
        return {
            "combusto": False,
            "distancia_sol": round(distancia, 2),
            "factor": 1.0,
        }

    intensidad = 1 - (distancia / orbe)
    factor = 1 - (intensidad * 0.35)

    return {
        "combusto": True,
        "distancia_sol": round(distancia, 2),
        "factor": round(factor, 2),
    }


PLANET_PROFILE = {
    "☉ Sol": {
        "direction": 3, "speculation": 1, "volatility": 2,
        "expansion": 3, "restriction": 0, "impulse": 4,
        "liquidity": 1, "fear": 0, "clarity": 5,
        "type": "luminary"
    },

    "☽ Luna": {
        "direction": 0, "speculation": 2, "volatility": 5,
        "expansion": 1, "restriction": 0, "impulse": 2,
        "liquidity": 3, "fear": 2, "clarity": -1,
        "type": "luminary"
    },

    "♂ Marte": {
        "direction": 4, "speculation": 4, "volatility": 8,
        "expansion": 2, "restriction": 0, "impulse": 9,
        "liquidity": 1, "fear": 3, "clarity": -1,
        "type": "malefic"
    },

    "☿ Mercurio": {
        "direction": 1, "speculation": 5, "volatility": 4,
        "expansion": 2, "restriction": 0, "impulse": 3,
        "liquidity": 2, "fear": 1, "clarity": 6,
        "type": "neutral"
    },

    "♃ Júpiter": {
        "direction": 8, "speculation": 4, "volatility": 1,
        "expansion": 10, "restriction": -1, "impulse": 3,
        "liquidity": 5, "fear": -4, "clarity": 4,
        "type": "benefic"
    },

    "♀ Venus": {
        "direction": 5, "speculation": 3, "volatility": -1,
        "expansion": 5, "restriction": -2, "impulse": 2,
        "liquidity": 8, "fear": -3, "clarity": 2,
        "type": "benefic"
    },

    "♄ Saturno": {
        "direction": -5, "speculation": -4, "volatility": 4,
        "expansion": -5, "restriction": 10, "impulse": -6,
        "liquidity": -5, "fear": 7, "clarity": 2,
        "type": "malefic"
    },

    "☊ Rahu": {
        "direction": 0, "speculation": 10, "volatility": 9,
        "expansion": 7, "restriction": 0, "impulse": 7,
        "liquidity": 2, "fear": 4, "clarity": -6,
        "type": "node"
    },

    "☋ Ketu": {
        "direction": -3, "speculation": -7, "volatility": 6,
        "expansion": -4, "restriction": 4, "impulse": -2,
        "liquidity": -4, "fear": 5, "clarity": -2,
        "type": "node"
    },
}

NAKSHATRA_PROFILE = {
    "Ashwini": {"direction": 3, "speculation": 5, "volatility": 5, "liquidity": 1, "momentum": 7, "innovation": 4, "fear": 0, "clarity": 1},
    "Bharani": {"direction": -2, "speculation": 1, "volatility": 6, "liquidity": -2, "momentum": 2, "innovation": 0, "fear": 4, "clarity": -2},
    "Krittika": {"direction": 1, "speculation": 2, "volatility": 5, "liquidity": 0, "momentum": 4, "innovation": 1, "fear": 2, "clarity": 3},
    "Rohini": {"direction": 5, "speculation": 3, "volatility": 1, "liquidity": 5, "momentum": 4, "innovation": 2, "fear": -2, "clarity": 3},
    "Mrigashira": {"direction": 1, "speculation": 4, "volatility": 3, "liquidity": 2, "momentum": 3, "innovation": 3, "fear": 1, "clarity": 1},
    "Ardra": {"direction": -4, "speculation": 5, "volatility": 9, "liquidity": -2, "momentum": 5, "innovation": 5, "fear": 5, "clarity": -5},
    "Punarvasu": {"direction": 4, "speculation": 2, "volatility": 2, "liquidity": 3, "momentum": 3, "innovation": 2, "fear": -1, "clarity": 4},
    "Pushya": {"direction": 4, "speculation": 1, "volatility": 1, "liquidity": 4, "momentum": 2, "innovation": 1, "fear": -2, "clarity": 5},
    "Ashlesha": {"direction": -3, "speculation": 4, "volatility": 7, "liquidity": -2, "momentum": 2, "innovation": 2, "fear": 5, "clarity": -5},
    "Magha": {"direction": 1, "speculation": 3, "volatility": 5, "liquidity": 0, "momentum": 4, "innovation": 1, "fear": 2, "clarity": 1},
    "Purva Phalguni": {"direction": 2, "speculation": 4, "volatility": 3, "liquidity": 3, "momentum": 2, "innovation": 1, "fear": 0, "clarity": 0},
    "Uttara Phalguni": {"direction": 4, "speculation": 2, "volatility": 1, "liquidity": 4, "momentum": 3, "innovation": 1, "fear": -1, "clarity": 4},
    "Hasta": {"direction": 3, "speculation": 2, "volatility": 2, "liquidity": 3, "momentum": 3, "innovation": 2, "fear": 0, "clarity": 5},
    "Chitra": {"direction": 2, "speculation": 5, "volatility": 5, "liquidity": 1, "momentum": 5, "innovation": 5, "fear": 1, "clarity": 2},
    "Swati": {"direction": 2, "speculation": 6, "volatility": 6, "liquidity": 2, "momentum": 5, "innovation": 6, "fear": 1, "clarity": 0},
    "Vishakha": {"direction": 3, "speculation": 4, "volatility": 4, "liquidity": 2, "momentum": 5, "innovation": 3, "fear": 1, "clarity": 2},
    "Anuradha": {"direction": 3, "speculation": 2, "volatility": 2, "liquidity": 3, "momentum": 3, "innovation": 2, "fear": 0, "clarity": 4},
    "Jyeshtha": {"direction": -2, "speculation": 4, "volatility": 7, "liquidity": -1, "momentum": 3, "innovation": 2, "fear": 4, "clarity": -3},
    "Mula": {"direction": -5, "speculation": 3, "volatility": 9, "liquidity": -4, "momentum": 4, "innovation": 3, "fear": 6, "clarity": -4},
    "Purva Ashadha": {"direction": 2, "speculation": 4, "volatility": 4, "liquidity": 2, "momentum": 4, "innovation": 2, "fear": 1, "clarity": 1},
    "Uttara Ashadha": {"direction": 5, "speculation": 2, "volatility": 2, "liquidity": 4, "momentum": 4, "innovation": 1, "fear": -1, "clarity": 5},
    "Shravana": {"direction": 3, "speculation": 1, "volatility": 1, "liquidity": 3, "momentum": 2, "innovation": 2, "fear": 0, "clarity": 5},
    "Dhanishta": {"direction": 3, "speculation": 5, "volatility": 5, "liquidity": 2, "momentum": 6, "innovation": 4, "fear": 1, "clarity": 1},
    "Shatabhisha": {"direction": 1, "speculation": 7, "volatility": 7, "liquidity": 1, "momentum": 5, "innovation": 8, "fear": 2, "clarity": -1},
    "Purva Bhadrapada": {"direction": -3, "speculation": 5, "volatility": 8, "liquidity": -2, "momentum": 4, "innovation": 4, "fear": 5, "clarity": -4},
    "Uttara Bhadrapada": {"direction": 3, "speculation": 1, "volatility": 2, "liquidity": 3, "momentum": 2, "innovation": 1, "fear": -1, "clarity": 4},
    "Revati": {"direction": 3, "speculation": 1, "volatility": 1, "liquidity": 4, "momentum": 2, "innovation": 2, "fear": -2, "clarity": 5},
}

NAKSHATRA_POWER = {
    "Ashwini": 1.10,
    "Bharani": 0.95,
    "Krittika": 1.00,
    "Rohini": 1.12,
    "Mrigashira": 1.03,
    "Ardra": 0.90,
    "Punarvasu": 1.08,
    "Pushya": 1.12,
    "Ashlesha": 0.88,
    "Magha": 1.00,
    "Purva Phalguni": 1.03,
    "Uttara Phalguni": 1.08,
    "Hasta": 1.07,
    "Chitra": 1.04,
    "Swati": 1.05,
    "Vishakha": 1.04,
    "Anuradha": 1.08,
    "Jyeshtha": 0.92,
    "Mula": 0.85,
    "Purva Ashadha": 1.02,
    "Uttara Ashadha": 1.10,
    "Shravana": 1.08,
    "Dhanishta": 1.06,
    "Shatabhisha": 1.05,
    "Purva Bhadrapada": 0.90,
    "Uttara Bhadrapada": 1.06,
    "Revati": 1.10,
}

NAKSHATRA_LORD = {
    "Ashwini": "☋ Ketu",
    "Bharani": "♀ Venus",
    "Krittika": "☉ Sol",
    "Rohini": "☽ Luna",
    "Mrigashira": "♂ Marte",
    "Ardra": "☊ Rahu",
    "Punarvasu": "♃ Júpiter",
    "Pushya": "♄ Saturno",
    "Ashlesha": "☿ Mercurio",
    "Magha": "☋ Ketu",
    "Purva Phalguni": "♀ Venus",
    "Uttara Phalguni": "☉ Sol",
    "Hasta": "☽ Luna",
    "Chitra": "♂ Marte",
    "Swati": "☊ Rahu",
    "Vishakha": "♃ Júpiter",
    "Anuradha": "♄ Saturno",
    "Jyeshtha": "☿ Mercurio",
    "Mula": "☋ Ketu",
    "Purva Ashadha": "♀ Venus",
    "Uttara Ashadha": "☉ Sol",
    "Shravana": "☽ Luna",
    "Dhanishta": "♂ Marte",
    "Shatabhisha": "☊ Rahu",
    "Purva Bhadrapada": "♃ Júpiter",
    "Uttara Bhadrapada": "♄ Saturno",
    "Revati": "☿ Mercurio",
}

def fuerza_regente_nakshatra(p, posiciones):

    lord = NAKSHATRA_LORD.get(
        p["Nakshatra"]
    )

    if lord is None:
        return 1.0

    fila = posiciones[
        posiciones["Planeta"] == lord
    ]

    if len(fila) == 0:
        return 1.0

    r = fila.iloc[0]

    _, mult = dignidad_planeta(
        r["Planeta"],
        r["Signo"]
    )

    return mult

def perfil_nakshatra(nombre):

    return NAKSHATRA_PROFILE.get(
        nombre,
        {
            "direction": 0,
            "speculation": 0,
            "volatility": 0,
            "liquidity": 0,
            "momentum": 0,
            "innovation": 0,
            "fear": 0,
            "clarity": 0,
        }
    )

def evaluar_planeta(p, posiciones=None):
    planeta = p["Planeta"]
    signo = p["Signo"]
    retro = bool(p["Retrógrado"])

    perfil = PLANET_PROFILE[planeta]

    dignidad, dignidad_mult = dignidad_planeta(planeta, signo)

    d = perfil["direction"] * dignidad_mult
    s = perfil["speculation"] * dignidad_mult
    v = perfil["volatility"]

    if retro and planeta not in ["☊ Rahu", "☋ Ketu"]:
        d *= 0.75
        s *= 0.85
        v *= 1.25
        
    perfil_nak = perfil_nakshatra(p["Nakshatra"])

    d += perfil_nak["direction"] * 0.25
    s += perfil_nak["speculation"] * 0.25
    v += perfil_nak["volatility"] * 0.25

    combustion = None

    if posiciones is not None:
        combustion = combustion_solar(p, posiciones)

        if combustion["combusto"]:
            d *= combustion["factor"]
            s *= combustion["factor"]
            v += 2
    
    return {
        "planeta": planeta,
        "signo": signo,
        "nakshatra": p["Nakshatra"],
        "dignidad": dignidad,
        "combustion": combustion,
        "retro": retro,
        "direction": d,
        "speculation": s,
        "volatility": v,
    }

def aplicar_nakshatra_planeta(p, resultado):

    perfil = perfil_nakshatra(
        p["Nakshatra"]
    )

    resultado["direction"] += perfil["direction"]
    resultado["speculation"] += perfil["speculation"]
    resultado["volatility"] += perfil["volatility"]

    return resultado

def evaluar_contexto_lunar(fecha):
    fase, nak, tithi = obtener_luna(fecha)
    perfil = perfil_nakshatra(nak)

    direction = perfil["direction"] * 0.60
    speculation = perfil["speculation"] * 0.60
    volatility = perfil["volatility"] * 0.60

    if fase in ["Creciente", "Creciente avanzada"]:
        direction += 2
        momentum = 2
    elif fase == "Luna llena":
        speculation += 2
        volatility += 4
        momentum = 1
    elif fase in ["Menguante", "Luna nueva"]:
        direction -= 2
        momentum = -2
    else:
        momentum = 0

    return {
        "fase": fase,
        "nakshatra_lunar": nak,
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
        "momentum": momentum,
    }

def fuerza_relacion(p1, p2, orbe=8):
    distancia = distancia_angular(p1["Longitud"], p2["Longitud"])
    mismo_signo = p1["Signo"] == p2["Signo"]
    conjuncion = distancia <= orbe

    aspecto = aspecto_entre_planetas(p1, p2)

    if not mismo_signo and not conjuncion and not aspecto["hay_aspecto"]:
        return None

    fuerza = 0

    if conjuncion:
        fuerza += 1 - (distancia / orbe)

    if mismo_signo:
        fuerza += 0.35

    if p1["Retrógrado"]:
        fuerza += 0.10

    if p2["Retrógrado"]:
        fuerza += 0.10

    if aspecto["hay_aspecto"]:
        fuerza += aspecto["fuerza"]

    return {
        "distancia": round(distancia, 2),
        "mismo_signo": mismo_signo,
        "aspecto": aspecto,
        "conjuncion": conjuncion,
        "fuerza": round(fuerza, 2),
        "signo": p1["Signo"] if mismo_signo else "Entre signos",
    }


def evaluar_relacion(p1, p2, orbe=8):
    fuerza = fuerza_relacion(p1, p2, orbe)

    if fuerza is None:
        return None

    e1 = evaluar_planeta(p1)
    e2 = evaluar_planeta(p2)

    perfil1 = PLANET_PROFILE[p1["Planeta"]]
    perfil2 = PLANET_PROFILE[p2["Planeta"]]

    direction = (e1["direction"] + e2["direction"]) * fuerza["fuerza"] * 0.22
    speculation = (e1["speculation"] + e2["speculation"]) * fuerza["fuerza"] * 0.22
    volatility = (e1["volatility"] + e2["volatility"]) * fuerza["fuerza"] * 0.22

    expansion_mix = perfil1["expansion"] + perfil2["expansion"]
    restriction_mix = perfil1["restriction"] + perfil2["restriction"]
    impulse_mix = perfil1["impulse"] + perfil2["impulse"]
    fear_mix = perfil1["fear"] + perfil2["fear"]
    clarity_mix = perfil1["clarity"] + perfil2["clarity"]

    direction += (expansion_mix - restriction_mix) * fuerza["fuerza"] * 0.18
    volatility += abs(impulse_mix) * fuerza["fuerza"] * 0.12
    speculation += max(expansion_mix, 0) * fuerza["fuerza"] * 0.10
    direction -= max(fear_mix, 0) * fuerza["fuerza"] * 0.10
    speculation += max(-clarity_mix, 0) * fuerza["fuerza"] * 0.12

    return {
        "planeta_1": p1["Planeta"],
        "planeta_2": p2["Planeta"],
        "signo": fuerza["signo"],
        "distancia": fuerza["distancia"],
        "conjuncion": fuerza["conjuncion"],
        "mismo_signo": fuerza["mismo_signo"],
        "fuerza": fuerza["fuerza"],
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
    }


def evaluar_todas_relaciones(posiciones, orbe=8):
    planetas = posiciones.to_dict("records")
    relaciones = []

    for p1, p2 in itertools.combinations(planetas, 2):
        r = evaluar_relacion(p1, p2, orbe)

        if r is not None:
            relaciones.append(r)

    return relaciones

def detectar_clusters(posiciones):
    clusters = []

    for signo in SIGNOS:

        grupo = posiciones[posiciones["Signo"] == signo]

        if len(grupo) < 3:
            continue

        planetas = grupo["Planeta"].tolist()

        clusters.append({
            "signo": signo,
            "planetas": planetas,
            "cantidad": len(planetas),
        })

    return clusters

def evaluar_cluster(cluster, posiciones):

    expansion = 0
    restriction = 0
    impulse = 0
    fear = 0
    liquidity = 0
    clarity = 0

    for planeta in cluster["planetas"]:

        perfil = PLANET_PROFILE[planeta]

        expansion += perfil["expansion"]
        restriction += perfil["restriction"]
        impulse += perfil["impulse"]
        fear += perfil["fear"]
        liquidity += perfil["liquidity"]
        clarity += perfil["clarity"]

    intensidad = 1 + (cluster["cantidad"] - 3) * 0.35

    dominancias = []

    for _, p in posiciones.iterrows():

        if p["Planeta"] not in cluster["planetas"]:
            continue

        if p["Signo"] != cluster["signo"]:
            continue

        dominancias.append({
            "planeta": p["Planeta"],
            "fuerza": fuerza_planeta_en_signo(p)
        })

    dominancias.sort(
        key=lambda x: x["fuerza"],
        reverse=True
    )

    dominante = dominancias[0]["planeta"]

    fuerza_regente = fuerza_regente_signo(
        cluster["signo"],
        posiciones
    )

    regente_mult = fuerza_regente / 100.0
    
    return {
        "signo": cluster["signo"],
        "planetas": cluster["planetas"],
        "cantidad": cluster["cantidad"],
        "dominante": dominante,
        "fuerza_regente": fuerza_regente,
        "expansion": round(expansion * intensidad * regente_mult, 2),
        "restriction": round(restriction * intensidad * regente_mult, 2),
        "impulse": round(impulse * intensidad * regente_mult, 2),
        "fear": round(fear * intensidad * regente_mult, 2),
        "liquidity": round(liquidity * intensidad * regente_mult, 2),
        "clarity": round(clarity * intensidad * regente_mult, 2),
    }

def fuerza_planeta_en_signo(p):

    planeta = p["Planeta"]
    signo = p["Signo"]

    _, mult = dignidad_planeta(planeta, signo)

    fuerza = 100 * mult

    if p["Retrógrado"]:

        if planeta in ["♃ Júpiter", "♀ Venus", "☿ Mercurio"]:
            fuerza *= 0.85

        elif planeta in ["♂ Marte", "♄ Saturno"]:
            fuerza *= 1.10

    return fuerza

def fuerza_regente_signo(signo, posiciones):


    regente = REGENTE_SIGNO[signo]

    fila = posiciones[
        posiciones["Planeta"] == regente
    ]

    if len(fila) == 0:
        return 100

    p = fila.iloc[0]

    _, mult = dignidad_planeta(
        p["Planeta"],
        p["Signo"]
    )

    fuerza = 100 * mult

    if p["Retrógrado"]:

        if p["Planeta"] in ["♃ Júpiter", "♀ Venus", "☿ Mercurio"]:
            fuerza *= 0.85

        elif p["Planeta"] in ["♂ Marte", "♄ Saturno"]:
            fuerza *= 1.10

    return round(fuerza, 2)

def evaluar_todos_clusters(posiciones):

    clusters = detectar_clusters(posiciones)

    return [
        evaluar_cluster(c, posiciones)
        for c in clusters
    ]

def evaluar_dia(fecha, orbe=8):
    posiciones = obtener_posiciones(fecha)

    planetas_eval = [
        evaluar_planeta(p, posiciones)
        for _, p in posiciones.iterrows()
    ]

    relaciones = evaluar_todas_relaciones(posiciones, orbe)
    aspectos_grado = enriquecer_aspectos_aplicativo(
        detectar_aspectos_por_grado(posiciones),
        posiciones
    )
    score_asp_grado = score_aspectos_grado(aspectos_grado)
    score_asp_contextual = score_aspectos_contextuales(aspectos_grado, posiciones)
    score_tithi_dia = score_tithi(fecha)
    score_luna_adv = score_luna_avanzada(fecha)
    score_signo_prox = score_cambio_signo_proximo(posiciones)
    score_disp = score_dispositores(posiciones)
    score_nak_prox = score_cambio_nakshatra_proximo(posiciones)
    score_velocidad = score_velocidad_planetaria(posiciones)
    clusters = evaluar_todos_clusters(posiciones)
    luna = evaluar_contexto_lunar(fecha)
    transiciones = detectar_transiciones(fecha)
    score_trans = score_transiciones(transiciones)
    transiciones_rel = detectar_transiciones_relaciones(fecha, orbe)
    score_trans_rel = score_transiciones_relaciones(transiciones_rel)
    transiciones_clusters = detectar_transiciones_clusters(fecha)
    score_trans_clusters = score_transiciones_clusters(transiciones_clusters)
    
    direction = 0
    speculation = 0
    volatility = 0

    for p in planetas_eval:
        direction += p["direction"] * 0.25
        speculation += p["speculation"] * 0.20
        volatility += p["volatility"] * 0.25

    for r in relaciones:
        direction += r["direction"]
        speculation += r["speculation"]
        volatility += r["volatility"]

    for c in clusters:
        direction += (c["expansion"] - c["restriction"]) * 0.15
        speculation += c["impulse"] * 0.10
        volatility += (c["fear"] + abs(c["impulse"])) * 0.08

    direction += luna["direction"]
    speculation += luna["speculation"]
    volatility += luna["volatility"]

    direction += score_trans["direction"]
    speculation += score_trans["speculation"]
    volatility += score_trans["volatility"]

    direction += score_trans_rel["direction"]
    speculation += score_trans_rel["speculation"]
    volatility += score_trans_rel["volatility"]

    direction += score_trans_clusters["direction"]
    speculation += score_trans_clusters["speculation"]
    volatility += score_trans_clusters["volatility"]

    direction += score_signo_prox["direction"]
    speculation += score_signo_prox["speculation"]
    volatility += score_signo_prox["volatility"]

    direction += score_nak_prox["direction"]
    speculation += score_nak_prox["speculation"]
    volatility += score_nak_prox["volatility"]

    direction += score_velocidad["direction"]
    speculation += score_velocidad["speculation"]
    volatility += score_velocidad["volatility"]

    direction += score_disp["direction"]
    speculation += score_disp["speculation"]
    volatility += score_disp["volatility"]

    direction += score_luna_adv["direction"]
    speculation += score_luna_adv["speculation"]
    volatility += score_luna_adv["volatility"]

    direction += score_tithi_dia["direction"]
    speculation += score_tithi_dia["speculation"]
    volatility += score_tithi_dia["volatility"]

    direction += score_asp_contextual["direction"]
    speculation += score_asp_contextual["speculation"]
    volatility += score_asp_contextual["volatility"]

    energia = (
        direction * 0.65
        + speculation * 0.08
        - max(volatility - 35, 0) * 0.35
    )
    diagnostico = diagnostico_dia({
        "direction": direction,
        "speculation": speculation,
        "volatility": volatility,
    })
    
    dominante, ranking_planetas = planeta_dominante(
        posiciones,
        relaciones,
        clusters
    )
    
    return {
        "fecha": fecha,
        "energia": round(energia, 2),
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "transiciones": transiciones,
        "score_transiciones": score_trans,
        "transiciones_relaciones": transiciones_rel,
        "score_transiciones_relaciones": score_trans_rel,
        "aspectos_grado": aspectos_grado,
        "score_dispositores": score_disp,
        "score_velocidad": score_velocidad,
        "score_luna_avanzada": score_luna_adv,
        "score_tithi": score_tithi_dia,
        "score_aspectos_contextuales": score_asp_contextual,
        "transiciones_clusters": transiciones_clusters,
        "score_transiciones_clusters": score_trans_clusters,
        "score_aspectos_grado": score_asp_grado,
        "score_cambio_nakshatra_proximo": score_nak_prox,
        "score_cambio_signo_proximo": score_signo_prox,
        "diagnostico": diagnostico,
        "volatility": round(volatility, 2),
        "luna": luna,
        "planetas": planetas_eval,
        "relaciones": relaciones,
        "clusters": clusters,
        "planeta_dominante": dominante,
        "ranking_planetas": ranking_planetas,
    }


def evaluar_presion_fin_de_semana(fecha_ref, orbe=8):
    lunes = fecha_ref - timedelta(days=fecha_ref.weekday())

    sabado = lunes - timedelta(days=2)
    domingo = lunes - timedelta(days=1)

    r_sabado = evaluar_dia(sabado, orbe)
    r_domingo = evaluar_dia(domingo, orbe)

    direction = (r_sabado["direction"] * 0.35) + (r_domingo["direction"] * 0.65)
    speculation = (r_sabado["speculation"] * 0.35) + (r_domingo["speculation"] * 0.65)
    volatility = (r_sabado["volatility"] * 0.35) + (r_domingo["volatility"] * 0.65)

    pressure = (
        direction * 0.45
        + speculation * 0.20
        - max(volatility - 40, 0) * 0.15
    )

    return {
        "sabado": r_sabado,
        "domingo": r_domingo,
        "weekend_pressure": round(pressure, 2),
        "weekend_direction": round(direction, 2),
        "weekend_speculation": round(speculation, 2),
        "weekend_volatility": round(volatility, 2),
    }

def evaluar_semana(fecha_ref, orbe=8):
    lunes = fecha_ref - timedelta(days=fecha_ref.weekday())
    dias = [lunes + timedelta(days=i) for i in range(5)]

    resultados = [
        evaluar_dia(d, orbe)
        for d in dias
    ]

    weekend = evaluar_presion_fin_de_semana(fecha_ref, orbe)

    resultados[0]["energia"] += weekend["weekend_pressure"] * 0.20
    resultados[0]["direction"] += weekend["weekend_direction"] * 0.10
    resultados[0]["speculation"] += weekend["weekend_speculation"] * 0.10
    resultados[0]["volatility"] += weekend["weekend_volatility"] * 0.10

    energia_media = sum(r["energia"] for r in resultados) / len(resultados)
    direction_media = sum(r["direction"] for r in resultados) / len(resultados)
    speculation_media = sum(r["speculation"] for r in resultados) / len(resultados)
    volatility_media = sum(r["volatility"] for r in resultados) / len(resultados)

    energia_inicio = resultados[0]["energia"]
    energia_fin = resultados[-1]["energia"]
    tendencia = energia_fin - energia_inicio

    if tendencia >= 8 and energia_media > 0:
        lectura = "🟢 Semana alcista"
    elif tendencia <= -8:
        lectura = "🔴 Semana bajista"
    elif energia_media >= 12 and tendencia >= -3:
        lectura = "🟡 Alcista débil"
    elif energia_media <= -6:
        lectura = "🟠 Presión bajista"
    else:
        lectura = "🟡 Semana mixta"
        
    return {
        "lunes": lunes,
        "dias": resultados,
        "weekend": weekend,
        "energia_media": round(energia_media, 2),
        "direction_media": round(direction_media, 2),
        "speculation_media": round(speculation_media, 2),
        "volatility_media": round(volatility_media, 2),
        "energia_inicio": round(energia_inicio, 2),
        "energia_fin": round(energia_fin, 2),
        "tendencia": round(tendencia, 2),
        "lectura": lectura,
    }

def detectar_transiciones(fecha, orbe=8):
    hoy = obtener_posiciones(fecha)
    ayer = obtener_posiciones(fecha - timedelta(days=1))

    eventos = []

    for _, p_hoy in hoy.iterrows():

        p_ayer = ayer[
            ayer["Planeta"] == p_hoy["Planeta"]
        ].iloc[0]

        if p_hoy["Signo"] != p_ayer["Signo"]:
            eventos.append({
                "tipo": "cambio_signo",
                "planeta": p_hoy["Planeta"],
                "de": p_ayer["Signo"],
                "a": p_hoy["Signo"]
            })

        if p_hoy["Nakshatra"] != p_ayer["Nakshatra"]:
            eventos.append({
                "tipo": "cambio_nakshatra",
                "planeta": p_hoy["Planeta"],
                "de": p_ayer["Nakshatra"],
                "a": p_hoy["Nakshatra"]
            })

        if p_hoy["Retrógrado"] != p_ayer["Retrógrado"]:
            eventos.append({
                "tipo": "cambio_retro",
                "planeta": p_hoy["Planeta"],
                "retro": p_hoy["Retrógrado"]
            })

    return eventos

def score_transiciones(eventos):

    direction = 0
    speculation = 0
    volatility = 0

    for e in eventos:

        if e["tipo"] == "cambio_retro":

            if e["retro"]:

                volatility += 6

                if e["planeta"] == "☿ Mercurio":
                    direction -= 4
                    speculation -= 2

                elif e["planeta"] == "♂ Marte":
                    volatility += 4

                elif e["planeta"] == "♃ Júpiter":
                    direction -= 3

            else:

                direction += 3
                volatility -= 2

        elif e["tipo"] == "cambio_signo":

            direction += 2
            volatility += 2

        elif e["tipo"] == "cambio_nakshatra":

            volatility += 1

    return {
        "direction": direction,
        "speculation": speculation,
        "volatility": volatility,
    }

def firma_relacion(r):
    return tuple(sorted([r["planeta_1"], r["planeta_2"]]))


def detectar_transiciones_relaciones(fecha, orbe=8):
    hoy = evaluar_todas_relaciones(obtener_posiciones(fecha), orbe)
    ayer = evaluar_todas_relaciones(obtener_posiciones(fecha - timedelta(days=1)), orbe)

    hoy_firmas = {firma_relacion(r): r for r in hoy}
    ayer_firmas = {firma_relacion(r): r for r in ayer}

    eventos = []

    for firma, r in hoy_firmas.items():
        if firma not in ayer_firmas:
            eventos.append({
                "tipo": "nueva_relacion",
                "planetas": firma,
                "relacion": r,
            })

    for firma, r in ayer_firmas.items():
        if firma not in hoy_firmas:
            eventos.append({
                "tipo": "relacion_rota",
                "planetas": firma,
                "relacion": r,
            })

    return eventos

def score_transiciones_relaciones(eventos):

    direction = 0
    speculation = 0
    volatility = 0

    for e in eventos:

        r = e["relacion"]

        if e["tipo"] == "nueva_relacion":
            direction += r["direction"] * 0.25
            speculation += r["speculation"] * 0.25
            volatility += abs(r["volatility"]) * 0.30

        elif e["tipo"] == "relacion_rota":
            direction -= r["direction"] * 0.15
            speculation -= r["speculation"] * 0.15
            volatility += 1

    return {
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
    }
def firma_cluster(c):
    return (
        c["signo"],
        tuple(sorted(c["planetas"]))
    )


def detectar_transiciones_clusters(fecha):
    hoy = detectar_clusters(obtener_posiciones(fecha))
    ayer = detectar_clusters(obtener_posiciones(fecha - timedelta(days=1)))

    hoy_firmas = {firma_cluster(c): c for c in hoy}
    ayer_firmas = {firma_cluster(c): c for c in ayer}

    eventos = []

    for firma, c in hoy_firmas.items():
        if firma not in ayer_firmas:
            eventos.append({
                "tipo": "nuevo_cluster",
                "cluster": c,
            })

    for firma, c in ayer_firmas.items():
        if firma not in hoy_firmas:
            eventos.append({
                "tipo": "cluster_roto",
                "cluster": c,
            })

    return eventos

def score_transiciones_clusters(eventos):

    direction = 0
    speculation = 0
    volatility = 0

    for e in eventos:

        c = e["cluster"]
        cantidad = c["cantidad"]

        if e["tipo"] == "nuevo_cluster":
            speculation += cantidad * 2
            volatility += cantidad * 3

        elif e["tipo"] == "cluster_roto":
            direction -= 1
            volatility += cantidad * 1.5

    return {
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
    }

def diagnostico_dia(resultado):

    dominante = "neutral"

    if resultado["volatility"] > 55:
        dominante = "volatilidad"

    if resultado["speculation"] > resultado["direction"] and resultado["speculation"] > 30:
        dominante = "especulación"

    if resultado["direction"] > 35 and resultado["volatility"] < 45:
        dominante = "dirección limpia"

    if resultado["direction"] < -15:
        dominante = "presión bajista"

    return dominante

def planeta_dominante(posiciones, relaciones, clusters):

    ranking = []

    for _, p in posiciones.iterrows():

        fuerza = fuerza_real_planeta(
            p,
            posiciones,
            relaciones,
            clusters
        )

        ranking.append({
            "planeta": p["Planeta"],
            "signo": p["Signo"],
            "nakshatra": p["Nakshatra"],
            "retro": bool(p["Retrógrado"]),
            "fuerza": fuerza,
        })

    ranking.sort(
        key=lambda x: x["fuerza"],
        reverse=True
    )

    return ranking[0], ranking

def fuerza_real_planeta(p, posiciones, relaciones, clusters):
    planeta = p["Planeta"]
    signo = p["Signo"]

    dignidad, dignidad_mult = dignidad_planeta(planeta, signo)

    fuerza = 100 * dignidad_mult
    fuerza *= fuerza_grado(p["Grado"])
    nak_mult = NAKSHATRA_POWER.get(p["Nakshatra"], 1.0)
    fuerza *= nak_mult
    fuerza *= fuerza_regente_nakshatra(
        p,
        posiciones
    )

    combustion = combustion_solar(p, posiciones)
    fuerza *= combustion["factor"]
    
    pada_mult = PADA_POWER.get(p["Pada"], 1.0)
    fuerza *= pada_mult
    
    if p["Retrógrado"]:
        if planeta in ["♃ Júpiter", "♀ Venus", "☿ Mercurio"]:
            fuerza *= 0.85
        elif planeta in ["♂ Marte", "♄ Saturno"]:
            fuerza *= 1.10

    if planeta == REGENTE_SIGNO.get(signo):
        fuerza += 15

    for r in relaciones:
        if planeta in [r["planeta_1"], r["planeta_2"]]:
            fuerza += abs(r["direction"]) * 0.8
            fuerza += abs(r["speculation"]) * 0.5
            fuerza += abs(r["volatility"]) * 0.4

    for c in clusters:
        if planeta in c["planetas"]:
            fuerza += c["cantidad"] * 8
            if c.get("dominante") == planeta:
                fuerza += 15

    asp = fuerza_aspectos_planeta(planeta, relaciones)
    fuerza += asp["total"] * 0.8
    red = centralidad_planeta(planeta, relaciones, clusters)
    fuerza += red["fuerza_red"] * 6
    
    cadena = cadena_regentes(planeta, posiciones)

    if len(cadena) >= 2:
        fuerza += 5

    if len(cadena) >= 4:
        fuerza -= 5

    return round(fuerza, 2)

def fuerza_grado(grado):

    if 10 <= grado <= 20:
        return 1.10

    if grado < 3:
        return 0.90

    if grado > 27:
        return 0.85

    return 1.00

def fuerza_aspectos_planeta(planeta, relaciones):

    emitidos = 0
    recibidos = 0

    for r in relaciones:
        if planeta not in [r["planeta_1"], r["planeta_2"]]:
            continue

        peso = (
            abs(r["direction"]) * 0.6
            + abs(r["speculation"]) * 0.4
            + abs(r["volatility"]) * 0.5
        )

        if r["planeta_1"] == planeta:
            emitidos += peso
        else:
            recibidos += peso

    return {
        "emitidos": round(emitidos, 2),
        "recibidos": round(recibidos, 2),
        "total": round(emitidos + recibidos, 2),
    }

def centralidad_planeta(planeta, relaciones, clusters):

    conexiones = 0
    fuerza_total = 0

    for r in relaciones:
        if planeta in [r["planeta_1"], r["planeta_2"]]:
            conexiones += 1
            fuerza_total += r["fuerza"]

    for c in clusters:
        if planeta in c["planetas"]:
            conexiones += c["cantidad"]
            fuerza_total += c["cantidad"] * 0.5

    return {
        "conexiones": conexiones,
        "fuerza_red": round(fuerza_total, 2),
    }

def cadena_regentes(planeta, posiciones, max_pasos=5):
    fila = posiciones[posiciones["Planeta"] == planeta]

    if len(fila) == 0:
        return []

    actual = fila.iloc[0]
    cadena = []

    for _ in range(max_pasos):
        signo = actual["Signo"]
        regente = REGENTE_SIGNO.get(signo)

        if regente is None:
            break

        cadena.append({
            "signo": signo,
            "regente": regente,
        })

        if regente == actual["Planeta"]:
            break

        fila_regente = posiciones[posiciones["Planeta"] == regente]

        if len(fila_regente) == 0:
            break

        actual = fila_regente.iloc[0]

    return cadena

def aspecto_por_grado(p1, p2, objetivo, orbe=6):
    diff = distancia_angular(p1["Longitud"], p2["Longitud"])
    distancia_al_aspecto = abs(diff - objetivo)

    if distancia_al_aspecto > orbe:
        return None

    fuerza = 1 - (distancia_al_aspecto / orbe)

    return {
        "objetivo": objetivo,
        "distancia_real": round(diff, 2),
        "orbe": round(distancia_al_aspecto, 2),
        "fuerza": round(fuerza, 2),
    }


def detectar_aspectos_por_grado(posiciones):
    planetas = posiciones.to_dict("records")
    aspectos = []

    objetivos = [0, 60, 90, 120, 180]

    for p1, p2 in itertools.combinations(planetas, 2):
        for objetivo in objetivos:
            asp = aspecto_por_grado(p1, p2, objetivo)

            if asp is None:
                continue

            aspectos.append({
                "planeta_1": p1["Planeta"],
                "planeta_2": p2["Planeta"],
                "aspecto": objetivo,
                "fuerza": asp["fuerza"],
                "orbe": asp["orbe"],
                "distancia_real": asp["distancia_real"],
            })

    return aspectos

def score_aspectos_grado(aspectos):

    direction = 0
    speculation = 0
    volatility = 0

    for a in aspectos:
        fuerza = a["fuerza"]

        if a["aspecto"] in [0, 120]:
            direction += 4 * fuerza
            speculation += 2 * fuerza

        elif a["aspecto"] == 60:
            direction += 2 * fuerza
            speculation += 1 * fuerza

        elif a["aspecto"] == 90:
            direction -= 2 * fuerza
            volatility += 5 * fuerza

        elif a["aspecto"] == 180:
            direction -= 3 * fuerza
            volatility += 6 * fuerza

    return {
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
    }

def distancia_cambio_signo(p):
    grado = p["Grado"]

    distancia_entrada = grado
    distancia_salida = 30 - grado

    return {
        "entrada": round(distancia_entrada, 2),
        "salida": round(distancia_salida, 2),
        "cerca_entrada": distancia_entrada <= 2,
        "cerca_salida": distancia_salida <= 2,
    }


def score_cambio_signo_proximo(posiciones):
    direction = 0
    speculation = 0
    volatility = 0
    eventos = []

    for _, p in posiciones.iterrows():
        d = distancia_cambio_signo(p)

        if d["cerca_entrada"]:
            volatility += 2
            eventos.append({
                "planeta": p["Planeta"],
                "tipo": "recién entrado",
                "signo": p["Signo"],
                "grado": p["Grado"],
            })

        if d["cerca_salida"]:
            volatility += 3
            direction -= 1
            eventos.append({
                "planeta": p["Planeta"],
                "tipo": "a punto de salir",
                "signo": p["Signo"],
                "grado": p["Grado"],
            })

    return {
        "direction": direction,
        "speculation": speculation,
        "volatility": volatility,
        "eventos": eventos,
    }

def distancia_cambio_nakshatra(p):
    longitud = p["Longitud"]
    tamaño_nak = 360 / 27

    pos_en_nak = longitud % tamaño_nak

    distancia_entrada = pos_en_nak
    distancia_salida = tamaño_nak - pos_en_nak

    return {
        "entrada": round(distancia_entrada, 2),
        "salida": round(distancia_salida, 2),
        "cerca_entrada": distancia_entrada <= 0.75,
        "cerca_salida": distancia_salida <= 0.75,
    }


def score_cambio_nakshatra_proximo(posiciones):
    direction = 0
    speculation = 0
    volatility = 0
    eventos = []

    for _, p in posiciones.iterrows():
        d = distancia_cambio_nakshatra(p)

        if d["cerca_entrada"]:
            volatility += 1.5
            eventos.append({
                "planeta": p["Planeta"],
                "tipo": "recién entrado nakshatra",
                "nakshatra": p["Nakshatra"],
            })

        if d["cerca_salida"]:
            volatility += 2
            speculation += 0.5
            eventos.append({
                "planeta": p["Planeta"],
                "tipo": "a punto de cambiar nakshatra",
                "nakshatra": p["Nakshatra"],
            })

    return {
        "direction": direction,
        "speculation": speculation,
        "volatility": volatility,
        "eventos": eventos,
    }

AVG_SPEED = {
    "☉ Sol": 0.985,
    "☽ Luna": 13.17,
    "♂ Marte": 0.52,
    "☿ Mercurio": 1.20,
    "♃ Júpiter": 0.083,
    "♀ Venus": 1.20,
    "♄ Saturno": 0.033,
    "☊ Rahu": 0.052,
    "☋ Ketu": 0.052,
}


def score_velocidad_planetaria(posiciones):
    direction = 0
    speculation = 0
    volatility = 0
    eventos = []

    for _, p in posiciones.iterrows():
        planeta = p["Planeta"]
        speed = abs(p["Velocidad"])
        avg = AVG_SPEED.get(planeta)

        if avg is None:
            continue

        ratio = speed / avg if avg else 1

        if ratio < 0.15:
            volatility += 4
            eventos.append({
                "planeta": planeta,
                "tipo": "estacionario",
                "ratio": round(ratio, 2),
            })

        elif ratio < 0.50:
            volatility += 2
            eventos.append({
                "planeta": planeta,
                "tipo": "muy lento",
                "ratio": round(ratio, 2),
            })

        elif ratio > 1.50:
            speculation += 1
            volatility += 1
            eventos.append({
                "planeta": planeta,
                "tipo": "muy rápido",
                "ratio": round(ratio, 2),
            })

    return {
        "direction": direction,
        "speculation": speculation,
        "volatility": volatility,
        "eventos": eventos,
    }

def tendencia_aspecto(p1, p2, objetivo):
    hoy = distancia_angular(p1["Longitud"], p2["Longitud"])

    # Aproximación usando velocidades relativas
    lon1_manana = (p1["Longitud"] + p1["Velocidad"]) % 360
    lon2_manana = (p2["Longitud"] + p2["Velocidad"]) % 360

    manana = distancia_angular(lon1_manana, lon2_manana)

    error_hoy = abs(hoy - objetivo)
    error_manana = abs(manana - objetivo)

    if error_manana < error_hoy:
        return "aplicativo"

    if error_manana > error_hoy:
        return "separativo"

    return "estable"


def enriquecer_aspectos_aplicativo(aspectos, posiciones):
    pos = {
        row["Planeta"]: row
        for _, row in posiciones.iterrows()
    }

    enriquecidos = []

    for a in aspectos:
        p1 = pos[a["planeta_1"]]
        p2 = pos[a["planeta_2"]]

        tendencia = tendencia_aspecto(
            p1,
            p2,
            a["aspecto"]
        )

        nuevo = dict(a)
        nuevo["tendencia"] = tendencia

        if tendencia == "aplicativo":
            nuevo["fuerza"] *= 1.20

        elif tendencia == "separativo":
            nuevo["fuerza"] *= 0.80

        nuevo["fuerza"] = round(nuevo["fuerza"], 2)

        enriquecidos.append(nuevo)

    return enriquecidos

def score_dispositores(posiciones):
    direction = 0
    speculation = 0
    volatility = 0
    eventos = []

    for _, p in posiciones.iterrows():
        planeta = p["Planeta"]
        cadena = cadena_regentes(planeta, posiciones)

        if not cadena:
            continue

        regente_final = cadena[-1]["regente"]
        fila = posiciones[posiciones["Planeta"] == regente_final]

        if len(fila) == 0:
            continue

        r = fila.iloc[0]
        dignidad, mult = dignidad_planeta(r["Planeta"], r["Signo"])

        if mult >= 1.15:
            direction += 1.5
            speculation += 0.5
        elif mult <= 0.70:
            direction -= 1.5
            volatility += 1.5

        eventos.append({
            "planeta": planeta,
            "regente_final": regente_final,
            "dignidad_regente": dignidad,
            "cadena": cadena,
        })

    return {
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
        "eventos": eventos,
    }

def score_luna_avanzada(fecha):
    fase, nak, tithi = obtener_luna(fecha)
    perfil = perfil_nakshatra(nak)

    direction = 0
    speculation = 0
    volatility = 0

    if fase in ["Creciente", "Creciente avanzada"]:
        direction += 2
        speculation += 1

    elif fase == "Luna llena":
        speculation += 2
        volatility += 4

    elif fase in ["Menguante", "Luna nueva"]:
        direction -= 2
        volatility += 1

    direction += perfil["direction"] * 0.35
    speculation += perfil["speculation"] * 0.35
    volatility += perfil["volatility"] * 0.35

    return {
        "fase": fase,
        "nakshatra": nak,
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
    }

def score_tithi(fecha):
    fase, nak, tithi = obtener_luna(fecha)

    direction = 0
    speculation = 0
    volatility = 0

    if tithi in [1, 2, 3, 4, 5]:
        direction += 1
        speculation += 0.5

    elif tithi in [8, 9, 10, 11, 12, 13]:
        direction += 1.5
        speculation += 1

    elif tithi in [14, 15]:
        speculation += 2
        volatility += 3

    elif tithi in [0, 29]:
        direction -= 2
        volatility += 2

    elif tithi in [23, 24, 25, 26, 27, 28]:
        direction -= 1
        volatility += 1

    return {
        "tithi": tithi,
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
    }

def fuerza_contextual_planeta(planeta, posiciones):
    fila = posiciones[posiciones["Planeta"] == planeta]

    if len(fila) == 0:
        return 1.0

    p = fila.iloc[0]
    _, mult = dignidad_planeta(p["Planeta"], p["Signo"])

    fuerza = mult

    if p["Retrógrado"]:
        if planeta in ["♂ Marte", "♄ Saturno"]:
            fuerza *= 1.10
        elif planeta in ["♃ Júpiter", "♀ Venus", "☿ Mercurio"]:
            fuerza *= 0.85

    if p["Grado"] < 3 or p["Grado"] > 27:
        fuerza *= 0.90
    elif 10 <= p["Grado"] <= 20:
        fuerza *= 1.10

    return round(fuerza, 2)


def score_aspectos_contextuales(aspectos, posiciones):
    direction = 0
    speculation = 0
    volatility = 0

    for a in aspectos:
        p1 = a["planeta_1"]
        p2 = a["planeta_2"]

        f1 = fuerza_contextual_planeta(p1, posiciones)
        f2 = fuerza_contextual_planeta(p2, posiciones)

        fuerza_total = a["fuerza"] * ((f1 + f2) / 2)

        if a["aspecto"] in [0, 120]:
            direction += 3 * fuerza_total
            speculation += 1.5 * fuerza_total

        elif a["aspecto"] == 60:
            direction += 1.5 * fuerza_total
            speculation += 0.8 * fuerza_total

        elif a["aspecto"] == 90:
            direction -= 2.5 * fuerza_total
            volatility += 5 * fuerza_total

        elif a["aspecto"] == 180:
            direction -= 3.5 * fuerza_total
            volatility += 6 * fuerza_total

    return {
        "direction": round(direction, 2),
        "speculation": round(speculation, 2),
        "volatility": round(volatility, 2),
    }

def nakshatra_pada(longitud):
    tamaño_nak = 360 / 27
    tamaño_pada = tamaño_nak / 4

    pos_en_nak = longitud % tamaño_nak
    pada = int(pos_en_nak // tamaño_pada) + 1

    return pada

PADA_POWER = {
    1: 1.03,
    2: 1.00,
    3: 0.98,
    4: 1.02,
}

if __name__ == "__main__":
    fecha = datetime(2026, 4, 13)

    resultado = evaluar_semana(fecha)

    print("Semana:", resultado["lunes"].strftime("%d/%m/%Y"))
    print("Lectura:", resultado["lectura"])
    print("Energía media:", resultado["energia_media"])
    print("Dirección:", resultado["direction_media"])
    print("Especulación:", resultado["speculation_media"])
    print("Volatilidad:", resultado["volatility_media"])
    print("Dominante lunes:", resultado["dias"][0]["planeta_dominante"])
