import json
from functools import lru_cache
from math import isfinite
from pathlib import Path


ARCHIVO = (
    Path(__file__).resolve().parent
    / "datos"
    / "limites_comunales.geojson"
)


@lru_cache(maxsize=1)
def cargar_limites():
    with ARCHIVO.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def dentro_anillo(x, y, anillo):
    dentro = False

    for i in range(len(anillo) - 1):
        x1, y1 = anillo[i]
        x2, y2 = anillo[i + 1]

        cruce = (x2-x1)*(y-y1) - (y2-y1)*(x-x1)

        if (
            abs(cruce) < 1e-10
            and min(x1, x2) <= x <= max(x1, x2)
            and min(y1, y2) <= y <= max(y1, y2)
        ):
            return True

        if (y1 > y) != (y2 > y):
            corte = x1 + (y-y1)*(x2-x1)/(y2-y1)

            if x < corte:
                dentro = not dentro

    return dentro


def punto_en_geometria(longitud, latitud, geometria):
    if geometria["type"] == "Polygon":
        poligonos = [geometria["coordinates"]]
    elif geometria["type"] == "MultiPolygon":
        poligonos = geometria["coordinates"]
    else:
        return False

    for anillos in poligonos:
        exterior = anillos[0]
        huecos = anillos[1:]

        if dentro_anillo(longitud, latitud, exterior):
            if not any(
                dentro_anillo(longitud, latitud, hueco)
                for hueco in huecos
            ):
                return True

    return False


def punto_permitido(sector, longitud, latitud):
    if not isfinite(longitud) or not isfinite(latitud):
        return False

    for feature in cargar_limites()["features"]:
        if feature["properties"]["sector"] == sector:
            return punto_en_geometria(
                longitud,
                latitud,
                feature["geometry"]
            )

    return False
