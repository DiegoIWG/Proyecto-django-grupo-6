
# Tu opinión SÍ importa

Proyecto de aplicación web desarrollado con Django y con ayuda de la IA
## Descripción

Foro ciudadano para publicar y consultar reportes
sobre problemas ambientales de Quintero, Puchuncaví
y Ventanas.

## Funcionalidades

- Crear reportes ambientales.
- Consultar publicaciones en un foro.
- Clasificar automáticamente los reportes por prioridad.
- Seleccionar ubicaciones mediante un mapa.
- Obtener direcciones aproximadas.
- Filtrar reportes por sector y prioridad.

## Requisitos

- Python compatible con Django 5.2.
- Conexión a internet para instalar dependencias
  y utilizar los servicios del mapa.

## Instalación en Windows

Abrir una terminal en la carpeta que contiene manage.py.

Crear el entorno virtual:

    py -m venv .venv

Instalar Django:

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Preparar la base de datos:

    .\.venv\Scripts\python.exe manage.py migrate

Iniciar el servidor:

    .\.venv\Scripts\python.exe manage.py runserver

Abrir en el navegador:

http://127.0.0.1:8000/

## Pruebas

Ejecutar:

    .\.venv\Scripts\python.exe manage.py test reportes

## Clasificación ambiental

La aplicación analiza el título y la descripción
del reporte mediante reglas programadas en Python.

La prioridad puede ser Baja, Media o Alta.

La clasificación es preliminar y no constituye
una evaluación oficial del riesgo ambiental.

## Limitaciones

La aplicación se ejecuta localmente.

Los datos se almacenan en SQLite.

La ubicación indicada por el usuario y la
información de los reportes no están verificadas
por una autoridad.

La visualización del mapa y la búsqueda de
direcciones requieren conexión a internet.
