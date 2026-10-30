from django.db import models
from .clasificacion import clasificar_reporte

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
    
    latitud = models.FloatField(
        null=True,
        blank=True
    )

    longitud = models.FloatField(
        null=True,
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    puntaje = models.PositiveSmallIntegerField(
        default=0,
        editable=False
    )

    prioridad = models.CharField(
        max_length=5,
        default='Baja',
        editable=False
    )

    motivos = models.JSONField(
        default=list,
        blank=True,
        editable=False
    )

    def save(self, *args, **kwargs):

        resultado = clasificar_reporte(
            self.titulo,
            self.descripcion
        )

        self.puntaje = resultado['puntaje']
        self.prioridad = resultado['prioridad']
        self.motivos = resultado['motivos']

        super().save(*args, **kwargs)


    def __str__(self):
        return self.titulo