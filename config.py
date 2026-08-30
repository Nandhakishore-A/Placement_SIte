import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Handle Vercel serverless environment writable database path
IS_VERCEL = os.getenv("VERCEL") == "1" or "VERCEL" in os.environ

if IS_VERCEL:
    db_path = Path("/tmp/placement.db")
    src_db = BASE_DIR / "instance" / "placement.db"
    if not src_db.exists():
        src_db = BASE_DIR / "placement.db"
    if src_db.exists() and not db_path.exists():
        try:
            shutil.copyfile(src_db, db_path)
        except Exception as e:
            print(f"Warning: Could not copy DB to /tmp: {e}")
    default_db_uri = f"sqlite:///{db_path}"
    upload_folder = "/tmp/uploads"
else:
    if (BASE_DIR / "instance" / "placement.db").exists():
        default_db_uri = f"sqlite:///{BASE_DIR / 'instance' / 'placement.db'}"
    else:
        default_db_uri = f"sqlite:///{BASE_DIR / 'placement.db'}"
    upload_folder = str(BASE_DIR / "static" / "uploads")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-placement-key-2026")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", default_db_uri)
    # Handle postgres:// vs postgresql:// for SQLAlchemy
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MongoDB Atlas
    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb+srv://nandhakishore252_db_user:w6SpqTWjNLynyZ0V@cluster0.qvm6fpo.mongodb.net/placement_db?retryWrites=true&w=majority&appName=Cluster0"
    )
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "placement_db")
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "zsfupefr")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "956281599364653")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "UJ5UEJgFVt17dwgd4vAK3YQ_6HM")
    
    # Uploads
    UPLOAD_FOLDER = upload_folder
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
