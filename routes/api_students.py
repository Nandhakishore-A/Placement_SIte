from flask import Blueprint, request, jsonify, session
from models import db, Student, Department, Offer
from auth import login_required, get_current_user, log_activity

students_bp = Blueprint("students_bp", __name__)

@students_bp.route("/api/departments", methods=["GET"])
@login_required
def get_departments():
    depts = Department.query.all()
    dept_data = []
    for d in depts:
        count = Student.query.filter_by(department_id=d.id).count()
        placed_count = Student.query.filter_by(department_id=d.id, placement_status="PLACED").count()
        dept_data.append({
            "id": d.id,
            "code": d.code,
            "name": d.name,
            "description": d.description,
            "student_count": count,
            "placed_count": placed_count,
            "placement_rate": round((placed_count / count * 100), 1) if count > 0 else 0
        })
    return jsonify(dept_data)

@students_bp.route("/api/students", methods=["GET"])
@login_required
def get_students():
    user = get_current_user()
    if user.role == "team_member":
        return jsonify({"error": "Access forbidden. Placement Team Members can only access Overall Dashboard and Company CRM."}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    dept_code = request.args.get("department", "").strip()
    status = request.args.get("status", "").strip()  # PLACED, YET TO BE PLACED
    search = request.args.get("search", "").strip()
    gender = request.args.get("gender", "").strip()
    min_ug = request.args.get("min_ug", type=float)
    
    query = Student.query
    
    if dept_code and dept_code != "ALL":
        dept = Department.query.filter_by(code=dept_code).first()
        if dept:
            query = query.filter(Student.department_id == dept.id)
            
    if status and status != "ALL":
        query = query.filter(Student.placement_status == status)
        
    if gender and gender != "ALL":
        query = query.filter(Student.gender == gender)
        
    if min_ug:
        query = query.filter(Student.ug_percent >= min_ug)
        
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.name.ilike(search_fmt),
                Student.roll_no.ilike(search_fmt),
                Student.email.ilike(search_fmt)
            )
        )
        
    total = query.count()
    students_page = query.order_by(Student.roll_no.asc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "students": [s.to_dict() for s in students_page]
    })

@students_bp.route("/api/students/<int:student_id>", methods=["GET"])
@login_required
def get_student_detail(student_id):
    user = get_current_user()
    if user.role == "team_member":
        return jsonify({"error": "Access forbidden for Placement Team Members."}), 403

    student = Student.query.get_or_404(student_id)
    data = student.to_dict()
    
    # Include complete placement drive history & attendance
    data["registrations"] = [r.to_dict() for r in student.registrations]
    data["attendances"] = [a.to_dict() for a in student.attendances]
    data["offers"] = [o.to_dict() for o in student.offers]
    data["ats_history"] = [ats.to_dict() for ats in student.ats_results]
    
    return jsonify(data)

