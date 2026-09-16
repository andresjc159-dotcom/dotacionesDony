"""Modelos de inventario: categorías, impuestos, atributos, productos, variantes y stock por sede."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.users.models import Sede


class Categoria(models.Model):
    """Categoría de productos, parametrizable y jerárquica."""

    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    padre = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="hijas",
    )
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Impuesto(models.Model):
    """Impuesto (IVA) parametrizable. Puede haber varios y marcar uno por defecto."""

    nombre = models.CharField(max_length=60)
    tarifa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Tarifa en porcentaje. Ej: 19.00 para IVA 19%.",
    )
    es_por_defecto = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "impuesto"
        verbose_name_plural = "impuestos"
        ordering = ["tarifa"]

    def __str__(self):
        return f"{self.nombre} ({self.tarifa}%)"


class Atributo(models.Model):
    """Tipo de característica especial de un producto (Talla, Color, Tipo de tela)."""

    nombre = models.CharField(max_length=60, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "atributo"
        verbose_name_plural = "atributos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ValorAtributo(models.Model):
    """Valor concreto de un atributo (S, M, L / Rojo, Azul / Algodón)."""

    atributo = models.ForeignKey(Atributo, on_delete=models.CASCADE, related_name="valores")
    valor = models.CharField(max_length=60)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "valor de atributo"
        verbose_name_plural = "valores de atributo"
        ordering = ["atributo", "orden", "valor"]
        unique_together = ("atributo", "valor")

    def __str__(self):
        return f"{self.atributo}: {self.valor}"


class Producto(models.Model):
    """Producto base. Si usa_variantes, el stock y precio se manejan por variante."""

    sku = models.CharField(max_length=60, unique=True)
    codigo_barras = models.CharField(max_length=60, blank=True)
    nombre = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos", null=True, blank=True
    )
    impuesto = models.ForeignKey(
        Impuesto,
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=True,
        help_text="Impuesto aplicable. Dejar vacío si el producto es exento.",
    )
    usa_variantes = models.BooleanField(
        default=False,
        help_text="Marcar si el producto tiene características especiales (talla, color, tela).",
    )
    atributos = models.ManyToManyField(Atributo, related_name="productos", blank=True)

    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_min = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_max = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    unidad = models.CharField(max_length=20, default="UND")

    estanteria = models.CharField(max_length=40, blank=True, verbose_name="Estantería")
    modulo = models.CharField(max_length=40, blank=True, verbose_name="Módulo")
    nivel = models.CharField(max_length=40, blank=True, verbose_name="Nivel")

    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.sku} - {self.nombre}"

    @property
    def stock_actual(self):
        """Stock total: suma de variantes si es variable, o del producto (todas las sedes)."""
        if self.usa_variantes:
            return self.variantes.aggregate(total=models.Sum("stock_sedes__cantidad"))["total"] or 0
        return self.stock_sedes.aggregate(total=models.Sum("cantidad"))["total"] or 0

    @property
    def ubicacion(self):
        partes = [p for p in (self.estanteria, self.modulo, self.nivel) if p]
        return " · ".join(partes) if partes else ""

    def stock_en_sede(self, sede):
        """Stock disponible en una sede específica."""
        if self.usa_variantes:
            return self.variantes.filter(stock_sedes__sede=sede).aggregate(
                total=models.Sum("stock_sedes__cantidad")
            )["total"] or 0
        obj = self.stock_sedes.filter(sede=sede).first()
        return obj.cantidad if obj else 0


class Variante(models.Model):
    """Combinación de valores de atributo para un producto variable (ropa)."""

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="variantes")
    sku = models.CharField(max_length=60, unique=True)
    codigo_barras = models.CharField(max_length=60, blank=True)
    valores = models.ManyToManyField(ValorAtributo, related_name="variantes")

    precio = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Precio propio; si se deja vacío se usa el del producto.",
    )
    costo = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Costo propio; si se deja vacío se usa el del producto.",
    )
    estanteria = models.CharField(max_length=40, blank=True, verbose_name="Estantería")
    modulo = models.CharField(max_length=40, blank=True, verbose_name="Módulo")
    nivel = models.CharField(max_length=40, blank=True, verbose_name="Nivel")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "variante"
        verbose_name_plural = "variantes"
        ordering = ["producto", "sku"]

    def __str__(self):
        return self.sku

    @property
    def precio_efectivo(self):
        return self.precio if self.precio is not None else self.producto.precio

    @property
    def costo_efectivo(self):
        return self.costo if self.costo is not None else self.producto.costo

    @property
    def descripcion_valores(self):
        return " / ".join(v.valor for v in self.valores.all())

    @property
    def ubicacion(self):
        partes = [p for p in (self.estanteria, self.modulo, self.nivel) if p]
        return " · ".join(partes) if partes else ""

    @property
    def ubicacion_efectiva(self):
        return self.ubicacion or self.producto.ubicacion

    @property
    def stock_actual(self):
        return self.stock_sedes.aggregate(total=models.Sum("cantidad"))["total"] or 0

    def stock_en_sede(self, sede):
        obj = self.stock_sedes.filter(sede=sede).first()
        return obj.cantidad if obj else 0


class StockSede(models.Model):
    """Cantidad disponible de un producto (o variante) en una sede."""

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="stocks")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="stock_sedes")
    variante = models.ForeignKey(
        Variante, on_delete=models.CASCADE, null=True, blank=True, related_name="stock_sedes"
    )
    cantidad = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = "stock por sede"
        verbose_name_plural = "stocks por sede"
        unique_together = ("sede", "producto", "variante")
        ordering = ["producto__nombre"]

    def __str__(self):
        ref = self.variante.sku if self.variante else self.producto.sku
        return f"{self.sede} · {ref} · {self.cantidad}"

    @classmethod
    def ajustar(cls, sede, producto, variante=None, delta=0):
        """Suma (o resta) `delta` al stock de la sede. Crea el registro si no existe."""
        if delta == 0:
            return None
        obj, _ = cls.objects.get_or_create(
            sede=sede, producto=producto, variante=variante, defaults={"cantidad": max(delta, 0)}
        )
        if _:
            return obj
        obj.cantidad = models.F("cantidad") + delta
        obj.save(update_fields=["cantidad"])
        obj.refresh_from_db()
        return obj
