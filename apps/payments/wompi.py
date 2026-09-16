"""Cliente de la pasarela Wompi (enlaces de pago)."""

import requests
from django.conf import settings


def crear_enlace_pago(orden, url_retorno):
    """Crea un enlace de pago en Wompi y devuelve su URL.

    Devuelve (url, error). Si no hay claves configuradas, devuelve (None, None)
    para indicar que se debe usar el flujo simulado de desarrollo.
    """
    if not settings.WOMPI_PRIVATE_KEY:
        return None, None

    url = f"{settings.WOMPI_BASE_URL}/v1/payment_links"
    headers = {
        "Authorization": f"Bearer {settings.WOMPI_PRIVATE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": f"Pedido {orden.numero} · Dotaciones Dony",
        "description": "Compra de dotaciones",
        "single_use": True,
        "currency": "COP",
        "amount_in_cents": int(orden.total * 100),
        "reference": orden.numero,
        "redirect_url": url_retorno,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        data = response.json()
    except requests.RequestException as exc:
        return None, f"Error de conexión con Wompi: {exc}"

    if response.status_code in (200, 201):
        link_id = (data.get("data") or {}).get("id")
        if link_id:
            return f"https://checkout.wompi.co/l/{link_id}", None
        return None, "Wompi no devolvió un enlace válido."

    error = (data.get("error") or {}).get("type") or f"HTTP {response.status_code}"
    return None, f"Wompi rechazó la solicitud: {error}"
