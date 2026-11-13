from django.urls import path
from . import views

urlpatterns = [path("<str:entidad>/<int:pk>/", views.historial, name="movimientos"), path("<str:entidad>/<int:pk>/nuevo/", views.movimiento, name="movimiento_nuevo")]
