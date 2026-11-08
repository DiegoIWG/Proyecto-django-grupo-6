from datetime import timedelta
from django.utils import timezone


DIAS_VISIBILIDAD = 21


def fecha_limite():
    return timezone.now() - timedelta(
        days=DIAS_VISIBILIDAD
    )
