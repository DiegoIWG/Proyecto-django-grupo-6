from django.test import SimpleTestCase, TestCase
from .clasificacion import clasificar_reporte
from .models import Reporte
from .clasificacion import clasificar_reporte
from django.urls import reverse

class PruebasClasificacion(SimpleTestCase):

    def test_incendio(self):
        resultado = clasificar_reporte(
            "Incendio en fabrica",
            "Hay un incendio activo."
        )
        self.assertEqual(resultado["prioridad"], "Alta")

    def test_humo(self):
        resultado = clasificar_reporte(
            "Humo en Quintero",
            "Hay humo saliendo de una fabrica."
        )
        self.assertEqual(resultado["prioridad"], "Media")

    def test_humo_recurrente(self):
        resultado = clasificar_reporte(
            "Humo en colegio",
            "Hay humo todos los dias cerca de un colegio."
        )
        self.assertEqual(resultado["prioridad"], "Alta")

    def test_basura(self):
        resultado = clasificar_reporte(
            "Basura acumulada",
            "Hay basura acumulada en un terreno."
        )
        self.assertEqual(resultado["prioridad"], "Baja")

    def test_negacion(self):
        resultado = clasificar_reporte(
            "Reporte ambiental",
            "No hay incendio, pero hay humo."
        )
        self.assertEqual(resultado["prioridad"], "Media")

    def test_riesgo_posible(self):
        resultado = clasificar_reporte(
            "Riesgo de incendio",
            "Existe riesgo de incendio en el sector."
        )
        self.assertEqual(resultado["prioridad"], "Media")


class PruebasReporte(TestCase):

    def test_clasificacion_al_crear(self):

        reporte = Reporte.objects.create(
            titulo="Humo en Quintero",
            descripcion="Hay humo cerca de viviendas.",
            sector="quintero"
        )

        self.assertEqual(reporte.prioridad, "Media")
        self.assertEqual(reporte.puntaje, 2)

    def test_clasificacion_al_editar(self):

        reporte = Reporte.objects.create(
            titulo="Basura acumulada",
            descripcion="Hay basura acumulada.",
            sector="ventanas"
        )

        self.assertEqual(reporte.prioridad, "Baja")

        reporte.titulo = "Incendio en el sector"
        reporte.descripcion = "Hay un incendio activo."
        reporte.save()

        reporte.refresh_from_db()

        self.assertEqual(reporte.prioridad, "Alta")
        self.assertEqual(reporte.puntaje, 5)


class PruebasForo(TestCase):

    def test_publicar_reporte(self):

        datos = {
            'titulo': 'Humo cerca de un colegio',
            'descripcion': 'Hay humo todos los dias cerca de un colegio.',
            'sector': 'quintero',
            'direccion': 'Direccion de prueba',
            'latitud': -32.78766,
            'longitud': -71.53228,
        }

        respuesta = self.client.post(
            reverse('crear_reporte'),
            datos
        )

        self.assertRedirects(respuesta, reverse('inicio'))

        reporte = Reporte.objects.get(
            titulo='Humo cerca de un colegio'
        )

        self.assertEqual(reporte.prioridad, 'Alta')
        self.assertEqual(reporte.puntaje, 4)
        self.assertAlmostEqual(reporte.latitud, -32.78766)

        pagina = self.client.get(reverse('inicio'))
        self.assertContains(pagina, reporte.titulo)

    def test_formulario_incompleto(self):

        respuesta = self.client.post(
            reverse('crear_reporte'),
            {
                'titulo': '',
                'descripcion': 'Hay humo en el sector.',
                'sector': 'quintero',
            }
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Reporte.objects.exists())

    def test_filtros(self):

        reporte1 = Reporte.objects.create(
            titulo='Humo en Quintero',
            descripcion='Hay humo en el sector.',
            sector='quintero'
        )

        Reporte.objects.create(
            titulo='Incendio en Ventanas',
            descripcion='Hay un incendio activo.',
            sector='ventanas'
        )

        respuesta = self.client.get(
            reverse('inicio'),
            {
                'sector': 'quintero',
                'prioridad': 'Media',
            }
        )

        encontrados = list(respuesta.context['reportes'])

        self.assertEqual(encontrados, [reporte1])

    def test_detalle_con_mapa(self):

        reporte = Reporte.objects.create(
            titulo='Contaminacion ambiental',
            descripcion='Hay humo en la zona.',
            sector='quintero',
            latitud=-32.78766,
            longitud=-71.53228
        )

        respuesta = self.client.get(
            reverse('detalle_reporte', args=[reporte.id])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'mapa_reporte')

    def test_reporte_inexistente(self):

        respuesta = self.client.get(
            reverse('detalle_reporte', args=[999999])
        )

        self.assertEqual(respuesta.status_code, 404)
