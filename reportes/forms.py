from django import forms
from .models import Reporte

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

        latitud = datos.get('latitud')
        longitud = datos.get('longitud')

        if (latitud is None) != (longitud is None):
            raise forms.ValidationError(
                "Debes indicar ambas coordenadas."
            )

        if latitud is not None:
            if not -90 <= latitud <= 90:
                self.add_error(
                    'latitud',
                    'Latitud fuera de rango.'
                )

            if not -180 <= longitud <= 180:
                self.add_error(
                    'longitud',
                    'Longitud fuera de rango.'
                )

        return datos
