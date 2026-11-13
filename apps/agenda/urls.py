from django.urls import path
from . import views

urlpatterns = [path("", views.semana, name="agenda"), path("nueva/", views.editar, name="cita_nueva"), path("<int:pk>/editar/", views.editar, name="cita_editar")]
