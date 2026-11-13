from django.urls import path
from . import views

urlpatterns = [path("", views.lista, name="empleados"), path("nuevo/", views.editar, name="empleado_nuevo"), path("<int:pk>/editar/", views.editar, name="empleado_editar"), path("mi-clave/", views.clave, name="clave")]
