from django.core.exceptions import ValidationError
from django.db import transaction
from apps.pedidos.models import Pedido
from .models import Pago


@transaction.atomic
def registrar_pago(*, pedido, importe, metodo, responsable, referencia=""):
    """Serializa los cobros de un pedido para evitar superar su saldo."""
    pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
    pago = Pago(pedido=pedido, importe=importe, metodo=metodo, responsable=responsable, referencia=referencia)
    pago.full_clean()
    if importe > pedido.saldo:
        raise ValidationError("El importe supera el saldo pendiente.")
    pago.save()
    return pago
