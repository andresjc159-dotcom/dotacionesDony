"""Servicios de pagos: confirmación de pagos e integración con ventas."""

from django.db import transaction
from django.utils import timezone

from apps.sales.models import Cliente, DetalleVenta, Venta
from apps.store.models import Orden
from apps.users.models import Sede

from .models import Pago


def sede_online():
    return Sede.objects.filter(tipo=Sede.Tipo.ONLINE).first() or Sede.objects.filter(activa=True).first()


def _mapear_metodo(pago):
    """Convierte el método de Wompi a los métodos internos de venta."""
    estado = (pago.wompi_estado or "").upper()
    if pago.metodo == Pago.Metodo.SIMULADO:
        return Venta.MetodoPago.OTRO
    if "NEQUI" in estado:
        return Venta.MetodoPago.NEQUI
    if "PSE" in estado:
        return Venta.MetodoPago.TRANSFERENCIA
    if "CARD" in estado:
        return Venta.MetodoPago.TARJETA
    return Venta.MetodoPago.OTRO


def confirmar_pago(pago):
    """Marca el pago y la orden como pagados, descuenta stock y crea la venta."""
    if pago.estado == Pago.Estado.APROBADO:
        return

    with transaction.atomic():
        pago.estado = Pago.Estado.APROBADO
        pago.save(update_fields=["estado"])

        orden = pago.orden
        if orden.estado == Orden.Estado.PAGADA:
            return

        sede = sede_online()
        if sede is None:
            return

        for detalle in orden.detalles.all():
            detalle.aplicar_stock(sede, 1)

        orden.estado = Orden.Estado.PAGADA
        orden.save(update_fields=["estado"])

        cliente, _ = Cliente.objects.get_or_create(
            documento=orden.documento or f"WEB-{orden.numero}",
            defaults={
                "nombre": orden.cliente_nombre,
                "email": orden.email,
                "telefono": orden.telefono,
                "direccion": orden.direccion,
            },
        )

        numero = f"V-{timezone.now().year}-{Venta.objects.count() + 1:05d}"
        venta = Venta.objects.create(
            numero=numero,
            sede=sede,
            cliente=cliente,
            cajero=None,
            subtotal=orden.subtotal,
            total_impuestos=orden.total_impuestos,
            total=orden.total,
            estado=Venta.Estado.PAGADA,
            metodo_pago=_mapear_metodo(pago),
        )

        for detalle in orden.detalles.all():
            costo = detalle.variante.costo_efectivo if detalle.variante else detalle.producto.costo
            DetalleVenta.objects.create(
                venta=venta,
                producto=detalle.producto,
                variante=detalle.variante,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
                costo_unitario=costo,
            )

    from apps.dispatch.services import notificar_orden_pagada

    notificar_orden_pagada(orden)