@students_bp.route("/api/students", methods=["POST"])
@login_required
def create_student():
    user = get_current_user()
    if user.role not in ["admin", "manager"]:
        return jsonify({"error": "Unauthorized. Only Admin and Manager can create students."}), 403
        
    data = request.get_json() or {}
    
    roll_no = data.get("roll_no", "").strip()
    name = data.get("name", "").strip()
    dept_id = data.get("department_id")
    email = data.get("email", "").strip()
    mobile = data.get("mobile_no", "").strip()
    
    if not roll_no or not name or not dept_id or not email or not mobile:
        return jsonify({"error": "Roll No, Name, Department, Email, and Mobile No are required."}), 400
        
    # Check uniqueness
    if Student.query.filter_by(roll_no=roll_no).first():
        return jsonify({"error": f"Student with Roll No {roll_no} already exists."}), 400
    if Student.query.filter_by(email=email).first():
        return jsonify({"error": f"Student with Email {email} already exists."}), 400
        
    student = Student(
        roll_no=roll_no,
        name=name,
        department_id=dept_id,
        gender=data.get("gender", "Male"),
        residency_type=data.get("residency_type", "Day Scholar"),
        sslc_percent=float(data.get("sslc_percent", 0)),
        hsc_percent=float(data.get("hsc_percent", 0)),
        ug_percent=float(data.get("ug_percent", 0)),
        pg_percent=float(data.get("pg_percent")) if data.get("pg_percent") else None,
        degree=data.get("degree", "B.E / B.Tech"),
        grad_year_10th=data.get("grad_year_10th"),
        grad_year_12th=data.get("grad_year_12th"),
        grad_year_ug=data.get("grad_year_ug", 2026),
        grad_year_pg=data.get("grad_year_pg"),
        email=email,
        mobile_no=mobile,
        github_url=data.get("github_url"),
        linkedin_url=data.get("linkedin_url"),
        portfolio_url=data.get("portfolio_url"),
        resume_url=data.get("resume_url"),
        self_intro_url=data.get("self_intro_url"),
        photo_url=data.get("photo_url"),
        drive_links=data.get("drive_links"),
        placement_status="YET TO BE PLACED"
    )
    
    db.session.add(student)
    db.session.commit()
    
    log_activity(user.id, "CREATE_STUDENT", "Student", student.id, f"Created student {student.name} ({student.roll_no})")
    
    return jsonify({"message": "Student created successfully", "student": student.to_dict()}), 201

@students_bp.route("/api/students/<int:student_id>", methods=["PUT"])
@login_required
def update_student(student_id):
    user = get_current_user()
    if user.role not in ["admin", "manager"]:
        return jsonify({"error": "Unauthorized. Only Admin and Manager can edit students."}), 403
        
    student = Student.query.get_or_404(student_id)
    data = request.get_json() or {}
    
    student.name = data.get("name", student.name)
    student.department_id = data.get("department_id", student.department_id)
    student.gender = data.get("gender", student.gender)
    student.residency_type = data.get("residency_type", student.residency_type)
    student.sslc_percent = float(data.get("sslc_percent", student.sslc_percent))
    student.hsc_percent = float(data.get("hsc_percent", student.hsc_percent))
    student.ug_percent = float(data.get("ug_percent", student.ug_percent))
    if "pg_percent" in data:
        student.pg_percent = float(data["pg_percent"]) if data["pg_percent"] else None
    student.degree = data.get("degree", student.degree)
    student.grad_year_10th = data.get("grad_year_10th", student.grad_year_10th)
    student.grad_year_12th = data.get("grad_year_12th", student.grad_year_12th)
    student.grad_year_ug = data.get("grad_year_ug", student.grad_year_ug)
    student.grad_year_pg = data.get("grad_year_pg", student.grad_year_pg)
    student.email = data.get("email", student.email)
    student.mobile_no = data.get("mobile_no", student.mobile_no)
    student.github_url = data.get("github_url", student.github_url)
    student.linkedin_url = data.get("linkedin_url", student.linkedin_url)
    student.portfolio_url = data.get("portfolio_url", student.portfolio_url)
    student.resume_url = data.get("resume_url", student.resume_url)
    student.self_intro_url = data.get("self_intro_url", student.self_intro_url)
    student.photo_url = data.get("photo_url", student.photo_url)
    student.drive_links = data.get("drive_links", student.drive_links)
    
    db.session.commit()
    log_activity(user.id, "UPDATE_STUDENT", "Student", student.id, f"Updated profile of {student.name} ({student.roll_no})")
    
    return jsonify({"message": "Student updated successfully", "student": student.to_dict()})

@students_bp.route("/api/students/<int:student_id>", methods=["DELETE"])
@login_required
def delete_student(student_id):
    user = get_current_user()
    if user.role not in ["admin", "manager"]:
        return jsonify({"error": "Unauthorized. Only Admin and Manager can delete students."}), 403
        
    student = Student.query.get_or_404(student_id)
    roll = student.roll_no
    name = student.name
    
    db.session.delete(student)
    db.session.commit()
    
    log_activity(user.id, "DELETE_STUDENT", "Student", student_id, f"Deleted student {name} ({roll})")
    return jsonify({"message": f"Student {name} ({roll}) deleted successfully"})
