from django import forms
from .models import ModeloPrenda, TipoPrenda


class TipoPrendaForm(forms.ModelForm):
    class Meta:
        model = TipoPrenda
        fields = ["nombre", "descripcion", "precio_base", "activo"]


class ModeloPrendaForm(forms.ModelForm):
    class Meta:
        model = ModeloPrenda
        fields = ["tipo_prenda", "nombre", "descripcion", "precio_base", "activo"]
