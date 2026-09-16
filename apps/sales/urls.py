from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("", views.ventas, name="ventas"),
    path("<int:pk>/", views.venta_detalle, name="venta_detalle"),
    path("<int:pk>/anular/", views.venta_anular, name="venta_anular"),
    path("clientes/", views.clientes, name="clientes"),
    path("clientes/nuevo/", views.cliente_form, name="cliente_nuevo"),
    path("clientes/<int:pk>/editar/", views.cliente_form, name="cliente_editar"),
    path("clientes/<int:pk>/eliminar/", views.cliente_eliminar, name="cliente_eliminar"),
]
