"""Formularios de despachos."""

from django import forms

from apps.inventory.forms import _estilizar
from apps.store.models import Orden

from .models import Despacho


class DespachoCreateForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = ["orden", "transportadora", "numero_guia", "notas"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["orden"].queryset = Orden.objects.filter(
            estado__in=[Orden.Estado.PAGADA, Orden.Estado.EN_DESPACHO]
        ).exclude(despacho__isnull=False)
        self.fields["orden"].label_from_instance = lambda o: f"{o.numero} · {o.cliente_nombre}"


class DespachoEditForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = ["transportadora", "numero_guia", "estado", "notas"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
