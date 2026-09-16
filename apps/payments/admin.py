from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("orden", "monto", "metodo", "estado", "referencia", "creado_en")
    list_filter = ("estado", "metodo")
    search_fields = ("referencia", "orden__numero")
