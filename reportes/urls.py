from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),

    path('nuevo/', views.crear_reporte, name='crear_reporte'),

    path(
        'reporte/<int:reporte_id>/',
        views.detalle_reporte,
        name='detalle_reporte'
    ),
]