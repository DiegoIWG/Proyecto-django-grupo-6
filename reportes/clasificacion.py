import re
import unicodedata

# Tipos de problemas y su puntaje base.
REGLAS = [
    ("Incendio", 5, ["incendio", "fuego fuera de control"]),
    ("Explosion", 5, ["explosion"]),
    ("Fuga de gas", 5, ["fuga de gas", "escape de gas"]),
    ("Derrame quimico", 5, ["derrame quimico", "sustancia toxica"]),
    ("Intoxicacion", 5, ["intoxicacion", "personas intoxicadas"]),

    ("Humo", 2, ["humo", "humareda", "emisiones contaminantes"]),
    ("Agua contaminada", 2, ["agua contaminada", "contaminacion del agua"]),
    ("Suelo contaminado", 2, ["suelo contaminado", "contaminacion del suelo"]),
    ("Dano ambiental", 2, ["peces muertos", "mortandad de peces"]),

    ("Residuos", 1, ["basura acumulada", "microbasural"]),
    ("Olores", 1, ["malos olores", "olor fuerte"]),
    ("Ruidos", 1, ["ruidos molestos"]),
]


# Situaciones que pueden aumentar la prioridad.
CONTEXTOS = [
    ("Problema recurrente", [
        "todos los dias", "cada dia", "desde hace semanas",
        "recurrente", "constantemente", "siempre", "casi siempre"
    ]),
    ("Lugar sensible", [
        "colegio", "escuela", "hospital",
        "jardin infantil", "cesfam", "asilo de ancianos",
        "hogar de ancianos", "orfanatos"
    ]),
    ("Muchas personas afectadas", [
        "muchos vecinos", "varias familias",
        "muchas personas", "toda la comunidad"
    ]),
]


def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        letra for letra in texto
        if unicodedata.category(letra) != "Mn"
    )


def clasificar_reporte(titulo, descripcion):
    texto = normalizar(titulo + " " + descripcion)

    puntaje_base = 0
    motivos = []
    hay_confirmado = False

    for nombre, puntos, expresiones in REGLAS:
        for expresion in expresiones:
            patron = r"\b" + re.escape(expresion) + r"\b"

            for coincidencia in re.finditer(patron, texto):
                anterior = texto[max(0, coincidencia.start() - 40):coincidencia.start()]

                negado = re.search(
                    r"(?:no hay|no hubo|no se observa|sin|simulacro de)"
                    r"\s+(?:(?:un|una|el|la)\s+)?$",
                    anterior
                )

                if negado:
                    continue

                posible = re.search(
                    r"(?:riesgo de|posible|podria haber)"
                    r"\s+(?:(?:un|una|el|la)\s+)?$",
                    anterior
                )

                puntos_actuales = min(puntos, 2) if posible else puntos
                puntaje_base = max(puntaje_base, puntos_actuales)

                if not posible:
                    hay_confirmado = True

                if nombre not in motivos:
                    motivos.append(nombre)

    # El contexto solo suma si se reconocio un problema.
    adicionales = 0

    if puntaje_base > 0:
        for nombre, expresiones in CONTEXTOS:
            if any(expresion in texto for expresion in expresiones):
                adicionales += 1
                motivos.append(nombre)

    # Maximo dos puntos adicionales.
    puntaje = min(5, puntaje_base + min(adicionales, 2))

    # Un reporte exclusivamente hipotetico no supera 3.
    if not hay_confirmado:
        puntaje = min(puntaje, 3)

    if puntaje >= 4:
        prioridad = "Alta"
    elif puntaje >= 2:
        prioridad = "Media"
    else:
        prioridad = "Baja"

    return {
        "puntaje": puntaje,
        "prioridad": prioridad,
        "motivos": motivos
    }
