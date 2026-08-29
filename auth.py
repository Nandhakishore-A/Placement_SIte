from functools import wraps
from flask import session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, ActivityLog

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

def log_activity(user_id, action_type, target_entity, target_id=None, description=""):
    try:
        ip = request.remote_addr if request else "127.0.0.1"
        log = ActivityLog(
            user_id=user_id,
            action_type=action_type,
            target_entity=target_entity,
            target_id=str(target_id) if target_id else None,
            description=description,
            ip_address=ip
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.session.rollback()

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
