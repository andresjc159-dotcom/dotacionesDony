"""Modelos de despachos (envíos de órdenes de la tienda online)."""

from django.db import models
from django.utils import timezone

from apps.store.models import Orden


class Despacho(models.Model):
    """Envío asociado a una orden pagada."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ENVIADO = "ENVIADO", "Enviado"
        ENTREGADO = "ENTREGADO", "Entregado"
        CANCELADO = "CANCELADO", "Cancelado"

    orden = models.OneToOneField(Orden, on_delete=models.CASCADE, related_name="despacho")
    transportadora = models.CharField(max_length=80)
    numero_guia = models.CharField(max_length=80, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=80, blank=True)
    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha = models.DateTimeField(default=timezone.now)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "despacho"
        verbose_name_plural = "despachos"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"Despacho {self.orden.numero} · {self.get_estado_display()}"

    def sincronizar_orden(self):
        """Mantiene el estado de la orden coherente con el del despacho."""
        if self.estado == self.Estado.ENVIADO:
            self.orden.estado = Orden.Estado.DESPACHADA
        elif self.estado == self.Estado.ENTREGADO:
            self.orden.estado = Orden.Estado.ENTREGADA
        else:
            self.orden.estado = Orden.Estado.EN_DESPACHO
        self.orden.save(update_fields=["estado"])
