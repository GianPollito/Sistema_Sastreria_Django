from decimal import Decimal
from django import forms
from .models import Insumo, MovimientoInventario, Proveedor, Tela


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "telefono", "correo"]


class TelaForm(forms.ModelForm):
    class Meta:
        model = Tela
        fields = ["codigo", "descripcion", "color", "composicion", "proveedor", "stock_minimo"]


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ["codigo", "descripcion", "unidad", "proveedor", "stock_minimo"]


class MovimientoForm(forms.Form):
    tipo = forms.ChoiceField(choices=MovimientoInventario.Tipo.choices)
    cantidad = forms.DecimalField(min_value=Decimal("0.01"), max_digits=12, decimal_places=2)
    detalle = forms.ModelChoiceField(queryset=None, required=False, label="Prenda del pedido")
    notas = forms.CharField(max_length=250, required=False, widget=forms.Textarea)

    def __init__(self, *args, detalles, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["detalle"].queryset = detalles
