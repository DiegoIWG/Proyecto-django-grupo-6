from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Reporte, Apelacion, Comentario
from .rut import normalizar_rut
from .geografia import punto_permitido


class ReporteForm(forms.ModelForm):

    class Meta:
        model = Reporte

        fields = [
            'titulo',
            'descripcion',
            'sector',
            'direccion',
            'latitud',
            'longitud',
        ]

        widgets = {
            'descripcion': forms.Textarea(
                attrs={'rows': 5}
            ),
            'latitud': forms.HiddenInput(),
            'longitud': forms.HiddenInput(),
        }

    
    def clean(self):
        datos = super().clean()

        sector = datos.get('sector')
        latitud = datos.get('latitud')
        longitud = datos.get('longitud')
        direccion = (datos.get('direccion') or '').strip()

        if latitud is None and longitud is None:
            if direccion:
                self.add_error(
                    'direccion',
                    'Selecciona un punto en el mapa '
                    'para indicar una dirección.'
                )
            return datos

        if latitud is None or longitud is None:
            raise forms.ValidationError(
                'Debes indicar ambas coordenadas.'
            )

        if not (-90 <= latitud <= 90):
            self.add_error(
                'latitud',
                'Latitud fuera de rango.'
            )
            return datos

        if not (-180 <= longitud <= 180):
            self.add_error(
                'longitud',
                'Longitud fuera de rango.'
            )
            return datos

        if sector and not punto_permitido(
            sector, longitud, latitud
        ):
            raise forms.ValidationError(
                'El punto seleccionado está fuera '
                'de la comuna indicada.'
            )

        return datos



class ApelacionForm(forms.ModelForm):

    class Meta:
        model = Apelacion
        fields = ['motivo']

        widgets = {
            'motivo': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': (
                    'Explica por qué el problema '
                    'ambiental todavía continúa.'
                )
            })
        }

        labels = {
            'motivo': 'Motivo de la apelación'
        }

    def clean_motivo(self):
        motivo = self.cleaned_data['motivo'].strip()

        if len(motivo) < 20:
            raise forms.ValidationError(
                'Explica el problema con al menos '
                '20 caracteres.'
            )

        return motivo


class RegistroRutForm(UserCreationForm):

    username = forms.CharField(
        label='RUT',
        max_length=15
    )

    first_name = forms.CharField(
        label='Alias público (opcional)',
        max_length=40,
        required=False
    )

    email = forms.EmailField(
        label='Correo electrónico',
        required=True
    )

    class Meta(UserCreationForm.Meta):
        fields = (
            'username',
            'first_name',
            'email',
            'password1',
            'password2'
        )

    def clean_username(self):
        rut = normalizar_rut(
            self.cleaned_data['username']
        )

        if get_user_model().objects.filter(
            username=rut
        ).exists():
            raise ValidationError(
                'No se puede registrar este RUT.'
            )

        return rut


class IngresoRutForm(AuthenticationForm):

    username = forms.CharField(
        label='RUT',
        max_length=15
    )

    def clean(self):
        valor = self.cleaned_data.get('username')

        if valor:
            try:
                self.cleaned_data['username'] = (
                    normalizar_rut(valor)
                )
            except ValidationError:
                raise self.get_invalid_login_error()

        return super().clean()

class ComentarioForm(forms.ModelForm):

    class Meta:
        model = Comentario
        fields = ['contenido']

        labels = {
            'contenido': 'Tu comentario'
        }

        widgets = {
            'contenido': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': (
                    'Comparte información sobre '
                    'este problema ambiental.'
                )
            })
        }

    def clean_contenido(self):
        contenido = self.cleaned_data['contenido'].strip()

        if len(contenido) < 15:
            raise forms.ValidationError(
                'El comentario debe tener '
                'al menos 15 caracteres.'
            )

        return contenido
