"""Vistas de la pasarela: webhook de Wompi."""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Pago
from .services import confirmar_pago


@csrf_exempt
def webhook(request):
    """Recibe notificaciones de Wompi y actualiza el estado de los pagos."""
    if request.method != "POST":
        return JsonResponse({"status": "method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"status": "invalid json"}, status=400)

    event = data.get("event")
    if event == "transaction.updated":
        txn = data.get("data", {}).get("transaction", {})
        referencia = txn.get("reference")
        estado = txn.get("status")
        pago = Pago.objects.filter(referencia=referencia).first()
        if pago:
            pago.wompi_estado = estado or ""
            pago.wompi_id = txn.get("id", "")
            pago.save(update_fields=["wompi_estado", "wompi_id"])
            if estado == "APPROVED":
                confirmar_pago(pago)

    return JsonResponse({"status": "ok"})
