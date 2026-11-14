from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import IngresoRutForm

urlpatterns = [
    path('', views.inicio, name='inicio'),

    path('nuevo/', views.crear_reporte, name='crear_reporte'),

    path(
        'reporte/<int:reporte_id>/',
        views.detalle_reporte,
        name='detalle_reporte'
    ),
    
    path(
        'reporte/<int:reporte_id>/apoyar/',
        views.apoyar_reporte,
        name='apoyar_reporte'
    ),

    path(
        'historial/',
        views.historial,
        name='historial'
    ),
    
    path(
        'reporte/<int:reporte_id>/apelacion/',
        views.solicitar_apelacion,
        name='solicitar_apelacion'
    ),

    path(
        'cuentas/registro/',
        views.registrarse,
        name='registrarse'
    ),

    path(
        'cuentas/ingresar/',
        auth_views.LoginView.as_view(
            template_name='reportes/iniciar_sesion.html',
            authentication_form=IngresoRutForm,
            redirect_authenticated_user=True
        ),
        name='iniciar_sesion'
    ),

    path(
        'cuentas/salir/',
        auth_views.LogoutView.as_view(
        next_page='inicio'
        ),
        name='cerrar_sesion'
    ),
]