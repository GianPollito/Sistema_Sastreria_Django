from django.core.exceptions import ValidationError
from django.db import models


class Cita(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT, related_name="citas")
    pedido = models.ForeignKey("pedidos.Pedido", null=True, blank=True, on_delete=models.PROTECT, related_name="citas")
    empleado = models.ForeignKey("cuentas.Empleado", on_delete=models.PROTECT)
    motivo = models.CharField(max_length=15, choices=[("medidas", "Toma de medidas"), ("prueba", "Prueba"), ("entrega", "Entrega")])
    inicio = models.DateTimeField(db_index=True)
    fin = models.DateTimeField()
    estado = models.CharField(max_length=15, choices=[("pendiente", "Pendiente"), ("realizada", "Realizada"), ("cancelada", "Cancelada")], default="pendiente")
    notas = models.TextField(blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(fin__gt=models.F("inicio")), name="cita_intervalo_valido")]

    def clean(self):
        if self.inicio and self.fin and self.fin <= self.inicio:
            raise ValidationError("La cita debe terminar después de comenzar.")
        if self.pedido_id and self.pedido.cliente_id != self.cliente_id:
            raise ValidationError("El pedido pertenece a otro cliente.")
