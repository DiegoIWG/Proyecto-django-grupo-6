from django.shortcuts import render, redirect, get_object_or_404
from .models import Reporte
from .forms import ReporteForm


def inicio(request):
    reportes = Reporte.objects.all().order_by('-fecha_creacion')

    contexto = {
        'reportes': reportes
    }

    return render(request, 'reportes/inicio.html', contexto)


def crear_reporte(request):

    if request.method == 'POST':
        formulario = ReporteForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            return redirect('inicio')

    else:
        formulario = ReporteForm()

    contexto = {
        'formulario': formulario
    }

    return render(request, 'reportes/crear_reporte.html', contexto)


def detalle_reporte(request, reporte_id):

    reporte = get_object_or_404(Reporte, id=reporte_id)

    contexto = {
        'reporte': reporte
    }

    return render(
        request,
        'reportes/detalle_reporte.html',
        contexto
    )

