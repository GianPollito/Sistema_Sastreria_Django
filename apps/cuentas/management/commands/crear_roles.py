from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Crea o sincroniza los permisos de los tres roles del taller."

    @transaction.atomic
    def handle(self, *args, **options):
        aplicaciones = ["cuentas", "clientes", "catalogo", "inventario", "pedidos", "pagos", "agenda", "panel"]
        permisos = Permission.objects.filter(content_type__app_label__in=aplicaciones)
        administrador, _ = Group.objects.get_or_create(name="Administrador")
        administrador.permissions.set(permisos)
        recepcionista, _ = Group.objects.get_or_create(name="Recepcionista")
        recepcionista.permissions.set([p for p in permisos if
            (p.content_type.app_label in {"clientes", "pedidos", "pagos", "agenda"} and not p.codename.startswith("delete_"))
            or p.codename.startswith("view_")])
        sastre, _ = Group.objects.get_or_create(name="Sastre")
        sastre.permissions.set([p for p in permisos if p.codename.startswith("view_")
            or p.codename in {"add_medida", "change_pedido", "add_movimientoinventario"}])
        self.stdout.write(self.style.SUCCESS("Roles del taller sincronizados."))
