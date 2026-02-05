from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Maquina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200))
    ubicacion = db.Column(db.String(100))
    fabricante = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    operador = db.Column(db.String(100))
    anio = db.Column(db.String(10))
    peso = db.Column(db.String(50))
    altura = db.Column(db.String(50))
    ancho = db.Column(db.String(50))
    largo = db.Column(db.String(50))
    voltaje = db.Column(db.String(50))
    motor_hp = db.Column(db.String(50))
    fuerza = db.Column(db.String(50))
    velocidad_inicial = db.Column(db.String(50))
    velocidad_final = db.Column(db.String(50))
    tipo_lubricacion = db.Column(db.String(100))
    funcionamiento = db.Column(db.Text)
    partes_requeridas = db.Column(db.Text)
    recomendaciones = db.Column(db.Text)
    imagen_maquina = db.Column(db.String(200))

    accesorios = db.relationship("Accesorio", backref="maquina", cascade="all, delete")
    historial = db.relationship("Historial", backref="maquina", cascade="all, delete")


class Accesorio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text)
    maquina_id = db.Column(db.Integer, db.ForeignKey("maquina.id"))


class Historial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(20))
    tipo = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    responsable = db.Column(db.String(100))
    observacion = db.Column(db.Text)
    maquina_id = db.Column(db.Integer, db.ForeignKey("maquina.id"))
