"""Vistas del módulo de bodega."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AjusteForm, CompraForm, DetalleCompraFormSet, ProveedorForm, TransferenciaForm
from .models import AjusteInventario, Compra, Proveedor, TransferenciaSede


def _proximo_numero_compra():
    año = __import__("django").utils.timezone.now().year
    total = Compra.objects.count() + 1
    return f"OC-{año}-{total:04d}"


# ---------------------------------------------------------------------------
# Proveedores
# ---------------------------------------------------------------------------

@login_required
def proveedores(request):
    contexto = {"titulo": "Proveedores", "proveedores": Proveedor.objects.all()}
    return render(request, "warehouse/proveedores.html", contexto)


@login_required
def proveedor_form(request, pk=None):
    instancia = get_object_or_404(Proveedor, pk=pk) if pk else None
    form = ProveedorForm(request.POST or None, instance=instancia)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"Proveedor «{obj.nombre}» guardado.")
        return redirect("warehouse:proveedores")
    contexto = {"titulo": "Nuevo proveedor" if not instancia else "Editar proveedor", "form": form}
    return render(request, "warehouse/proveedor_form.html", contexto)


@login_required
def proveedor_eliminar(request, pk):
    obj = get_object_or_404(Proveedor, pk=pk)
    if request.method == "POST":
        nombre = obj.nombre
        obj.delete()
        messages.success(request, f"Proveedor «{nombre}» eliminado.")
        return redirect("warehouse:proveedores")
    contexto = {"titulo": "Eliminar proveedor", "objeto": obj, "cancelar": "warehouse:proveedores"}
    return render(request, "inventory/config_eliminar.html", contexto)


# ---------------------------------------------------------------------------
# Compras (entradas de mercancía)
# ---------------------------------------------------------------------------

@login_required
def compras(request):
    contexto = {"titulo": "Compras", "compras": Compra.objects.select_related("proveedor", "sede").all()}
    return render(request, "warehouse/compras.html", contexto)


@login_required
def compra_nueva(request):
    form = CompraForm(request.POST or None)
    formset = DetalleCompraFormSet(request.POST or None, instance=Compra())
    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                compra = form.save(commit=False)
                compra.numero = _proximo_numero_compra()
                compra.creado_por = request.user
                compra.save()
                formset.instance = compra
                detalles = formset.save(commit=False)
                total = 0
                for detalle in detalles:
                    detalle.save()
                    detalle.aplicar_stock(1)
                    total += detalle.subtotal
                for eliminado in formset.deleted_objects:
                    pass
                compra.total = total
                compra.save(update_fields=["total"])
            messages.success(request, f"Compra «{compra.numero}» registrada. Stock actualizado.")
            return redirect("warehouse:compras")
    contexto = {"titulo": "Nueva compra", "form": form, "formset": formset}
    return render(request, "warehouse/compra_form.html", contexto)


@login_required
def compra_detalle(request, pk):
    compra = get_object_or_404(Compra.objects.prefetch_related("detalles__producto", "detalles__variante"), pk=pk)
    contexto = {"titulo": compra.numero, "compra": compra}
    return render(request, "warehouse/compra_detalle.html", contexto)


@login_required
def compra_eliminar(request, pk):
    compra = get_object_or_404(Compra.objects.prefetch_related("detalles"), pk=pk)
    if request.method == "POST":
        with transaction.atomic():
            for detalle in compra.detalles.all():
                detalle.aplicar_stock(-1)
            compra.delete()
        messages.success(request, f"Compra «{compra.numero}» eliminada y stock revertido.")
        return redirect("warehouse:compras")
    contexto = {"titulo": "Eliminar compra", "objeto": compra, "cancelar": "warehouse:compras"}
    return render(request, "inventory/config_eliminar.html", contexto)


# ---------------------------------------------------------------------------
# Ajustes de inventario
# ---------------------------------------------------------------------------

@login_required
def ajustes(request):
    contexto = {
        "titulo": "Ajustes de inventario",
        "ajustes": AjusteInventario.objects.select_related("sede", "producto", "variante").all(),
    }
    return render(request, "warehouse/ajustes.html", contexto)


@login_required
def ajuste_nuevo(request):
    form = AjusteForm(request.POST or None, initial={"sede": request.user.sede_id})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            ajuste = form.save(commit=False)
            ajuste.creado_por = request.user
            ajuste.save()
            ajuste.aplicar_stock(1)
        messages.success(request, "Ajuste registrado. Stock actualizado.")
        return redirect("warehouse:ajustes")
    contexto = {"titulo": "Nuevo ajuste", "form": form}
    return render(request, "warehouse/ajuste_form.html", contexto)


@login_required
def ajuste_eliminar(request, pk):
    ajuste = get_object_or_404(AjusteInventario, pk=pk)
    if request.method == "POST":
        with transaction.atomic():
            ajuste.aplicar_stock(-1)
            ajuste.delete()
        messages.success(request, "Ajuste eliminado y stock revertido.")
        return redirect("warehouse:ajustes")
    contexto = {"titulo": "Eliminar ajuste", "objeto": ajuste, "cancelar": "warehouse:ajustes"}
    return render(request, "inventory/config_eliminar.html", contexto)


# ---------------------------------------------------------------------------
# Transferencias entre sedes
# ---------------------------------------------------------------------------

@login_required
def transferencias(request):
    contexto = {
        "titulo": "Transferencias",
        "transferencias": TransferenciaSede.objects.select_related("origen", "destino", "producto", "variante").all(),
    }
    return render(request, "warehouse/transferencias.html", contexto)


@login_required
def transferencia_nueva(request):
    form = TransferenciaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            transferencia = form.save(commit=False)
            transferencia.creado_por = request.user
            transferencia.estado = TransferenciaSede.Estado.COMPLETADA
            transferencia.save()
            transferencia.aplicar_stock(1)
        messages.success(request, "Transferencia realizada. Stock actualizado.")
        return redirect("warehouse:transferencias")
    contexto = {"titulo": "Nueva transferencia", "form": form}
    return render(request, "warehouse/transferencia_form.html", contexto)


@login_required
def transferencia_eliminar(request, pk):
    transferencia = get_object_or_404(TransferenciaSede, pk=pk)
    if request.method == "POST":
        with transaction.atomic():
            transferencia.aplicar_stock(-1)
            transferencia.delete()
        messages.success(request, "Transferencia eliminada y stock revertido.")
        return redirect("warehouse:transferencias")
    contexto = {"titulo": "Eliminar transferencia", "objeto": transferencia, "cancelar": "warehouse:transferencias"}
    return render(request, "inventory/config_eliminar.html", contexto)
