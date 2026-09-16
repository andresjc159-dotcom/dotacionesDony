"""Modelos de usuarios, roles y sedes de Dotaciones Dony."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Sede(models.Model):
    """Una ubicación física u online de la empresa."""

    class Tipo(models.TextChoices):
        FISICA = "FISICA", "Física"
        ONLINE = "ONLINE", "Online"

    nombre = models.CharField(max_length=120, unique=True)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.FISICA)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "sede"
        verbose_name_plural = "sedes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class User(AbstractUser):
    """Usuario del sistema con un rol específico y pertenencia a una sede."""

    class Rol(models.TextChoices):
        MASTER = "MASTER", "Master"
        ADMIN = "ADMIN", "Administrador"
        CAJA = "CAJA", "Caja"
        BODEGA = "BODEGA", "Bodega"

    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.CAJA)
    sede = models.ForeignKey(
        Sede,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
    )

    @property
    def es_master(self):
        return self.rol == self.Rol.MASTER

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"
