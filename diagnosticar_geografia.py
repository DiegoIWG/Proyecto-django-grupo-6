from reportes.geografia import cargar_limites, punto_permitido


def extraer_puntos(coordenadas):
    if isinstance(coordenadas[0], (int, float)):
        return [coordenadas]

    puntos = []
    for elemento in coordenadas:
        puntos.extend(extraer_puntos(elemento))
    return puntos


datos = cargar_limites()

for zona in datos['features']:
    propiedades = zona['properties']
    geometria = zona['geometry']
    puntos = extraer_puntos(geometria['coordinates'])

    longitudes = [p[0] for p in puntos]
    latitudes = [p[1] for p in puntos]

    print("\nComuna:", propiedades['sector'])
    print("Nombre:", propiedades.get('comuna'))
    print("Geometría:", geometria['type'])
    print("Longitudes:", min(longitudes), max(longitudes))
    print("Latitudes:", min(latitudes), max(latitudes))

print("\nPRUEBAS:")
print("Quintero:", punto_permitido(
    'quintero', -71.52664, -32.78292
))
print("Puchuncaví:", punto_permitido(
    'puchuncavi', -71.42416, -32.73111
))
