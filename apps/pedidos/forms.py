from django import forms
from .models import Pedido, DetallePedido
from apps.catalogo.models import TipoPrenda, ModeloPrenda
from apps.clientes.models import Medida


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente", "modalidad", "fecha_prometida", "prioridad", "sastre", "notas"]
        widgets = {"fecha_prometida": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sastre"].queryset = self.fields["sastre"].queryset.filter(activo=True, usuario__is_active=True, usuario__groups__name__in=["Sastre", "Administrador"]).distinct()


class DetalleForm(forms.ModelForm):
    class Meta:
        model = DetallePedido
        fields = ["tipo_prenda", "modelo", "medida", "descripcion", "cantidad", "precio_unitario"]

    def __init__(self, *args, pedido, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.pedido = pedido
        self.fields["medida"].queryset = Medida.objects.filter(cliente_id=pedido.cliente_id)
        self.fields["tipo_prenda"].queryset = TipoPrenda.objects.filter(activo=True)
        self.fields["modelo"].queryset = ModeloPrenda.objects.filter(activo=True, tipo_prenda__activo=True)
