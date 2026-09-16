"""Formularios del módulo de ventas y caja."""

from django import forms

from apps.inventory.forms import _estilizar

from .models import CajaTurno, Cliente, Venta


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "documento", "email", "telefono", "direccion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)


class AperturaCajaForm(forms.ModelForm):
    class Meta:
        model = CajaTurno
        fields = ["monto_inicial"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)


class CierreCajaForm(forms.Form):
    monto_cierre = forms.DecimalField(
        max_digits=12, decimal_places=2, label="Monto final en caja", min_value=0
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)


class CobrarForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(), required=False, label="Cliente",
        empty_label="Consumidor final",
    )
    metodo_pago = forms.ChoiceField(choices=Venta.MetodoPago.choices, label="Método de pago")
    monto_recibido = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False, label="Monto recibido (efectivo)",
        help_text="Solo para pago en efectivo.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
