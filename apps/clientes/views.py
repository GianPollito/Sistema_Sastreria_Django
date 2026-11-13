from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.cuentas.access import acceso, es_sastre, pedidos_visibles
from .models import Cliente
from .forms import MedidaForm


@acceso("clientes.view_cliente")
def ficha(request, pk):
    clientes = Cliente.objects.all()
    if es_sastre(request.user):
        clientes = clientes.filter(pedidos__sastre__usuario=request.user).distinct()
    cliente = get_object_or_404(clientes, pk=pk)
    return render(request, "clientes/ficha.html", {"cliente": cliente, "medidas": cliente.medidas.select_related("tipo_prenda", "responsable__usuario"),
        "pedidos": pedidos_visibles(request.user).filter(cliente=cliente), "campos_medida": ["cuello", "hombro", "pecho", "cintura", "cadera", "largo_manga", "largo_pantalon", "largo_prenda"]})


@acceso("clientes.add_medida")
def medida(request, pk):
    clientes = Cliente.objects.all()
    if es_sastre(request.user):
        clientes = clientes.filter(pedidos__sastre__usuario=request.user).distinct()
    cliente = get_object_or_404(clientes, pk=pk)
    form = MedidaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ficha = form.save(commit=False)
        ficha.cliente = cliente
        ficha.responsable = request.user.empleado
        ficha.save()
        messages.success(request, "Nueva versión de medidas guardada; las anteriores se conservan.")
        return redirect("cliente", pk=pk)
    return render(request, "clientes/medida.html", {"form": form, "cliente": cliente})
