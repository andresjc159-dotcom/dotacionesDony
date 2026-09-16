from django.contrib import admin

from .models import AjusteInventario, Compra, DetalleCompra, Proveedor, TransferenciaSede


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "documento", "telefono", "email", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "documento", "email")


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("numero", "proveedor", "sede", "fecha", "total")
    list_filter = ("sede", "fecha")
    search_fields = ("numero", "proveedor__nombre")
    inlines = [DetalleCompraInline]


@admin.register(AjusteInventario)
class AjusteAdmin(admin.ModelAdmin):
    list_display = ("producto", "variante", "tipo", "cantidad", "sede", "fecha", "motivo")
    list_filter = ("tipo", "sede", "fecha")


@admin.register(TransferenciaSede)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ("producto", "variante", "cantidad", "origen", "destino", "estado", "fecha")
    list_filter = ("estado", "origen", "destino")
