import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from models import db
from seed_data import seed_database

app = create_app()

with app.app_context():
    db.create_all()
    try:
        from models import User
        if not User.query.first():
            seed_database(app)
    except Exception as e:
        print(f"Vercel DB Init: {e}")
