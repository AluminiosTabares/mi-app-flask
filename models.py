from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Maquina(db.Model):
    __tablename__ = 'maquinas'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200))
    ubicacion = db.Column(db.String(100))
    fabricante = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    operador = db.Column(db.String(100))
    anio = db.Column(db.String(20))
    
    # Especificaciones físicas
    peso = db.Column(db.String(50))
    altura = db.Column(db.String(50))
    ancho = db.Column(db.String(50))
    largo = db.Column(db.String(50))
    
    # Especificaciones técnicas
    voltaje = db.Column(db.String(50))
    motor_hp = db.Column(db.String(50))
    fuerza = db.Column(db.String(50))
    velocidad_inicial = db.Column(db.String(50))
    velocidad_final = db.Column(db.String(50))
    tipo_lubricacion = db.Column(db.String(100))
    
    # Textos largos
    funcionamiento = db.Column(db.Text)
    partes_requeridas = db.Column(db.Text)
    recomendaciones = db.Column(db.Text)
    
    # Datos complejos: Guardamos la lista [] como texto para que sea fácil
    accesorios = db.Column(db.Text, default="[]") 
    historial = db.Column(db.Text, default="[]")
    
    imagen_maquina = db.Column(db.String(500))

class Extintor(db.Model):
    __tablename__ = 'extintores'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    area = db.Column(db.String(100))
    tipo = db.Column(db.String(100))
    capacidad = db.Column(db.String(50))
    fecha_vencimiento = db.Column(db.String(20))
    notificado = db.Column(db.Boolean, default=False)
