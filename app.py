import os
from flask import Flask, render_template, send_from_directory, jsonify, redirect, url_for, session
from flask_cors import CORS
from config import Config, BASE_DIR
from auth import login_required, get_current_user
from db_mongo import init_mongo_indexes, get_db

# Import API blueprints
from routes.api_auth import auth_bp
from routes.api_students import students_bp
from routes.api_companies import companies_bp
from routes.api_placements import placements_bp
from routes.api_ats import ats_bp
from routes.api_reports import reports_bp
from routes.api_upload import upload_bp

def create_app():
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        template_folder=str(BASE_DIR / "templates")
    )
    app.config.from_object(Config)
    
    CORS(app)
    
    # Initialize MongoDB Indexes
    try:
        init_mongo_indexes()
    except Exception as e:
        print(f"[WARN] MongoDB Index initialization notice: {e}")
    
    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(placements_bp)
    app.register_blueprint(ats_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(upload_bp)
    
    # Ensure local upload directories exist
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, "resumes"), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, "photos"), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, "jds"), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, "general"), exist_ok=True)
    
    # UI Page Routes
    @app.route("/")
    def index():
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("index.html")
        
    @app.route("/login")
    def login_page():
        return render_template("login.html")
        
    @app.route("/dashboard")
    def dashboard_page():
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("index.html")

    @app.route("/static/<path:filename>")
    def custom_static(filename):
        return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

    # Health & Meta
    @app.route("/api/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "database": "MongoDB Atlas",
            "cloud_storage": "Cloudinary",
            "service": "Placement Management System API",
            "version": "1.0.0"
        })

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
        
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[OK] Placement Management System running with MongoDB Atlas on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
