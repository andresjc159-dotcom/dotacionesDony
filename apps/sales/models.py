"""Modelos de ventas y caja: clientes, turnos de caja, ventas y detalles."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.inventory.models import Producto, StockSede, Variante
from apps.users.models import Sede


class Cliente(models.Model):
    """Cliente para ventas y despachos."""

    nombre = models.CharField(max_length=180)
    documento = models.CharField(max_length=40, blank=True, help_text="Cédula o NIT")
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class CajaTurno(models.Model):
    """Apertura y cierre de caja por sede y usuario."""

    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta"
        CERRADA = "CERRADA", "Cerrada"

    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="turnos")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="turnos"
    )
    fecha_apertura = models.DateTimeField(default=timezone.now)
    monto_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_cierre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTA)

    class Meta:
        verbose_name = "turno de caja"
        verbose_name_plural = "turnos de caja"
        ordering = ["-fecha_apertura"]

    def __str__(self):
        return f"{self.sede} · {self.fecha_apertura:%d/%m/%Y %H:%M} · {self.estado}"

    @property
    def total_ventas(self):
        return self.ventas.filter(estado=Venta.Estado.PAGADA).aggregate(t=models.Sum("total"))["t"] or 0

    @property
    def total_efectivo(self):
        return self.ventas.filter(estado=Venta.Estado.PAGADA, metodo_pago=Venta.MetodoPago.EFECTIVO).aggregate(
            t=models.Sum("total")
        )["t"] or 0


class Venta(models.Model):
    """Venta registrada en caja (control de ingresos)."""

    class Estado(models.TextChoices):
        PAGADA = "PAGADA", "Pagada"
        CREDITO = "CREDITO", "Crédito"
        ANULADA = "ANULADA", "Anulada"

    class MetodoPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        NEQUI = "NEQUI", "Nequi"
        OTRO = "OTRO", "Otro"

    numero = models.CharField(max_length=40, unique=True)
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="ventas")
    caja = models.ForeignKey(
        CajaTurno, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas"
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True, related_name="ventas")
    cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="ventas"
    )
    fecha = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PAGADA)
    metodo_pago = models.CharField(max_length=14, choices=MetodoPago.choices, default=MetodoPago.EFECTIVO)
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "venta"
        verbose_name_plural = "ventas"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return self.numero

    @property
    def cambio(self):
        if self.monto_recibido and self.metodo_pago == self.MetodoPago.EFECTIVO:
            return self.monto_recibido - self.total
        return 0

    def anular(self):
        """Anula la venta y revierte el stock."""
        if self.estado == self.Estado.ANULADA:
            return
        for detalle in self.detalles.all():
            detalle.aplicar_stock(-1)
        self.estado = self.Estado.ANULADA
        self.save(update_fields=["estado"])


class DetalleVenta(models.Model):
    """Línea de una venta."""

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_venta")
    variante = models.ForeignKey(
        Variante, on_delete=models.PROTECT, null=True, blank=True, related_name="detalles_venta"
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "detalle de venta"
        verbose_name_plural = "detalles de venta"

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    @property
    def utilidad(self):
        return (self.precio_unitario - self.costo_unitario) * self.cantidad

    def aplicar_stock(self, factor=1):
        """Descarga stock de la sede de la venta (factor -1 revierte/restaura)."""
        StockSede.ajustar(self.venta.sede, self.producto, self.variante, -factor * self.cantidad)
