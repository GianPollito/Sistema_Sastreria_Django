from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

POSITIVO = MinValueValidator(Decimal("0.01"))
NO_NEGATIVO = MinValueValidator(Decimal("0"))


class Proveedor(models.Model):
    nombre = models.CharField(max_length=160)
    telefono = models.CharField(max_length=30, blank=True)
    correo = models.EmailField(blank=True)

    def __str__(self):
        return self.nombre


class MaterialBase(models.Model):
    codigo = models.CharField(max_length=40, unique=True)
    descripcion = models.CharField(max_length=200)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    existencias = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[NO_NEGATIVO])
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[NO_NEGATIVO])

    class Meta:
        abstract = True
        constraints = [models.CheckConstraint(condition=models.Q(existencias__gte=0), name="%(class)s_stock_no_negativo")]

    @property
    def stock_bajo(self):
        return self.existencias <= self.stock_minimo

    def __str__(self):
        return f"{self.codigo} · {self.descripcion}"


class Tela(MaterialBase):
    color = models.CharField(max_length=80)
    composicion = models.CharField(max_length=160)


class Insumo(MaterialBase):
    unidad = models.CharField(max_length=30, default="unidad")


class MovimientoInventario(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        CONSUMO = "consumo", "Consumo"
        DEVOLUCION = "devolucion", "Devolución"

    tela = models.ForeignKey(Tela, null=True, blank=True, on_delete=models.PROTECT)
    insumo = models.ForeignKey(Insumo, null=True, blank=True, on_delete=models.PROTECT)
    detalle = models.ForeignKey("pedidos.DetallePedido", null=True, blank=True, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, validators=[POSITIVO])
    responsable = models.ForeignKey("cuentas.Empleado", on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    notas = models.CharField(max_length=250, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=(models.Q(tela__isnull=False, insumo__isnull=True) | models.Q(tela__isnull=True, insumo__isnull=False)), name="movimiento_un_material"),
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name="movimiento_cantidad_positiva"),
        ]

    def clean(self):
        if bool(self.tela_id) == bool(self.insumo_id):
            raise ValidationError("Selecciona exactamente una tela o un insumo.")
        if self.tipo == self.Tipo.CONSUMO and not self.detalle_id:
            raise ValidationError("El consumo debe estar vinculado a una prenda.")
