from decimal import Decimal
from django import forms
from .models import Pago


class PagoForm(forms.Form):
    importe = forms.DecimalField(min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    metodo = forms.ChoiceField(choices=Pago._meta.get_field("metodo").choices)
    referencia = forms.CharField(max_length=120, required=False)
