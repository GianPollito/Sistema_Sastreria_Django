from django.conf import settings
from django.db import models


class Empleado(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.get_username()
