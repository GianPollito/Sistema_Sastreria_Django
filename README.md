# Atelier · Sistema de sastrería

## Sistema local listo para pruebas

Django Templates y CSS propio, con panel operativo, clientes, medidas versionadas,
catálogo, telas, insumos, proveedores, pedidos con múltiples prendas, arreglos rápidos,
cobros, recibos, agenda semanal y gestión de empleados. Tablero con arrastre entre etapas,
silueta SVG para tomar medidas y estilos de impresión para órdenes y recibos.
No se habilita registro público; REGISTRATION_CODE se lee por compatibilidad con el entorno solicitado.

## Acceso y base de trabajo

Abre [el taller local](http://127.0.0.1:8123/).

El usuario local es `administrador`; conserva la contraseña que tenía `demo_admin`.
Las otras cuentas demo y todos los datos de prueba fueron retirados, incluido el pedido
adicional. Se conservan los roles y permisos necesarios para comenzar a trabajar.

Desde Equipo, el administrador puede crear cuentas propias, asignar roles y desactivar
empleados. Cada empleado puede cambiar su contraseña desde su nombre en la cabecera.
No se muestran contraseñas guardadas. La base está lista para registrar datos propios.

## Instalación en Windows

Python 3.11 o superior compatible con Django 5.2. MariaDB 10.5 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

El archivo `.env` contiene la configuración privada de tu equipo y está excluido de Git.
`.env.example` es una plantilla pública sin contraseñas ni clave secreta. Para una nueva
instalación, copia `.env.example` a `.env`, completa tus credenciales locales y asigna
una clave secreta de Django propia. No publiques esos valores en GitHub.
La configuración lee todas las variables, usa utf8mb4 y activa el modo SQL estricto.

Antes de iniciar o conectar servicios, comprobar sus puertos:

```powershell
netstat -ano | findstr :3307
netstat -ano | findstr :8123
```

3307 debe corresponder a tu MariaDB. Si 8123 tiene un proceso escuchando, escoge otro
puerto libre, compruébalo con el mismo comando y sustituye 8123 al ejecutar Django.
No cierres procesos de otros proyectos. En Linux usa `ss -ltn` o `lsof -i :8123`.

Crea una base vacía en tu instancia MariaDB (no sobrescribas una existente).
También puedes ejecutar `manage.py preparar_base`, que solo la crea si no existe:

```sql
CREATE DATABASE sastreria_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Después:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py crear_roles
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8123
```

Abre http://127.0.0.1:8123/. El cierre de sesión usa POST y protección CSRF.
No se ha configurado despliegue de producción.
En una instalación nueva, la ficha del superusuario se crea automáticamente. En esta
instalación ya existe `administrador`; no necesitas crearlo otra vez.
Para detener Django, pulsa Ctrl+C
en su terminal. No cambies el puerto de MariaDB ni añadas variables de puerto al `.env`.

## Recorrido para probar el sistema

1. Entra como `administrador`. El panel muestra entregas atrasadas, próximas entregas,
   ingresos del mes, encargos por etapa, citas del día y materiales con stock bajo.
2. Abre Clientes, crea una ficha y pulsa Tomar medidas. Selecciona tipo de prenda,
   pulsa un punto de la silueta y registra sus centímetros. Una segunda toma crea
   otra versión; nunca modifica la ficha anterior.
3. Crea un encargo, elige cliente, modalidad, fecha, prioridad y sastre. En su ficha,
   añade una o varias prendas, el modelo, las medidas y el precio acordado. Puedes
   corregir las prendas y precios mientras el pedido esté Recibido y no tenga cobros.
4. Registra un adelanto desde la ficha del pedido. Se abre el comprobante imprimible.
   El sistema rechaza importes superiores al saldo y cantidades no positivas.
5. En Telas o Insumos, abre Movimientos. Registra entradas para aumentar existencias
   y consumos vinculados a una prenda. El saldo de material se actualiza de forma
   transaccional. Una devolución exige un consumo previo de esa misma prenda y material.
6. Avanza el encargo por Recibido → Corte → Confección → Prueba → Ajustes → Listo →
   Entregado, arrastrándolo en el tendedero o usando el botón de su ficha. No se permiten
   saltos ni entregas con saldo pendiente. Cobra el saldo antes de entregar.
7. En Agenda, reserva una cita y cambia de semana. Se rechazan intervalos invertidos,
   citas solapadas para el mismo empleado y pedidos de un cliente distinto. Puedes
   marcar citas realizadas o canceladas desde Editar cita.
8. Usa Arreglo rápido para crear un dobladillo: añade descripción y precio sin medidas
   ni catálogo; conserva la misma trazabilidad de estados y pagos.
9. Imprime una ficha de pedido o comprobante con su botón. Usa la vista previa del
   navegador o Guardar como PDF; la cabecera, navegación y acciones no se imprimen.
10. Crea cuentas de Sastre y Recepcionista desde Equipo y comprueba sus permisos.
    En tablet, usa el botón de avance de la ficha si el navegador no admite arrastre táctil.

No hay borrado de fichas ni cobros desde la interfaz: se conserva el historial del taller.
El catálogo permite desactivar prendas/modelos y Equipo permite desactivar empleados.
El cliente y la modalidad de un pedido quedan fijados tras su creación para proteger
las relaciones con sus medidas. Las notas, fecha, prioridad y asignación pueden editarse
hasta la entrega. El recibo es una constancia interna, no un comprobante fiscal.

El comando `datos_demo` sigue disponible como recurso opcional de desarrollo. No lo
ejecutes sobre tu base de trabajo si quieres mantenerla sin registros de demostración.

## Organización y datos

`config/` contiene settings y URLs; `apps/` separa cuentas, clientes, catálogo,
inventario, pedidos, pagos, agenda y panel. `templates/` y `static/` contienen la interfaz.

Cliente tiene múltiples versiones de Medida por TipoPrenda. Cada DetallePedido conserva
el precio acordado y referencia la versión de medidas utilizada. Los detalles de un
pedido avanzan juntos. Un arreglo no necesita ficha ni tipo de prenda.

Proveedor, Tela e Insumo se separan del catálogo y del pedido para evitar duplicación.
MovimientoInventario referencia un único material; los consumos ligados a detalles
representan las relaciones de consumo de telas e insumos sin duplicar tablas.
Los servicios bloquean filas al consumir stock y cobrar. Pedido calcula total y saldo;
HistorialEstado conserva los cambios. Las claves foráneas usan PROTECT para conservar historial.
Se indexan estado, fecha prometida, cliente, fecha de pago e inicio de cita.

Los grupos son Administrador, Recepcionista y Sastre. Ejecutar `crear_roles` sincroniza
permisos. Las vistas exigen empleado activo y permiso; el sastre solo ve pedidos y clientes
asignados, sus cobros y su agenda. Puede registrar nuevas medidas y consumos y avanzar
etapas. Recepción gestiona clientes, pedidos, medidas, citas y cobros; no modifica el
inventario ni las cuentas. Administración gestiona todos los módulos.

Las consultas de ingresos y citas del día utilizan rangos de fechas calculados en
America/Lima, sin requerir que MariaDB tenga cargadas sus tablas de zonas horarias.

## Verificación

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --settings=config.test_settings --noinput
```

Las pruebas usan MariaDB y crean una base temporal `test_atelier_<nombre aleatorio>`,
separada de `sastreria_db`, que Django elimina al terminar. El usuario de base de datos
necesita permisos para crear y eliminar esa base temporal. No se usa SQLite.

Resultado: 30 pruebas aprobadas. Cubren rutas, formularios, login/logout, CSRF, permisos,
empleados inactivos, versiones de medidas, arreglos, edición de prendas, restricciones de
precio, consumo/devolución de materiales, sobrepagos, transiciones, entrega con deuda,
citas, indicadores mensuales, escape de texto y carga idempotente de demostración.
También se verificaron migraciones, configuración y la interfaz mediante navegador,
incluidos el arrastre real, el foco de los puntos SVG y los tamaños de tablet y móvil.
El recorrido HTTP completo comprueba creación de pedido, prendas, adelanto, consumo,
avance de etapas, cobro del saldo y entrega. No se ha enviado ninguna impresión física.
