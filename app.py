import io
from flask import Flask, flash, redirect, render_template, request, session, make_response,url_for,send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from weasyprint import HTML
from datetime import datetime
import locale
import re
# Configure the application
app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Session configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite as the database
db = SQL("sqlite:///Inventario.db")

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login view

# User class for Flask-Login


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


@app.after_request
def after_request(response):
    """
    Ensure responses aren't cached
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
@login_required
def index():

    search = request.args.get("search", "").strip()

    # Consultar la base de datos
    if search:

        query = "SELECT * FROM Productos WHERE nombre LIKE ?"
        items = db.execute(query, f"{search}%")  # Comodín solo al final
    else:

        items = db.execute("SELECT * FROM Productos")

    return render_template("index.html", items=items)


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":

        if not request.form.get("username"):
            return render_template("login.html")
        elif not request.form.get("password"):
            return render_template("login.html")

        user = db.execute("select * from users where username = ?",
                          request.form.get("username"))

        if len(user) != 1 or not check_password_hash(
            user[0]["hash"], request.form.get("password")
        ):
            flash("error")
            return render_template("login.html")

        session["id"] = user[0]["username"]

        # Create user object for Flask-Login
        user_obj = User(user[0]["id"], user[0]["username"])
        login_user(user_obj)

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            flash("Todos los campos son obligatorios", "error")
            return render_template("register.html")

        if password != confirmation:
            flash("Las contraseñas no coinciden", "error")
            return render_template("register.html")

        hash_password = generate_password_hash(password)

        try:
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_password)
            flash("Registro exitoso. Ahora puede iniciar sesión", "success")
            return redirect("/login")
        except:
            flash("El nombre de usuario ya existe", "error")
            return render_template("register.html")

    return render_template("register.html")


@login_manager.user_loader
def load_user(user_id):
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if user:
        return User(user[0]["id"], user[0]["username"])
    return None


@app.route("/logout")
@login_required
def logout():

    session.clear()


    return redirect("/")


@app.route("/test_db")
def test_db():
    try:
        users = db.execute("SELECT * FROM users")
        return f"Conexión exitosa. Usuarios encontrados: {len(users)}"
    except Exception as e:
        return f"Error en la conexión a la base de datos: {e}"

# Clientes


@app.route("/clientes", methods=["GET"])
@login_required
def clientes():
    """Mostrar todos los clientes"""
    clientes = db.execute("SELECT * FROM Clientes")
    return render_template("clientes.html", clientes=clientes)


@app.route("/clientes/agregar", methods=["POST"])
@login_required
def agregar_cliente():
    """Agregar un nuevo cliente"""
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    telefono = request.form.get("telefono")
    email = request.form.get("email")

    if not nombre or not telefono or not email:
        flash("Todos los campos son obligatorios", "error")
        return redirect("/clientes")

    try:
        db.execute("INSERT INTO Clientes (nombre, direccion, telefono, email) VALUES (?, ?, ?, ?)",
                   nombre, direccion, telefono, email)
        flash("Cliente agregado exitosamente", "success")
    except Exception as e:
        flash(f"Error al agregar cliente: {e}", "error")

    return redirect("/clientes")


@app.route("/clientes/editar/<int:cliente_id>", methods=["POST"])
@login_required
def editar_cliente(cliente_id):
    """Editar un cliente existente"""
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    telefono = request.form.get("telefono")
    email = request.form.get("email")

    if not nombre or not telefono or not email:
        flash("Todos los campos son obligatorios", "error")
        return redirect("/clientes")

    try:
        db.execute("UPDATE Clientes SET nombre = ?, direccion = ?, telefono = ?, email = ? WHERE id = ?",
                   nombre, direccion, telefono, email, cliente_id)
        flash("Cliente actualizado exitosamente", "success")
    except Exception as e:
        flash(f"Error al actualizar el cliente: {e}", "error")

    return redirect("/clientes")


@app.route("/clientes/eliminar/<int:cliente_id>", methods=["POST"])
@login_required
def eliminar_cliente(cliente_id):
    """Eliminar un cliente"""
    try:
        db.execute("DELETE FROM Clientes WHERE id = ?", cliente_id)
        flash("Cliente eliminado exitosamente", "success")
    except Exception as e:
        flash(f"Error al eliminar: El cliente ya facturado", "error")

    return redirect("/clientes")
# FinClientes

# Proveedores
@app.route("/proveedores", methods=["GET"])
@login_required
def proveedores():
    """Mostrar todos los Proveedores"""
    proveedores = db.execute("SELECT * FROM Proveedores")
    return render_template("proveedores.html", proveedores=proveedores)


@app.route("/proveedores/agregar", methods=["POST"])
@login_required
def agregar_proveedor():
    """Agregar un nuevo proveedor"""
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    ruc = request.form.get("ruc")
    telefono = request.form.get("telefono")
    email = request.form.get("email")

    if not nombre or not telefono or not email:
        flash("Todos los campos son obligatorios", "error")
        return redirect("/proveedores")

    try:
        db.execute("INSERT INTO Proveedores (nombre, direccion, ruc, telefono, email) VALUES (?, ?, ?, ?, ?)",
                   nombre, direccion, ruc, telefono, email)
        flash("Proveedor agregado exitosamente", "success")
    except Exception as e:
        flash(f"Error al agregar proveedor: {e}", "error")

    return redirect("/proveedores")


@app.route("/proveedores/editar/<int:proveedor_id>", methods=["POST"])
@login_required
def editar_proveedor(proveedor_id):
    """Editar un proveedor existente"""
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    ruc = request.form.get("ruc")
    telefono = request.form.get("telefono")
    email = request.form.get("email")

    if not nombre or not telefono or not email:
        flash("Todos los campos son obligatorios", "error")
        return redirect("/proveedores")

    try:
        db.execute("UPDATE Proveedores SET nombre = ?, direccion = ?, ruc = ?, telefono = ?, email = ? WHERE id = ?",
                   nombre, direccion, ruc, telefono, email, proveedor_id)
        flash("Proveedor actualizado exitosamente", "success")
    except Exception as e:
        flash(f"Error al actualizar el proveedor: {e}", "error")

    return redirect("/proveedores")


@app.route("/proveedores/eliminar/<int:proveedor_id>", methods=["POST"])
@login_required
def eliminar_proveedor(proveedor_id):
    """Eliminar un proveedor"""
    try:
        db.execute("DELETE FROM Proveedores WHERE id = ?", proveedor_id)
        flash("Proveedor eliminado exitosamente", "success")
    except Exception as e:
        flash(f"Error al eliminar: El Proveedor ya facturado", "error")

    return redirect("/proveedores")


# FinProveedores




# productos
@app.route("/productos", methods=["GET"])
@login_required
def productos():
    """Mostrar la lista de productos"""
    productos = db.execute("SELECT * FROM Productos")
    return render_template("productos.html", productos=productos)


@app.route("/productos/agregar", methods=["POST"])
@login_required
def agregar_producto():
    """Agregar un nuevo producto"""
    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    precio = request.form.get("precio")
    stock = request.form.get("stock")

    if not nombre or not precio or not stock:
        flash("Todos los campos obligatorios deben ser completados", "error")
        return redirect("/productos")

    try:
        db.execute(
            "INSERT INTO Productos (nombre, descripcion, precio, stock) VALUES (?, ?, ?, ?)",
            nombre,
            descripcion,
            float(precio),
            int(stock),
        )
        flash("Producto agregado exitosamente", "success")
    except Exception as e:
        flash(f"Error al agregar el producto: {e}", "error")

    return redirect("/productos")


@app.route("/productos/editar/<int:producto_id>", methods=["POST"])
@login_required
def editar_producto(producto_id):
    """Editar un producto existente"""
    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    precio = request.form.get("precio")
    stock = request.form.get("stock")

    if not nombre or not precio or not stock:
        flash("Todos los campos obligatorios deben ser completados", "error")
        return redirect("/productos")

    try:
        db.execute(
            "UPDATE Productos SET nombre = ?, descripcion = ?, precio = ?, stock = ? WHERE id = ?",
            nombre,
            descripcion,
            float(precio),
            int(stock),
            producto_id,
        )
        flash("Producto actualizado exitosamente", "success")
    except Exception as e:
        flash(f"Error al actualizar el producto: {e}", "error")

    return redirect("/productos")


@app.route("/productos/eliminar/<int:producto_id>", methods=["POST"])
@login_required
def eliminar_producto(producto_id):
    """Eliminar un producto"""
    try:
        db.execute("DELETE FROM Productos WHERE id = ?", producto_id)
        flash("Producto eliminado exitosamente", "success")
    except Exception as e:
        flash(f"Error al eliminar: Producto ya facturado", "error")

    return redirect("/productos")

# finProductos


# incioVentas
@app.route("/ventas", methods=["GET", "POST"])
@login_required
def ventas():
    if request.method == "POST":
        cliente_id = request.form.get("cliente")
        productos_seleccionados = {
            key.split("_")[1]: int(value)
            for key, value in request.form.items() if key.startswith("cantidad_") and int(value) >= 0
        }

        total = 0
        for producto_id, cantidad in productos_seleccionados.items():
            producto = db.execute("SELECT * FROM Productos WHERE id = ?", producto_id)[0]
            if producto["stock"] < cantidad:
                flash(f"Stock insuficiente para {producto['nombre']}", "error")
                return redirect("/ventas")
            db.execute("UPDATE Productos SET stock = stock - ? WHERE id = ?", cantidad, producto_id)
            total += producto["precio"] * cantidad


        db.execute("INSERT INTO Ventas (cliente_id, total) VALUES (?, ?)", cliente_id, total)
        venta_id = db.execute("SELECT last_insert_rowid()")[0]["last_insert_rowid()"]


        for producto_id, cantidad in productos_seleccionados.items():
            db.execute("INSERT INTO DetalleVenta (venta_id, producto_id, cantidad) VALUES (?, ?, ?)",
                       venta_id, producto_id, cantidad)

        ultimo = db.execute("SELECT numero_factura FROM Facturas ORDER BY id DESC LIMIT 1")
        if ultimo:
            import re
            match = re.search(r'\d+', ultimo[0]["numero_factura"])
            base = int(match.group()) if match else 0
            numero_factura = f"F{base + 1:04d}"
        else:
            numero_factura = "F0001"


        fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute("""
            INSERT INTO Facturas (venta_id, numero_factura, fecha_emision)
            VALUES (?, ?, ?)
        """, venta_id, numero_factura, fecha_emision)

        flash(f"Venta procesada con éxito. Factura N° {numero_factura}", "success")
        return redirect(f"/ventas?venta_id={venta_id}")

    clientes = db.execute("SELECT * FROM Clientes")
    productos = db.execute("SELECT * FROM Productos")
    venta_id = request.args.get("venta_id")
    return render_template("ventas.html", clientes=clientes, productos=productos, venta_id=venta_id)



# FinVentas

# Factura

@app.route("/factura", methods=["GET", "POST"])
@login_required
def factura():
    clientes = db.execute("SELECT * FROM Clientes")
    cliente_seleccionado = None
    compras = []
    total_general = 0

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        if not cliente_id:
            flash("Seleccione un cliente", "error")
            return redirect("/factura")


        cliente_seleccionado = db.execute(
            "SELECT * FROM Clientes WHERE id = ?", cliente_id)
        if not cliente_seleccionado:
            flash("Cliente no encontrado", "error")
            return redirect("/factura")
        cliente_seleccionado = cliente_seleccionado[0]

        ultima_venta = db.execute("""
            SELECT id, fecha FROM Ventas
            WHERE cliente_id = ?
            ORDER BY fecha DESC
            LIMIT 1
        """, cliente_id)

        if not ultima_venta:
            flash(f"El cliente {
                  cliente_seleccionado['nombre']} no tiene ventas registradas.", "info")
        else:
            id_venta = ultima_venta[0]["id"]
            compras = db.execute("""
                SELECT Productos.nombre AS producto,
                       DetalleVenta.cantidad,
                       Productos.precio AS precio_unitario,
                       (DetalleVenta.cantidad * Productos.precio) AS total,
                       Ventas.fecha  # Añadir la fecha de la venta aquí
                FROM DetalleVenta
                JOIN Productos ON DetalleVenta.producto_id = Productos.id
                JOIN Ventas ON DetalleVenta.venta_id = Ventas.id  # Unir con la tabla de ventas
                WHERE DetalleVenta.venta_id = ?
            """, id_venta)

            total_general = sum(compra["total"] for compra in compras)

    return render_template(
        "factura.html",
        clientes=clientes,
        cliente_seleccionado=cliente_seleccionado,
        compras=compras,
        total_general=total_general
    )

@app.route("/factura/pdf", methods=["POST"])
@login_required
def factura_pdf():
    cliente_id = request.form.get("cliente_id")
    if not cliente_id:
        flash("Seleccione un cliente", "error")
        return redirect("/factura")


    cliente = db.execute("SELECT * FROM Clientes WHERE id = ?", cliente_id)[0]

    compras = db.execute("""
        SELECT Ventas.fecha, Productos.nombre AS producto, DetalleVenta.cantidad,
               Productos.precio AS precio_unitario,
               (DetalleVenta.cantidad * Productos.precio) AS total
        FROM Ventas
        JOIN DetalleVenta ON Ventas.id = DetalleVenta.venta_id
        JOIN Productos ON DetalleVenta.producto_id = Productos.id
        WHERE Ventas.cliente_id = ?
        ORDER BY Ventas.fecha DESC
    """, cliente_id)

    total_general = sum(compra["total"] for compra in compras)


    resultado = db.execute("SELECT numero_factura FROM Facturas ORDER BY id DESC LIMIT 1")
    if resultado:
        import re
        match = re.search(r'\d+', resultado[0]["numero_factura"])
        base = int(match.group()) if match else 0
        nuevo_numero = f"F{base + 1:04d}"
    else:
        nuevo_numero = "F0001"

    fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_mostrar = datetime.now().strftime("%d de %B de %Y")


    db.execute(
        "INSERT INTO Facturas (venta_id, numero_factura, fecha_emision) VALUES (?, ?, ?)",
        None, nuevo_numero, fecha_emision
    )

    rendered = render_template(
        "factura_pdf.html",
        cliente=cliente,
        productos=compras,
        total_general=total_general,
        numero_factura=nuevo_numero,
        fecha_emision=fecha_mostrar,
        as_url=url_for('static', filename='as.png', _external=True)
    )

    pdf = HTML(string=rendered).write_pdf()

    archivo_pdf = f"Historial_{cliente['nombre'].replace(' ', '_')}_{nuevo_numero}.pdf"
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={archivo_pdf}"
    return response



@app.route("/factura/pdf/<int:venta_id>")
@login_required
def factura_pdf_unica(venta_id):
    # Obtener venta y cliente
    venta = db.execute("SELECT * FROM Ventas WHERE id = ?", venta_id)[0]
    cliente = db.execute("SELECT * FROM Clientes WHERE id = ?", venta["cliente_id"])[0]

    compras = db.execute("""
        SELECT Productos.nombre AS producto,
               DetalleVenta.cantidad,
               Productos.precio AS precio_unitario,
               (DetalleVenta.cantidad * Productos.precio) AS total,
               Ventas.fecha
        FROM DetalleVenta
        JOIN Productos ON DetalleVenta.producto_id = Productos.id
        JOIN Ventas ON DetalleVenta.venta_id = Ventas.id
        WHERE Ventas.id = ?
    """, venta_id)

    total_general = sum(c["total"] for c in compras)

    resultado = db.execute("SELECT numero_factura, fecha_emision FROM Facturas WHERE venta_id = ?", venta_id)
    if resultado:
        numero_factura = resultado[0]["numero_factura"]
        fecha_mostrar = datetime.strptime(resultado[0]["fecha_emision"], "%Y-%m-%d %H:%M:%S").strftime("%d de %B de %Y")
    else:

        ultimo = db.execute("SELECT numero_factura FROM Facturas ORDER BY id DESC LIMIT 1")
        if ultimo:
            import re
            match = re.search(r'\d+', ultimo[0]["numero_factura"])
            base = int(match.group()) if match else 0
            numero_factura = f"F{base + 1:04d}"
        else:
            numero_factura = "F0001"

        fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_mostrar = datetime.now().strftime("%d de %B de %Y")


        db.execute(
            "INSERT INTO Facturas (venta_id, numero_factura, fecha_emision) VALUES (?, ?, ?)",
            venta_id, numero_factura, fecha_emision
        )

    rendered = render_template(
        "factura_pdf.html",
        cliente=cliente,
        productos=compras,
        total_general=total_general,
        numero_factura=numero_factura,
        fecha_emision=fecha_mostrar,
        as_url=url_for('static', filename='as.png', _external=True)
    )

    pdf = HTML(string=rendered, base_url=request.base_url).write_pdf()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=Factura_{venta_id}.pdf"
    return response




@app.route("/factura/historial/pdf", methods=["POST"])
@login_required
def factura_historial_pdf():
    cliente_id = request.form.get("cliente_id")
    if not cliente_id:
        flash("Seleccione un cliente", "error")
        return redirect("/factura")


    cliente = db.execute("SELECT * FROM Clientes WHERE id = ?", cliente_id)[0]


    compras = db.execute("""
        SELECT Ventas.fecha, Productos.nombre AS producto, DetalleVenta.cantidad,
               Productos.precio AS precio_unitario,
               (DetalleVenta.cantidad * Productos.precio) AS total
        FROM Ventas
        JOIN DetalleVenta ON Ventas.id = DetalleVenta.venta_id
        JOIN Productos ON DetalleVenta.producto_id = Productos.id
        WHERE Ventas.cliente_id = ?
        ORDER BY Ventas.fecha DESC
    """, cliente_id)


    total_general = sum(compra["total"] for compra in compras)


    ultimo = db.execute("SELECT numero_factura FROM Facturas ORDER BY id DESC LIMIT 1")

    if ultimo:
        match = re.search(r'\d+', ultimo[0]["numero_factura"])
        numero_base = int(match.group()) if match else 0
        numero_factura = f"F{numero_base + 1:04d}"
    else:
        numero_factura = "F0001"


    fecha_emision_sql = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_emision_display = datetime.now().strftime("%d de %B de %Y")


    db.execute("""
        INSERT INTO Facturas (venta_id, numero_factura, fecha_emision)
        VALUES (?, ?, ?)
    """, None, numero_factura, fecha_emision_sql)

    rendered = render_template(
        "factura_pdf.html",
        cliente=cliente,
        productos=compras,
        total_general=total_general,
        numero_factura=numero_factura,
        fecha_emision=fecha_emision_display,
        as_url=url_for('static', filename='as.png', _external=True)
    )

    pdf = HTML(string=rendered).write_pdf()


    archivo_pdf = f"Historial_{cliente['nombre'].replace(' ', '_')}_{numero_factura}.pdf"
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={archivo_pdf}"
    return response

# FinFactura


if __name__ == "__main__":
    app.run(debug=True)
