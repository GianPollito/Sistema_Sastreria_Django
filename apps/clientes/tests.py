from datetime import timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils import timezone
from apps.agenda.models import Cita
from apps.inventario.models import MovimientoInventario, Tela
from apps.pedidos.models import DetallePedido


class ValidacionesTests(SimpleTestCase):
    def test_cita_rechaza_intervalo_invertido(self):
        inicio = timezone.now()
        with self.assertRaises(ValidationError):
            Cita(inicio=inicio, fin=inicio - timedelta(minutes=10)).clean()

    def test_movimiento_exige_un_material(self):
        with self.assertRaises(ValidationError):
            MovimientoInventario().clean()
        with self.assertRaises(ValidationError):
            MovimientoInventario(tela_id=1, insumo_id=1).clean()

    def test_consumo_exige_detalle(self):
        with self.assertRaises(ValidationError):
            MovimientoInventario(tela_id=1, tipo="consumo").clean()

    def test_subtotal_decimal(self):
        detalle = DetallePedido(cantidad=3, precio_unitario=Decimal("18.50"))
        self.assertEqual(detalle.subtotal, Decimal("55.50"))

    def test_aviso_stock_incluye_umbral(self):
        self.assertTrue(Tela(existencias=Decimal("2"), stock_minimo=Decimal("2")).stock_bajo)
        self.assertFalse(Tela(existencias=Decimal("3"), stock_minimo=Decimal("2")).stock_bajo)
