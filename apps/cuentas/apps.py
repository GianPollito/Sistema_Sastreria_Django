from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cuentas"
    verbose_name = "Equipo del taller"

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save
        from .models import Empleado

        def completar_superusuario(sender, instance, raw=False, **kwargs):
            if not raw and instance.is_superuser:
                Empleado.objects.get_or_create(usuario=instance)

        post_save.connect(completar_superusuario, sender=get_user_model(), weak=False, dispatch_uid="cuentas.completar_superusuario")
