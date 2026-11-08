from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from .models import Reporte, Apelacion

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
