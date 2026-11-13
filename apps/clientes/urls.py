from django.urls import path
from . import views

urlpatterns = [path("<int:pk>/", views.ficha, name="cliente"), path("<int:pk>/medidas/nueva/", views.medida, name="medida_nueva")]
