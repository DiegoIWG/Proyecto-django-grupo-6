from django.test import SimpleTestCase, TestCase
from .clasificacion import clasificar_reporte
from .models import Reporte


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
