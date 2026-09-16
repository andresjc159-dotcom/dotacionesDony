from django.contrib import admin

from .models import CajaTurno, Cliente, DetalleVenta, Venta


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "documento", "telefono", "email")
    search_fields = ("nombre", "documento", "email")


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("numero", "sede", "cliente", "cajero", "fecha", "total", "estado", "metodo_pago")
    list_filter = ("estado", "metodo_pago", "sede", "fecha")
    search_fields = ("numero", "cliente__nombre")
    inlines = [DetalleVentaInline]


@admin.register(CajaTurno)
class CajaTurnoAdmin(admin.ModelAdmin):
    list_display = ("sede", "usuario", "fecha_apertura", "monto_inicial", "estado", "fecha_cierre")
    list_filter = ("estado", "sede")
