import os
os.environ["PGCLIENTENCODING"] = "UTF8"
from flask import Flask, render_template, request, redirect, url_for, session #importar modulos necesarios de flask
from datetime import datetime #para manejar fechas 
import json, os #para manejar archivos y json 
from werkzeug.utils import secure_filename #para manejar nombres de archivos seguros
import locale
import json
import os
import threading
import webbrowser
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import db

load_dotenv()

print("DATABASE_URL =", repr(os.getenv("DATABASE_URL")))

#locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

RUTA_EXTINTORES = "extintores.json"  # Tu archivo está en la raíz del proyecto




def cargar_extintores():
    if not os.path.exists(RUTA_EXTINTORES): 
        return []
    with open(RUTA_EXTINTORES, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_extintores(lista):
    with open(RUTA_EXTINTORES, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

UPLOAD_FOLDER = "static/uploads" #carpeta para guardar las imagenes subidas 
os.makedirs(UPLOAD_FOLDER, exist_ok=True) #crear carpetas de subida si no existen 



app = Flask(__name__)
cloudinary.config(
  cloudinary_url = os.getenv('CLOUDINARY_URL')
)
app.secret_key = "clave_secreta_123"

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
if app.config["SQLALCHEMY_DATABASE_URI"] and app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
    # Render a veces da la URL como postgres://, pero SQLAlchemy necesita postgresql://
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

    # ========= CONFIGURACIÓN DE CORREO =========
    # ========= CONFIGURACIÓN DE CORREO (FORZADA) =========
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Cambiamos a 465
app.config['MAIL_USE_SSL'] = True # Cambiamos TLS por SSL
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'tabarescontabilidad@gmail.com'
app.config['MAIL_PASSWORD'] = 'vjapueleyptlstrc' # Tus 16 letras
app.config['MAIL_DEFAULT_SENDER'] = ('Notificaciones Tabares', 'tabarescontabilidad@gmail.com')

mail = Mail(app)

# ========= FUNCIÓN PARA ENVIAR CORREO =========
def enviar_correo(asunto, mensaje_html):
    with app.app_context():
        # Usamos app.config para asegurarnos de que use el correo de la empresa
        msg = Message(asunto, recipients=[app.config['MAIL_USERNAME']])
        msg.html = mensaje_html
        mail.send(msg)



# ========= FUNCIÓN PARA REVISAR EXTINTORES VENCIDOS =========
def revisar_extintores_vencidos():
    if not os.path.exists("extintores.json"):
        return

    with open("extintores.json", "r", encoding="utf-8") as archivo:
        extintores = json.load(archivo)

    # Asegurar campo notificado
    for e in extintores:
        if "notificado" not in e:
            e["notificado"] = False

    hoy = datetime.now().date()
    hubo_cambios = False  # 🔹 para saber si hay que guardar

    for e in extintores:
        if e["notificado"]:
            continue

        fecha_vencimiento = datetime.strptime(
            e["fecha_vencimiento"], "%Y-%m-%d"
        ).date()

        dias_restantes = (fecha_vencimiento - hoy).days

        if dias_restantes <= 0:
            asunto = "⛔ EXTINTOR VENCIDO"
        elif dias_restantes <= 7:
            asunto = "🚨 EXTINTOR POR VENCER"
        else:
            continue


        mensaje_html = f"""
        <div style="
            background-color:#f4f7fb;
            padding:40px;   
            font-family:Arial, sans-serif;
        ">
            <div style="
                max-width:500px;
                margin:auto;
                background:white;
                border-radius:14px;
                overflow:hidden;
                box-shadow:0px 8px 25px rgba(0,0,0,0.15);
            ">
                
                <div style="
                    background:linear-gradient(90deg, #0d6efd, #0b5ed7);
                    color:white;
                    padding:20px;
                    text-align:center;
                    font-size:20px;
                    font-weight:bold;
                ">
                    🚨 ALERTA DE EXTINTOR
                </div>

                <div style="padding:25px; color:#333;">
                    <p style="font-size:16px;"><strong>Número:</strong> {e["numero"]}</p>
                    <p><strong>Área:</strong> {e["area"]}</p>
                    <p><strong>Tipo:</strong> {e["tipo"]}</p>
                    <p><strong>Capacidad:</strong> {e["capacidad"]}</p>
                    <p><strong>Fecha vencimiento:</strong> {e["fecha_vencimiento"]}</p>

                    <div style="
                        margin-top:20px;
                        padding:15px;
                        border-radius:10px;
                        background-color:{'#ffdddd' if dias_restantes <= 0 else '#fff3cd'};
                        color:{'#b02a37' if dias_restantes <= 0 else '#856404'};
                        text-align:center;
                        font-weight:bold;
                        font-size:16px;
                    ">
                        {'EXTINTOR VENCIDO ⛔' if dias_restantes <= 0 else f'VENCE EN {dias_restantes} DÍAS ⚠️'}
                    </div>
                </div>

                <div style="
                    background:#f1f1f1;
                    text-align:center;
                    padding:15px;
                    font-size:13px;
                    color:#555;
                ">
                    Sistema de Gestión de Seguridad • ChipCore
                </div>
            </div>
        </div>
        """

        enviar_correo(asunto, mensaje_html)


    # ✅ MARCAR COMO NOTIFICADO
        e["notificado"] = True
        hubo_cambios = True

    if hubo_cambios:
        with open("extintores.json", "w", encoding="utf-8") as f:
            json.dump(extintores, f, indent=4, ensure_ascii=False)

    # ✅ GUARDAR LOS CAMBIOS AL ARCHIVO
    with open("extintores.json", "w", encoding="utf-8") as f:
        json.dump(extintores, f, indent=4, ensure_ascii=False)




# ========== USUARIOS ==========
#usuarios predefinidos con sus roles y contraseñas 
usuarios = {
    "angel": {"password": "1", "rol": "admin"},
    "luis": {"password": "1", "rol": "admin"},
    "karen": {"password": "1", "rol": "admin"}
}

# ========== ARCHIVO DE FICHAS ==========
#nombre del archivo json donde se guardan las fichas 
DATA_FILE = "fichas.json"

#carga las fichas desde el archivo json
def cargar_fichas():
    """Carga las fichas desde el archivo JSON."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


#guarda las fichas en el archivo json 
def guardar_fichas(fichas):
    """Guarda las fichas en el archivo JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(fichas, f, indent=4, ensure_ascii=False)

# ========== RUTA PRINCIPAL ==========
#ruta para la pagina principal
@app.route("/")
def home():
    return redirect(url_for("login"))



# ========== LOGIN ==========
#ruta para el login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]

        if usuario in usuarios and usuarios[usuario]["password"] == contrasena:
            session["usuario"] = usuario
            session["rol"] = usuarios[usuario]["rol"]

            if session["rol"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("empleado_dashboard"))
        else:
            return "❌ Usuario o contraseña incorrectos"

    return render_template("login.html")

# ========== PANEL ADMIN ==========
#ruta para el panel de control del admin
@app.route("/admin/dashboard")
def admin_dashboard():
    if "rol" in session and session["rol"] == "admin":
        return render_template("panel_control_adminl.html")
    return redirect(url_for("login"))

# ========== FICHAS (ADMIN) ==========
#ruta para la lista de fichas (solo admin) 
@app.route("/admin/fichas")
def admin_fichas():
    if "rol" in session and session["rol"] == "admin":
        fichas = cargar_fichas()
        return render_template("fichas_lista.html", fichas=fichas)
    return redirect(url_for("login"))


# 🔹 Nueva ficha (solo admin) 
@app.route("/admin/fichas/nueva", methods=["GET", "POST"])
def nueva_ficha():
    if "rol" in session and session["rol"] == "admin":
        if request.method == "POST":
            fichas = cargar_fichas()

            imagen_maquina = request.files.get("imagen_maquina")
            ruta_img_maquina = None
            
            if imagen_maquina and imagen_maquina.filename != '':
                try:
                    # 1. Subir directamente a Cloudinary
                    upload_result = cloudinary.uploader.upload(imagen_maquina)
                    # 2. Guardamos la URL segura que nos da la nube
                    ruta_img_maquina = upload_result["secure_url"]
                    print(f"✅ Imagen subida a Cloudinary: {ruta_img_maquina}")
                except Exception as e:
                    print(f"❌ Error al subir a Cloudinary: {e}")
                    ruta_img_maquina = None

            # Leer los accesorios (separados por coma)
            accesorios_texto = request.form.get("accesorios", "")
            accesorios_lista = [a.strip() for a in accesorios_texto.split(",") if a.strip()]

            # Crear historial si se llenaron datos
            historial = []
            if request.form.get("historial_fecha") or request.form.get("historial_tipo"):
                historial.append({
                    "fecha": request.form.get("historial_fecha"),
                    "tipo": request.form.get("historial_tipo"),
                    "descripcion": request.form.get("historial_descripcion"),
                    "responsable": request.form.get("historial_responsable"),
                    "observacion": request.form.get("historial_observacion")
                })

            # Crear nueva ficha con todos los datos
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
                "historial": historial,
                "imagen_maquina": ruta_img_maquina  # Aquí se guarda el link de la nube
            }
            fichas.append(nueva)
            guardar_fichas(fichas)
            return redirect(url_for("admin_fichas"))

        return render_template("ficha_form.html")
    return redirect(url_for("login"))

@app.route("/admin/fichas/<codigo>/agregar_historial", methods=["GET", "POST"])
def agregar_historial(codigo):
    if "rol" in session and session["rol"] == "admin":
        fichas = cargar_fichas()
        ficha = next((f for f in fichas if f["codigo"] == codigo), None)

        if not ficha:
            return "Ficha no encontrada", 404

        if request.method == "POST":
            nuevo_historial = {
                "fecha": request.form.get("fecha"),
                "tipo": request.form.get("tipo"),
                "descripcion": request.form.get("descripcion"),
                "responsable": request.form.get("responsable"),
                "observacion": request.form.get("observacion")
            }

            # ✅ Asegurar que historial exista
            if "historial" not in ficha or ficha["historial"] is None:
                ficha["historial"] = []

            # ✅ Agregar correctamente
            ficha["historial"].append(nuevo_historial)
            guardar_fichas(fichas)

            return redirect(url_for("ver_ficha", codigo=codigo))

        return render_template("agregar_historial.html", ficha=ficha)

    return redirect(url_for("login"))


@app.route("/fichas/<codigo>/editar", methods=["GET", "POST"])
def editar_ficha(codigo):
    if "rol" in session and session["rol"] == "admin":
        fichas = cargar_fichas()
        ficha = next((f for f in fichas if f["codigo"] == codigo), None)


        if not ficha:
            return "❌ Ficha no encontrada"

        if request.method == "POST":
            # ✅ Actualizar todos los campos principales
            ficha["nombre"] = request.form.get("nombre")
            ficha["fabricante"] = request.form.get("fabricante")
            ficha["modelo"] = request.form.get("modelo")
            ficha["operador"] = request.form.get("operador")
            ficha["anio"] = request.form.get("anio")
            ficha["ubicacion"] = request.form.get("ubicacion")
            ficha["peso"] = request.form.get("peso")
            ficha["altura"] = request.form.get("altura")
            ficha["ancho"] = request.form.get("ancho")
            ficha["largo"] = request.form.get("largo")
            ficha["voltaje"] = request.form.get("voltaje")
            ficha["motor_hp"] = request.form.get("motor_hp")
            ficha["fuerza"] = request.form.get("fuerza")
            ficha["velocidad_inicial"] = request.form.get("velocidad_inicial")
            ficha["velocidad_final"] = request.form.get("velocidad_final")
            ficha["tipo_lubricacion"] = request.form.get("tipo_lubricacion")
            ficha["funcionamiento"] = request.form.get("funcionamiento")
            ficha["partes_requeridas"] = request.form.get("partes_requeridas")
            ficha["recomendaciones"] = request.form.get("recomendaciones")
            ficha["accesorios"] = [a.strip() for a in request.form.get("accesorios", "").split(",") if a.strip()]

            # ✅ Editar historial de mantenimiento existente
            historiales_actualizados = []
            for i in range(len(ficha.get("historial", []))):
                fecha = request.form.get(f"historial_fecha_{i}")
                tipo = request.form.get(f"historial_tipo_{i}")
                descripcion = request.form.get(f"historial_descripcion_{i}")
                responsable = request.form.get(f"historial_responsable_{i}")
                observacion = request.form.get(f"historial_observacion_{i}")

                if any([fecha, tipo, descripcion, responsable, observacion]):
                    historiales_actualizados.append({
                        "fecha": fecha,
                        "tipo": tipo,   
                        "descripcion": descripcion,
                        "responsable": responsable,
                        "observacion": observacion
                    })

            ficha["historial"] = historiales_actualizados

            # ===== MANEJO DE IMAGEN (OPCIONAL) =====
            imagen = request.files.get("imagen_maquina")

            if imagen and imagen.filename:
                nombre_seguro = secure_filename(imagen.filename)
                ruta_imagen = os.path.join("static", "uploads", nombre_seguro)
                imagen.save(ruta_imagen)

                ficha["imagen_maquina"] = nombre_seguro
            # Si no se sube imagen, NO se toca la imagen existente


            guardar_fichas(fichas)  
            return redirect(url_for("ver_ficha", codigo=codigo))

        return render_template("editar_ficha.html", ficha=ficha)
    return redirect(url_for("login"))





# 🔹 Ver ficha (admin y empleado pueden acceder) 

@app.route("/fichas/<codigo>")
def ver_ficha(codigo):
    if "rol" in session and session["rol"] in ["admin", "empleado"]:
        fichas = cargar_fichas()
        ficha = next((f for f in fichas if f["codigo"] == codigo), None)
        if ficha:
            return render_template("ficha_maquina.html", ficha=ficha)
        return "Ficha no encontrada"
    return redirect(url_for("login"))

# ========== LOGOUT ==========
#ruta para cerrar sesion
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



#ruta para formatear fechas en plantillas
@app.template_filter('datetimeformat') 
def datetimeformat(value, format='%B %Y'): #formatear fecha a formato legible en español
    if isinstance(value, str): #si el valor es una cadena, convertirlo a objeto datetime
        value = datetime.strptime(value, '%Y-%m-%d') #formato esperado en el JSON
    return value.strftime(format) #devolver fecha formateada

#ruta para editar la fecha de vencimiento de un extintor
@app.route("/extintores/editar/<int:numero>", methods=["GET", "POST"])
def editar_extintor(numero): #editar la fecha de vencimiento de un extintor
    # 1. Cargar lista de extintores desde tu JSON
    extintores = cargar_extintores()

    # 2. Buscar el extintor por el número
    extintor = next((e for e in extintores if int(e["numero"]) == int(numero)), None)

    if not extintor: 
        return "❌ Extintor no encontrado"

    # 3. Si se envía el formulario, actualizar la fecha
    if request.method == "POST":
        nueva_fecha = request.form.get("fecha") 
        extintor["fecha_vencimiento"] = nueva_fecha

        guardar_extintores(extintores)
        return redirect(url_for("admin_equipos"))  # ← Asegúrate que tu vista se llama así

    # 4. Mostrar HTML de edición
    return render_template("editar_extintor.html", extintor=extintor)



#ruta para la pagina de administracion de equipos de emergencia (extintores y camillas)
@app.route("/admin/equipos")
def admin_equipos(): 
    if "rol" in session and session["rol"] == "admin":

        #Cargar los extintores desde el JSON
        extintores = cargar_extintores()

        hoy = datetime.today().date()
        lista = []

        # Procesar cada extintor para determinar su estado
        for extintor in extintores:
            fecha_v = datetime.strptime(extintor["fecha_vencimiento"], "%Y-%m-%d").date()
            dias_restantes = (fecha_v - hoy).days

            # Determinar estado y clase CSS
            if dias_restantes < 0:
                estado = "Vencido"
                clase = "vencido"
            elif dias_restantes <= 15:
                estado = f"Vence en {dias_restantes} días"
                clase = "por-vencer"
            else:
                estado = f"Vigente ({dias_restantes} días restantes)"
                clase = "vigente"

            # Construir la lista con la información necesaria
            lista.append({
                "area": extintor["area"],
                "numero": extintor["numero"],
                "tipo": extintor["tipo"],
                "capacidad": extintor["capacidad"],
                "fecha": extintor["fecha_vencimiento"],
                "estado": estado,
                "clase": clase
            })

        # Renderizar la plantilla con la lista procesada
        return render_template("extintores_index.html", extintores=lista)

    # Si no es admin, redirigir al login
    return redirect(url_for("login"))


# ========== MAIN ==========
#ejecutar la aplicacion

# ========= PRUEBA DE ENVÍO DE CORREO =========
# ========= PRUEBA DE ENVÍO DE CORREO =========
@app.route("/probar-correo")
def probar_correo():
    try:
        destinatario = app.config['MAIL_USERNAME']
        msg = Message(
            subject="🚨 ALERTA SISTEMA TABARES",
            recipients=[destinatario],
            body=f"Este correo debe llegar a {destinatario}. Si lo ves, el sistema está listo."
        )
        mail.send(msg)
        return f"✅ Correo enviado a {destinatario}. Revisa la bandeja de entrada y SPAM."
    except Exception as e:
        return f"❌ Error al enviar correo: {str(e)}"


# Mueve la revisión aquí arriba para que corra siempre al iniciar
with app.app_context():
    try:
        revisar_extintores_vencidos()
        print("✅ Revisión de extintores completada al iniciar.")
    except Exception as e:
        print(f"⚠️ No se pudo revisar extintores: {e}")

if __name__ == "__main__":
    # En tu PC seguirá funcionando con debug
    app.run(debug=True)



