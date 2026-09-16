"""Servicios de notificaciones por correo."""

from django.conf import settings
from django.core.mail import send_mail


def notificar_orden_pagada(orden):
    asunto = f"Dotaciones Dony · Pedido {orden.numero} confirmado"
    cuerpo = (
        f"Hola {orden.cliente_nombre},\n\n"
        f"Recibimos tu pedido {orden.numero} por un total de ${orden.total}.\n"
        "Tu pago fue aprobado y pronto lo prepararemos para el despacho.\n\n"
        "¡Gracias por comprar en Dotaciones Dony!"
    )
    _enviar(orden.email, asunto, cuerpo)


def notificar_despacho_enviado(despacho):
    orden = despacho.orden
    asunto = f"Dotaciones Dony · Tu pedido {orden.numero} fue enviado"
    cuerpo = (
        f"Hola {orden.cliente_nombre},\n\n"
        f"Tu pedido {orden.numero} fue enviado por {despacho.transportadora}.\n"
        f"Número de guía: {despacho.numero_guia or 'por confirmar'}.\n\n"
        "¡Gracias por tu compra!"
    )
    _enviar(orden.email, asunto, cuerpo)


def _enviar(destinatario, asunto, cuerpo):
    remitente = settings.DEFAULT_FROM_EMAIL
    try:
        send_mail(asunto, cuerpo, remitente, [destinatario], fail_silently=True)
    except Exception:
        pass
