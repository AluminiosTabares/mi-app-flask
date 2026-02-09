import os
os.environ["PGCLIENTENCODING"] = "UTF8"
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime 
import json
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from models import db

load_dotenv()

# Configuración de Archivos
RUTA_EXTINTORES = "extintores.json"
DATA_FILE = "fichas.json"

def cargar_extintores():
    if not os.path.exists(RUTA_EXTINTORES): 
        return []
    with open(RUTA_EXTINTORES, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_extintores(lista):
    with open(RUTA_EXTINTORES, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

def cargar_fichas():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_fichas(fichas):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(fichas, f, indent=4, ensure_ascii=False)

app = Flask(__name__)

# Configuración Cloudinary
# Configuración Cloudinary simplificada
cloudinary.config( 
    cloudinary_url = os.environ.get('CLOUDINARY_URL') 
)

app.secret_key = "clave_secreta_123"

# Configuración DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
if app.config["SQLALCHEMY_DATABASE_URI"] and app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Configuración Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'tabarescontabilidad@gmail.com'
app.config['MAIL_PASSWORD'] = 'vjapueleyptlstrc'
app.config['MAIL_DEFAULT_SENDER'] = ('Notificaciones Tabares', 'tabarescontabilidad@gmail.com')

mail = Mail(app)

def enviar_correo(asunto, mensaje_html):
    with app.app_context():
        msg = Message(asunto, recipients=[app.config['MAIL_USERNAME']])
        msg.html = mensaje_html
        mail.send(msg)

def revisar_extintores_vencidos():
    if not os.path.exists(RUTA_EXTINTORES): return
    extintores = cargar_extintores()
    hoy = datetime.now().date()
    hubo_cambios = False

    for e in extintores:
        if e.get("notificado"): continue
        fecha_v = datetime.strptime(e["fecha_vencimiento"], "%Y-%m-%d").date()
        dias = (fecha_v - hoy).days
        
        if dias <= 0 or dias <= 7:
            asunto = "⛔ EXTINTOR VENCIDO" if dias <= 0 else "🚨 EXTINTOR POR VENCER"
            # (Aquí va tu mensaje_html largo que ya tienes...)
            # Por brevedad no repito todo el HTML del correo aquí
            e["notificado"] = True
            hubo_cambios = True

    if hubo_cambios:
        guardar_extintores(extintores)

# ========== USUARIOS ==========
usuarios = {
    "administrador": {"password": "tabares2026", "rol": "admin"},
    "empleado": {"password": "tabares123", "rol": "empleado"}
}

# ========== RUTAS DE ACCESO ==========

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].lower()
        contrasena = request.form["contrasena"]

        if usuario in usuarios and usuarios[usuario]["password"] == contrasena:
            session["usuario"] = usuario
            session["rol"] = usuarios[usuario]["rol"]

            if session["rol"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("admin_fichas")) 
        else:
            return "❌ Usuario o contraseña incorrectos"
    return render_template("login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "rol" in session and session["rol"] == "admin":
        return render_template("panel_control_adminl.html")
    return redirect(url_for("login"))

# ========== GESTIÓN DE FICHAS (ADMIN Y EMPLEADO) ==========

@app.route("/admin/fichas")
def admin_fichas():
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        fichas = cargar_fichas()
        return render_template("fichas_lista.html", fichas=fichas)
    return redirect(url_for("login"))

# ========== MODIFICACIÓN DE RUTA: NUEVA FICHA ==========
@app.route("/admin/fichas/nueva", methods=["GET", "POST"])
def nueva_ficha():
    # El empleado y el admin pueden entrar aquí
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        if request.method == "POST":
            fichas = cargar_fichas()
            imagen_maquina = request.files.get("imagen_maquina")
            ruta_img_maquina = None
            
            if imagen_maquina and imagen_maquina.filename != '':
                try:
                    # Subida a Cloudinary
                    upload_result = cloudinary.uploader.upload(imagen_maquina)
                    ruta_img_maquina = upload_result["secure_url"]
                except Exception as e:
                    print(f"❌ Error Cloudinary: {e}")

            accesorios_lista = [a.strip() for a in request.form.get("accesorios", "").split(",") if a.strip()]

            nueva = {
                "codigo": request.form.get("codigo"),
                "nombre": request.form.get("nombre"),
                "ubicacion": request.form.get("ubicacion"),
                "fabricante": request.form.get("fabricante"),
                "modelo": request.form.get("modelo"),
                "operador": request.form.get("operador"),
                "anio": request.form.get("anio"),
                "peso": request.form.get("peso"),
                "altura": request.form.get("altura"),
                "ancho": request.form.get("ancho"),
                "largo": request.form.get("largo"),
                "voltaje": request.form.get("voltaje"),
                "motor_hp": request.form.get("motor_hp"),
                "fuerza": request.form.get("fuerza"),
                "velocidad_inicial": request.form.get("velocidad_inicial"),
                "velocidad_final": request.form.get("velocidad_final"),
                "tipo_lubricacion": request.form.get("tipo_lubricacion"),
                "funcionamiento": request.form.get("funcionamiento"),
                "partes_requeridas": request.form.get("partes_requeridas"),
                "recomendaciones": request.form.get("recomendaciones"),
                "accesorios": accesorios_lista,
                "historial": [],
                "imagen_maquina": ruta_img_maquina
            }
            fichas.append(nueva)
            guardar_fichas(fichas)
            return redirect(url_for("admin_fichas"))
        return render_template("ficha_form.html")
    return redirect(url_for("login"))

# ========== MODIFICACIÓN DE RUTA: EDITAR FICHA (CORREGIDA LA IMAGEN) ==========
@app.route("/fichas/<codigo>/editar", methods=["GET", "POST"])
def editar_ficha(codigo):
    # El empleado y el admin pueden entrar aquí
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        fichas = cargar_fichas()
        ficha = next((f for f in fichas if f["codigo"] == codigo), None)
        if not ficha: return "❌ Ficha no encontrada"

        if request.method == "POST":
            # Actualizamos datos de texto
            campos = ["nombre", "fabricante", "modelo", "operador", "anio", "ubicacion", "peso", "altura", "ancho", "largo", "voltaje", "motor_hp", "fuerza", "velocidad_inicial", "velocidad_final", "tipo_lubricacion", "funcionamiento", "partes_requeridas", "recomendaciones"]
            for campo in campos:
                ficha[campo] = request.form.get(campo)
            
            ficha["accesorios"] = [a.strip() for a in request.form.get("accesorios", "").split(",") if a.strip()]

            # CORRECCIÓN DE IMAGEN: Subir a Cloudinary si se selecciona una nueva
            imagen = request.files.get("imagen_maquina")
            if imagen and imagen.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(imagen)
                    ficha["imagen_maquina"] = upload_result["secure_url"]
                    print(f"✅ Nueva imagen subida: {ficha['imagen_maquina']}")
                except Exception as e:
                    print(f"❌ Error al actualizar imagen en Cloudinary: {e}")

            guardar_fichas(fichas)  
            return redirect(url_for("ver_ficha", codigo=codigo))
        return render_template("editar_ficha.html", ficha=ficha)
    return redirect(url_for("login"))
    return redirect(url_for("login"))

@app.route("/admin/fichas/<codigo>/agregar_historial", methods=["GET", "POST"])
def agregar_historial(codigo):
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        fichas = cargar_fichas()
        ficha = next((f for f in fichas if f["codigo"] == codigo), None)
        if not ficha: return "Ficha no encontrada", 404

        if request.method == "POST":
            nuevo = {
                "fecha": request.form.get("fecha"),
                "tipo": request.form.get("tipo"),
                "descripcion": request.form.get("descripcion"),
                "responsable": request.form.get("responsable"),
                "observacion": request.form.get("observacion")
            }
            if "historial" not in ficha: ficha["historial"] = []
            ficha["historial"].append(nuevo)
            guardar_fichas(fichas)
            return redirect(url_for("ver_ficha", codigo=codigo))
        return render_template("agregar_historial.html", ficha=ficha)
    return redirect(url_for("login"))

@app.route("/fichas/<codigo>")
def ver_ficha(codigo):
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        fichas = cargar_fichas()
        ficha = next((f for f in fichas if f["codigo"] == codigo), None)
        if ficha: return render_template("ficha_maquina.html", ficha=ficha)
        return "Ficha no encontrada"
    return redirect(url_for("login"))

# ========== GESTIÓN DE EXTINTORES (SOLO ADMIN) ==========

@app.route("/admin/equipos")
def admin_equipos(): 
    if "rol" in session and session["rol"] == "admin":
        extintores = cargar_extintores()
        hoy = datetime.today().date()
        lista = []
        for e in extintores:
            fecha_v = datetime.strptime(e["fecha_vencimiento"], "%Y-%m-%d").date()
            dias = (fecha_v - hoy).days
            estado = "Vencido" if dias < 0 else f"Vence en {dias} días" if dias <= 15 else "Vigente"
            clase = "vencido" if dias < 0 else "por-vencer" if dias <= 15 else "vigente"
            lista.append({**e, "estado": estado, "clase": clase, "fecha": e["fecha_vencimiento"]})
        return render_template("extintores_index.html", extintores=lista)
    
    if "usuario" in session:
        return "⚠️ Acceso denegado: Solo el administrador puede gestionar extintores.", 403
    return redirect(url_for("login"))

@app.route("/extintores/editar/<int:numero>", methods=["GET", "POST"])
def editar_extintor(numero):
    if "rol" in session and session["rol"] == "admin":
        extintores = cargar_extintores()
        extintor = next((e for e in extintores if int(e["numero"]) == numero), None)
        if not extintor: return "❌ Extintor no encontrado"
        if request.method == "POST":
            extintor["fecha_vencimiento"] = request.form.get("fecha")
            guardar_extintores(extintores)
            return redirect(url_for("admin_equipos"))
        return render_template("editar_extintor.html", extintor=extintor)
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.template_filter('datetimeformat') 
def datetimeformat(value, format='%B %Y'):
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d')
    return value.strftime(format)

with app.app_context():
    try:
        revisar_extintores_vencidos()
    except Exception as e:
        print(f"⚠️ Error revisión: {e}")

if __name__ == "__main__":
    app.run(debug=True)
