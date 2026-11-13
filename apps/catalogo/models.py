from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class TipoPrenda(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class ModeloPrenda(models.Model):
    tipo_prenda = models.ForeignKey(TipoPrenda, on_delete=models.PROTECT, related_name="modelos")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0"))])
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tipo_prenda", "nombre"], name="modelo_nombre_por_tipo")]

    def __str__(self):
        return f"{self.tipo_prenda} · {self.nombre}"
