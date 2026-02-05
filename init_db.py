import os
os.environ["PGCLIENTENCODING"] = "UTF8"


from app import app
from models import db

with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente")
