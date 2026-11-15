import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from reportes.geografia import punto_en_geometria

URL = (
    "https://services9.arcgis.com/kKJR3Qt68ohAWuet/"
    "ArcGIS/rest/services/Comunas_de_Chile/"
    "FeatureServer/0/query"
)

parametros = {
    "where": "cut IN (5105,5107)",
    "outFields": "cut,comuna",
    "returnGeometry": "true",
    "outSR": "4326",
    "f": "geojson",
}

solicitud = Request(
    URL + "?" + urlencode(parametros),
    headers={"User-Agent": "ProyectoIWG400/1.0"}
)

with urlopen(solicitud, timeout=40) as respuesta:
    datos = json.load(respuesta)

if datos.get("type") != "FeatureCollection":
    raise RuntimeError(
        f"Respuesta cartográfica inesperada: {datos}"
    )

comunas = {
    5105: ('puchuncavi', 'PUCHUNCAVI'),
    5107: ('quintero', 'QUINTERO'),
}

agrupadas = {
    'puchuncavi': [],
    'quintero': [],
}

cantidad = {
    'puchuncavi': 0,
    'quintero': 0,
}

for feature in datos.get('features', []):

    propiedades = feature['properties']
    codigo = int(propiedades['cut'])

    if codigo not in comunas:
        continue

    sector, nombre = comunas[codigo]

    if propiedades['comuna'].upper() != nombre:
        raise RuntimeError(
            f'Nombre inesperado para {codigo}'
        )

    geometria = feature['geometry']

    if geometria['type'] == 'Polygon':
        partes = [geometria['coordinates']]

    elif geometria['type'] == 'MultiPolygon':
        partes = geometria['coordinates']

    else:
        raise RuntimeError('Geometría no reconocida')

    agrupadas[sector].extend(partes)
    cantidad[sector] += 1


resultado = {
    'type': 'FeatureCollection',
    'features': []
}

for sector, partes in agrupadas.items():

    if not partes:
        raise RuntimeError(
            f'No se encontraron polígonos de {sector}'
        )

    resultado['features'].append({
        'type': 'Feature',
        'properties': {
            'sector': sector
        },
        'geometry': {
            'type': 'MultiPolygon',
            'coordinates': partes
        }
    })


# Comprobar puntos de referencia antes de guardar.
referencias = {
    'quintero': (-71.52664, -32.78292),
    'puchuncavi': (-71.42416, -32.73111),
}

for feature in resultado['features']:

    sector = feature['properties']['sector']
    longitud, latitud = referencias[sector]

    correcto = punto_en_geometria(
        longitud,
        latitud,
        feature['geometry']
    )

    print(
        sector,
        'fragmentos encontrados:', cantidad[sector],
        'punto de referencia válido:', correcto
    )

    if not correcto:
        raise RuntimeError(
            f'La geometría de {sector} no pasó '
            'la comprobación. No se sobrescribirá '
            'el archivo GeoJSON.'
        )


destino = Path(
    'reportes/datos/limites_comunales.geojson'
)

destino.parent.mkdir(
    parents=True,
    exist_ok=True
)

destino.write_text(
    json.dumps(resultado, ensure_ascii=False),
    encoding='utf-8'
)

print('GeoJSON actualizado correctamente.')


encontradas = {}

for feature in datos.get("features", []):
    propiedades = feature["properties"]
    codigo = int(propiedades["cut"])

    if codigo not in comunas:
        continue

    sector, nombre_esperado = comunas[codigo]
    nombre = propiedades["comuna"].lower()

    if nombre_esperado not in nombre:
        raise RuntimeError(
            f"El código {codigo} corresponde a {nombre}. "
            "Revisa la fuente antes de continuar."
        )

    geometria = feature.get("geometry")

    if not geometria or geometria["type"] not in (
        "Polygon", "MultiPolygon"
    ):
        raise RuntimeError("Geometría inesperada")

    propiedades["sector"] = sector
    encontradas[sector] = feature

if set(encontradas) != {"quintero", "puchuncavi"}:
    raise RuntimeError(
        "No se encontraron correctamente las dos comunas."
    )

resultado = {
    "type": "FeatureCollection",
    "features": list(encontradas.values())
}

destino = Path("reportes/datos/limites_comunales.geojson")
destino.parent.mkdir(parents=True, exist_ok=True)

destino.write_text(
    json.dumps(resultado, ensure_ascii=False),
    encoding="utf-8"
)

print("GeoJSON guardado correctamente:", destino)
print("Comunas:", ", ".join(encontradas))
