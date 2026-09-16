"""Vistas de usuarios: login, logout, inicio y panel."""

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import redirect, render


def inicio(request):
    """Página de aterrizaje. Redirige al panel si ya hay sesión activa."""
    if request.user.is_authenticated:
        return redirect("users:dashboard")
    return render(request, "landing.html")


class LoginView(BaseLoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect("users:login")


@login_required
def dashboard(request):
    """Panel principal según el rol del usuario."""
    from apps.inventory.models import Categoria, Producto
    from apps.users.models import Sede

    productos = Producto.objects.all()
    stock_bajo = [p for p in productos if p.stock_actual <= p.stock_min]

    contexto = {
        "titulo": "Panel de control",
        "usuario": request.user,
        "total_productos": productos.count(),
        "stock_bajo": stock_bajo,
        "total_categorias": Categoria.objects.count(),
        "total_sedes": Sede.objects.count(),
    }
    return render(request, "dashboard.html", contexto)
