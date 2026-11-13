from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Insumo, MovimientoInventario, Tela


@transaction.atomic
def registrar_movimiento(*, material, tipo, cantidad, responsable, detalle=None, notas=""):
    """Bloquea el material para que dos consumos no utilicen el mismo stock."""
    if not isinstance(material, (Tela, Insumo)):
        raise ValidationError("Material desconocido.")
    material = type(material).objects.select_for_update().get(pk=material.pk)
    campo = "tela" if isinstance(material, Tela) else "insumo"
    movimiento = MovimientoInventario(**{campo: material}, tipo=tipo, cantidad=cantidad,
        responsable=responsable, detalle=detalle, notas=notas)
    movimiento.full_clean()
    if detalle:
        from apps.pedidos.models import Pedido
        pedido = Pedido.objects.select_for_update().get(pk=detalle.pedido_id)
        if pedido.estado == Pedido.Estado.ENTREGADO:
            raise ValidationError("Un encargo entregado ya no admite movimientos.")
    if tipo == MovimientoInventario.Tipo.DEVOLUCION:
        if not detalle:
            raise ValidationError("Indica la prenda a la que corresponde la devolución.")
        from django.db.models import Sum
        anteriores = MovimientoInventario.objects.filter(detalle=detalle, **{campo: material})
        consumido = anteriores.filter(tipo="consumo").aggregate(total=Sum("cantidad"))["total"] or 0
        devuelto = anteriores.filter(tipo="devolucion").aggregate(total=Sum("cantidad"))["total"] or 0
        if cantidad > consumido - devuelto:
            raise ValidationError("La devolución supera el material consumido en esta prenda.")
    nuevo_stock = material.existencias + (-cantidad if tipo == MovimientoInventario.Tipo.CONSUMO else cantidad)
    if nuevo_stock < 0:
        raise ValidationError("No hay existencias suficientes para este consumo.")
    material.existencias = nuevo_stock
    material.save(update_fields=["existencias"])
    movimiento.save()
    return movimiento
