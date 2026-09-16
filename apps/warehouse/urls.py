from django.urls import path

from . import views

app_name = "warehouse"

urlpatterns = [
    # Proveedores
    path("proveedores/", views.proveedores, name="proveedores"),
    path("proveedores/nuevo/", views.proveedor_form, name="proveedor_nuevo"),
    path("proveedores/<int:pk>/editar/", views.proveedor_form, name="proveedor_editar"),
    path("proveedores/<int:pk>/eliminar/", views.proveedor_eliminar, name="proveedor_eliminar"),
    # Compras
    path("compras/", views.compras, name="compras"),
    path("compras/nueva/", views.compra_nueva, name="compra_nueva"),
    path("compras/<int:pk>/", views.compra_detalle, name="compra_detalle"),
    path("compras/<int:pk>/eliminar/", views.compra_eliminar, name="compra_eliminar"),
    # Ajustes
    path("ajustes/", views.ajustes, name="ajustes"),
    path("ajustes/nuevo/", views.ajuste_nuevo, name="ajuste_nuevo"),
    path("ajustes/<int:pk>/eliminar/", views.ajuste_eliminar, name="ajuste_eliminar"),
    # Transferencias
    path("transferencias/", views.transferencias, name="transferencias"),
    path("transferencias/nueva/", views.transferencia_nueva, name="transferencia_nueva"),
    path("transferencias/<int:pk>/eliminar/", views.transferencia_eliminar, name="transferencia_eliminar"),
]
