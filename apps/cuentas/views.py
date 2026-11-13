from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .access import acceso
from .forms import EmpleadoForm
from .models import Empleado


@acceso("cuentas.view_empleado")
def lista(request):
    return render(request, "cuentas/lista.html", {"empleados": Empleado.objects.select_related("usuario").prefetch_related("usuario__groups")})


@acceso()
def editar(request, pk=None):
    if not request.user.has_perm(f"cuentas.{'change' if pk else 'add'}_empleado"):
        raise PermissionDenied
    empleado = get_object_or_404(Empleado, pk=pk) if pk else None
    inicial = {}
    if empleado:
        u = empleado.usuario
        inicial = {"usuario": u.username, "nombre": u.first_name, "apellido": u.last_name, "correo": u.email,
            "telefono": empleado.telefono, "activo": empleado.activo, "rol": u.groups.filter(name__in=["Administrador", "Sastre", "Recepcionista"]).first()}
    form = EmpleadoForm(request.POST or None, initial=inicial, empleado=empleado)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        if empleado and empleado.usuario_id == request.user.pk and (not datos["activo"] or datos["rol"].name != "Administrador"):
            form.add_error(None, "Conserva tu acceso de administrador; otro administrador puede modificar tu cuenta.")
        else:
            with transaction.atomic():
                usuario = empleado.usuario if empleado else get_user_model()()
                usuario.username, usuario.first_name, usuario.last_name = datos["usuario"], datos["nombre"], datos["apellido"]
                usuario.email, usuario.is_active = datos["correo"], datos["activo"]
                if datos["clave"]:
                    usuario.set_password(datos["clave"])
                usuario.save()
                usuario.groups.set([datos["rol"]])
                if not empleado:
                    empleado = Empleado(usuario=usuario)
                empleado.telefono, empleado.activo = datos["telefono"], datos["activo"]
                empleado.save()
                if usuario.pk == request.user.pk:
                    update_session_auth_hash(request, usuario)
            messages.success(request, "Cuenta del taller guardada.")
            return redirect("empleados")
    return render(request, "gestion/form.html", {"form": form, "titulo": "Cuenta de empleado", "volver": reverse("empleados")})


@acceso()
def clave(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        update_session_auth_hash(request, usuario)
        messages.success(request, "Contraseña actualizada.")
        return redirect("panel")
    return render(request, "gestion/form.html", {"form": form, "titulo": "Cambiar mi contraseña", "volver": reverse("panel")})
