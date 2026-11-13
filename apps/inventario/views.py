from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from apps.cuentas.access import acceso, es_sastre, pedidos_visibles
from apps.pedidos.models import DetallePedido
from .forms import MovimientoForm
from .models import Tela, Insumo
from .services import registrar_movimiento


@acceso("inventario.add_movimientoinventario")
def movimiento(request, entidad, pk):
    if entidad not in ["telas", "insumos"]:
        from django.http import Http404
        raise Http404
    material = get_object_or_404(Tela if entidad == "telas" else Insumo, pk=pk)
    detalles = DetallePedido.objects.filter(pedido__in=pedidos_visibles(request.user)).exclude(pedido__estado="entregado").select_related("pedido")
    form = MovimientoForm(request.POST or None, detalles=detalles)
    if es_sastre(request.user):
        form.fields["tipo"].choices = [("consumo", "Consumo")]
    if request.method == "POST" and form.is_valid():
        try:
            registrar_movimiento(material=material, responsable=request.user.empleado, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Movimiento registrado y existencias actualizadas.")
            return redirect("movimientos", entidad=entidad, pk=pk)
    return render(request, "gestion/form.html", {"titulo": f"Movimiento · {material}", "form": form, "volver": reverse("movimientos", args=[entidad, pk]),
        "nota": f"Disponible: {material.existencias} {'metros' if entidad == 'telas' else material.unidad}. Los consumos deben indicar la prenda del encargo."})


@acceso("inventario.view_movimientoinventario")
def historial(request, entidad, pk):
    if entidad not in ["telas", "insumos"]:
        from django.http import Http404
        raise Http404
    material = get_object_or_404(Tela if entidad == "telas" else Insumo, pk=pk)
    movimientos = material.movimientoinventario_set.select_related("responsable__usuario", "detalle__pedido").order_by("-fecha")
    if es_sastre(request.user):
        movimientos = movimientos.filter(detalle__pedido__sastre__usuario=request.user)
    from django.core.paginator import Paginator
    pagina = Paginator(movimientos, 30).get_page(request.GET.get("pagina"))
    return render(request, "inventario/historial.html", {"material": material, "entidad": entidad, "pagina": pagina})
