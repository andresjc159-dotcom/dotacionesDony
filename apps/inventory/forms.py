"""Formularios del módulo de inventario."""

from django import forms

from .models import Atributo, Categoria, Impuesto, Producto, ValorAtributo, Variante

INPUT_CLASS = "input"
CHECK_CLASS = "switch"


def _estilizar(form):
    """Aplica las clases CSS del tema futurista a los widgets del formulario."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", CHECK_CLASS)
        elif isinstance(widget, forms.Textarea):
            widget.attrs.setdefault("class", "textarea")
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs.setdefault("class", INPUT_CLASS)
        elif isinstance(widget, forms.CheckboxSelectMultiple):
            widget.attrs.setdefault("class", "checkbox-grid")
        else:
            widget.attrs.setdefault("class", INPUT_CLASS)


class ProductoForm(forms.ModelForm):
    """Alta y edición de productos."""

    class Meta:
        model = Producto
        fields = [
            "sku",
            "codigo_barras",
            "nombre",
            "descripcion",
            "categoria",
            "impuesto",
            "usa_variantes",
            "atributos",
            "precio",
            "costo",
            "stock_min",
            "stock_max",
            "unidad",
            "estanteria",
            "modulo",
            "nivel",
            "imagen",
            "activo",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "atributos": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        if not self.instance.pk and "impuesto" in self.fields:
            default = Impuesto.objects.filter(es_por_defecto=True, activo=True).first()
            if default:
                self.fields["impuesto"].initial = default.pk
        for name in ("sku", "codigo_barras", "nombre", "precio", "costo", "unidad"):
            self.fields[name].widget.attrs.setdefault("autocomplete", "off")

    def clean(self):
        cleaned = super().clean()
        usa_variantes = cleaned.get("usa_variantes")
        if usa_variantes and not cleaned.get("atributos"):
            self.add_error("atributos", "Selecciona al menos un atributo para un producto con variantes.")
        return cleaned


class VarianteForm(forms.ModelForm):
    """Formulario para una variante dentro del formset."""

    class Meta:
        model = Variante
        fields = ["sku", "codigo_barras", "valores", "precio", "costo", "estanteria", "modulo", "nivel", "activo"]
        widgets = {
            "valores": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["precio"].widget.attrs["placeholder"] = "Opcional (usa el del producto)"
        self.fields["costo"].widget.attrs["placeholder"] = "Opcional (usa el del producto)"


VarianteFormSet = forms.inlineformset_factory(
    Producto,
    Variante,
    form=VarianteForm,
    extra=1,
    can_delete=True,
)


class CategoriaForm(forms.ModelForm):
    """Alta y edición de categorías."""

    class Meta:
        model = Categoria
        fields = ["nombre", "slug", "padre", "activa"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["slug"].required = False
        self.fields["slug"].help_text = "Se genera automáticamente si se deja vacío."
        self.fields["padre"].queryset = Categoria.objects.exclude(pk=self.instance.pk)


class ImpuestoForm(forms.ModelForm):
    """Alta y edición de impuestos."""

    class Meta:
        model = Impuesto
        fields = ["nombre", "tarifa", "es_por_defecto", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("es_por_defecto"):
            Impuesto.objects.filter(es_por_defecto=True).exclude(pk=self.instance.pk).update(es_por_defecto=False)
        return cleaned


class AtributoForm(forms.ModelForm):
    """Alta y edición de atributos (tipo de característica)."""

    class Meta:
        model = Atributo
        fields = ["nombre", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)


class ValorAtributoForm(forms.ModelForm):
    """Valor de un atributo dentro del formset."""

    class Meta:
        model = ValorAtributo
        fields = ["valor", "orden"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)


ValorAtributoFormSet = forms.inlineformset_factory(
    Atributo,
    ValorAtributo,
    form=ValorAtributoForm,
    extra=1,
    can_delete=True,
)
