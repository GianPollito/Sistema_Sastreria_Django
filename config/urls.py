from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from apps.panel.views import inicio

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ingresar/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("", inicio, name="panel"),
    path("cuaderno/", include("apps.panel.urls")),
    path("clientes/", include("apps.clientes.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
    path("inventario/", include("apps.inventario.urls")),
    path("pagos/", include("apps.pagos.urls")),
    path("agenda/", include("apps.agenda.urls")),
    path("equipo/", include("apps.cuentas.urls")),
]
