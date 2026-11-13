from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    nombre = models.CharField(max_length=160, db_index=True)
    documento = models.CharField(max_length=30, blank=True)
    telefono = models.CharField(max_length=30)
    correo = models.EmailField(blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    preferencias = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Medida(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="medidas")
    tipo_prenda = models.ForeignKey("catalogo.TipoPrenda", on_delete=models.PROTECT)
    fecha = models.DateTimeField(default=timezone.now)
    responsable = models.ForeignKey("cuentas.Empleado", on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True)
    cuello = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    hombro = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    pecho = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    cintura = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    cadera = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    largo_manga = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    largo_pantalon = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    largo_prenda = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])

    class Meta:
        ordering = ["-fecha", "-pk"]
        indexes = [models.Index(fields=["cliente", "tipo_prenda", "fecha"])]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Las medidas son históricas. Registra una nueva versión.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cliente} · {self.tipo_prenda} · {self.fecha:%d/%m/%Y}"
