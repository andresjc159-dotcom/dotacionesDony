"""Vistas del módulo de despachos."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import DespachoCreateForm, DespachoEditForm
from .models import Despacho
from .services import notificar_despacho_enviado


@login_required
def despachos(request):
    estado = request.GET.get("estado", "")
    qs = Despacho.objects.select_related("orden")
    if estado:
        qs = qs.filter(estado=estado)
    contexto = {
        "titulo": "Despachos",
        "despachos": qs,
        "estado": estado,
        "estados": Despacho.Estado.choices,
    }
    return render(request, "dispatch/lista.html", contexto)


@login_required
def despacho_nuevo(request):
    form = DespachoCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        despacho = form.save(commit=False)
        orden = despacho.orden
        despacho.direccion = orden.direccion
        despacho.ciudad = orden.ciudad
        despacho.save()
        despacho.sincronizar_orden()
        messages.success(request, f"Despacho creado para {orden.numero}.")
        return redirect("dispatch:despachos")
    contexto = {"titulo": "Nuevo despacho", "form": form}
    return render(request, "dispatch/despacho_form.html", contexto)


@login_required
def despacho_editar(request, pk):
    despacho = get_object_or_404(Despacho, pk=pk)
    form = DespachoEditForm(request.POST or None, instance=despacho)
    if request.method == "POST" and form.is_valid():
        despacho = form.save(commit=False)
        if despacho.estado == Despacho.Estado.ENVIADO and not despacho.fecha_envio:
            despacho.fecha_envio = timezone.now()
        if despacho.estado == Despacho.Estado.ENTREGADO and not despacho.fecha_entrega:
            despacho.fecha_entrega = timezone.now()
        despacho.save()
        despacho.sincronizar_orden()
        if despacho.estado == Despacho.Estado.ENVIADO:
            notificar_despacho_enviado(despacho)
        messages.success(request, "Despacho actualizado.")
        return redirect("dispatch:despachos")
    contexto = {"titulo": f"Editar despacho {despacho.orden.numero}", "form": form, "despacho": despacho}
    return render(request, "dispatch/despacho_form.html", contexto)


@login_required
def despacho_detalle(request, pk):
    despacho = get_object_or_404(
        Despacho.objects.select_related("orden").prefetch_related("orden__detalles__producto", "orden__detalles__variante"),
        pk=pk,
    )
    contexto = {"titulo": f"Despacho {despacho.orden.numero}", "despacho": despacho}
    return render(request, "dispatch/detalle.html", contexto)
