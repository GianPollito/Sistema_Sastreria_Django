from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from apps.pedidos.models import Pedido


def es_sastre(usuario):
    return not usuario.is_superuser and not usuario.groups.filter(name__in=["Administrador", "Recepcionista"]).exists() and usuario.groups.filter(name="Sastre").exists()


def acceso(permiso=None):
    """Exige una cuenta de empleado activa además del permiso del módulo."""
    def decorar(vista):
        @login_required
        @wraps(vista)
        def comprobar(request, *args, **kwargs):
            empleado = getattr(request.user, "empleado", None)
            if not empleado or not empleado.activo or (permiso and not request.user.has_perm(permiso)):
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return comprobar
    return decorar


def pedidos_visibles(usuario):
    pedidos = Pedido.objects.select_related("cliente", "sastre__usuario").prefetch_related("detalles", "pagos")
    return pedidos.filter(sastre__usuario=usuario) if es_sastre(usuario) else pedidos


def pedido_visible(usuario, pk):
    return get_object_or_404(pedidos_visibles(usuario), pk=pk)
