from django.contrib import admin

from .models import Atributo, Categoria, Impuesto, Producto, StockSede, ValorAtributo, Variante


class ValorAtributoInline(admin.TabularInline):
    model = ValorAtributo
    extra = 1


@admin.register(Atributo)
class AtributoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    inlines = [ValorAtributoInline]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "padre", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)


@admin.register(Impuesto)
class ImpuestoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tarifa", "es_por_defecto", "activo")
    list_filter = ("activo", "es_por_defecto")


class VarianteInline(admin.TabularInline):
    model = Variante
    extra = 0
    fields = ("sku", "codigo_barras", "valores", "precio", "costo", "activo")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("sku", "nombre", "categoria", "usa_variantes", "precio", "stock_actual", "activo")
    list_filter = ("usa_variantes", "activo", "categoria")
    search_fields = ("sku", "nombre", "codigo_barras")
    inlines = [VarianteInline]


@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    list_display = ("sku", "producto", "descripcion_valores", "precio_efectivo", "stock_actual", "activo")
    list_filter = ("activo", "producto__categoria")
    search_fields = ("sku", "producto__nombre")


@admin.register(StockSede)
class StockSedeAdmin(admin.ModelAdmin):
    list_display = ("sede", "producto", "variante", "cantidad")
    list_filter = ("sede",)
    search_fields = ("producto__sku", "producto__nombre", "variante__sku")
