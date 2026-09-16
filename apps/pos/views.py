"""Vistas del punto de venta (POS) y control de caja."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.inventory.models import Producto, Variante
from apps.sales.forms import AperturaCajaForm, CierreCajaForm, CobrarForm
from apps.sales.models import CajaTurno, DetalleVenta, Venta


def _cart(request):
    return request.session.get("carrito", [])


def _save_cart(request, cart):
    request.session["carrito"] = cart
    request.session.modified = True


def _turno_abierto(sede):
    return CajaTurno.objects.filter(sede=sede, estado=CajaTurno.Estado.ABIERTA).first()


def _lineas_carrito(cart):
    lineas = []
    for item in cart:
        producto = Producto.objects.filter(pk=item["producto_id"]).first()
        variante = Variante.objects.filter(pk=item["variante_id"]).first() if item.get("variante_id") else None
        if producto is None:
            continue
        precio = float(item["precio"])
        lineas.append({
            "producto": producto,
            "variante": variante,
            "cantidad": item["cantidad"],
            "precio": precio,
            "costo": float(item.get("costo", 0)),
            "subtotal": precio * item["cantidad"],
        })
    return lineas


def _totales(lineas):
    subtotal = sum(l["subtotal"] for l in lineas)
    impuestos = 0.0
    for l in lineas:
        impuesto = l["producto"].impuesto
        if impuesto and impuesto.tarifa > 0:
            impuestos += l["subtotal"] * float(impuesto.tarifa) / (100 + float(impuesto.tarifa))
    return {
        "subtotal": subtotal,
        "descuento": 0.0,
        "impuestos": round(impuestos, 2),
        "total": round(subtotal, 2),
    }


@login_required
def caja(request):
    sede = request.user.sede

    if not sede:
        if not request.user.es_master:
            messages.error(request, "Tu usuario no tiene una sede asignada.")
            return redirect("users:dashboard")
        from apps.users.models import Sede
        sede = Sede.objects.filter(activa=True).first()

    turno = _turno_abierto(sede)

    if not turno:
        form = AperturaCajaForm()
        return render(request, "pos/apertura.html", {"titulo": "Abrir caja", "form": form})

    carrito = _lineas_carrito(_cart(request))
    totales = _totales(carrito)
    productos = Producto.objects.filter(activo=True).prefetch_related("variantes__valores")
    cobrar_form = CobrarForm()
    cierre_form = CierreCajaForm()

    contexto = {
        "titulo": "Caja",
        "turno": turno,
        "carrito": carrito,
        "totales": totales,
        "productos": productos,
        "cobrar_form": cobrar_form,
        "cierre_form": cierre_form,
    }
    return render(request, "pos/caja.html", contexto)


@login_required
def caja_abrir(request):
    if request.method == "POST":
        sede = request.user.sede
        if not sede:
            messages.error(request, "Tu usuario no tiene una sede asignada.")
            return redirect("pos:caja")
        if _turno_abierto(sede):
            messages.info(request, "Ya hay una caja abierta en esta sede.")
            return redirect("pos:caja")
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            turno = form.save(commit=False)
            turno.sede = sede
            turno.usuario = request.user
            turno.save()
            messages.success(request, "Caja abierta correctamente.")
    return redirect("pos:caja")


@login_required
def caja_cerrar(request):
    if request.method == "POST":
        turno = _turno_abierto(request.user.sede) if request.user.sede else None
        if not turno:
            messages.error(request, "No hay caja abierta.")
            return redirect("pos:caja")
        form = CierreCajaForm(request.POST)
        if form.is_valid():
            turno.monto_cierre = form.cleaned_data["monto_cierre"]
            turno.fecha_cierre = timezone.now()
            turno.estado = CajaTurno.Estado.CERRADA
            turno.save()
            messages.success(request, "Caja cerrada correctamente.")
    return redirect("pos:caja")


@login_required
def caja_agregar(request):
    if request.method == "POST":
        producto_id = request.POST.get("producto_id")
        variante_id = request.POST.get("variante_id") or None
        try:
            cantidad = max(1, int(request.POST.get("cantidad", "1")))
        except ValueError:
            cantidad = 1

        producto = get_object_or_404(Producto, pk=producto_id, activo=True)
        variante = None
        if producto.usa_variantes:
            variante = get_object_or_404(Variante, pk=variante_id, producto=producto)
            precio = variante.precio_efectivo
            costo = variante.costo_efectivo
        else:
            precio = producto.precio
            costo = producto.costo

        sede = request.user.sede
        stock = producto.stock_en_sede(sede) if sede else producto.stock_actual
        if variante:
            stock = variante.stock_en_sede(sede) if sede else variante.stock_actual

        carrito = _cart(request)
        key = f"{producto_id}-{variante_id or 0}"
        for item in carrito:
            if f"{item['producto_id']}-{item['variante_id'] or 0}" == key:
                if item["cantidad"] + cantidad > stock:
                    messages.error(request, f"Stock insuficiente para «{producto.nombre}».")
                    return redirect("pos:caja")
                item["cantidad"] += cantidad
                break
        else:
            if cantidad > stock:
                messages.error(request, f"Stock insuficiente para «{producto.nombre}».")
                return redirect("pos:caja")
            carrito.append({
                "producto_id": producto_id,
                "variante_id": variante.id if variante else None,
                "cantidad": cantidad,
                "precio": str(precio),
                "costo": str(costo),
            })
        _save_cart(request, carrito)
    return redirect("pos:caja")


@login_required
def caja_quitar(request):
    if request.method == "POST":
        idx = request.POST.get("idx")
        carrito = _cart(request)
        try:
            idx = int(idx)
            if 0 <= idx < len(carrito):
                carrito.pop(idx)
                _save_cart(request, carrito)
        except (ValueError, TypeError):
            pass
    return redirect("pos:caja")


@login_required
def caja_cobrar(request):
    if request.method == "POST":
        sede = request.user.sede
        turno = _turno_abierto(sede) if sede else None
        cart = _cart(request)
        lineas = _lineas_carrito(cart)
        if not lineas:
            messages.error(request, "El carrito está vacío.")
            return redirect("pos:caja")

        form = CobrarForm(request.POST)
        if form.is_valid():
            # Validar stock antes de vender.
            for l in lineas:
                sede_val = sede
                if l["variante"]:
                    disponible = l["variante"].stock_en_sede(sede_val) if sede_val else l["variante"].stock_actual
                else:
                    disponible = l["producto"].stock_en_sede(sede_val) if sede_val else l["producto"].stock_actual
                if disponible < l["cantidad"]:
                    messages.error(request, f"Stock insuficiente para «{l['producto'].nombre}».")
                    return redirect("pos:caja")

            totales = _totales(lineas)
            metodo = form.cleaned_data["metodo_pago"]
            monto_recibido = form.cleaned_data["monto_recibido"]

            with transaction.atomic():
                numero = f"V-{timezone.now().year}-{Venta.objects.count() + 1:05d}"
                venta = Venta.objects.create(
                    numero=numero,
                    sede=sede,
                    caja=turno,
                    cliente=form.cleaned_data["cliente"],
                    cajero=request.user,
                    subtotal=totales["subtotal"],
                    descuento=totales["descuento"],
                    total_impuestos=totales["impuestos"],
                    total=totales["total"],
                    metodo_pago=metodo,
                    monto_recibido=monto_recibido if metodo == Venta.MetodoPago.EFECTIVO else None,
                )
                for l in lineas:
                    detalle = DetalleVenta.objects.create(
                        venta=venta,
                        producto=l["producto"],
                        variante=l["variante"],
                        cantidad=l["cantidad"],
                        precio_unitario=l["precio"],
                        costo_unitario=l["costo"],
                    )
                    detalle.aplicar_stock(1)
            _save_cart(request, [])
            messages.success(request, f"Venta {numero} registrada.")
            return redirect("sales:venta_detalle", pk=venta.pk)

    return redirect("pos:caja")
