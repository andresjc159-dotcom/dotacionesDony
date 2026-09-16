"""Formularios del módulo de bodega."""

from django import forms

from apps.inventory.forms import _estilizar
from apps.inventory.models import Producto, Variante

from .models import AjusteInventario, Compra, DetalleCompra, Proveedor, TransferenciaSede


class VarianteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.sku} · {obj.descripcion_valores}"


def _variante_field(required=False):
    return VarianteChoiceField(
        queryset=Variante.objects.filter(activo=True).select_related("producto"),
        required=required,
        label="Variante",
        help_text="Solo para productos que usan variantes.",
    )


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "documento", "telefono", "email", "direccion", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ["proveedor", "sede", "fecha"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["fecha"].widget = forms.DateInput(attrs={"type": "date", "class": "input"})


class DetalleCompraForm(forms.ModelForm):
    variante = _variante_field()

    class Meta:
        model = DetalleCompra
        fields = ["producto", "variante", "cantidad", "costo_unitario"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["producto"].queryset = Producto.objects.filter(activo=True)

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        variante = cleaned.get("variante")
        if producto and producto.usa_variantes and not variante:
            self.add_error("variante", "Este producto usa variantes: selecciona una.")
        if producto and not producto.usa_variantes and variante:
            self.add_error("variante", "Este producto es genérico: deja la variante vacía.")
        return cleaned


DetalleCompraFormSet = forms.inlineformset_factory(
    Compra,
    DetalleCompra,
    form=DetalleCompraForm,
    extra=1,
    can_delete=True,
)


class AjusteForm(forms.ModelForm):
    variante = _variante_field()

    class Meta:
        model = AjusteInventario
        fields = ["sede", "producto", "variante", "tipo", "cantidad", "motivo", "fecha"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["fecha"].widget = forms.DateInput(attrs={"type": "date", "class": "input"})
        self.fields["producto"].queryset = Producto.objects.filter(activo=True)

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        variante = cleaned.get("variante")
        if producto and producto.usa_variantes and not variante:
            self.add_error("variante", "Este producto usa variantes: selecciona una.")
        if producto and not producto.usa_variantes and variante:
            self.add_error("variante", "Este producto es genérico: deja la variante vacía.")
        return cleaned


class TransferenciaForm(forms.ModelForm):
    variante = _variante_field()

    class Meta:
        model = TransferenciaSede
        fields = ["origen", "destino", "producto", "variante", "cantidad", "fecha"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["fecha"].widget = forms.DateInput(attrs={"type": "date", "class": "input"})
        self.fields["producto"].queryset = Producto.objects.filter(activo=True)

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        variante = cleaned.get("variante")
        origen = cleaned.get("origen")
        destino = cleaned.get("destino")
        if producto and producto.usa_variantes and not variante:
            self.add_error("variante", "Este producto usa variantes: selecciona una.")
        if producto and not producto.usa_variantes and variante:
            self.add_error("variante", "Este producto es genérico: deja la variante vacía.")
        if origen and destino and origen == destino:
            self.add_error("destino", "El origen y el destino deben ser sedes distintas.")
        return cleaned
