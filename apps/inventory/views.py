"""Vistas del módulo de inventario."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AtributoForm,
    CategoriaForm,
    ImpuestoForm,
    ProductoForm,
    ValorAtributoFormSet,
    VarianteFormSet,
)
from .models import Atributo, Categoria, Impuesto, Producto


@login_required
def lista_productos(request):
    """Catálogo de productos con stock y alertas de mín/máx."""
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.select_related("categoria", "impuesto").prefetch_related("variantes")
    if q:
        productos = productos.filter(nombre__icontains=q) | productos.filter(sku__icontains=q)

    contexto = {
        "titulo": "Inventario",
        "productos": productos,
        "q": q,
    }
    return render(request, "inventory/lista.html", contexto)


@login_required
def ubicaciones(request):
    """Mapa de ubicaciones: estantería, módulo y nivel por producto/variante."""
    q = request.GET.get("q", "").strip().lower()
    solo_faltantes = request.GET.get("faltantes") == "1"

    items = []
    productos = Producto.objects.filter(activo=True).select_related("categoria").prefetch_related("variantes__valores")
    for p in productos:
        if p.usa_variantes:
            for v in p.variantes.all():
                items.append({
                    "sku": v.sku,
                    "nombre": p.nombre,
                    "detalle": v.descripcion_valores,
                    "categoria": p.categoria.nombre if p.categoria else "",
                    "ubicacion": v.ubicacion_efectiva,
                    "stock": v.stock_actual,
                    "producto_id": p.pk,
                })
        else:
            items.append({
                "sku": p.sku,
                "nombre": p.nombre,
                "detalle": "",
                "categoria": p.categoria.nombre if p.categoria else "",
                "ubicacion": p.ubicacion,
                "stock": p.stock_actual,
                "producto_id": p.pk,
            })

    if q:
        items = [i for i in items if q in i["nombre"].lower() or q in i["sku"].lower() or q in i["ubicacion"].lower()]
    if solo_faltantes:
        items = [i for i in items if not i["ubicacion"]]

    items.sort(key=lambda i: (i["ubicacion"] == "", i["ubicacion"].lower(), i["nombre"].lower()))

    contexto = {
        "titulo": "Ubicaciones",
        "items": items,
        "q": request.GET.get("q", ""),
        "solo_faltantes": solo_faltantes,
    }
    return render(request, "inventory/ubicaciones.html", contexto)


@login_required
def producto_nuevo(request):
    """Alta de un nuevo producto (con variantes si aplica)."""
    form = ProductoForm(request.POST or None, request.FILES or None)
    formset = VarianteFormSet(request.POST or None, instance=Producto())

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            producto = form.save()
            formset.instance = producto
            variantes = formset.save(commit=False)
            for variante in variantes:
                variante.producto = producto
                variante.save()
                formset.save_m2m()
            if not producto.usa_variantes:
                for variante in variantes:
                    variante.delete()
            messages.success(request, f"Producto «{producto.nombre}» creado correctamente.")
            return redirect("inventory:productos")

    contexto = {
        "titulo": "Nuevo producto",
        "form": form,
        "formset": formset,
        "es_nuevo": True,
    }
    return render(request, "inventory/form.html", contexto)


@login_required
def producto_editar(request, pk):
    """Edición de un producto y sus variantes."""
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    formset = VarianteFormSet(request.POST or None, request.FILES or None, instance=producto)

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            producto = form.save()
            variantes = formset.save()
            messages.success(request, f"Producto «{producto.nombre}» actualizado.")
            return redirect("inventory:productos")

    contexto = {
        "titulo": f"Editar · {producto.nombre}",
        "form": form,
        "formset": formset,
        "es_nuevo": False,
        "producto": producto,
    }
    return render(request, "inventory/form.html", contexto)


@login_required
def producto_eliminar(request, pk):
    """Desactivación/eliminación de un producto."""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"Producto «{nombre}» eliminado.")
        return redirect("inventory:productos")
    contexto = {"titulo": "Eliminar producto", "producto": producto}
    return render(request, "inventory/eliminar.html", contexto)


# ---------------------------------------------------------------------------
# Parámetros (catálogo): categorías, impuestos y atributos
# ---------------------------------------------------------------------------

@login_required
def parametros(request):
    """Página única de parámetros con las tres tablas de configuración."""
    contexto = {
        "titulo": "Parámetros",
        "categorias": Categoria.objects.all(),
        "impuestos": Impuesto.objects.all(),
        "atributos": Atributo.objects.prefetch_related("valores").all(),
    }
    return render(request, "inventory/parametros.html", contexto)


@login_required
def categoria_form(request, pk=None):
    instancia = get_object_or_404(Categoria, pk=pk) if pk else None
    form = CategoriaForm(request.POST or None, instance=instancia)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"Categoría «{obj.nombre}» guardada.")
        return redirect("inventory:parametros")
    contexto = {"titulo": "Nueva categoría" if not instancia else "Editar categoría", "form": form, "cancelar": "inventory:parametros"}
    return render(request, "inventory/config_form.html", contexto)


@login_required
def categoria_eliminar(request, pk):
    obj = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        nombre = obj.nombre
        obj.delete()
        messages.success(request, f"Categoría «{nombre}» eliminada.")
        return redirect("inventory:parametros")
    contexto = {"titulo": "Eliminar categoría", "objeto": obj, "cancelar": "inventory:parametros"}
    return render(request, "inventory/config_eliminar.html", contexto)


@login_required
def impuesto_form(request, pk=None):
    instancia = get_object_or_404(Impuesto, pk=pk) if pk else None
    form = ImpuestoForm(request.POST or None, instance=instancia)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"Impuesto «{obj.nombre}» guardado.")
        return redirect("inventory:parametros")
    contexto = {"titulo": "Nuevo impuesto" if not instancia else "Editar impuesto", "form": form, "cancelar": "inventory:parametros"}
    return render(request, "inventory/config_form.html", contexto)


@login_required
def impuesto_eliminar(request, pk):
    obj = get_object_or_404(Impuesto, pk=pk)
    if request.method == "POST":
        nombre = obj.nombre
        obj.delete()
        messages.success(request, f"Impuesto «{nombre}» eliminado.")
        return redirect("inventory:parametros")
    contexto = {"titulo": "Eliminar impuesto", "objeto": obj, "cancelar": "inventory:parametros"}
    return render(request, "inventory/config_eliminar.html", contexto)


@login_required
def atributo_form(request, pk=None):
    instancia = get_object_or_404(Atributo, pk=pk) if pk else None
    form = AtributoForm(request.POST or None, instance=instancia)
    formset = ValorAtributoFormSet(request.POST or None, instance=instancia)
    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            obj = form.save()
            formset.instance = obj
            formset.save()
            messages.success(request, f"Atributo «{obj.nombre}» guardado.")
            return redirect("inventory:parametros")
    contexto = {
        "titulo": "Nuevo atributo" if not instancia else "Editar atributo",
        "form": form,
        "formset": formset,
        "con_valores": True,
        "cancelar": "inventory:parametros",
    }
    return render(request, "inventory/config_form.html", contexto)


@login_required
def atributo_eliminar(request, pk):
    obj = get_object_or_404(Atributo, pk=pk)
    if request.method == "POST":
        nombre = obj.nombre
        obj.delete()
        messages.success(request, f"Atributo «{nombre}» eliminado.")
        return redirect("inventory:parametros")
    contexto = {"titulo": "Eliminar atributo", "objeto": obj, "cancelar": "inventory:parametros"}
    return render(request, "inventory/config_eliminar.html", contexto)
