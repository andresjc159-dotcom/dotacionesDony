"""Formularios de la tienda online."""

from django import forms

from apps.inventory.forms import _estilizar


class CheckoutForm(forms.Form):
    cliente_nombre = forms.CharField(label="Nombre completo", max_length=180)
    documento = forms.CharField(label="Documento (cédula/NIT)", max_length=40, required=False)
    email = forms.EmailField(label="Correo electrónico")
    telefono = forms.CharField(label="Teléfono", max_length=30, required=False)
    direccion = forms.CharField(label="Dirección de entrega", max_length=255)
    ciudad = forms.CharField(label="Ciudad", max_length=80, required=False)
    notas = forms.CharField(label="Notas del pedido", widget=forms.Textarea(attrs={"rows": 2}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
