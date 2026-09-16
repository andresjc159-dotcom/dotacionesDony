"""Rutas principales del proyecto Dotaciones Dony."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.users.urls")),
    path("inventario/", include("apps.inventory.urls")),
    path("bodega/", include("apps.warehouse.urls")),
    path("caja/", include("apps.pos.urls")),
    path("ventas/", include("apps.sales.urls")),
    path("reportes/", include("apps.reports.urls")),
    path("tienda/", include("apps.store.urls")),
    path("wompi/", include("apps.payments.urls")),
    path("despachos/", include("apps.dispatch.urls")),
]
