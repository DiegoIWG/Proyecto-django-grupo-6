from django.db import models

# Create your models here.
class Reporte(models.Model):

    SECTORES = [
        ('quintero', 'Quintero'),
        ('puchuncavi', 'Puchuncaví'),
        ('ventanas', 'Ventanas'),
    ]

    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    sector = models.CharField(max_length=20, choices=SECTORES)
    direccion = models.CharField(max_length=200, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo