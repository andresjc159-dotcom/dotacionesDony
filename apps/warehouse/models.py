"""Modelos de bodega: proveedores, compras, ajustes y transferencias entre sedes."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.inventory.models import Producto, StockSede, Variante
from apps.users.models import Sede


class Proveedor(models.Model):
    """Proveedor de mercancía."""

    nombre = models.CharField(max_length=180, unique=True)
    documento = models.CharField(max_length=40, blank=True, help_text="NIT o cédula")
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    """Orden de compra / entrada de mercancía a bodega."""

    numero = models.CharField(max_length=40, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="compras")
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="compras")
    fecha = models.DateField(default=timezone.now)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="compras"
    )
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "compra"
        verbose_name_plural = "compras"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return self.numero


class DetalleCompra(models.Model):
    """Línea de una compra: producto (o variante) y cantidad recibida."""

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_compra")
    variante = models.ForeignKey(
        Variante, on_delete=models.PROTECT, null=True, blank=True, related_name="detalles_compra"
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "detalle de compra"
        verbose_name_plural = "detalles de compra"

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.costo_unitario

    def aplicar_stock(self, factor=1):
        """Aplica (+1 entrada / -1 reversa) la cantidad al stock de la sede de la compra."""
        StockSede.ajustar(self.compra.sede, self.producto, self.variante, factor * self.cantidad)


class AjusteInventario(models.Model):
    """Entrada o salida manual de inventario (mermas, conteos, daños, etc.)."""

    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"

    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="ajustes")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="ajustes")
    variante = models.ForeignKey(
        Variante, on_delete=models.PROTECT, null=True, blank=True, related_name="ajustes"
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.ENTRADA)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    motivo = models.CharField(max_length=255, blank=True)
    fecha = models.DateField(default=timezone.now)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ajustes"
    )

    class Meta:
        verbose_name = "ajuste de inventario"
        verbose_name_plural = "ajustes de inventario"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.producto} x{self.cantidad}"

    def aplicar_stock(self, factor=1):
        """Aplica el ajuste al stock de la sede (entrada suma, salida resta)."""
        signo = 1 if self.tipo == self.Tipo.ENTRADA else -1
        StockSede.ajustar(self.sede, self.producto, self.variante, factor * signo * self.cantidad)


class TransferenciaSede(models.Model):
    """Movimiento de inventario entre dos sedes."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADA = "COMPLETADA", "Completada"

    origen = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="transferencias_salida")
    destino = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="transferencias_entrada")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="transferencias")
    variante = models.ForeignKey(
        Variante, on_delete=models.PROTECT, null=True, blank=True, related_name="transferencias"
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha = models.DateField(default=timezone.now)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transferencias"
    )

    class Meta:
        verbose_name = "transferencia"
        verbose_name_plural = "transferencias"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.origen} → {self.destino} · {self.producto} x{self.cantidad}"

    def aplicar_stock(self, factor=1):
        """Resta del origen y suma al destino (factor -1 revierte)."""
        StockSede.ajustar(self.origen, self.producto, self.variante, -factor * self.cantidad)
        StockSede.ajustar(self.destino, self.producto, self.variante, factor * self.cantidad)
