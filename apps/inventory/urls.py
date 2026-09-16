from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Productos
    path("productos/", views.lista_productos, name="productos"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/eliminar/", views.producto_eliminar, name="producto_eliminar"),

    # Ubicaciones
    path("ubicaciones/", views.ubicaciones, name="ubicaciones"),

    # Parámetros
    path("parametros/", views.parametros, name="parametros"),
    path("categorias/nueva/", views.categoria_form, name="categoria_nueva"),
    path("categorias/<int:pk>/editar/", views.categoria_form, name="categoria_editar"),
    path("categorias/<int:pk>/eliminar/", views.categoria_eliminar, name="categoria_eliminar"),
    path("impuestos/nuevo/", views.impuesto_form, name="impuesto_nuevo"),
    path("impuestos/<int:pk>/editar/", views.impuesto_form, name="impuesto_editar"),
    path("impuestos/<int:pk>/eliminar/", views.impuesto_eliminar, name="impuesto_eliminar"),
    path("atributos/nuevo/", views.atributo_form, name="atributo_nuevo"),
    path("atributos/<int:pk>/editar/", views.atributo_form, name="atributo_editar"),
    path("atributos/<int:pk>/eliminar/", views.atributo_eliminar, name="atributo_eliminar"),
]
