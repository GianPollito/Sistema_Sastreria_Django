from datetime import date, datetime, time, timedelta
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from apps.cuentas.access import acceso, es_sastre, pedidos_visibles
from apps.cuentas.models import Empleado
from .forms import CitaForm
from .models import Cita


@acceso("agenda.view_cita")
def semana(request):
    try:
        dia = date.fromisoformat(request.GET.get("fecha", ""))
    except ValueError:
        dia = timezone.localdate()
    if not 1900 <= dia.year <= 2100:
        dia = timezone.localdate()
    lunes = dia - timedelta(days=dia.weekday())
    inicio = timezone.make_aware(datetime.combine(lunes, time.min))
    citas = Cita.objects.select_related("cliente", "empleado__usuario", "pedido").filter(inicio__gte=inicio, inicio__lt=inicio + timedelta(days=7)).order_by("inicio")
    if es_sastre(request.user):
        citas = citas.filter(empleado__usuario=request.user)
    dias = [{"fecha": lunes + timedelta(days=i), "citas": [c for c in citas if timezone.localdate(c.inicio) == lunes + timedelta(days=i)]} for i in range(7)]
    return render(request, "agenda/semana.html", {"dias": dias, "lunes": lunes, "anterior": (lunes - timedelta(days=7)).isoformat(), "siguiente": (lunes + timedelta(days=7)).isoformat()})


@acceso()
def editar(request, pk=None):
    if not request.user.has_perm(f"agenda.{'change' if pk else 'add'}_cita"):
        raise PermissionDenied
    objeto = get_object_or_404(Cita, pk=pk) if pk else None
    form = CitaForm(request.POST or None, instance=objeto)
    form.fields["pedido"].queryset = pedidos_visibles(request.user)
    if request.method == "POST" and form.is_valid():
        # Bloquear al empleado serializa reservas simultáneas en el mismo horario.
        with transaction.atomic():
            Empleado.objects.select_for_update().get(pk=form.cleaned_data["empleado"].pk)
            datos = form.cleaned_data
            solapada = Cita.objects.filter(empleado=datos["empleado"], inicio__lt=datos["fin"], fin__gt=datos["inicio"]).exclude(estado="cancelada").exclude(pk=pk).exists()
            if solapada and datos["estado"] != "cancelada":
                form.add_error(None, "Ese horario acaba de reservarse. Elige otro.")
            else:
                form.save()
                messages.success(request, "Cita guardada en la agenda.")
                return redirect("agenda")
    return render(request, "gestion/form.html", {"form": form, "titulo": "Editar cita" if pk else "Reservar una cita", "volver": reverse("agenda")})
