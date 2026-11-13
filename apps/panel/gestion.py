"""Listados y formularios comunes, con configuración explícita por entidad."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from apps.cuentas.access import acceso, es_sastre
from apps.clientes.forms import ClienteForm
from apps.catalogo.forms import TipoPrendaForm, ModeloPrendaForm
from apps.inventario.forms import ProveedorForm, TelaForm, InsumoForm

ENTIDADES = {
    "clientes": (ClienteForm, "Clientes", ["nombre", "telefono", "correo"], ["nombre", "documento", "telefono"]),
    "prendas": (TipoPrendaForm, "Tipos de prenda", ["nombre", "precio_base", "activo"], ["nombre"]),
    "modelos": (ModeloPrendaForm, "Modelos del atelier", ["nombre", "tipo_prenda", "precio_base", "activo"], ["nombre"]),
    "proveedores": (ProveedorForm, "Proveedores", ["nombre", "telefono", "correo"], ["nombre"]),
    "telas": (TelaForm, "Biblioteca de telas", ["codigo", "descripcion", "color", "existencias", "stock_minimo"], ["codigo", "descripcion", "color"]),
    "insumos": (InsumoForm, "Insumos del taller", ["codigo", "descripcion", "unidad", "existencias", "stock_minimo"], ["codigo", "descripcion"]),
}


def configuracion(entidad):
    if entidad not in ENTIDADES:
        from django.http import Http404
        raise Http404
    return ENTIDADES[entidad]


@acceso()
def listado(request, entidad):
    formulario, titulo, campos, busqueda = configuracion(entidad)
    modelo = formulario._meta.model
    permiso = f"{modelo._meta.app_label}.view_{modelo._meta.model_name}"
    if not request.user.has_perm(permiso):
        raise PermissionDenied
    objetos = modelo.objects.all().order_by("pk")
    if entidad == "clientes" and es_sastre(request.user):
        objetos = objetos.filter(pedidos__sastre__usuario=request.user).distinct()
    q = request.GET.get("q", "").strip()
    if q:
        filtro = Q()
        for campo in busqueda:
            filtro |= Q(**{f"{campo}__icontains": q})
        objetos = objetos.filter(filtro)
    pagina = Paginator(objetos, 20).get_page(request.GET.get("pagina"))
    filas = []
    for objeto in pagina:
        valores = []
        for campo in campos:
            valor = getattr(objeto, campo)
            valores.append("Sí" if valor is True else "No" if valor is False else valor if valor is not None and valor != "" else "—")
        filas.append({"objeto": objeto, "valores": valores, "bajo": getattr(objeto, "stock_bajo", False)})
    return render(request, "gestion/lista.html", {"titulo": titulo, "entidad": entidad,
        "columnas": [modelo._meta.get_field(c).verbose_name.capitalize() for c in campos], "filas": filas,
        "pagina": pagina, "q": q, "puede_crear": request.user.has_perm(f"{modelo._meta.app_label}.add_{modelo._meta.model_name}"),
        "puede_editar": request.user.has_perm(f"{modelo._meta.app_label}.change_{modelo._meta.model_name}")})


@acceso()
def editar(request, entidad, pk=None):
    formulario, titulo, *_ = configuracion(entidad)
    modelo = formulario._meta.model
    if not request.user.has_perm(f"{modelo._meta.app_label}.{'change' if pk else 'add'}_{modelo._meta.model_name}"):
        raise PermissionDenied
    objeto = get_object_or_404(modelo, pk=pk) if pk else None
    form = formulario(request.POST or None, instance=objeto)
    if request.method == "POST" and form.is_valid():
        objeto = form.save(commit=False)
        # No sobrescribir existencias si otro empleado registra un consumo al mismo tiempo.
        if objeto.pk:
            objeto.save(update_fields=formulario._meta.fields)
        else:
            objeto.save()
        messages.success(request, "Ficha guardada en el cuaderno.")
        if entidad == "clientes":
            return redirect("cliente", pk=objeto.pk)
        return redirect("lista", entidad=entidad)
    return render(request, "gestion/form.html", {"titulo": f"{'Editar' if pk else 'Nueva ficha'} · {titulo}", "form": form,
        "volver": reverse("lista", kwargs={"entidad": entidad}),
        "nota": "El stock se registra con movimientos de entrada, consumo o devolución." if entidad in ["telas", "insumos"] else ""})
