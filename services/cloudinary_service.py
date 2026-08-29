import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

# Try importing cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    HAS_CLOUDINARY = True
except ImportError:
    HAS_CLOUDINARY = False

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg", "txt"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def init_cloudinary():
    if HAS_CLOUDINARY and Config.CLOUDINARY_CLOUD_NAME and Config.CLOUDINARY_API_KEY:
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET,
            secure=True
        )
        return True
    return False

def upload_file(file_storage, folder: str = "placement_docs") -> dict:
    """
    Uploads a file to Cloudinary if configured; otherwise saves locally into static/uploads/<folder>.
    Returns dict: {"url": str, "public_id": str, "filename": str, "source": "cloudinary"|"local"}
    """
    if not file_storage or not allowed_file(file_storage.filename):
        return {"error": "Invalid file format or empty file."}
    
    orig_filename = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex[:10]}_{orig_filename}"
    
    # 1. Cloudinary attempt
    if init_cloudinary():
        try:
            upload_result = cloudinary.uploader.upload(
                file_storage,
                folder=folder,
                resource_type="auto",
                public_id=unique_name.rsplit(".", 1)[0]
            )
            return {
                "url": upload_result.get("secure_url"),
                "public_id": upload_result.get("public_id"),
                "filename": orig_filename,
                "source": "cloudinary"
            }
        except Exception as e:
            print(f"Cloudinary upload failed ({e}), falling back to local storage.")
    
    # 2. Local Storage Fallback
    target_dir = os.path.join(Config.UPLOAD_FOLDER, folder)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, unique_name)
    
    file_storage.seek(0)
    file_storage.save(file_path)
    
    local_url = f"/static/uploads/{folder}/{unique_name}"
    return {
        "url": local_url,
        "public_id": unique_name,
        "filename": orig_filename,
        "source": "local"
    }
