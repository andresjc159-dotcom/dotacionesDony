from django.contrib import admin

from .models import DetalleOrden, Orden


class DetalleOrdenInline(admin.TabularInline):
    model = DetalleOrden
    extra = 0


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente_nombre", "email", "fecha", "total", "estado")
    list_filter = ("estado", "fecha")
    search_fields = ("numero", "cliente_nombre", "email", "documento")
    inlines = [DetalleOrdenInline]
