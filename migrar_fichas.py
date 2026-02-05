import json
from app import app, db
from models import Maquina, Accesorio, Historial

def migrar():
    # USAMOS encoding='utf-8' PARA EVITAR EL ERROR DE ACENTOS
    try:
        with open('fichas.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except FileNotFoundError:
        print("Error: No se encontró el archivo fichas.json")
        return
    except UnicodeDecodeError:
        print("Error de codificación: Intentando con otro formato...")
        with open('fichas.json', 'r', encoding='latin-1') as f:
            datos = json.load(f)

    with app.app_context():
        # OPCIONAL: db.create_all() crea las tablas si no existen
        db.create_all()

        for item in datos:
            # Crear la máquina
            # Esto va dentro del bucle 'for item in datos:'
            nueva_maquina = Maquina(
                codigo=item.get('codigo'),
                nombre=item.get('nombre'),
                ubicacion=item.get('ubicacion'),
                fabricante=item.get('fabricante'),
                modelo=item.get('modelo'),
                operador=item.get('operador'),
                anio=item.get('anio'), 
                peso=item.get('peso'),
                altura=item.get('altura'),
                ancho=item.get('ancho'),
                largo=item.get('largo'),
                voltaje=item.get('voltaje'),
                motor_hp=item.get('motor_hp'),
                fuerza=item.get('fuerza'),
                velocidad_inicial=item.get('velocidad_inicial'),
                velocidad_final=item.get('velocidad_final'),
                tipo_lubricacion=item.get('tipo_lubricacion'),
                funcionamiento=item.get('funcionamiento'),
                partes_requeridas=item.get('partes_requeridas'),
                recomendaciones=item.get('recomendaciones'),
                imagen_maquina=item.get('imagen_maquina')
            )
            
            db.session.add(nueva_maquina)
            db.session.flush() # Para obtener el ID de la máquina antes de guardar

            # Si el JSON tiene una lista de accesorios
            if 'accesorios' in item:
                for acc in item['accesorios']:
                    nuevo_acc = Accesorio(
                        descripcion=acc.get('descripcion'),
                        maquina_id=nueva_maquina.id
                    )
                    db.session.add(nuevo_acc)

        db.session.commit()
        print("¡Migración completada con éxito!")

if __name__ == '__main__':
    migrar()