import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


def numero_pedido():
    return f"AT-{uuid.uuid4().hex[:12].upper()}"


class Pedido(models.Model):
    class Estado(models.TextChoices):
        RECIBIDO = "recibido", "Recibido"
        CORTE = "corte", "Corte"
        CONFECCION = "confeccion", "Confección"
        PRUEBA = "prueba", "Prueba"
        AJUSTES = "ajustes", "Ajustes"
        LISTO = "listo", "Listo"
        ENTREGADO = "entregado", "Entregado"

    numero = models.CharField(max_length=20, unique=True, default=numero_pedido, editable=False)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT, related_name="pedidos")
    modalidad = models.CharField(max_length=10, choices=[("medida", "A medida"), ("arreglo", "Arreglo rápido")], default="medida")
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.RECIBIDO, db_index=True)
    prioridad = models.CharField(max_length=10, choices=[("normal", "Normal"), ("alta", "Alta")], default="normal")
    fecha_prometida = models.DateField(db_index=True)
    sastre = models.ForeignKey("cuentas.Empleado", null=True, blank=True, on_delete=models.PROTECT, related_name="pedidos")
    notas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha_prometida", "pk"]
        indexes = [models.Index(fields=["estado", "fecha_prometida"])]

    @property
    def total(self):
        return sum((d.subtotal for d in self.detalles.all()), Decimal("0.00"))

    @property
    def abonado(self):
        return self.pagos.aggregate(total=models.Sum("importe"))["total"] or Decimal("0.00")

    @property
    def saldo(self):
        return self.total - self.abonado

    def __str__(self):
        return self.numero


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, related_name="detalles")
    tipo_prenda = models.ForeignKey("catalogo.TipoPrenda", null=True, blank=True, on_delete=models.PROTECT)
    modelo = models.ForeignKey("catalogo.ModeloPrenda", null=True, blank=True, on_delete=models.PROTECT)
    medida = models.ForeignKey("clientes.Medida", null=True, blank=True, on_delete=models.PROTECT)
    descripcion = models.CharField(max_length=250)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(cantidad__gt=0, precio_unitario__gte=0), name="detalle_importes_validos")]

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.pedido.numero} · {self.descripcion}"

    def clean(self):
        if self.modelo_id and self.modelo.tipo_prenda_id != self.tipo_prenda_id:
            raise ValidationError("El modelo no corresponde al tipo de prenda.")
        if self.medida_id and self.pedido_id and (self.medida.cliente_id != self.pedido.cliente_id or self.medida.tipo_prenda_id != self.tipo_prenda_id):
            raise ValidationError("La ficha de medidas no corresponde al cliente y la prenda.")
        if self.pedido_id and self.pedido.modalidad == "medida" and (not self.tipo_prenda_id or not self.medida_id):
            raise ValidationError("Una confección a medida requiere tipo de prenda y ficha de medidas.")


class HistorialEstado(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, related_name="historial")
    anterior = models.CharField(max_length=15, choices=Pedido.Estado.choices)
    nuevo = models.CharField(max_length=15, choices=Pedido.Estado.choices)
    fecha = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey("cuentas.Empleado", on_delete=models.PROTECT)
