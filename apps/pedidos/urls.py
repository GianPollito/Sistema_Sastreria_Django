from django.urls import path
from . import views

urlpatterns = [
    path("", views.tablero, name="tablero"), path("nuevo/", views.crear, name="pedido_nuevo"),
    path("<int:pk>/", views.ficha, name="pedido"), path("<int:pk>/editar/", views.editar, name="pedido_editar"),
    path("<int:pk>/prenda/", views.agregar_detalle, name="detalle_nuevo"),
    path("<int:pk>/prenda/<int:detalle_pk>/editar/", views.agregar_detalle, name="detalle_editar"),
    path("<int:pk>/estado/", views.estado, name="pedido_estado"), path("<int:pk>/cobrar/", views.cobrar, name="cobrar"),
]
