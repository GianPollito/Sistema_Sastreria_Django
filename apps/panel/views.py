from datetime import datetime, time, timedelta
from decimal import Decimal
from django.db.models import Count, F, Sum
from django.shortcuts import render
from django.utils import timezone
from apps.cuentas.access import acceso, es_sastre, pedidos_visibles
from apps.inventario.models import Tela, Insumo
from apps.pagos.models import Pago
from apps.agenda.models import Cita
from apps.pedidos.models import Pedido


@acceso("pedidos.view_pedido")
def inicio(request):
    hoy = timezone.localdate()
    pedidos = pedidos_visibles(request.user)
    abiertos = pedidos.exclude(estado="entregado")
    # Rangos UTC calculados por Django: no requieren tablas de zonas horarias en MariaDB.
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    inicio_mes = timezone.make_aware(datetime.combine(hoy.replace(day=1), time.min))
    mes_siguiente = (hoy.replace(day=28) + timedelta(days=4)).replace(day=1)
    fin_mes = timezone.make_aware(datetime.combine(mes_siguiente, time.min))
    pagos = Pago.objects.filter(pedido__in=pedidos, fecha__gte=inicio_mes, fecha__lt=fin_mes)
    citas = Cita.objects.filter(inicio__gte=inicio_dia, inicio__lt=inicio_dia + timedelta(days=1), estado="pendiente").select_related("cliente", "empleado__usuario").order_by("inicio")
    if es_sastre(request.user):
        citas = citas.filter(empleado__usuario=request.user)
    cantidades = dict(pedidos.values("estado").annotate(cantidad=Count("pk")).values_list("estado", "cantidad"))
    etapas = [{"nombre": nombre, "cantidad": cantidades.get(codigo, 0)} for codigo, nombre in Pedido.Estado.choices]
    return render(request, "panel/inicio.html", {
        "hoy": hoy, "abiertos": abiertos.count(), "atrasados": abiertos.filter(fecha_prometida__lt=hoy),
        "proximos": abiertos.filter(fecha_prometida__range=[hoy, hoy + timedelta(days=7)]),
        "ingresos": pagos.aggregate(total=Sum("importe"))["total"] or Decimal("0"), "etapas": etapas, "citas": citas,
        "telas_bajas": Tela.objects.filter(existencias__lte=F("stock_minimo")),
        "insumos_bajos": Insumo.objects.filter(existencias__lte=F("stock_minimo")),
    })
