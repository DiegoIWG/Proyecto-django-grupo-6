# Tu opinión SÍ importa

Aplicación web desarrollada en Django para publicar, consultar y apoyar reportes ciudadanos sobre problemas ambientales de las comunas de **Quintero** y **Puchuncaví** (incluida la localidad de **Ventanas**).

Es un proyecto académico del equipo **Los 214B (Grupo 6)** para IWG400. Durante su desarrollo se utilizaron herramientas de inteligencia artificial como apoyo para comprender, revisar y mejorar código; las decisiones de implementación corresponden al equipo.

## Funcionalidades

- **Reportes ambientales:** personas con sesión iniciada pueden crear reportes con título, descripción, comuna y una ubicación opcional en el mapa. También pueden consultar sus propios reportes.
- **Clasificación automática:** el título y la descripción se procesan mediante reglas programadas en Python, que generan un puntaje, una prioridad (*Baja*, *Media* o *Alta*) y motivos explicativos.
- **Mapa y ubicación:** permite seleccionar coordenadas en Quintero o Puchuncaví. La ubicación se comprueba contra polígonos comunales guardados en un archivo GeoJSON. Se intenta obtener una dirección aproximada mediante un servicio externo.
- **Foro público:** muestra reportes activos; permite filtrar por comuna y prioridad, además de ordenar por fecha o por apoyos del período vigente.
- **Apoyos ciudadanos:** usuarios registrados pueden apoyar o retirar su apoyo a un reporte activo. Se admite un apoyo por cuenta y por período de vigencia. Los apoyos no cambian la prioridad ambiental.
- **Comentarios:** usuarios registrados pueden comentar reportes activos. Los comentarios pueden ocultarse desde la administración.
- **Historial:** los reportes dejan de aparecer en el foro principal después de **21 días**, pero siguen consultables. Que un reporte esté archivado **no significa que el problema se haya resuelto**.
- **Apelaciones y reactivación:** se puede solicitar la reactivación de un reporte archivado. Un administrador revisa la solicitud y puede aprobarla o rechazarla con una justificación; si se aprueba, comienza un nuevo período de 21 días.
- **Cuentas:** registro e inicio de sesión utilizando RUT normalizado, contraseña y correo electrónico. El alias público es opcional. Se utiliza la autenticación incorporada de Django.

## Tecnologías

- Python y **Django 5.2.18** (versión fijada en `requirements.txt`).
- **SQLite** para persistencia de datos local.
- **HTML, CSS y JavaScript** para las páginas.
- **MapLibre GL JS** para los mapas y un servicio cartográfico externo para la visualización.
- **GeoJSON** local para validar los límites de las comunas.
- Servicio externo de geocodificación inversa para intentar mostrar direcciones aproximadas.

## Instalación y ejecución en Windows

Se necesita Python compatible con Django 5.2, conexión a Internet para instalar dependencias y acceso a Internet para cargar los servicios cartográficos externos.

Abrir **PowerShell** en la carpeta que contiene `manage.py`.

**1. Crear un entorno virtual:**

```powershell
py -m venv .venv
```

**2. Instalar las dependencias:**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**3. Preparar la base de datos:**

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

**4. Iniciar el servidor local:**

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Abrir <http://127.0.0.1:8000/> en el navegador.

> La base de datos `db.sqlite3` no se distribuye en el repositorio. Cada instalación comienza con una base de datos local creada mediante las migraciones. El GeoJSON de las dos comunas sí debe permanecer dentro del proyecto.

### Crear una cuenta de administración (opcional)

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Panel de administración: <http://127.0.0.1:8000/admin/>.

## Cómo utilizar la aplicación

1. Crear una cuenta o iniciar sesión para publicar un reporte.
2. Completar el título, la descripción y la comuna. Si se usa el mapa, marcar un punto dentro de la comuna seleccionada.
3. Publicar el reporte y consultarlo en el foro. La aplicación calcula automáticamente su prioridad y muestra los motivos.
4. Abrir el detalle de un reporte para ver su ubicación, apoyar la publicación o comentar (las dos últimas acciones requieren sesión iniciada y un reporte activo).
5. Consultar reportes antiguos en el historial. Cuando corresponde, se puede pedir su reactivación para revisión administrativa.


## Clasificación ambiental

La aplicación analiza automáticamente el título y la
descripción de cada reporte mediante reglas de Python.

El sistema reconoce 27 categorías de problemas
ambientales, incluyendo:

- Derrames de petróleo y combustibles.
- Fugas de gases y sustancias químicas.
- Incendios y explosiones.
- Contaminación del aire, agua y suelo.
- Residuos peligrosos y microbasurales.
- Daños a la fauna, flora y ecosistemas.
- Ruidos, olores y emisiones industriales.

### Cálculo de prioridad

Los reportes reciben un puntaje de 0 a 5:

- Baja: 0–1 puntos.
- Media: 2–3 puntos.
- Alta: 4–5 puntos.

El sistema también considera factores como
la recurrencia, los lugares sensibles y
la cantidad de personas afectadas.

La clasificación es preliminar y no constituye
una evaluación oficial del riesgo ambiental.

Los apoyos ciudadanos no modifican la prioridad.


## Pruebas

Desde la carpeta de `manage.py`, ejecutar:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test reportes
```

El proyecto contiene pruebas para clasificación, publicación de reportes, validación geográfica, filtros, autenticación, apoyos, comentarios, archivado y apelaciones.

## Archivos importantes

```text
manage.py
requirements.txt
Tu_opinion_nos_importa/   # Configuración principal de Django
reportes/
  models.py               # Reportes, apoyos, apelaciones y comentarios
  forms.py                # Formularios y validaciones
  views.py                # Flujo de las páginas
  clasificacion.py        # Reglas de prioridad ambiental
  vigencia.py             # Período de 21 días
  rut.py                  # Normalización/validación de RUT
  geografia.py            # Verificación de puntos en polígonos
  datos/limites_comunales.geojson
  templates/reportes/     # Páginas HTML
  static/reportes/css/    # Hoja de estilos
  tests.py                # Pruebas automatizadas
```

## Alcance y limitaciones

- La clasificación es **preliminar**, basada en reglas; no reemplaza una evaluación oficial de riesgo ambiental.
- Las publicaciones, las coordenadas y las direcciones aportadas por usuarios **no están verificadas oficialmente**. La dirección obtenida automáticamente puede ser aproximada o no estar disponible.
- El archivo de límites comunales permite comprobar si un punto se encuentra dentro de la comuna seleccionada, pero no comprueba la veracidad de una denuncia.
- La validación del dígito verificador de un RUT **no confirma la identidad** de quien se registra. El formulario comprueba el formato del correo electrónico, pero **no confirma su propiedad** mediante un mensaje de verificación.
- La plataforma no envía reportes automáticamente a autoridades ni gestiona respuestas oficiales.
- Se trata de una versión académica preparada para uso **local**. Antes de publicarla en Internet sería necesario reforzar seguridad, privacidad, verificación de cuentas, moderación y configuración de despliegue.
- Los mapas y las direcciones aproximadas dependen de servicios externos y pueden requerir conexión a Internet.

## Estado del proyecto

Versión académica funcional en desarrollo y preparación para demostración. Los reportes se conservan en SQLite local y se organizan por períodos de visibilidad de 21 días.
