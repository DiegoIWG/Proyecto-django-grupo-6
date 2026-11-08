from django.shortcuts import render, redirect, get_object_or_404
from .models import Reporte, Apoyo
from .forms import ReporteForm
from django.views.decorators.http import require_POST
from django.db.models import Count


def inicio(request):
    reportes = Reporte.objects.all()

    # Obtener filtros seleccionados.
    sector = request.GET.get('sector', '')
    prioridad = request.GET.get('prioridad', '')

    # Comprobar sectores validos.
    sectores_validos = [
        codigo for codigo, nombre in Reporte.SECTORES
    ]

    if sector in sectores_validos:
        reportes = reportes.filter(sector=sector)
    else:
        sector = ''

    # Comprobar prioridades validas.
    prioridades = ['Alta', 'Media', 'Baja']

    if prioridad in prioridades:
        reportes = reportes.filter(prioridad=prioridad)
    else:
        prioridad = ''

    # Ordenar por fecha y contar apoyos de cada reporte.
    reportes = reportes.annotate(
        total_apoyos=Count('apoyos')
    ).order_by('-fecha_creacion')

    contexto = {
        'reportes': reportes,
        'sectores': Reporte.SECTORES,
        'prioridades': prioridades,
        'sector_actual': sector,
        'prioridad_actual': prioridad
    }

    return render(
        request,
        'reportes/inicio.html',
        contexto
    )


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

    reporte = get_object_or_404(
        Reporte,
        id=reporte_id
    )

    coordenadas = None

    if reporte.latitud is not None and reporte.longitud is not None:
        coordenadas = {
            'lat': reporte.latitud,
            'lng': reporte.longitud
        }

    sesion = request.session.session_key

    if sesion:
        apoyado = Apoyo.objects.filter(
            reporte=reporte,
            sesion=sesion
        ).exists()
    else:
        apoyado = False

    contexto = {
        'reporte': reporte,
        'coordenadas': coordenadas,
        'apoyado': apoyado
    }

    return render(
        request,
        'reportes/detalle_reporte.html',
        contexto
    )


@require_POST
def apoyar_reporte(request, reporte_id):

    reporte = get_object_or_404(
        Reporte,
        id=reporte_id
    )

    if not request.session.session_key:
        request.session.create()
        request.session.modified = True

    apoyo, creado = Apoyo.objects.get_or_create(
        reporte=reporte,
        sesion=request.session.session_key
    )

    if not creado:
        apoyo.delete()

    return redirect(
        'detalle_reporte',
        reporte_id=reporte.id
    )