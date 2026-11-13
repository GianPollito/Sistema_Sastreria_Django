from django.urls import path
from . import gestion

urlpatterns = [path("<str:entidad>/", gestion.listado, name="lista"), path("<str:entidad>/nuevo/", gestion.editar, name="crear"), path("<str:entidad>/<int:pk>/editar/", gestion.editar, name="editar")]
