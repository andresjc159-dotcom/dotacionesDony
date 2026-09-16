"""Vistas de la tienda online (públicas)."""

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.inventory.models import Categoria, Producto, Variante
from apps.payments.models import Pago
from apps.payments.services import confirmar_pago
from apps.payments.wompi import crear_enlace_pago

from .forms import CheckoutForm
from .models import DetalleOrden, Orden

CART_KEY = "carrito_web"


def _cart(request):
    return request.session.get(CART_KEY, [])


def _save_cart(request, cart):
    request.session[CART_KEY] = cart
    request.session.modified = True


def _lineas(cart):
    lineas = []
    for item in cart:
        producto = Producto.objects.filter(pk=item["producto_id"], activo=True).first()
        variante = Variante.objects.filter(pk=item["variante_id"]).first() if item.get("variante_id") else None
        if producto is None:
            continue
        precio = float(item["precio"])
        lineas.append({
            "producto": producto,
            "variante": variante,
            "cantidad": item["cantidad"],
            "precio": precio,
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
        "impuestos": round(impuestos, 2),
        "total": round(subtotal, 2),
    }


def catalogo(request):
    q = request.GET.get("q", "").strip()
    cat_id = request.GET.get("categoria")
    productos = Producto.objects.filter(activo=True).select_related("categoria").prefetch_related("variantes")
    if q:
        productos = productos.filter(nombre__icontains=q) | productos.filter(sku__icontains=q)
    if cat_id:
        productos = productos.filter(categoria_id=cat_id)

    contexto = {
        "titulo": "Catálogo",
        "productos": productos,
        "q": q,
        "categorias": Categoria.objects.filter(activa=True),
        "categoria_sel": cat_id,
    }
    return render(request, "store/catalogo.html", contexto)


def producto_detalle(request, pk):
    producto = get_object_or_404(Producto.objects.prefetch_related("variantes__valores"), pk=pk, activo=True)
    contexto = {"titulo": producto.nombre, "producto": producto}
    return render(request, "store/detalle.html", contexto)


def carrito(request):
    lineas = _lineas(_cart(request))
    totales = _totales(lineas)
    contexto = {"titulo": "Carrito", "carrito": lineas, "totales": totales}
    return render(request, "store/carrito.html", contexto)


def carrito_agregar(request):
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
        else:
            precio = producto.precio

        cart = _cart(request)
        key = f"{producto_id}-{variante_id or 0}"
        for item in cart:
            if f"{item['producto_id']}-{item['variante_id'] or 0}" == key:
                item["cantidad"] += cantidad
                break
        else:
            cart.append({
                "producto_id": producto_id,
                "variante_id": variante.id if variante else None,
                "cantidad": cantidad,
                "precio": str(precio),
            })
        _save_cart(request, cart)
        messages.success(request, "Producto agregado al carrito.")
    return redirect(request.META.get("HTTP_REFERER") or "store:catalogo")


def carrito_quitar(request):
    if request.method == "POST":
        idx = request.POST.get("idx")
        cart = _cart(request)
        try:
            idx = int(idx)
            if 0 <= idx < len(cart):
                cart.pop(idx)
                _save_cart(request, cart)
        except (ValueError, TypeError):
            pass
    return redirect("store:carrito")


def checkout(request):
    lineas = _lineas(_cart(request))
    if not lineas:
        messages.info(request, "Tu carrito está vacío.")
        return redirect("store:catalogo")

    totales = _totales(lineas)
    form = CheckoutForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            numero = f"W-{timezone.now().year}-{Orden.objects.count() + 1:05d}"
            orden = Orden.objects.create(
                numero=numero,
                cliente_nombre=form.cleaned_data["cliente_nombre"],
                documento=form.cleaned_data["documento"],
                email=form.cleaned_data["email"],
                telefono=form.cleaned_data["telefono"],
                direccion=form.cleaned_data["direccion"],
                ciudad=form.cleaned_data["ciudad"],
                notas=form.cleaned_data["notas"],
                subtotal=totales["subtotal"],
                total_impuestos=totales["impuestos"],
                total=totales["total"],
            )
            for l in lineas:
                DetalleOrden.objects.create(
                    orden=orden,
                    producto=l["producto"],
                    variante=l["variante"],
                    cantidad=l["cantidad"],
                    precio_unitario=l["precio"],
                )
            pago = Pago.objects.create(
                orden=orden,
                monto=totales["total"],
                metodo=Pago.Metodo.WOMPI,
                referencia=orden.numero,
            )
            _save_cart(request, [])

        url_retorno = request.build_absolute_uri(reverse("store:orden", args=[orden.pk]))
        enlace, error = crear_enlace_pago(orden, url_retorno)
        if enlace:
            return redirect(enlace)
        pago.metodo = Pago.Metodo.SIMULADO
        pago.save(update_fields=["metodo"])
        messages.info(request, "Pasarela no configurada: usa el pago simulado para probar.")
        return redirect("store:simular_pago", pk=orden.pk)

    contexto = {"titulo": "Checkout", "carrito": lineas, "totales": totales, "form": form}
    return render(request, "store/checkout.html", contexto)


def orden(request, pk):
    orden = get_object_or_404(Orden.objects.prefetch_related("detalles__producto", "detalles__variante"), pk=pk)
    contexto = {"titulo": orden.numero, "orden": orden}
    return render(request, "store/orden.html", contexto)


def simular_pago(request, pk):
    orden = get_object_or_404(Orden, pk=pk)
    if request.method == "POST":
        pago = orden.pagos.filter(estado=Pago.Estado.PENDIENTE).first()
        if pago:
            confirmar_pago(pago)
            messages.success(request, "Pago aprobado (simulado). ¡Gracias por tu compra!")
        return redirect("store:orden", pk=orden.pk)
    contexto = {"titulo": "Pago simulado", "orden": orden}
    return render(request, "store/simular_pago.html", contexto)
