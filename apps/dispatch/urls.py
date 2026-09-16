from django.urls import path

from . import views

app_name = "dispatch"

urlpatterns = [
    path("", views.despachos, name="despachos"),
    path("nuevo/", views.despacho_nuevo, name="despacho_nuevo"),
    path("<int:pk>/editar/", views.despacho_editar, name="despacho_editar"),
    path("<int:pk>/", views.despacho_detalle, name="despacho_detalle"),
]
