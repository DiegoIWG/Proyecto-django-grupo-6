from django.contrib import admin

# Register your models here.
from .models import Reporte

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'sector', 'fecha_creacion')
    list_filter = ('sector',)
    search_fields = ('titulo', 'descripcion')