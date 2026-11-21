import re
import unicodedata

# Tipos de problemas y su puntaje base.
REGLAS = [
    # Emergencias / exposición aguda: base 5
    ("Incendio", 5, [
        "incendio", "fuego fuera de control", "incendio forestal",
        "incendio industrial", "incendio en fabrica", "fuego descontrolado",
    ]),
    
    ("Explosion", 5, [
        "explosion","explosiones", "estallido industrial",
    ]),
    
    ("Fuga de gas", 5, [
        "fuga de gas", "escape de gas", "fuga de gas licuado",
        "fuga de gas natural", "fuga de glp", "escape de amoniaco",
        "fuga de amoniaco", "fuga de cloro", "liberacion de gas toxico",
    ]),
    
    ("Derrame de hidrocarburos", 5, [
        "derrame de petroleo", "derrame de crudo", "derrame de hidrocarburos",
        "derrame de hidrocarburo", "derrame de diesel", "derrame de bencina",
        "derrame de gasolina", "derrame de combustible", "petroleo derramado",
        "combustible derramado", "fuga de combustible", "filtracion de combustible",
        "mancha de petroleo", "vertido de petroleo", "vertimiento de petroleo",
        "vertimiento de hidrocarburos", "derrame de aceite industrial",
    ]),
    
    ("Derrame quimico", 5, [
        "derrame quimico", "sustancia toxica", "derrame de acido", 
        "derrame de solvente", "vertido de sustancias toxicas", 
        "vertimiento de sustancias toxicas",
        "fuga de sustancias toxicas", "sustancia toxica derramada",
        "derrame de productos quimicos", "derrame de pesticidas",
    ]),
    
    ("Intoxicacion", 5, [
        "intoxicacion", "intoxicaciones", "personas intoxicadas",
        "intoxicados por humo", "intoxicados por gases",
        "desmayo por gases", "desmayos por gases", "envenenamiento por gases",
    ]),
    
    ("Gases toxicos", 5, [
        "nube toxica", "nube de gas toxico", "gases toxicos liberados",
        "emanacion de gases toxicos", "liberacion de gases toxicos",
    ]),
    
    # Impactos severos cuando el texto describe una condición concreta: base 4
    ("Residuos peligrosos", 4, [
        "residuos toxicos abandonados", "residuos peligrosos abandonados",
        "desechos toxicos abandonados", "tambores con quimicos abandonados",
        "asbesto abandonado", "material con asbesto abandonado",
    ]),
    
    ("Emision de contaminantes peligrosos", 4, [
        "emision de benceno", "emisiones de benceno",
        "emision de dioxido de azufre", "emisiones de dioxido de azufre",
        "liberacion de benceno", "emision de gases toxicos",
    ]),
    
    ("Mortandad importante de fauna", 4, [
        "mortandad masiva de peces", "peces muertos por cientos",
        "aves empetroladas", "aves cubiertas de petroleo",
        "fauna cubierta de petroleo", "mortandad masiva de aves",
    ]),

    # Contaminación concreta / daños observables: base 3
    ("Aguas servidas", 3, [
        "descarga de aguas servidas", "aguas servidas al mar",
        "aguas servidas en la playa", "vertimiento de aguas servidas",
        "alcantarillado desbordado", "rebalse de alcantarillado",
    ]),

    ("Vertimiento no identificado", 3, [
        "descarga de liquido desconocido", "vertimiento de liquido desconocido",
        "tuberia descarga liquido al mar", "descarga de liquido al mar",
        "liquido sospechoso en el mar",
    ]),

    ("Contaminacion por aceites", 3, [
        "mancha aceitosa", "pelicula aceitosa en el agua",
        "agua con aceite industrial", "manchas de aceite en la playa",
    ]),

    ("Destruccion de ecosistemas", 3, [
        "relleno de humedal", "destruccion de humedal",
        "tala de bosque nativo", "tala ilegal de arboles nativos",
        "destruccion de vegetacion nativa", "extraccion ilegal de aridos",
        "destruccion de dunas", "intervencion de humedal",
    ]),

    # Problemas ambientales relevantes: base 2
    ("Humo", 2, [
        "humo", "humareda", "humo negro","emisiones contaminantes",
        "emisiones industriales", "gases contaminantes", "hollin",
        "humo de chimenea", "humo industrial",
    ]),
    
    ("Polvo y material particulado", 2, [
        "polvo industrial", "polvillo industrial", "material particulado",
        "ceniza industrial", "cenizas industriales", "polvo de carbon",
        "polvo en suspension", "particulas en suspension",
    ]),
    
    ("Agua contaminada", 2, [
        "agua contaminada", "contaminacion del agua", "contaminacion del mar",
        "agua de color extrano", "agua con espuma extrana",
        "agua turbia por descargas", "espuma sospechosa en el agua",
    ]),

    ("Suelo contaminado", 2, [
        "suelo contaminado", "contaminacion del suelo", "tierra contaminada",
        "terreno contaminado", "filtracion al suelo",
    ]),

    ("Dano ambiental", 2, [
        "peces muertos", "mortandad de peces", "aves muertas",
        "animales muertos en la playa", "fauna afectada",
        "vegetacion afectada", "plantas secas por contaminacion",
    ]),

    ("Residuos en playas y mar", 2, [
        "basura en la playa", "residuos en el mar", "plasticos en el mar",
        "basura flotando en el mar", "redes abandonadas en la playa",
        "neumaticos en la playa",
    ]),

    ("Vertedero irregular", 2, [
        "vertedero clandestino", "basural ilegal", "quema de basura",
        "quema de residuos", "quema de neumaticos",
    ]),

    ("Olor a combustible", 2, [
        "olor a petroleo", "olor a combustible", "olor a diesel",
        "olor a gasolina", "olor a bencina", "olor a gas",
        "olor a solventes", "olor quimico intenso",
    ]),

    # Molestias y problemas de menor intensidad descrita: base 1
    ("Residuos", 1, [
        "basura acumulada", "microbasural", "escombros abandonados",
        "neumaticos abandonados", "residuos acumulados",
        "basura domiciliaria acumulada",
    ]),

    ("Olores", 1, [
        "malos olores", "olor fuerte", "mal olor", "olor desagradable",
        "hedor persistente", "olor nauseabundo",
    ]),
    
    ("Ruidos", 1, [
        "ruidos molestos", "ruido excesivo", "ruidos constantes",
        "vibraciones industriales", "ruido industrial", "maquinaria ruidosa",
    ]),

    ("Contaminacion luminica", 1, [
        "contaminacion luminica", "luz invasiva nocturna",
        "exceso de iluminacion nocturna",
    ]),
]


