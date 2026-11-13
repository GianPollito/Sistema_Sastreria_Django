from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import MySQLdb


class Command(BaseCommand):
    help = "Crea la base configurada solo si no existe; no borra datos ni aplica migraciones."

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        nombre = db["NAME"]
        if not nombre or not all(c.isascii() and (c.isalnum() or c == "_") for c in nombre):
            raise CommandError("El nombre de base debe contener solo letras, números y guiones bajos.")
        conexion = MySQLdb.connect(host=db["HOST"], port=int(db["PORT"]), user=db["USER"], passwd=db["PASSWORD"], charset="utf8mb4")
        try:
            with conexion.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{nombre}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        finally:
            conexion.close()
        self.stdout.write(self.style.SUCCESS("Base local disponible; no se han modificado tablas existentes."))
