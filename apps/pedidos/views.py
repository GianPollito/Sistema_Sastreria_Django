from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from apps.cuentas.access import acceso, es_sastre, pedido_visible, pedidos_visibles
from apps.pagos.forms import PagoForm
from apps.pagos.services import registrar_pago
from .forms import PedidoForm, DetalleForm
from .models import Pedido, DetallePedido
from .services import cambiar_estado


@acceso("pedidos.view_pedido")
def tablero(request):
    pedidos = pedidos_visibles(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        pedidos = pedidos.filter(Q(numero__icontains=q) | Q(cliente__nombre__icontains=q))
    if request.GET.get("modalidad") in ["arreglo", "medida"]:
        pedidos = pedidos.filter(modalidad=request.GET["modalidad"])
    columnas = [{"codigo": codigo, "nombre": nombre, "pedidos": pedidos.filter(estado=codigo)} for codigo, nombre in Pedido.Estado.choices]
    return render(request, "pedidos/tablero.html", {"columnas": columnas, "q": q, "modalidad": request.GET.get("modalidad", "")})


@acceso("pedidos.add_pedido")
def crear(request):
    form = PedidoForm(request.POST or None, initial={"modalidad": "arreglo" if request.GET.get("arreglo") else "medida"})
    if request.method == "POST" and form.is_valid():
        pedido = form.save()
        messages.success(request, "Encargo abierto. Añade ahora las prendas o el arreglo y su precio.")
        return redirect("pedido", pk=pedido.pk)
    return render(request, "gestion/form.html", {"form": form, "titulo": "Un nuevo encargo", "volver": reverse("tablero"),
        "nota": "En el siguiente paso registrarás las prendas, el precio y el adelanto. Los arreglos no exigen ficha de medidas."})


@acceso("pedidos.change_pedido")
def editar(request, pk):
    if es_sastre(request.user):
        raise PermissionDenied
    pedido = pedido_visible(request.user, pk)
    if pedido.estado == Pedido.Estado.ENTREGADO:
        messages.error(request, "Un pedido entregado conserva su ficha original.")
        return redirect("pedido", pk=pk)
    form = PedidoForm(request.POST or None, instance=pedido)
    # El cliente y la modalidad quedan fijados para conservar la coherencia de las prendas.
    form.fields["cliente"].disabled = True
    form.fields["modalidad"].disabled = True
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            actual = Pedido.objects.select_for_update().get(pk=pk)
            if actual.estado == Pedido.Estado.ENTREGADO:
                messages.error(request, "El pedido acaba de entregarse y ya no admite cambios.")
                return redirect("pedido", pk=pk)
            for campo in ["fecha_prometida", "prioridad", "sastre", "notas"]:
                setattr(actual, campo, form.cleaned_data[campo])
            actual.save(update_fields=["fecha_prometida", "prioridad", "sastre", "notas"])
        messages.success(request, "Datos del encargo actualizados.")
        return redirect("pedido", pk=pk)
    return render(request, "gestion/form.html", {"form": form, "titulo": f"Editar {pedido.numero}", "volver": reverse("pedido", args=[pk])})


@acceso("pedidos.view_pedido")
def ficha(request, pk):
    pedido = pedido_visible(request.user, pk)
    etapas = [{"codigo": codigo, "nombre": nombre, "pasada": i <= Pedido.Estado.values.index(pedido.estado)} for i, (codigo, nombre) in enumerate(Pedido.Estado.choices)]
    indice = Pedido.Estado.values.index(pedido.estado)
    return render(request, "pedidos/ficha.html", {"pedido": pedido, "etapas": etapas,
        "siguiente": Pedido.Estado.values[indice + 1] if indice < 6 else None,
        "siguiente_nombre": Pedido.Estado.labels[indice + 1] if indice < 6 else None,
        "puede_gestionar": not es_sastre(request.user), "pago_form": PagoForm(),
        "historial": pedido.historial.select_related("responsable__usuario"),
    })


@acceso("pedidos.add_detallepedido")
def agregar_detalle(request, pk, detalle_pk=None):
    pedido = pedido_visible(request.user, pk)
    from django.shortcuts import get_object_or_404
    detalle = get_object_or_404(DetallePedido, pk=detalle_pk, pedido=pedido) if detalle_pk else None
    form = DetalleForm(request.POST or None, pedido=pedido, instance=detalle)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            bloqueado = Pedido.objects.select_for_update().get(pk=pk)
            if bloqueado.estado != Pedido.Estado.RECIBIDO or bloqueado.pagos.exists():
                form.add_error(None, "Las prendas se fijan antes de cobrar y comenzar el corte.")
            else:
                form.save()
                messages.success(request, "Prenda añadida al encargo.")
                return redirect("pedido", pk=pk)
    return render(request, "gestion/form.html", {"form": form, "titulo": f"Prenda / arreglo · {pedido.numero}", "volver": reverse("pedido", args=[pk]),
        "nota": "Selecciona la versión de medidas correspondiente al cliente y al tipo de prenda. En arreglos, estos campos son opcionales."})


@require_POST
@acceso("pedidos.change_pedido")
def estado(request, pk):
    pedido = pedido_visible(request.user, pk)
    try:
        cambiar_estado(pedido=pedido, nuevo=request.POST.get("estado"), usuario=request.user)
    except ValidationError as error:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": " ".join(error.messages)}, status=400)
        messages.error(request, " ".join(error.messages))
    else:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True})
        messages.success(request, "El encargo avanzó una puntada.")
    return redirect("pedido", pk=pk)


@require_POST
@acceso("pagos.add_pago")
def cobrar(request, pk):
    pedido = pedido_visible(request.user, pk)
    form = PagoForm(request.POST)
    if form.is_valid():
        try:
            pago = registrar_pago(pedido=pedido, responsable=request.user.empleado, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Cobro registrado.")
            return redirect("comprobante", pk=pago.pk)
    return render(request, "gestion/form.html", {"form": form, "titulo": f"Cobro · {pedido.numero}", "volver": reverse("pedido", args=[pk])})
