from django.urls import path

from . import views

app_name = "pos"

urlpatterns = [
    path("", views.caja, name="caja"),
    path("abrir/", views.caja_abrir, name="abrir"),
    path("cerrar/", views.caja_cerrar, name="cerrar"),
    path("agregar/", views.caja_agregar, name="agregar"),
    path("quitar/", views.caja_quitar, name="quitar"),
    path("cobrar/", views.caja_cobrar, name="cobrar"),
]
