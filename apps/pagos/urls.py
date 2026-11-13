from django.urls import path
from . import views

urlpatterns = [path("", views.lista, name="pagos"), path("<int:pk>/comprobante/", views.comprobante, name="comprobante")]
