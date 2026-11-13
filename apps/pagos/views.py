from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from apps.cuentas.access import acceso, pedidos_visibles
from .models import Pago


@acceso("pagos.view_pago")
def lista(request):
    pagos = Pago.objects.filter(pedido__in=pedidos_visibles(request.user)).select_related("pedido__cliente", "responsable__usuario").order_by("-fecha")
    return render(request, "pagos/lista.html", {"pagina": Paginator(pagos, 25).get_page(request.GET.get("pagina"))})


@acceso("pagos.view_pago")
def comprobante(request, pk):
    pago = get_object_or_404(Pago.objects.select_related("pedido__cliente", "responsable__usuario").filter(pedido__in=pedidos_visibles(request.user)), pk=pk)
    return render(request, "pagos/comprobante.html", {"pago": pago, "pedido": pago.pedido})
