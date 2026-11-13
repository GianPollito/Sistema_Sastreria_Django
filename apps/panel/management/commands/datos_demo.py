"""Datos locales reproducibles: nunca borra ni reinicia información existente."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.cuentas.models import Empleado
from apps.clientes.models import Cliente, Medida
from apps.catalogo.models import TipoPrenda, ModeloPrenda
from apps.inventario.models import Proveedor, Tela, Insumo
from apps.inventario.services import registrar_movimiento
from apps.pedidos.models import Pedido, DetallePedido
from apps.pedidos.services import cambiar_estado
from apps.pagos.services import registrar_pago
from apps.agenda.models import Cita


class Command(BaseCommand):
    help = "Añade cuentas y encargos ficticios para probar el taller; no sustituye datos existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("crear_roles", stdout=self.stdout)
        empleados = {}
        for nombre, apellido, rol, usuario in [
            ("Elena", "Vargas", "Administrador", "demo_admin"),
            ("Mateo", "Salazar", "Sastre", "demo_sastre"),
            ("Lucía", "Torres", "Recepcionista", "demo_recepcion"),
        ]:
            cuenta, nueva = get_user_model().objects.get_or_create(username=usuario, defaults={"first_name": nombre, "last_name": apellido})
            if nueva:
                cuenta.set_password("AtelierDemo2026!")
                cuenta.save()
                cuenta.groups.add(Group.objects.get(name=rol))
                empleado = Empleado.objects.create(usuario=cuenta, telefono="999000111")
            else:
                empleado = getattr(cuenta, "empleado", None)
                if not empleado or not cuenta.groups.filter(name=rol).exists():
                    raise CommandError("Existe una cuenta con nombre reservado de demo. No se ha modificado; revisa la colisión.")
            empleados[rol] = empleado
        if Pedido.objects.filter(numero="DEMO-001").exists():
            self.stdout.write("La demostración ya existe; se conserva su estado actual y sus contraseñas.")
            return
        hoy = timezone.localdate()
        proveedor, _ = Proveedor.objects.get_or_create(nombre="Textiles del Sur · Demo", defaults={"telefono": "014441212", "correo": "contacto@example.com"})
        tipos = []
        for nombre, precio in [("Traje", "1800"), ("Camisa", "280"), ("Pantalón", "350"), ("Vestido", "850")]:
            prenda, _ = TipoPrenda.objects.get_or_create(nombre=nombre, defaults={"precio_base": Decimal(precio)})
            tipos.append(prenda)
        modelos = []
        for tipo, nombre in zip(tipos, ["Dos botones · corte clásico", "Cuello italiano", "Pinza simple", "Corte evasé"]):
            modelo, _ = ModeloPrenda.objects.get_or_create(tipo_prenda=tipo, nombre=nombre)
            modelos.append(modelo)
        telas = []
        for codigo, descripcion, color, composicion, metros in [
            ("DEMO-L01", "Lana merino Super 120", "Carbón", "100% lana", "32"),
            ("DEMO-L02", "Lino de verano", "Natural", "100% lino", "18"),
            ("DEMO-A01", "Popelina fina", "Marfil", "100% algodón", "24"),
            ("DEMO-S01", "Sarga de vestir", "Verde botella", "Lana y viscosa", "2"),
        ]:
            tela, creada = Tela.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion, "color": color, "composicion": composicion, "proveedor": proveedor, "stock_minimo": 3})
            if creada:
                registrar_movimiento(material=tela, tipo="entrada", cantidad=Decimal(metros), responsable=empleados["Administrador"], notas="Inventario inicial de demostración")
            telas.append(tela)
        for codigo, descripcion, unidad, cantidad in [("DEMO-B01", "Botones de corozo", "unidad", "60"), ("DEMO-H01", "Hilo de algodón marfil", "carrete", "2")]:
            insumo, creado = Insumo.objects.get_or_create(codigo=codigo, defaults={"descripcion": descripcion, "unidad": unidad, "proveedor": proveedor, "stock_minimo": 5})
            if creado:
                registrar_movimiento(material=insumo, tipo="entrada", cantidad=Decimal(cantidad), responsable=empleados["Administrador"])
        nombres = ["Andrés Mendoza", "Valeria Ríos", "Gabriel Paredes", "Camila Arce", "Joaquín Flores", "Isabel Romero", "Diego Acosta", "Mariana León"]
        for i, nombre in enumerate(nombres):
            cliente = Cliente.objects.create(nombre=nombre, documento=f"DEMO-{i+1:04}", telefono=f"999120{i+1:03}", correo=f"cliente{i+1}@example.com", direccion="Miraflores, Lima", preferencias="Prefiere un calce cómodo y acabados discretos. Datos ficticios de demostración.")
            indice = i % 4
            medidas = Medida.objects.create(cliente=cliente, tipo_prenda=tipos[indice], responsable=empleados["Sastre"], cuello=38, hombro=44, pecho=98, cintura=84, cadera=100, largo_manga=62, largo_pantalon=104, largo_prenda=74, observaciones="Ficha de prueba, medidas en centímetros.")
            if i == 0:
                Medida.objects.create(cliente=cliente, tipo_prenda=tipos[indice], responsable=empleados["Sastre"], cuello=39, hombro=44, pecho=100, cintura=86, cadera=101, largo_manga=62, largo_pantalon=104, largo_prenda=74, observaciones="Segunda versión: ajuste de contorno.")
            arreglo = i == 7
            pedido = Pedido.objects.create(numero=f"DEMO-{i+1:03}", cliente=cliente, modalidad="arreglo" if arreglo else "medida", fecha_prometida=hoy + timedelta(days=[3, -2, 1, 5, 8, 0, -1, 2][i]), prioridad="alta" if i in [1, 5] else "normal", sastre=empleados["Sastre"], notas="Dobladillo y ajuste de cintura." if arreglo else "Conservar margen de costura para futuros ajustes. Primera prueba antes del acabado.")
            detalle = DetallePedido.objects.create(pedido=pedido, tipo_prenda=None if arreglo else tipos[indice], modelo=None if arreglo else modelos[indice], medida=None if arreglo else medidas, descripcion="Dobladillo de pantalón" if arreglo else str(modelos[indice]), cantidad=1, precio_unitario=Decimal("35") if arreglo else tipos[indice].precio_base)
            if not arreglo:
                registrar_movimiento(material=telas[i % 3], tipo="consumo", cantidad=Decimal("2.5"), responsable=empleados["Sastre"], detalle=detalle)
            registrar_pago(pedido=pedido, importe=pedido.total if i == 6 else (pedido.total / 2).quantize(Decimal("0.01")), metodo="efectivo" if i % 2 else "transferencia", responsable=empleados["Recepcionista"], referencia="Demostración")
            for estado in Pedido.Estado.values[1:(i % 7) + 1]:
                cambiar_estado(pedido=pedido, nuevo=estado, usuario=empleados["Administrador"].usuario)
            if i < 5:
                inicio = timezone.make_aware(datetime.combine(hoy + timedelta(days=i), time(10 + i, 0)))
                Cita.objects.create(cliente=cliente, pedido=pedido, empleado=empleados["Sastre"], motivo="prueba", inicio=inicio, fin=inicio + timedelta(minutes=45), notas="Cita de demostración.")
        self.stdout.write(self.style.SUCCESS("Demostración creada: tres cuentas, ocho clientes y ocho encargos. Las credenciales de prueba están en README.md."))
