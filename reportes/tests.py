from django.test import SimpleTestCase, TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from .clasificacion import clasificar_reporte
from .models import Reporte, Apoyo, Apelacion
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
    
    def test_reactivacion_conserva_fecha_original(self):

        self.antiguo.refresh_from_db()

        fecha_original = self.antiguo.fecha_creacion

        self.antiguo.fecha_reactivacion = timezone.now()

        self.antiguo.save(
            update_fields=['fecha_reactivacion']
        )

        self.antiguo.refresh_from_db()

        self.assertEqual(
            self.antiguo.fecha_creacion,
            fecha_original
        )

        self.assertFalse(
            self.antiguo.esta_archivado
        )

        foro = self.client.get(reverse('inicio'))
        historial = self.client.get(reverse('historial'))

        self.assertIn(
            self.antiguo,
            foro.context['reportes']
        )

        self.assertNotIn(
            self.antiguo,
            historial.context['reportes']
        )


class PruebasApelaciones(TestCase):

    def setUp(self):
        self.reporte = Reporte.objects.create(
            titulo="Humo persistente",
            descripcion="Hay humo todos los dias.",
            sector="quintero"
        )

        Reporte.objects.filter(
            id=self.reporte.id
        ).update(
            fecha_creacion=timezone.now()
            - timedelta(days=22)
        )

        self.reporte.refresh_from_db()

        self.url = reverse(
            'solicitar_apelacion',
            args=[self.reporte.id]
        )

    def test_enviar_apelacion(self):
        respuesta = self.client.post(
            self.url,
            {
                'motivo': (
                    'El humo sigue apareciendo '
                    'todos los dias en el sector.'
                )
            }
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Apelacion.objects.count(), 1)

        apelacion = Apelacion.objects.first()

        self.assertEqual(
            apelacion.estado,
            'pendiente'
        )

        self.assertTrue(
            self.reporte.esta_archivado
        )

    def test_evitar_apelaciones_duplicadas(self):
        datos = {
            'motivo': (
                'El problema ambiental '
                'todavia no se ha solucionado.'
            )
        }

        self.client.post(self.url, datos)
        self.client.post(self.url, datos)

        self.assertEqual(
            Apelacion.objects.count(),
            1
        )

    def test_motivo_demasiado_corto(self):
        respuesta = self.client.post(
            self.url,
            {'motivo': 'Sigue igual'}
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            Apelacion.objects.count(),
            0
        )

    def test_reporte_activo_no_se_apela(self):
        activo = Reporte.objects.create(
            titulo="Problema reciente",
            descripcion="Hay basura en el sector.",
            sector="quintero"
        )

        url = reverse(
            'solicitar_apelacion',
            args=[activo.id]
        )

        respuesta = self.client.post(
            url,
            {
                'motivo': (
                    'El problema ambiental '
                    'todavia no se ha solucionado.'
                )
            }
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            Apelacion.objects.count(),
            0
        )


class PruebasRevisionApelaciones(TestCase):

    def setUp(self):
        administrador = get_user_model().objects.create_superuser(
            username='admin_pruebas',
            email='admin@example.com',
            password='clave_de_prueba_123'
        )

        self.client.force_login(administrador)

        self.reporte = Reporte.objects.create(
            titulo='Humo persistente',
            descripcion='Hay humo en el sector.',
            sector='quintero'
        )

        Reporte.objects.filter(
            pk=self.reporte.pk
        ).update(
            fecha_creacion=timezone.now()
            - timedelta(days=22)
        )

        self.reporte.refresh_from_db()

        self.apelacion = Apelacion.objects.create(
            reporte=self.reporte,
            motivo='El problema sigue sin solucionarse.'
        )

        self.url = reverse(
            'admin:reportes_apelacion_change',
            args=[self.apelacion.pk]
        )

    def revisar(self, estado, respuesta):
        return self.client.post(
            self.url,
            {
                'estado': estado,
                'respuesta_revision': respuesta,
                '_save': 'Guardar',
            }
        )

    def test_aprobar_con_justificacion(self):

        respuesta = self.revisar(
            'aprobada',
            'Se aprueba porque el problema ambiental continúa.'
        )

        self.assertEqual(respuesta.status_code, 302)

        self.apelacion.refresh_from_db()
        self.reporte.refresh_from_db()

        self.assertEqual(
            self.reporte.numero_periodo,
            2
        )

        self.assertEqual(
            self.apelacion.estado,
            'aprobada'
        )

        self.assertFalse(
            self.reporte.esta_archivado
        )

        self.assertIsNotNone(
            self.apelacion.fecha_revision
        )

        detalle = self.client.get(
            reverse(
                'detalle_reporte',
                args=[self.reporte.pk]
            )
        )

        self.assertContains(
            detalle,
            'Se aprueba porque el problema ambiental continúa.'
        )

    def test_rechazar_con_justificacion(self):

        respuesta = self.revisar(
            'rechazada',
            'Se rechaza porque la solicitud no aporta información suficiente.'
        )

        self.assertEqual(respuesta.status_code, 302)

        self.apelacion.refresh_from_db()
        self.reporte.refresh_from_db()

        self.assertEqual(
            self.apelacion.estado,
            'rechazada'
        )

        self.assertTrue(
            self.reporte.esta_archivado
        )

    def test_justificacion_obligatoria(self):

        respuesta = self.revisar(
            'aprobada',
            ''
        )

        self.assertEqual(respuesta.status_code, 200)

        self.apelacion.refresh_from_db()
        self.reporte.refresh_from_db()

        self.assertEqual(
            self.apelacion.estado,
            'pendiente'
        )

        self.assertTrue(
            self.reporte.esta_archivado
        )

    def test_no_aprobar_dos_veces(self):

        self.revisar(
            'aprobada',
            'Se confirma que el problema ambiental continúa.'
        )

        self.reporte.refresh_from_db()
        primera_fecha = self.reporte.fecha_reactivacion

        segunda_respuesta = self.revisar(
            'aprobada',
            'Intento de aprobar nuevamente la apelación.'
        )

        self.reporte.refresh_from_db()

        self.assertEqual(
            segunda_respuesta.status_code,
            403
        )

        self.assertEqual(
            self.reporte.fecha_reactivacion,
            primera_fecha
        )


