from django.db import models
from django.conf import settings
from .clasificacion import clasificar_reporte
from .vigencia import fecha_limite

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


    fecha_reactivacion = models.DateTimeField(
        null=True,
        blank=True
    )

    numero_periodo = models.PositiveIntegerField(
        default=1
    )

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

    @property
    def esta_archivado(self):

        fecha_inicio = (
            self.fecha_reactivacion
            or self.fecha_creacion
        )

        return fecha_inicio <= fecha_limite()

    def __str__(self):
        return self.titulo


class Apoyo(models.Model):

    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        related_name='apoyos'
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apoyos_ciudadanos'
    )

    sesion = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        default=None
        )

    periodo = models.PositiveIntegerField(
        default=1
    )

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reporte', 'sesion', 'periodo'],
                condition=models.Q(
                    usuario__isnull=False
                ),
                name='apoyo_unico_usuario_periodo'
            ),
            
            models.UniqueConstraint(
                fields=['reporte', 'sesion', 'periodo'],
                condition=(
                    models.Q(usuario__isnull=True)
                    & ~models.Q(sesion='')
                ),
                name='apoyo_unico_sesion_anonimo'
            )
        ]


class Apelacion(models.Model):

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        related_name='apelaciones'
    )

    motivo = models.TextField(max_length=1000)

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default='pendiente'
    )

    fecha_solicitud = models.DateTimeField(
        auto_now_add=True
    )
    
    fecha_revision = models.DateTimeField(
        null=True,
        blank=True
    )

    respuesta_revision = models.TextField(
        max_length=1000,
        blank=True,
        default='',
        verbose_name='Respuesta del administrador',
        help_text=(
            'Esta respuesta será visible '
            'para los ciudadanos.'
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reporte'],
                condition=models.Q(estado='pendiente'),
                name='apelacion_pendiente_unica'
            )
        ]

    def __str__(self):
        return f'Apelacion del reporte {self.reporte_id}'

class Comentario(models.Model):

    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        related_name='comentarios'
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comentarios_ciudadanos'
    )

    alias_publico = models.CharField(
        max_length=40
    )

    contenido = models.TextField(
        max_length=1000
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    visible = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ['-fecha_creacion', '-id']

    def __str__(self):
        return f'Comentario de {self.alias_publico}'
