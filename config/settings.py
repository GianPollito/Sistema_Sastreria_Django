import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [v.strip() for v in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if v.strip()]
CSRF_TRUSTED_ORIGINS = [v.strip() for v in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if v.strip()]
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"
REGISTRATION_CODE = os.getenv("REGISTRATION_CODE", "")
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    *[f"apps.{name}" for name in ("cuentas", "clientes", "catalogo", "inventario", "pedidos", "pagos", "agenda", "panel")],
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.mysql", "NAME": os.environ["DB_NAME"],
    "USER": os.environ["DB_USER"], "PASSWORD": os.environ["DB_PASSWORD"], "HOST": os.environ["DB_HOST"],
    "PORT": os.environ["DB_PORT"], "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"}}}
AUTH_PASSWORD_VALIDATORS = [{"NAME": f"django.contrib.auth.password_validation.{name}"} for name in
    ("UserAttributeSimilarityValidator", "MinimumLengthValidator", "CommonPasswordValidator", "NumericPasswordValidator")]
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "panel"
LOGOUT_REDIRECT_URL = "login"
