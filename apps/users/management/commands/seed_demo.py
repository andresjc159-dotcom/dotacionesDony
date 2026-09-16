"""Comando para poblar la base de datos con datos iniciales de demo.

Uso: python manage.py seed_demo
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import Atributo, Categoria, Impuesto, Producto, StockSede, ValorAtributo, Variante
from apps.users.models import Sede

User = get_user_model()


class Command(BaseCommand):
    help = "Crea datos iniciales: sedes, roles, catálogo y usuario master."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Creando datos demo..."))

        # --- Sedes -----------------------------------------------------------
        sede_principal, _ = Sede.objects.get_or_create(
            nombre="Sede Principal",
            defaults={"tipo": Sede.Tipo.FISICA, "direccion": "Carrera 10 # 20-30, Bogotá", "telefono": "601 000 0000"},
        )
        sede_online, _ = Sede.objects.get_or_create(
            nombre="Tienda Online",
            defaults={"tipo": Sede.Tipo.ONLINE, "direccion": "www.dotacionesdony.co"},
        )

        # --- Usuario master --------------------------------------------------
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@dotacionesdony.co",
                password="admin123",
                first_name="Master",
                last_name="Dony",
                rol=User.Rol.MASTER,
                sede=None,
            )
            self.stdout.write(self.style.SUCCESS("  ✔ Usuario master: admin / admin123"))

        # --- Impuesto por defecto (IVA 19%) ----------------------------------
        Impuesto.objects.get_or_create(
            nombre="IVA 19%",
            defaults={"tarifa": 19.00, "es_por_defecto": True},
        )
        Impuesto.objects.get_or_create(
            nombre="Exento",
            defaults={"tarifa": 0.00},
        )

        # --- Categorías ------------------------------------------------------
        cat_camisas, _ = Categoria.objects.get_or_create(nombre="Camisas")
        cat_pantalones, _ = Categoria.objects.get_or_create(nombre="Pantalones")
        cat_overoles, _ = Categoria.objects.get_or_create(nombre="Overoles")
        cat_accesorios, _ = Categoria.objects.get_or_create(nombre="Accesorios")

        # --- Atributos y valores --------------------------------------------
        attr_talla, _ = Atributo.objects.get_or_create(nombre="Talla")
        attr_color, _ = Atributo.objects.get_or_create(nombre="Color")
        attr_tela, _ = Atributo.objects.get_or_create(nombre="Tipo de tela")

        tallas = ["S", "M", "L", "XL"]
        colores = ["Azul", "Gris", "Negro"]
        telas = ["Algodón", "Poliéster"]

        valores_talla = [ValorAtributo.objects.get_or_create(atributo=attr_talla, valor=t, defaults={"orden": i})[0] for i, t in enumerate(tallas)]
        valores_color = [ValorAtributo.objects.get_or_create(atributo=attr_color, valor=c, defaults={"orden": i})[0] for i, c in enumerate(colores)]
        valores_tela = [ValorAtributo.objects.get_or_create(atributo=attr_tela, valor=t, defaults={"orden": i})[0] for i, t in enumerate(telas)]

        iva = Impuesto.objects.get(nombre="IVA 19%")

        # --- Productos con variantes (ropa) ----------------------------------
        camisa, created = Producto.objects.get_or_create(
            sku="CAM-001",
            defaults={
                "nombre": "Camisa de trabajo industrial",
                "categoria": cat_camisas,
                "impuesto": iva,
                "usa_variantes": True,
                "precio": 55000,
                "costo": 30000,
                "stock_min": 10,
                "stock_max": 60,
            },
        )
        camisa.atributos.set([attr_talla, attr_color, attr_tela])

        if created:
            idx = 1
            for talla in valores_talla:
                for color in valores_color:
                    variante = Variante.objects.create(
                        producto=camisa,
                        sku=f"CAM-001-{talla.valor}-{color.valor}",
                    )
                    variante.valores.set([talla, color, valores_tela[0]])
                    StockSede.ajustar(sede_principal, camisa, variante, 20 + idx)
                    idx += 1

        # --- Producto genérico ----------------------------------------------
        gorra, _ = Producto.objects.get_or_create(
            sku="GOR-001",
            defaults={
                "nombre": "Gorra tipo dotación",
                "categoria": cat_accesorios,
                "impuesto": iva,
                "usa_variantes": False,
                "precio": 18000,
                "costo": 9000,
                "stock_min": 15,
                "stock_max": 150,
            },
        )
        StockSede.ajustar(sede_principal, gorra, None, 120)

        overol, _ = Producto.objects.get_or_create(
            sku="OVE-001",
            defaults={
                "nombre": "Overol dos piezas",
                "categoria": cat_overoles,
                "impuesto": iva,
                "usa_variantes": True,
                "precio": 95000,
                "costo": 55000,
                "stock_min": 5,
                "stock_max": 40,
            },
        )

        # --- Ubicaciones de ejemplo ------------------------------------------
        gorra.estanteria, gorra.modulo, gorra.nivel = "Estantería 1", "Módulo 2", "Nivel A"
        gorra.save(update_fields=["estanteria", "modulo", "nivel"])

        overol.estanteria, overol.modulo, overol.nivel = "Estantería 2", "Módulo 1", ""
        overol.save(update_fields=["estanteria", "modulo", "nivel"])

        camisa.estanteria, camisa.modulo, camisa.nivel = "Estantería 3", "Módulo 1", ""
        camisa.save(update_fields=["estanteria", "modulo", "nivel"])

        self.stdout.write(self.style.SUCCESS("Datos demo creados correctamente."))
        self.stdout.write(self.style.SUCCESS("  Login: admin / admin123"))
