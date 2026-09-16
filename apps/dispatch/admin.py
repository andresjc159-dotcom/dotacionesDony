from django.contrib import admin

from .models import Despacho


@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = ("orden", "transportadora", "numero_guia", "ciudad", "estado", "fecha")
    list_filter = ("estado", "transportadora", "fecha")
    search_fields = ("orden__numero", "numero_guia", "orden__cliente_nombre")
