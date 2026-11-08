from django.test import SimpleTestCase, TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from .clasificacion import clasificar_reporte
from .models import Reporte, Apoyo
from .clasificacion import clasificar_reporte
from datetime import timedelta


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


class PruebasApoyos(TestCase):

    def setUp(self):
        self.reporte = Reporte.objects.create(
            titulo="Humo en Quintero",
            descripcion="Hay humo todos los dias.",
            sector="quintero"
        )

        self.url = reverse(
            'apoyar_reporte',
            args=[self.reporte.id]
        )

    def test_agregar_y_quitar_apoyo(self):
        self.client.post(self.url)

        self.assertEqual(
            Apoyo.objects.count(), 1
        )

        self.assertIn(
            settings.SESSION_COOKIE_NAME,
            self.client.cookies
        )

        self.client.post(self.url)

        self.assertEqual(
            Apoyo.objects.count(), 0
        )

    def test_dos_navegadores(self):
        otro_navegador = Client()

        self.client.post(self.url)
        otro_navegador.post(self.url)

        self.assertEqual(
            Apoyo.objects.count(), 2
        )

    def test_no_permite_get(self):
        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code, 405
        )

        self.assertEqual(
            Apoyo.objects.count(), 0
        )

    def test_prioridad_no_cambia(self):
        prioridad_original = self.reporte.prioridad
        puntaje_original = self.reporte.puntaje

        self.client.post(self.url)

        self.reporte.refresh_from_db()

        self.assertEqual(
            self.reporte.prioridad,
            prioridad_original
        )

        self.assertEqual(
            self.reporte.puntaje,
            puntaje_original
        )

    def test_contador_en_foro(self):
        self.client.post(self.url)

        respuesta = self.client.get(
            reverse('inicio')
        )

        reporte = respuesta.context['reportes'].get(
            id=self.reporte.id
        )

        self.assertEqual(
            reporte.total_apoyos, 1
        )


class PruebasArchivado(TestCase):

    def setUp(self):
        self.activo = Reporte.objects.create(
            titulo="Reporte reciente",
            descripcion="Hay humo en el sector.",
            sector="quintero"
        )

        self.antiguo = Reporte.objects.create(
            titulo="Reporte antiguo",
            descripcion="Hay humo en el sector.",
            sector="quintero"
        )

        Reporte.objects.filter(
            pk=self.antiguo.pk
        ).update(
            fecha_creacion=timezone.now()
            - timedelta(days=22)
        )

    def test_solo_activos_en_foro(self):
        respuesta = self.client.get(
            reverse('inicio')
        )

        reportes = respuesta.context['reportes']

        self.assertIn(self.activo, reportes)
        self.assertNotIn(self.antiguo, reportes)

    def test_antiguos_en_historial(self):
        respuesta = self.client.get(
            reverse('historial')
        )

        reportes = respuesta.context['reportes']

        self.assertIn(self.antiguo, reportes)
        self.assertNotIn(self.activo, reportes)

    def test_detalle_archivado(self):
        respuesta = self.client.get(
            reverse(
                'detalle_reporte',
                args=[self.antiguo.id]
            )
        )

        self.assertEqual(
            respuesta.status_code, 200
        )

        self.assertTrue(
            respuesta.context['archivado']
        )

    def test_archivado_no_recibe_apoyos(self):
        respuesta = self.client.post(
            reverse(
                'apoyar_reporte',
                args=[self.antiguo.id]
            )
        )

        self.assertEqual(
            respuesta.status_code, 403
        )

        self.assertEqual(
            Apoyo.objects.filter(
                reporte=self.antiguo
            ).count(),
            0
        )
    