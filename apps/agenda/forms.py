from django import forms
from .models import Cita


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ["cliente", "pedido", "empleado", "motivo", "inicio", "fin", "estado", "notas"]
        widgets = {campo: forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M") for campo in ["inicio", "fin"]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["empleado"].queryset = self.fields["empleado"].queryset.filter(activo=True, usuario__is_active=True)

    def clean(self):
        datos = super().clean()
        if all(datos.get(c) for c in ["inicio", "fin", "empleado"]) and datos.get("estado") != "cancelada":
            if Cita.objects.filter(empleado=datos["empleado"], inicio__lt=datos["fin"], fin__gt=datos["inicio"]).exclude(estado="cancelada").exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("El empleado ya tiene una cita en ese horario.")
        return datos