# Situaciones que pueden aumentar la prioridad.
CONTEXTOS = [
    ("Problema recurrente", [
        "todos los dias", "cada dia", "desde hace semanas", "recurrente",
        "constantemente", "siempre", "casi siempre", "todas las noches",
        "cada noche", "desde hace meses", "varias veces por semana",
    ]),
    
    ("Lugar sensible", [
        "colegio", "escuela", "hospital", "jardin infantil", "cesfam",
        "asilo de ancianos", "hogar de ancianos", "orfanatos",
        "sala cuna", "centro de salud", "residencia de adultos mayores",
    ]),

    ("Muchas personas afectadas", [
        "muchos vecinos", "varias familias", "muchas personas", 
        "toda la comunidad", "decenas de personas", 
        "numerosas familias", "gran cantidad de vecinos",
    ]),
]


# No se interpretan como eventos confirmados.
NEGACIONES = (
    "no hay", "no hubo", "no existe", "no se observa", "no se observo",
    "no se detecta", "no se detecto", "no se registro", "sin",
    "sin evidencia de", "sin indicios de", "simulacro de",
    "falsa alarma de", "se descarto", "se descarta",
    "no se produjo", "no ocurrio", "no ocurrira",
)
POSIBILIDADES = (
    "riesgo de", "posible", "posibles", "podria haber", "puede haber",
    "sospecha de", "presunto", "presunta", "aparente", "aparentemente",
    "temor de", "probable", "posibilidad de",
)


def normalizar(texto):
    texto = str(texto or "")
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        letra for letra in texto
        if unicodedata.category(letra) != "Mn"
    )


def buscar_estado_previo(texto, inicio):
    """Detecta negación o posibilidad justo antes de una expresión.

    Una ventana corta y un patrón anclado reducen asociaciones con frases lejanas.
    No pretende comprender lenguaje natural libre con exactitud.
    """
    anterior = texto[max(0, inicio - 85):inicio]
    articulos = r"(?:(?:un|una|unos|unas|el|la|los|las)\s+)?"

    for expresion in NEGACIONES:
        patron = r"\b" + re.escape(expresion) + r"\s+" + articulos + r"$"
        if re.search(patron, anterior):
            return "negado"

    for expresion in POSIBILIDADES:
        patron = r"\b" + re.escape(expresion) + r"\s+" + articulos + r"$"
        if re.search(patron, anterior):
            return "posible"

    return "afirmado"


def clasificar_reporte(titulo, descripcion):
    texto = normalizar(titulo + " " + descripcion)

    puntaje_base = 0
    motivos = []
    hay_confirmado = False

    for nombre, puntos, expresiones in REGLAS:
        for expresion in expresiones:
            patron = r"\b" + re.escape(expresion) + r"\b"

            for coincidencia in re.finditer(patron, texto):
                estado = buscar_estado_previo(texto, coincidencia.start())

                if estado == "negado":
                    continue

                puntos_actuales = min(puntos, 2) if estado == "posible" else puntos
                puntaje_base = max(puntaje_base, puntos_actuales)
                if estado == "afirmado":
                    hay_confirmado = True
                if nombre not in motivos:
                    motivos.append(nombre)

    adicionales = 0
    if puntaje_base > 0:
        for nombre, expresiones in CONTEXTOS:
            if any(
                re.search(r"\b" + re.escape(expresion) + r"\b", texto)
                for expresion in expresiones
            ):
                adicionales += 1
                motivos.append(nombre)

    puntaje = min(5, puntaje_base + min(adicionales, 2))
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
        "motivos": motivos,
    }
