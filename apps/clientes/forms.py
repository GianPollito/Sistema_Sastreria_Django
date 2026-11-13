from django import forms
from .models import Cliente, Medida


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "documento", "telefono", "correo", "direccion", "preferencias"]


class MedidaForm(forms.ModelForm):
    class Meta:
        model = Medida
        fields = ["tipo_prenda", "cuello", "hombro", "pecho", "cintura", "cadera", "largo_manga", "largo_pantalon", "largo_prenda", "observaciones"]

    def clean(self):
        datos = super().clean()
        if not any(datos.get(campo) for campo in self.Meta.fields[1:-1]):
            raise forms.ValidationError("Registra al menos una medida en centímetros.")
        return datos
