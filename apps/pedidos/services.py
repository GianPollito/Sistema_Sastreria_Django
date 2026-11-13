from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import HistorialEstado, Pedido


@transaction.atomic
def cambiar_estado(*, pedido, nuevo, usuario):
    """Comprueba permisos y asignación dentro de la misma transacción."""
    pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
    if not usuario.has_perm("pedidos.change_pedido"):
        raise PermissionDenied
    empleado = getattr(usuario, "empleado", None)
    if not empleado or not empleado.activo:
        raise PermissionDenied
    if usuario.groups.filter(name="Sastre").exists() and not (usuario.is_superuser or usuario.groups.filter(name="Administrador").exists()):
        if pedido.sastre_id != empleado.pk:
            raise PermissionDenied
    etapas = list(Pedido.Estado.values)
    if not pedido.detalles.exists():
        raise ValidationError("Añade al menos una prenda antes de iniciar la confección.")
    if nuevo not in etapas or etapas.index(nuevo) != etapas.index(pedido.estado) + 1:
        raise ValidationError("Avanza a la siguiente etapa del pedido.")
    if nuevo == Pedido.Estado.ENTREGADO and pedido.saldo > 0:
        raise ValidationError("Registra el cobro del saldo antes de entregar.")
    HistorialEstado.objects.create(pedido=pedido, anterior=pedido.estado, nuevo=nuevo, responsable=empleado)
    pedido.estado = nuevo
    pedido.save(update_fields=["estado"])
    return pedido
