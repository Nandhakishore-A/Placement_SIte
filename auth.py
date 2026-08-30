from functools import wraps
from datetime import datetime
from flask import session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from db_mongo import get_db, get_next_sequence

class MongoUser:
    def __init__(self, doc):
        self.doc = doc or {}
        self.id = self.doc.get("id")
        self.username = self.doc.get("username", "")
        self.email = self.doc.get("email", "")
        self.role = self.doc.get("role", "")
        self.member_id = self.doc.get("member_id", "")
        self.full_name = self.doc.get("full_name", "")
        self.password_hash = self.doc.get("password_hash", "")
        
    def to_dict(self):
        created_at = self.doc.get("created_at")
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "member_id": self.member_id,
            "full_name": self.full_name,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created_at, datetime) else str(created_at)
        }

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)

def get_current_user():
    user_info = session.get("user_info")
    if user_info and isinstance(user_info, dict) and "id" in user_info:
        return MongoUser(user_info)
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    user_doc = db.users.find_one({"id": user_id})
    if not user_doc:
        return None
    session["user_info"] = {
        "id": user_doc.get("id"),
        "username": user_doc.get("username"),
        "email": user_doc.get("email"),
        "role": user_doc.get("role"),
        "member_id": user_doc.get("member_id"),
        "full_name": user_doc.get("full_name")
    }
    return MongoUser(user_doc)

def log_activity(user_id, action_type, target_entity, target_id=None, description=""):
    try:
        ip = request.remote_addr if request else "127.0.0.1"
        db = get_db()
        db.activity_logs.insert_one({
            "user_id": user_id,
            "action_type": action_type,
            "target_entity": target_entity,
            "target_id": str(target_id) if target_id else None,
            "description": description,
            "ip_address": ip,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        print(f"Error logging activity: {e}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Authentication required. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """
    allowed_roles can be a list: ['admin', 'manager', 'team_member']
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required. Please log in."}), 401
            
            # Admin always has access to all functions
            if user.role == "admin":
                return f(*args, **kwargs)
            
            if user.role not in allowed_roles:
                return jsonify({
                    "error": f"Access forbidden. Your role ({user.role}) is not authorized for this section."
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_only(f):
    return role_required(["admin"])(f)

def student_dashboard_access(f):
    """Admin and Manager have access to Student Directory & Student Profiles."""
    return role_required(["admin", "manager"])(f)

def company_crm_access(f):
    """Admin and Placement Team Members have access to Company CRM."""
    return role_required(["admin", "team_member"])(f)

def drives_and_ats_access(f):
    """Admin only."""
    return role_required(["admin"])(f)
