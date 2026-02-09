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
from models import db, Maquina, Extintor

load_dotenv()

app = Flask(__name__)

# CONFIGURACIÓN CLOUDINARY
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

# --- UTILIDADES ---

def enviar_correo(asunto, mensaje_html):
    with app.app_context():
        msg = Message(asunto, recipients=[app.config['MAIL_USERNAME']])
        msg.html = mensaje_html
        mail.send(msg)

# Usuarios estáticos (Podrías moverlos a la DB luego si quieres)
usuarios = {
    "administrador": {"password": "tabares2026", "rol": "admin"},
    "empleado": {"password": "tabares123", "rol": "empleado"}
}

# --- RUTAS DE AUTENTICACIÓN ---

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if "rol" in session and session["rol"] == "admin":
        return render_template("panel_control_adminl.html")
    return redirect(url_for("login"))

# --- RUTAS DE FICHAS TÉCNICAS (MÁQUINAS) ---

@app.route("/admin/fichas")
def admin_fichas():
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        # Consulta directa a la DB
        fichas = Maquina.query.all()
        # Convertimos accesorios e historial de JSON string a lista para el HTML
        for f in fichas:
            f.accesorios_list = json.loads(f.accesorios) if f.accesorios else []
        return render_template("fichas_lista.html", fichas=fichas)
    return redirect(url_for("login"))

@app.route("/admin/fichas/nueva", methods=["GET", "POST"])
def nueva_ficha():
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        if request.method == "POST":
            imagen_maquina = request.files.get("imagen_maquina")
            ruta_img_maquina = None
            
            if imagen_maquina and imagen_maquina.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(imagen_maquina)
                    ruta_img_maquina = upload_result["secure_url"]
                except Exception as e:
                    print(f"❌ Error Cloudinary: {e}")

            # Procesar accesorios como lista -> JSON String
            accesorios_lista = [a.strip() for a in request.form.get("accesorios", "").split(",") if a.strip()]
            
            nueva = Maquina(
                codigo=request.form.get("codigo"),
                nombre=request.form.get("nombre"),
                ubicacion=request.form.get("ubicacion"),
                fabricante=request.form.get("fabricante"),
                modelo=request.form.get("modelo"),
                operador=request.form.get("operador"),
                anio=request.form.get("anio"),
                peso=request.form.get("peso"),
                altura=request.form.get("altura"),
                ancho=request.form.get("ancho"),
                largo=request.form.get("largo"),
                voltaje=request.form.get("voltaje"),
                motor_hp=request.form.get("motor_hp"),
                fuerza=request.form.get("fuerza"),
                velocidad_inicial=request.form.get("velocidad_inicial"),
                velocidad_final=request.form.get("velocidad_final"),
                tipo_lubricacion=request.form.get("tipo_lubricacion"),
                funcionamiento=request.form.get("funcionamiento"),
                partes_requeridas=request.form.get("partes_requeridas"),
                recomendaciones=request.form.get("recomendaciones"),
                accesorios=json.dumps(accesorios_lista),
                historial=json.dumps([]),
                imagen_maquina=ruta_img_maquina
            )
            db.session.add(nueva)
            db.session.commit()
            return redirect(url_for("admin_fichas"))
        return render_template("ficha_form.html")
    return redirect(url_for("login"))

@app.route("/fichas/<codigo>")
def ver_ficha(codigo):
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        ficha = Maquina.query.filter_by(codigo=codigo).first()
        if ficha:
            # --- CORRECCIÓN DE ACCESORIOS ---
            try:
                # Si es un string que parece JSON (tiene []), lo convertimos a lista
                if isinstance(ficha.accesorios, str) and "[" in ficha.accesorios:
                    ficha.accesorios_list = json.loads(ficha.accesorios)
                else:
                    # Si ya es lista o es un formato simple, lo manejamos así
                    ficha.accesorios_list = [ficha.accesorios] if ficha.accesorios else []
            except Exception:
                ficha.accesorios_list = []

            # --- CORRECCIÓN DE HISTORIAL ---
            try:
                if isinstance(ficha.historial, str) and "[" in ficha.historial:
                    ficha.historial_list = json.loads(ficha.historial)
                else:
                    ficha.historial_list = []
            except Exception:
                ficha.historial_list = []
            
            return render_template("ficha_maquina.html", ficha=ficha)
        return "Ficha no encontrada", 404
    return redirect(url_for("login"))

