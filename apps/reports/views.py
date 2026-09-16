"""Vistas del módulo de reportes y predicción."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.users.models import Sede

from . import analytics


def _rango(request):
    hoy = timezone.localdate()
    desde = request.GET.get("desde") or (hoy - timedelta(days=analytics.DIAS_HISTORIA - 1)).isoformat()
    hasta = request.GET.get("hasta") or hoy.isoformat()
    return desde, hasta


@login_required
def reporte(request):
    desde, hasta = _rango(request)
    sede_id = request.GET.get("sede")
    sede = Sede.objects.filter(pk=sede_id).first() if sede_id else None

    ventas_dia = list(analytics.ventas_por_dia(desde, hasta, sede))
    max_total = max((v["total"] for v in ventas_dia), default=0)

    contexto = {
        "titulo": "Reportes",
        "desde": desde,
        "hasta": hasta,
        "sede": sede,
        "sedes": Sede.objects.all(),
        "total_ventas": analytics.total_ventas(desde, hasta, sede),
        "utilidad": analytics.utilidad(desde, hasta, sede),
        "numero_ventas": analytics.numero_ventas(desde, hasta, sede),
        "ticket_promedio": analytics.ticket_promedio(desde, hasta, sede),
        "ventas_por_dia": ventas_dia,
        "max_total": max_total,
        "top_productos": analytics.top_productos(desde, hasta, sede),
        "stock_bajo": analytics.stock_bajo(),
    }
    return render(request, "reports/reporte.html", contexto)


@login_required
def prediccion(request):
    contexto = {
        "titulo": "Predicción y mín/máx",
        "sugerencias": analytics.sugerencias_todos(),
        "dias_historia": analytics.DIAS_HISTORIA,
        "dias_reposicion": analytics.DIAS_REPOSICION,
        "dias_revision": analytics.DIAS_REVISION,
    }
    return render(request, "reports/prediccion.html", contexto)


@login_required
def aplicar_minmax(request):
    if request.method == "POST":
        n = analytics.aplicar_sugerencias()
        messages.success(request, f"Mín/máx actualizados en {n} producto(s).")
    return redirect("reports:prediccion")