class PruebasApoyosPorPeriodo(TestCase):
    def setUp(self):
        self.reporte = Reporte.objects.create(
            titulo='Humo persistente',
            descripcion='Hay humo en el sector.',
            sector='quintero'
        )

        self.url = reverse(
            'apoyar_reporte',
            args=[self.reporte.pk]
        )

    def reactivar_reporte(self):

        Reporte.objects.filter(
            pk=self.reporte.pk
        ).update(
            fecha_creacion=timezone.now()
            - timedelta(days=22)
        )

        self.reporte.refresh_from_db()

        self.assertTrue(
            self.reporte.esta_archivado
        )

        self.reporte.numero_periodo += 1
        self.reporte.fecha_reactivacion = timezone.now()

        self.reporte.save(
            update_fields=[
                'numero_periodo',
                'fecha_reactivacion'
            ]
        )

    def test_conservar_apoyos_anteriores(self):

        self.client.post(self.url)

        self.assertEqual(
            Apoyo.objects.count(),
            1
        )

        self.reactivar_reporte()

        detalle = self.client.get(
            reverse(
                'detalle_reporte',
                args=[self.reporte.pk]
            )
        )

        self.assertEqual(
            detalle.context['apoyos_actuales'],
            0
        )

        self.assertEqual(
            detalle.context['apoyos_anteriores'],
            1
        )

        self.client.post(self.url)

        self.assertEqual(
            Apoyo.objects.count(),
            2
        )

        self.assertEqual(
            Apoyo.objects.filter(
                periodo=1
            ).count(),
            1
        )

        self.assertEqual(
            Apoyo.objects.filter(
                periodo=2
            ).count(),
            1
        )

    def test_quitar_apoyo_actual_no_borra_anterior(self):

        self.client.post(self.url)

        self.reactivar_reporte()

        self.client.post(self.url)
        self.client.post(self.url)

        self.assertEqual(
            Apoyo.objects.count(),
            1
        )

        self.assertEqual(
            Apoyo.objects.first().periodo,
            1
        )


class PruebasOrdenForo(TestCase):

    def setUp(self):
        self.reactivado = Reporte.objects.create(
            titulo='Reporte reactivado',
            descripcion='Hay humo en el sector.',
            sector='quintero'
        )

        self.reciente = Reporte.objects.create(
            titulo='Reporte reciente',
            descripcion='Hay basura en el sector.',
            sector='puchuncavi'
        )

        ahora = timezone.now()

        Reporte.objects.filter(
            pk=self.reactivado.pk
        ).update(
            fecha_creacion=ahora - timedelta(days=40),
            fecha_reactivacion=ahora - timedelta(hours=2),
            numero_periodo=2
        )

        Reporte.objects.filter(
            pk=self.reciente.pk
        ).update(
            fecha_creacion=ahora - timedelta(days=2)
        )

        # Cuatro apoyos del período anterior
        for numero in range(4):
            Apoyo.objects.create(
                reporte=self.reactivado,
                sesion=f'antiguo_{numero}',
                periodo=1
            )

        # Un apoyo del período actual
        Apoyo.objects.create(
            reporte=self.reactivado,
            sesion='actual_1',
            periodo=2
        )

        # Dos apoyos en el reporte reciente
        for numero in range(2):
            Apoyo.objects.create(
                reporte=self.reciente,
                sesion=f'reciente_{numero}',
                periodo=1
            )

    def test_ordenar_por_apoyos_actuales(self):
        respuesta = self.client.get(
            reverse('inicio'),
            {'orden': 'apoyados'}
        )

        reportes = list(respuesta.context['reportes'])

        self.assertEqual(
            reportes[0].pk,
            self.reciente.pk
        )

        self.assertEqual(
            reportes[0].total_apoyos,
            2
        )

        self.assertEqual(
            reportes[1].total_apoyos,
            1
        )

    def test_ordenar_por_fecha_vigente(self):
        respuesta = self.client.get(
            reverse('inicio'),
            {'orden': 'recientes'}
        )

        reportes = list(respuesta.context['reportes'])

        self.assertEqual(
            reportes[0].pk,
            self.reactivado.pk
        )

    def test_orden_invalido(self):
        respuesta = self.client.get(
            reverse('inicio'),
            {'orden': 'desconocido'}
        )

        self.assertEqual(
            respuesta.context['orden'],
            'recientes'
        )

    def test_combinar_filtro_y_orden(self):
        respuesta = self.client.get(
            reverse('inicio'),
            {
                'sector': 'quintero',
                'orden': 'apoyados'
            }
        )

        reportes = list(respuesta.context['reportes'])

        self.assertEqual(len(reportes), 1)

        self.assertEqual(
            reportes[0].pk,
            self.reactivado.pk
        )
