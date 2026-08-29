from flask import Blueprint, request, jsonify
from services.cloudinary_service import upload_file
from auth import login_required, get_current_user, log_activity

upload_bp = Blueprint("upload_bp", __name__)

@upload_bp.route("/api/upload", methods=["POST"])
@login_required
def handle_file_upload():
    user = get_current_user()
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in form data 'file'."}), 400
        
    file = request.files["file"]
    folder = request.form.get("folder", "general")
    
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400
        
    upload_res = upload_file(file, folder=folder)
    if "error" in upload_res:
        return jsonify(upload_res), 400
        
    log_activity(user.id, "FILE_UPLOAD", "Document", None, f"Uploaded {upload_res.get('filename')} to {folder} via {upload_res.get('source')}")
    
    return jsonify({
        "message": "File uploaded successfully",
        "url": upload_res.get("url"),
        "filename": upload_res.get("filename"),
        "source": upload_res.get("source")
    })
