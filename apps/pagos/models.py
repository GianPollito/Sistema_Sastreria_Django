import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


def numero_comprobante():
    return f"REC-{uuid.uuid4().hex[:12].upper()}"


class Pago(models.Model):
    pedido = models.ForeignKey("pedidos.Pedido", on_delete=models.PROTECT, related_name="pagos")
    importe = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    metodo = models.CharField(max_length=15, choices=[("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("tarjeta", "Tarjeta")])
    referencia = models.CharField(max_length=120, blank=True)
    comprobante = models.CharField(max_length=20, default=numero_comprobante, unique=True, editable=False)
    responsable = models.ForeignKey("cuentas.Empleado", on_delete=models.PROTECT)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(importe__gt=0), name="pago_importe_positivo")]
