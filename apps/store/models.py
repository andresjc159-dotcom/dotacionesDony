"""Modelos de la tienda online: órdenes y detalles."""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.inventory.models import Producto, StockSede, Variante


class Orden(models.Model):
    """Pedido realizado desde la tienda online."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADA = "PAGADA", "Pagada"
        EN_DESPACHO = "EN_DESPACHO", "En despacho"
        DESPACHADA = "DESPACHADA", "Despachada"
        ENTREGADA = "ENTREGADA", "Entregada"
        CANCELADA = "CANCELADA", "Cancelada"

    numero = models.CharField(max_length=40, unique=True)
    cliente_nombre = models.CharField(max_length=180)
    documento = models.CharField(max_length=40, blank=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=80, blank=True)
    notas = models.TextField(blank=True)

    fecha = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)

    class Meta:
        verbose_name = "orden"
        verbose_name_plural = "órdenes"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return self.numero


class DetalleOrden(models.Model):
    """Línea de una orden online."""

    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_orden")
    variante = models.ForeignKey(
        Variante, on_delete=models.PROTECT, null=True, blank=True, related_name="detalles_orden"
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "detalle de orden"
        verbose_name_plural = "detalles de orden"

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def aplicar_stock(self, sede, factor=1):
        """Descuenta stock de la sede indicada (factor -1 restaura)."""
        StockSede.ajustar(sede, self.producto, self.variante, -factor * self.cantidad)
