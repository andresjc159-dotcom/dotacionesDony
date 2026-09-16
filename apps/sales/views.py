"""Vistas del módulo de ventas: lista, detalle/ticket, anulación y clientes."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm
from .models import Cliente, Venta


@login_required
def ventas(request):
    q = request.GET.get("q", "").strip()
    ventas = Venta.objects.select_related("sede", "cliente", "cajero").prefetch_related("detalles")
    if q:
        ventas = ventas.filter(numero__icontains=q) | ventas.filter(cliente__nombre__icontains=q)

    total = sum(v.total for v in ventas if v.estado == Venta.Estado.PAGADA)
    contexto = {
        "titulo": "Ventas",
        "ventas": ventas,
        "q": q,
        "total_pagadas": total,
    }
    return render(request, "sales/ventas.html", contexto)


@login_required
def venta_detalle(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related("sede", "cliente", "cajero").prefetch_related("detalles__producto", "detalles__variante"),
        pk=pk,
    )
    contexto = {"titulo": venta.numero, "venta": venta}
    return render(request, "sales/ticket.html", contexto)


@login_required
def venta_anular(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == "POST":
        with transaction.atomic():
            venta.anular()
        messages.success(request, f"Venta {venta.numero} anulada y stock restaurado.")
        return redirect("sales:ventas")
    contexto = {"titulo": "Anular venta", "objeto": venta, "cancelar": "sales:ventas"}
    return render(request, "inventory/config_eliminar.html", contexto)


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

@login_required
def clientes(request):
    contexto = {"titulo": "Clientes", "clientes": Cliente.objects.all()}
    return render(request, "sales/clientes.html", contexto)


@login_required
def cliente_form(request, pk=None):
    instancia = get_object_or_404(Cliente, pk=pk) if pk else None
    form = ClienteForm(request.POST or None, instance=instancia)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"Cliente «{obj.nombre}» guardado.")
        return redirect("sales:clientes")
    contexto = {"titulo": "Nuevo cliente" if not instancia else "Editar cliente", "form": form}
    return render(request, "sales/cliente_form.html", contexto)


@login_required
def cliente_eliminar(request, pk):
    obj = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        nombre = obj.nombre
        obj.delete()
        messages.success(request, f"Cliente «{nombre}» eliminado.")
        return redirect("sales:clientes")
    contexto = {"titulo": "Eliminar cliente", "objeto": obj, "cancelar": "sales:clientes"}
    return render(request, "inventory/config_eliminar.html", contexto)
