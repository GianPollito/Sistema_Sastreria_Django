"""Pruebas de integración en una base MariaDB temporal independiente."""
import uuid
from .settings import *  # noqa: F403

DATABASES["default"]["TEST"] = {"NAME": f"test_atelier_{uuid.uuid4().hex[:12]}"}  # noqa: F405
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
