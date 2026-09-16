"""Modelos de pagos de la pasarela (Wompi)."""

from django.db import models

from apps.store.models import Orden


class Pago(models.Model):
    """Intento de pago asociado a una orden."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        ERROR = "ERROR", "Error"

    class Metodo(models.TextChoices):
        WOMPI = "WOMPI", "Wompi"
        SIMULADO = "SIMULADO", "Simulado (desarrollo)"

    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="pagos")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=12, choices=Metodo.choices, default=Metodo.WOMPI)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    referencia = models.CharField(max_length=80, blank=True, help_text="Referencia de la pasarela.")
    wompi_id = models.CharField(max_length=80, blank=True)
    wompi_estado = models.CharField(max_length=40, blank=True, help_text="Estado crudo de Wompi.")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.orden.numero} · {self.estado}"
