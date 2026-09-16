"""Funciones de analítica y predicción de ventas para Dotaciones Dony.

Sin dependencias externas: se usa agregación de Django y estadística simple
(media móvil + demanda diaria) para sugerir mínimos y máximos de inventario.
"""

import math
from datetime import timedelta

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.inventory.models import Producto
from apps.sales.models import DetalleVenta, Venta

# Parámetros de predicción (pueden parametrizarse más adelante).
DIAS_HISTORIA = 30      # días de ventas usados para calcular la demanda.
DIAS_REPOSICION = 7     # días que tarda en llegar un pedido (lead time).
DIAS_REVISION = 15      # días entre revisiones de inventario.


def _ventas_validas(desde, hasta, sede=None):
    qs = Venta.objects.filter(estado=Venta.Estado.PAGADA, fecha__date__range=(desde, hasta))
    if sede:
        qs = qs.filter(sede=sede)
    return qs


def total_ventas(desde, hasta, sede=None):
    return _ventas_validas(desde, hasta, sede).aggregate(t=Sum("total"))["t"] or 0


def numero_ventas(desde, hasta, sede=None):
    return _ventas_validas(desde, hasta, sede).count()


def ticket_promedio(desde, hasta, sede=None):
    n = numero_ventas(desde, hasta, sede)
    return (total_ventas(desde, hasta, sede) / n) if n else 0


def utilidad(desde, hasta, sede=None):
    detalles = DetalleVenta.objects.filter(
        venta__estado=Venta.Estado.PAGADA,
        venta__fecha__date__range=(desde, hasta),
    )
    if sede:
        detalles = detalles.filter(venta__sede=sede)
    return detalles.aggregate(
        u=Sum((F("precio_unitario") - F("costo_unitario")) * F("cantidad"))
    )["u"] or 0


def ventas_por_dia(desde, hasta, sede=None):
    return (
        _ventas_validas(desde, hasta, sede)
        .annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(total=Sum("total"), cantidad=Count("id"))
        .order_by("dia")
    )


def top_productos(desde, hasta, sede=None, n=5):
    detalles = DetalleVenta.objects.filter(
        venta__estado=Venta.Estado.PAGADA,
        venta__fecha__date__range=(desde, hasta),
    )
    if sede:
        detalles = detalles.filter(venta__sede=sede)
    return list(
        detalles.values("producto__nombre")
        .annotate(cantidad=Sum("cantidad"))
        .order_by("-cantidad")[:n]
    )


def stock_bajo():
    productos = Producto.objects.filter(activo=True)
    return [p for p in productos if p.stock_actual <= p.stock_min]


def _demanda_diaria(producto, dias=DIAS_HISTORIA):
    """Promedio de unidades vendidas por día en los últimos `dias` días."""
    desde = timezone.localdate() - timedelta(days=dias - 1)
    total = DetalleVenta.objects.filter(
        venta__estado=Venta.Estado.PAGADA,
        venta__fecha__date__gte=desde,
        producto=producto,
    ).aggregate(t=Sum("cantidad"))["t"] or 0
    return total / dias


def sugerencias_producto(producto):
    """Calcula mín/máx sugeridos y venta esperada para un producto."""
    demanda = _demanda_diaria(producto)
    min_sug = math.ceil(demanda * DIAS_REPOSICION)
    max_sug = math.ceil(demanda * (DIAS_REPOSICION + DIAS_REVISION))
    return {
        "producto": producto,
        "demanda_diaria": round(demanda, 2),
        "venta_esperada_30dias": math.ceil(demanda * 30),
        "min_actual": producto.stock_min,
        "max_actual": producto.stock_max,
        "min_sug": min_sug,
        "max_sug": max_sug,
        "stock_actual": producto.stock_actual,
    }


def sugerencias_todos():
    return [sugerencias_producto(p) for p in Producto.objects.filter(activo=True)]


def aplicar_sugerencias():
    """Aplica los mín/máx sugeridos a todos los productos activos. Retorna el conteo."""
    actualizados = 0
    for p in Producto.objects.filter(activo=True):
        s = sugerencias_producto(p)
        if p.stock_min != s["min_sug"] or p.stock_max != s["max_sug"]:
            p.stock_min = s["min_sug"]
            p.stock_max = s["max_sug"]
            p.save(update_fields=["stock_min", "stock_max"])
            actualizados += 1
    return actualizados
