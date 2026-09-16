from django.contrib import admin

from .models import Sede, User


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "telefono", "activa")
    list_filter = ("tipo", "activa")
    search_fields = ("nombre", "direccion")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "get_full_name", "rol", "sede", "is_active")
    list_filter = ("rol", "is_active", "sede")
    search_fields = ("username", "first_name", "last_name", "email")
