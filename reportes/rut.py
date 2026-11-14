import re
from django.core.exceptions import ValidationError

def normalizar_rut(valor):
    limpio = re.sub(
        r'[\s.-]',
        '',
        str(valor)
    ).upper()

    if not re.fullmatch(r'\d{1,8}[\dK]', limpio):
        raise ValidationError(
            'Ingresa un RUT válido.'
        )

    cuerpo = limpio[:-1]
    digito = limpio[-1]
    numero = int(cuerpo)

    if numero == 0:
        raise ValidationError(
            'Ingresa un RUT válido.'
        )

    multiplicadores = [2, 3, 4, 5, 6, 7]

    suma = sum(
        int(cifra) * multiplicadores[i % 6]
        for i, cifra in enumerate(reversed(cuerpo))
    )

    resultado = 11 - (suma % 11)

    if resultado == 11:
        esperado = '0'
    elif resultado == 10:
        esperado = 'K'
    else:
        esperado = str(resultado)

    if digito != esperado:
        raise ValidationError(
            'El dígito verificador del RUT es incorrecto.'
        )

    return f'{numero}-{digito}'
