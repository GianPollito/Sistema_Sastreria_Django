from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.cuentas.models import Empleado
from apps.catalogo.models import TipoPrenda
from apps.clientes.models import Cliente, Medida
from apps.inventario.models import Proveedor, Tela, Insumo, MovimientoInventario
from apps.inventario.services import registrar_movimiento
from apps.pedidos.models import Pedido, DetallePedido
from apps.pedidos.services import cambiar_estado
from apps.pagos.models import Pago
from apps.pagos.services import registrar_pago
from apps.agenda.forms import CitaForm
from apps.agenda.models import Cita


class TallerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("crear_roles", verbosity=0)
        cls.usuarios = {}
        for nombre, rol in [("admin", "Administrador"), ("sastre", "Sastre"), ("recepcion", "Recepcionista")]:
            usuario = get_user_model().objects.create_user(nombre, password="PruebaAtelier2026!")
            usuario.groups.add(Group.objects.get(name=rol))
            Empleado.objects.create(usuario=usuario)
            cls.usuarios[nombre] = usuario
        cls.cliente = Cliente.objects.create(nombre="Cliente de prueba", telefono="999111222")
        cls.otro_cliente = Cliente.objects.create(nombre="Otro cliente", telefono="999111333")
        cls.tipo = TipoPrenda.objects.create(nombre="Camisa", precio_base=200)
        cls.medida = Medida.objects.create(cliente=cls.cliente, tipo_prenda=cls.tipo, responsable=cls.usuarios["sastre"].empleado, pecho=98)
        cls.pedido = Pedido.objects.create(cliente=cls.cliente, sastre=cls.usuarios["sastre"].empleado, fecha_prometida=timezone.localdate() + timedelta(days=2))
        cls.detalle = DetallePedido.objects.create(pedido=cls.pedido, tipo_prenda=cls.tipo, medida=cls.medida, descripcion="Camisa de lino", precio_unitario=200)
        cls.ajeno = Pedido.objects.create(cliente=cls.otro_cliente, fecha_prometida=timezone.localdate(), modalidad="arreglo")
        cls.proveedor = Proveedor.objects.create(nombre="Proveedor prueba")
        cls.tela = Tela.objects.create(codigo="LIN01", descripcion="Lino", color="Crudo", composicion="Lino", proveedor=cls.proveedor, existencias=10, stock_minimo=2)
        cls.insumo = Insumo.objects.create(codigo="BOT01", descripcion="Botón", proveedor=cls.proveedor, existencias=20)

    def entrar(self, nombre="admin"):
        self.client.force_login(self.usuarios[nombre])

    def test_rutas_principales_y_formularios(self):
        self.entrar()
        rutas = [reverse("panel"), reverse("tablero"), reverse("pedido", args=[self.pedido.pk]), reverse("pedido_nuevo"),
            reverse("pedido_editar", args=[self.pedido.pk]), reverse("detalle_nuevo", args=[self.pedido.pk]),
            reverse("cliente", args=[self.cliente.pk]), reverse("medida_nueva", args=[self.cliente.pk]),
            reverse("agenda"), reverse("cita_nueva"), reverse("pagos"), reverse("empleados"), reverse("empleado_nuevo"), reverse("clave"),
            reverse("movimientos", args=["telas", self.tela.pk]), reverse("movimiento_nuevo", args=["telas", self.tela.pk])]
        for entidad in ["clientes", "prendas", "modelos", "proveedores", "telas", "insumos"]:
            rutas.extend([reverse("lista", args=[entidad]), reverse("crear", args=[entidad])])
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_login_logout_y_csrf(self):
        navegador = Client(enforce_csrf_checks=True)
        self.assertEqual(navegador.get(reverse("panel")).status_code, 302)
        self.assertEqual(navegador.get(reverse("login")).status_code, 200)
        self.assertEqual(navegador.post(reverse("login"), {"username": "admin", "password": "PruebaAtelier2026!"}).status_code, 403)
        token = navegador.cookies["csrftoken"].value
        respuesta = navegador.post(reverse("login"), {"username": "admin", "password": "PruebaAtelier2026!", "csrfmiddlewaretoken": token})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(navegador.get(reverse("logout")).status_code, 405)
        self.assertEqual(navegador.post(reverse("logout"), {"csrfmiddlewaretoken": navegador.cookies["csrftoken"].value}).status_code, 302)

    def test_cliente_y_medidas_versionadas(self):
        self.entrar("recepcion")
        respuesta = self.client.post(reverse("crear", args=["clientes"]), {"nombre": "Ana Prueba", "telefono": "999444555"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Cliente.objects.filter(nombre="Ana Prueba").exists())
        self.client.post(reverse("medida_nueva", args=[self.cliente.pk]), {"tipo_prenda": self.tipo.pk, "pecho": "100.5"})
        self.assertEqual(self.cliente.medidas.count(), 2)
        self.medida.pecho = 102
        with self.assertRaises(ValidationError):
            self.medida.save()

    def test_sastre_solo_accede_pedidos_clientes_asignados(self):
        self.entrar("sastre")
        self.assertEqual(self.client.get(reverse("pedido", args=[self.pedido.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("pedido", args=[self.ajeno.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("cliente", args=[self.otro_cliente.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("lista", args=["clientes"])), "Otro cliente")
        self.assertEqual(self.client.get(reverse("pedido_editar", args=[self.pedido.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("crear", args=["telas"])).status_code, 403)

    def test_recepcion_no_administra_equipo_ni_stock(self):
        self.entrar("recepcion")
        self.assertEqual(self.client.get(reverse("empleado_nuevo")).status_code, 403)
        self.assertEqual(self.client.get(reverse("movimiento_nuevo", args=["telas", self.tela.pk])).status_code, 403)

    def test_empleado_inactivo_no_accede(self):
        self.usuarios["sastre"].empleado.activo = False
        self.usuarios["sastre"].empleado.save()
        self.entrar("sastre")
        self.assertEqual(self.client.get(reverse("panel")).status_code, 403)

    def test_cobro_saldo_y_comprobante(self):
        self.entrar("recepcion")
        respuesta = self.client.post(reverse("cobrar", args=[self.pedido.pk]), {"importe": "80", "metodo": "efectivo"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.pedido.saldo, Decimal("120"))
        self.assertContains(self.client.get(respuesta.url), "Recibo de pago")
        with self.assertRaises(ValidationError):
            registrar_pago(pedido=self.pedido, importe=Decimal("121"), metodo="efectivo", responsable=self.usuarios["recepcion"].empleado)
        self.assertEqual(Pago.objects.count(), 1)

    def test_pago_negativo_rechazado(self):
        with self.assertRaises(ValidationError):
            registrar_pago(pedido=self.pedido, importe=Decimal("-1"), metodo="efectivo", responsable=self.usuarios["recepcion"].empleado)

    def test_stock_consumo_devolucion_y_limites(self):
        empleado = self.usuarios["sastre"].empleado
        registrar_movimiento(material=self.tela, tipo="consumo", cantidad=Decimal("3"), responsable=empleado, detalle=self.detalle)
        self.tela.refresh_from_db()
        self.assertEqual(self.tela.existencias, Decimal("7"))
        with self.assertRaises(ValidationError):
            registrar_movimiento(material=self.tela, tipo="consumo", cantidad=Decimal("8"), responsable=empleado, detalle=self.detalle)
        registrar_movimiento(material=self.tela, tipo="devolucion", cantidad=Decimal("2"), responsable=empleado, detalle=self.detalle)
        with self.assertRaises(ValidationError):
            registrar_movimiento(material=self.tela, tipo="devolucion", cantidad=Decimal("2"), responsable=empleado, detalle=self.detalle)
        self.tela.refresh_from_db()
        self.assertEqual(self.tela.existencias, Decimal("9"))
        self.assertEqual(MovimientoInventario.objects.count(), 2)

    def test_sastre_no_registra_entrada(self):
        self.entrar("sastre")
        respuesta = self.client.post(reverse("movimiento_nuevo", args=["telas", self.tela.pk]), {"tipo": "entrada", "cantidad": "10"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(MovimientoInventario.objects.count(), 0)

    def test_transiciones_sin_saltos_y_sin_entrega_con_deuda(self):
        admin = self.usuarios["admin"]
        with self.assertRaises(ValidationError):
            cambiar_estado(pedido=self.pedido, nuevo="listo", usuario=admin)
        for estado in ["corte", "confeccion", "prueba", "ajustes", "listo"]:
            cambiar_estado(pedido=self.pedido, nuevo=estado, usuario=admin)
        with self.assertRaises(ValidationError):
            cambiar_estado(pedido=self.pedido, nuevo="entregado", usuario=admin)
        registrar_pago(pedido=self.pedido, importe=Decimal("200"), metodo="tarjeta", responsable=admin.empleado)
        cambiar_estado(pedido=self.pedido, nuevo="entregado", usuario=admin)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "entregado")
        self.assertEqual(self.pedido.historial.count(), 6)

    def test_no_avanza_pedido_sin_prendas(self):
        with self.assertRaises(ValidationError):
            cambiar_estado(pedido=self.ajeno, nuevo="corte", usuario=self.usuarios["admin"])

    def test_tablero_ajax_valida_en_servidor(self):
        self.entrar("sastre")
        url = reverse("pedido_estado", args=[self.pedido.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {"estado": "listo"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 400)
        self.assertEqual(self.client.post(url, {"estado": "corte"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 200)

    def test_flujo_arreglo_sin_medidas(self):
        self.entrar("recepcion")
        respuesta = self.client.post(reverse("pedido_nuevo"), {"cliente": self.cliente.pk, "modalidad": "arreglo", "fecha_prometida": timezone.localdate().isoformat(), "prioridad": "normal", "sastre": self.usuarios["sastre"].empleado.pk})
        self.assertEqual(respuesta.status_code, 302)
        pedido = Pedido.objects.latest("pk")
        respuesta = self.client.post(reverse("detalle_nuevo", args=[pedido.pk]), {"descripcion": "Dobladillo", "cantidad": "1", "precio_unitario": "25"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(pedido.total, Decimal("25"))
        self.assertIsNone(pedido.detalles.get().medida_id)

    def test_medidas_de_otro_cliente_rechazadas(self):
        self.entrar("recepcion")
        medida = Medida.objects.create(cliente=self.otro_cliente, tipo_prenda=self.tipo, responsable=self.usuarios["sastre"].empleado, pecho=90)
        respuesta = self.client.post(reverse("detalle_nuevo", args=[self.pedido.pk]), {"tipo_prenda": self.tipo.pk, "medida": medida.pk, "descripcion": "Camisa", "cantidad": "1", "precio_unitario": "200"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.pedido.detalles.count(), 1)

    def test_no_se_agregan_prendas_despues_de_cobrar(self):
        registrar_pago(pedido=self.pedido, importe=Decimal("10"), metodo="efectivo", responsable=self.usuarios["recepcion"].empleado)
        self.entrar("recepcion")
        respuesta = self.client.post(reverse("detalle_nuevo", args=[self.pedido.pk]), {"tipo_prenda": self.tipo.pk, "medida": self.medida.pk, "descripcion": "Camisa extra", "cantidad": "1", "precio_unitario": "200"})
        self.assertContains(respuesta, "antes de cobrar")
        self.assertEqual(self.pedido.detalles.count(), 1)

    def test_cita_solapada_y_cliente_incorrecto(self):
        inicio = timezone.now() + timedelta(days=1)
        Cita.objects.create(cliente=self.cliente, empleado=self.usuarios["sastre"].empleado, motivo="medidas", inicio=inicio, fin=inicio + timedelta(hours=1))
        datos = {"cliente": self.cliente.pk, "empleado": self.usuarios["sastre"].empleado.pk, "motivo": "prueba", "inicio": inicio, "fin": inicio + timedelta(minutes=30), "estado": "pendiente"}
        form = CitaForm(datos)
        self.assertFalse(form.is_valid())
        cita = Cita(cliente=self.otro_cliente, pedido=self.pedido, inicio=inicio, fin=inicio + timedelta(hours=1))
        with self.assertRaises(ValidationError):
            cita.clean()

    def test_creacion_empleado_y_rol(self):
        self.entrar()
        respuesta = self.client.post(reverse("empleado_nuevo"), {"usuario": "nuevo_sastre", "nombre": "Nuevo", "rol": Group.objects.get(name="Sastre").pk, "clave": "ClaveNuevaAtelier2026!", "activo": "on"})
        self.assertEqual(respuesta.status_code, 302)
        usuario = get_user_model().objects.get(username="nuevo_sastre")
        self.assertTrue(usuario.check_password("ClaveNuevaAtelier2026!"))
        self.assertTrue(usuario.groups.filter(name="Sastre").exists())

    def test_busqueda_y_escaping_notas(self):
        self.cliente.preferencias = '<script>alert("xss")</script>'
        self.cliente.save()
        self.entrar()
        respuesta = self.client.get(reverse("cliente", args=[self.cliente.pk]))
        self.assertNotContains(respuesta, '<script>alert("xss")</script>')
        self.assertContains(respuesta, "&lt;script&gt;")
        self.assertNotContains(self.client.get(reverse("lista", args=["clientes"]), {"q": "inexistente"}), "Otro cliente")

    def test_demo_idempotente_y_todas_etapas(self):
        call_command("datos_demo", verbosity=0)
        self.assertEqual(Pedido.objects.filter(numero__startswith="DEMO-").count(), 8)
        cantidad = Pago.objects.count()
        call_command("datos_demo", verbosity=0)
        self.assertEqual(Pago.objects.count(), cantidad)
        self.assertEqual(set(Pedido.objects.filter(numero__startswith="DEMO-").values_list("estado", flat=True)), set(Pedido.Estado.values))

    def test_panel_ingresos_y_citas_sin_tablas_timezone_mariadb(self):
        registrar_pago(pedido=self.pedido, importe=Decimal("80"), metodo="efectivo", responsable=self.usuarios["recepcion"].empleado)
        inicio = timezone.now()
        Cita.objects.create(cliente=self.cliente, empleado=self.usuarios["sastre"].empleado, motivo="prueba", inicio=inicio, fin=inicio + timedelta(minutes=30))
        self.entrar()
        respuesta = self.client.get(reverse("panel"))
        self.assertEqual(respuesta.context["ingresos"], Decimal("80"))
        self.assertEqual(len(respuesta.context["citas"]), 1)

    def test_editar_prenda_antes_del_cobro(self):
        self.entrar("recepcion")
        respuesta = self.client.post(reverse("detalle_editar", args=[self.pedido.pk, self.detalle.pk]), {"tipo_prenda": self.tipo.pk, "medida": self.medida.pk, "descripcion": "Camisa con puño francés", "cantidad": "2", "precio_unitario": "210"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.pedido.total, Decimal("420"))

    def test_recorrido_completo_http_confeccion_a_medida(self):
        self.entrar("recepcion")
        respuesta = self.client.post(reverse("pedido_nuevo"), {"cliente": self.cliente.pk, "modalidad": "medida", "fecha_prometida": (timezone.localdate() + timedelta(days=10)).isoformat(), "prioridad": "alta", "sastre": self.usuarios["sastre"].empleado.pk, "notas": "Puño francés"})
        self.assertEqual(respuesta.status_code, 302)
        pedido = Pedido.objects.latest("pk")
        respuesta = self.client.post(reverse("detalle_nuevo", args=[pedido.pk]), {"tipo_prenda": self.tipo.pk, "medida": self.medida.pk, "descripcion": "Camisa", "cantidad": "2", "precio_unitario": "180"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(pedido.total, Decimal("360"))
        self.assertEqual(self.client.post(reverse("cobrar", args=[pedido.pk]), {"importe": "100", "metodo": "efectivo"}).status_code, 302)
        self.entrar("sastre")
        respuesta = self.client.post(reverse("movimiento_nuevo", args=["telas", self.tela.pk]), {"tipo": "consumo", "cantidad": "3", "detalle": pedido.detalles.get().pk})
        self.assertEqual(respuesta.status_code, 302)
        for estado in ["corte", "confeccion", "prueba", "ajustes", "listo"]:
            respuesta = self.client.post(reverse("pedido_estado", args=[pedido.pk]), {"estado": estado}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.client.post(reverse("pedido_estado", args=[pedido.pk]), {"estado": "entregado"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 400)
        self.entrar("recepcion")
        respuesta = self.client.post(reverse("cobrar", args=[pedido.pk]), {"importe": "260", "metodo": "transferencia", "referencia": "PRUEBA-001"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertContains(self.client.get(respuesta.url), "260,00")
        self.assertEqual(self.client.post(reverse("pedido_estado", args=[pedido.pk]), {"estado": "entregado"}).status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, "entregado")
        self.assertEqual(pedido.saldo, Decimal("0"))
        self.assertContains(self.client.get(reverse("pedido", args=[pedido.pk])), "Imprimir ficha")

    def test_cita_desde_formulario_y_cancelacion_libera_horario(self):
        self.entrar("recepcion")
        inicio = timezone.localtime(timezone.now() + timedelta(days=2)).replace(second=0, microsecond=0)
        datos = {"cliente": self.cliente.pk, "pedido": self.pedido.pk, "empleado": self.usuarios["sastre"].empleado.pk, "motivo": "prueba", "inicio": inicio.strftime("%Y-%m-%dT%H:%M"), "fin": (inicio + timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M"), "estado": "pendiente"}
        self.assertEqual(self.client.post(reverse("cita_nueva"), datos).status_code, 302)
        cita = Cita.objects.latest("pk")
        self.assertEqual(self.client.post(reverse("cita_nueva"), datos).status_code, 200)
        self.assertEqual(Cita.objects.count(), 1)
        self.assertEqual(self.client.post(reverse("cita_editar", args=[cita.pk]), {**datos, "estado": "cancelada"}).status_code, 302)
        self.assertEqual(self.client.post(reverse("cita_nueva"), datos).status_code, 302)
        self.assertEqual(Cita.objects.count(), 2)

    def test_superusuario_tiene_ficha_automatica(self):
        usuario = get_user_model().objects.create_superuser("propietario", "propietario@example.com", "PruebaAtelier2026!")
        self.assertTrue(Empleado.objects.filter(usuario=usuario, activo=True).exists())
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse("panel")).status_code, 200)
