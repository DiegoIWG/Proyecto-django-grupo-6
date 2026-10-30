from django.test import SimpleTestCase
from .clasificacion import clasificar_reporte


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
