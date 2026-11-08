from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Count, F, Q
from django.http import HttpResponseForbidden
from django.db.models.functions import Coalesce
from django.db import IntegrityError, transaction
from .models import Reporte, Apoyo, Apelacion
from .forms import ReporteForm, ApelacionForm
from .vigencia import fecha_limite

def inicio(request):
    orden = request.GET.get('orden', 'recientes')

    if orden not in ('recientes', 'apoyados'):
        orden = 'recientes'
    
    reportes = Reporte.objects.annotate(
        fecha_inicio_vigencia=Coalesce(
            'fecha_reactivacion',
            'fecha_creacion'
        )
    ).filter(
        fecha_inicio_vigencia__gt=fecha_limite()
    )

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

    # Ordenar por fecha o por votos (dentro del periodo actual) y contar apoyos de cada reporte.
    reportes = reportes.annotate(
        total_apoyos=Count(
            'apoyos',
            filter=Q(
                apoyos__periodo=F('numero_periodo')
            )
        )
    )

    if orden == 'apoyados':
        reportes = reportes.order_by(
            '-total_apoyos',
            '-fecha_inicio_vigencia',
            '-id'
        )
    else:
        reportes = reportes.order_by(
            '-fecha_inicio_vigencia',
            '-id'
        )

    contexto = {
        'reportes': reportes,
        'sectores': Reporte.SECTORES,
        'prioridades': prioridades,
        'sector_actual': sector,
        'prioridad_actual': prioridad,
        'orden': orden
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
            sesion=sesion,
            periodo=reporte.numero_periodo
        ).exists()
    else:
        apoyado = False

    contexto = {
        'reporte': reporte,
        'coordenadas': coordenadas,
        'apoyado': apoyado
    }

    contexto['archivado'] = reporte.esta_archivado

    contexto['apelacion_pendiente'] = (
        reporte.apelaciones.filter(
            estado='pendiente'
        ).exists()
    )

    contexto['ultima_apelacion'] = (
        reporte.apelaciones
        .order_by('-fecha_solicitud', '-id')
        .first()
        )

    contexto['apoyos_actuales'] = (
        reporte.apoyos.filter(
            periodo=reporte.numero_periodo
        ).count()
    )   

    contexto['apoyos_anteriores'] = (
        reporte.apoyos.exclude(
            periodo=reporte.numero_periodo
        ).count()
    )

    contexto['apoyos_totales'] = (
        reporte.apoyos.count()
    )

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
    
    if reporte.esta_archivado:
        return HttpResponseForbidden(
            "Este reporte está archivado y "
            "ya no puede recibir apoyos."
        )

    if not request.session.session_key:
        request.session.create()
        request.session.modified = True

    apoyo, creado = Apoyo.objects.get_or_create(
        reporte=reporte,
        sesion=request.session.session_key,
        periodo=reporte.numero_periodo
    )

    if not creado:
        apoyo.delete()

    return redirect(
        'detalle_reporte',
        reporte_id=reporte.id
    )


def historial(request):
    reportes = Reporte.objects.annotate(
        fecha_inicio_vigencia=Coalesce(
            'fecha_reactivacion',
            'fecha_creacion'
        )
    ).filter(
        fecha_inicio_vigencia__lte=fecha_limite()
    ).order_by('-fecha_creacion')

    contexto = {
        'reportes': reportes
    }

    return render(
        request,
        'reportes/historial.html',
        contexto
    )


@require_http_methods(["GET", "POST"])
def solicitar_apelacion(request, reporte_id):

    reporte = get_object_or_404(
        Reporte,
        id=reporte_id
    )

    if not reporte.esta_archivado:
        return redirect(
            'detalle_reporte',
            reporte_id=reporte.id
        )

    pendiente = Apelacion.objects.filter(
        reporte=reporte,
        estado='pendiente'
    ).exists()

    if pendiente:
        return render(
            request,
            'reportes/solicitar_apelacion.html',
            {
                'reporte': reporte,
                'pendiente': True
            }
        )

    formulario = ApelacionForm(
        request.POST if request.method == 'POST' else None
    )

    if request.method == 'POST' and formulario.is_valid():

        apelacion = formulario.save(commit=False)
        apelacion.reporte = reporte

        try:
            with transaction.atomic():
                apelacion.save()
        except IntegrityError:
            return render(
                request,
                'reportes/solicitar_apelacion.html',
                {
                    'reporte': reporte,
                    'pendiente': True
                }
            )

        return redirect(
            'detalle_reporte',
            reporte_id=reporte.id
        )

    return render(
        request,
        'reportes/solicitar_apelacion.html',
        {
            'reporte': reporte,
            'formulario': formulario,
            'pendiente': False
        }
    )
