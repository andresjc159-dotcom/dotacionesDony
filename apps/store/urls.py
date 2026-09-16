from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("producto/<int:pk>/", views.producto_detalle, name="producto_detalle"),
    path("carrito/", views.carrito, name="carrito"),
    path("carrito/agregar/", views.carrito_agregar, name="carrito_agregar"),
    path("carrito/quitar/", views.carrito_quitar, name="carrito_quitar"),
    path("checkout/", views.checkout, name="checkout"),
    path("orden/<int:pk>/", views.orden, name="orden"),
    path("orden/<int:pk>/simular-pago/", views.simular_pago, name="simular_pago"),
]
