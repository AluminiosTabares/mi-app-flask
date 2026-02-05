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
            nueva_maquina = Maquina(
                codigo=item.get('codigo'),
                nombre=item.get('nombre'),
                ubicacion=item.get('ubicacion'),
                # Agrega aquí todos los campos de tu JSON que coincidan con models.py
                funcionamiento=item.get('funcionamiento'),
                recomendaciones=item.get('recomendaciones')
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