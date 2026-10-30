from django.shortcuts import render
from .models import Reporte


def inicio(request):
    reportes = Reporte.objects.all().order_by('-fecha_creacion')

    contexto = {
        'reportes': reportes
    }

    return render(request, 'reportes/inicio.html', contexto)