@app.route("/fichas/<codigo>/editar", methods=["GET", "POST"])
def editar_ficha(codigo):
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        ficha = Maquina.query.filter_by(codigo=codigo).first()
        if not ficha: return "❌ Ficha no encontrada", 404

        if request.method == "POST":
            ficha.nombre = request.form.get("nombre")
            ficha.fabricante = request.form.get("fabricante")
            ficha.modelo = request.form.get("modelo")
            ficha.operador = request.form.get("operador")
            ficha.anio = request.form.get("anio")
            ficha.ubicacion = request.form.get("ubicacion")
            ficha.peso = request.form.get("peso")
            ficha.altura = request.form.get("altura")
            ficha.ancho = request.form.get("ancho")
            ficha.largo = request.form.get("largo")
            ficha.voltaje = request.form.get("voltaje")
            ficha.motor_hp = request.form.get("motor_hp")
            ficha.fuerza = request.form.get("fuerza")
            ficha.velocidad_inicial = request.form.get("velocidad_inicial")
            ficha.velocidad_final = request.form.get("velocidad_final")
            ficha.tipo_lubricacion = request.form.get("tipo_lubricacion")
            ficha.funcionamiento = request.form.get("funcionamiento")
            ficha.partes_requeridas = request.form.get("partes_requeridas")
            ficha.recomendaciones = request.form.get("recomendaciones")
            
            accesorios_lista = [a.strip() for a in request.form.get("accesorios", "").split(",") if a.strip()]
            ficha.accesorios = json.dumps(accesorios_lista)

            imagen = request.files.get("imagen_maquina")
            if imagen and imagen.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(imagen)
                    ficha.imagen_maquina = upload_result["secure_url"]
                except Exception as e:
                    print(f"❌ Error Cloudinary Edit: {e}")

            db.session.commit()
            return redirect(url_for("ver_ficha", codigo=codigo))
        
        # Para el template de edición, convertimos el JSON a string separado por comas
        ficha.accesorios_str = ", ".join(json.loads(ficha.accesorios)) if ficha.accesorios else ""
        return render_template("editar_ficha.html", ficha=ficha)
    return redirect(url_for("login"))

@app.route("/admin/fichas/<codigo>/agregar_historial", methods=["GET", "POST"])
def agregar_historial(codigo):
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        ficha = Maquina.query.filter_by(codigo=codigo).first()
        if not ficha: return "Ficha no encontrada", 404
        
        if request.method == "POST":
            nuevo_evento = {
                "fecha": request.form.get("fecha"),
                "tipo": request.form.get("tipo"),
                "descripcion": request.form.get("descripcion"),
                "responsable": request.form.get("responsable"),
                "observacion": request.form.get("observacion")
            }
            # Cargar historial actual, añadir y guardar
            historial_actual = json.loads(ficha.historial) if ficha.historial else []
            historial_actual.append(nuevo_evento)
            ficha.historial = json.dumps(historial_actual)
            
            db.session.commit()
            return redirect(url_for("ver_ficha", codigo=codigo))
        return render_template("agregar_historial.html", ficha=ficha)
    return redirect(url_for("login"))

# --- RUTAS DE EQUIPOS (EXTINTORES) ---

@app.route("/admin/equipos")
def admin_equipos(): 
    if "rol" in session and session["rol"] == "admin":
        extintores = Extintor.query.order_by(Extintor.numero).all()
        hoy = datetime.today().date()
        lista_final = []
        
        for e in extintores:
            try:
                fecha_v = datetime.strptime(e.fecha_vencimiento, "%Y-%m-%d").date()
                dias = (fecha_v - hoy).days
                estado = "Vencido" if dias < 0 else f"Vence en {dias} días" if dias <= 15 else "Vigente"
                clase = "vencido" if dias < 0 else "por-vencer" if dias <= 15 else "vigente"
            except:
                estado, clase = "Error Fecha", ""

            lista_final.append({
                "id": e.id,
                "numero": e.numero,
                "area": e.area,
                "tipo": e.tipo,
                "capacidad": e.capacidad,
                "fecha": e.fecha_vencimiento,
                "estado": estado,
                "clase": clase
            })
        return render_template("extintores_index.html", extintores=lista_final)
    return redirect(url_for("login"))

@app.route("/extintores/editar/<int:numero>", methods=["GET", "POST"])
def editar_extintor(numero):
    if "rol" in session and session["rol"] == "admin":
        extintor = Extintor.query.filter_by(numero=numero).first()
        if not extintor: return "❌ Extintor no encontrado", 404
            
        if request.method == "POST":
            extintor.fecha_vencimiento = request.form.get("fecha")
            extintor.notificado = False # Resetear notificación al actualizar fecha
            db.session.commit()
            return redirect(url_for("admin_equipos"))
            
        return render_template("editar_extintor.html", extintor=extintor)
    return redirect(url_for("login"))

# --- FILTROS Y EXTRAS ---

@app.template_filter('datetimeformat') 
def datetimeformat(value, format='%d/%m/%Y'):
    if not value:
        return ""
    # Si ya es un objeto datetime, lo formateamos
    if isinstance(value, datetime):
        return value.strftime(format)
    # Si es un string, intentamos convertirlo
    if isinstance(value, str):
        try:
            # Intentamos el formato estándar de la DB
            fecha_dt = datetime.strptime(value, '%Y-%m-%d')
            return fecha_dt.strftime(format)
        except:
            # Si falla, devolvemos el texto original para no romper la app
            return value
    return value

if __name__ == "__main__":
    app.run(debug=True)
