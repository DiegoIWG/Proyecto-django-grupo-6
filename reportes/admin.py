from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from .models import Reporte, Apelacion, Comentario

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 
                    'sector', 
                    'prioridad',
                    'puntaje',
                    'fecha_creacion'
                    )
    list_filter = ('sector', 'prioridad')
    search_fields = ('titulo', 'descripcion')


class RevisionApelacionForm(forms.ModelForm):

    class Meta:
        model = Apelacion
        fields = ['estado', 'respuesta_revision']

    def clean(self):
        datos = super().clean()

        estado = datos.get('estado')
        respuesta = (
            datos.get('respuesta_revision') or ''
        ).strip()

        if estado in ('aprobada', 'rechazada'):

            if len(respuesta) < 20:
                self.add_error(
                    'respuesta_revision',
                    'La justificación debe tener '
                    'al menos 20 caracteres.'
                )

            if (
                estado == 'aprobada'
                and not self.instance.reporte.esta_archivado
            ):
                self.add_error(
                    'estado',
                    'No se puede reactivar un '
                    'reporte que ya está activo.'
                )

        datos['respuesta_revision'] = respuesta

        return datos


@admin.register(Apelacion)
class ApelacionAdmin(admin.ModelAdmin):

    form = RevisionApelacionForm

    list_display = (
        'id',
        'reporte',
        'solicitante',
        'motivo_resumido',
        'estado',
        'fecha_solicitud',
        'fecha_revision',
    )

    list_filter = ('estado',)

    search_fields = (
        'reporte__titulo',
        'motivo',
    )

    fields = (
        'reporte',
        'motivo',
        'estado',
        'respuesta_revision',
        'fecha_solicitud',
        'fecha_revision',
    )

    readonly_fields = (
        'reporte',
        'motivo',
        'fecha_solicitud',
        'fecha_revision',
    )

    actions = None

    @admin.display(
        description='Motivo de apelación'
    )
    def motivo_resumido(self, obj):
        if len(obj.motivo) > 100:
            return obj.motivo[:100] + '...'

        return obj.motivo

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.estado != 'pendiente':
            return False

        return super().has_change_permission(
            request, obj
        )

    @transaction.atomic
    def save_model(self, request, obj, form, change):

        actual = (
            Apelacion.objects
            .select_for_update()
            .select_related('reporte')
            .get(pk=obj.pk)
        )

        if actual.estado != 'pendiente':
            raise PermissionDenied(
                'Esta apelación ya fue revisada.'
            )

        if obj.estado in ('aprobada', 'rechazada'):

            ahora = timezone.now()
            obj.fecha_revision = ahora

            if obj.estado == 'aprobada':

                reporte = actual.reporte

                if not reporte.esta_archivado:
                    raise PermissionDenied(
                        'El reporte ya está activo.'
                    )
                
                reporte.numero_periodo += 1
                reporte.fecha_reactivacion = ahora

                reporte.save(
                    update_fields=[
                        'numero_periodo',
                        'fecha_reactivacion'
                    ]
                )

        super().save_model(
            request, obj, form, change
        )

    @admin.display(description='Solicitante')
    def solicitante(self, obj):

        if not obj.usuario_id:
            return 'Solicitud anterior al registro'

        alias = (
            obj.usuario.first_name.strip()
            or 'Ciudadano'
        )

        return f'{alias} (cuenta #{obj.usuario_id})'


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'reporte',
        'alias_publico',
        'fecha_creacion',
        'visible'
    )

    list_display_links = ('id',)

    list_editable = ('visible',)

    list_filter = ('visible',)

    search_fields = (
        'alias_publico',
        'contenido',
        'reporte__titulo'
    )

    readonly_fields = (
        'usuario',
        'alias_publico',
        'contenido',
        'fecha_creacion'
    )

    def has_add_permission(self, request):
        return False
