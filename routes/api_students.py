import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from db_mongo import get_db, get_next_sequence
from auth import login_required, get_current_user, log_activity

students_bp = Blueprint("students_bp", __name__)

def student_to_dict(doc):
    if not doc:
        return {}
    res = dict(doc)
    if "_id" in res:
        res["_id"] = str(res["_id"])
    else:
        res["_id"] = str(res.get("id", ""))
    if isinstance(res.get("created_at"), datetime):
        res["created_at"] = res["created_at"].strftime("%Y-%m-%d")
    return res

@students_bp.route("/api/departments", methods=["GET"])
@login_required
def get_departments():
    db = get_db()
    depts = list(db.departments.find().sort("id", 1))
    
    # 1 Single fast MongoDB Aggregation for all departments
    pipeline = [
        {
            "$group": {
                "_id": "$department_code",
                "total": {"$sum": 1},
                "placed": {
                    "$sum": {"$cond": [{"$eq": ["$placement_status", "PLACED"]}, 1, 0]}
                }
            }
        }
    ]
    agg_results = {item["_id"]: item for item in db.students.aggregate(pipeline)}
    
    dept_data = []
    for d in depts:
        code = d.get("code")
        counts = agg_results.get(code, {"total": 0, "placed": 0})
        count = counts["total"]
        placed_count = counts["placed"]
        dept_data.append({
            "id": d.get("id"),
            "code": code,
            "name": d.get("name"),
            "description": d.get("description", ""),
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
    status = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()
    gender = request.args.get("gender", "").strip()
    min_ug = request.args.get("min_ug", type=float)
    
    db = get_db()
    filters = {}
    
    if dept_code and dept_code != "ALL":
        filters["department_code"] = dept_code
        
    if status and status != "ALL":
        filters["placement_status"] = status
        
    if gender and gender != "ALL":
        filters["gender"] = gender
        
    if min_ug is not None:
        filters["ug_percent"] = {"$gte": min_ug}
        
    if search:
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        filters["$or"] = [
            {"name": search_regex},
            {"roll_no": search_regex},
            {"email": search_regex}
        ]
        
    total = db.students.count_documents(filters)
    students_cursor = db.students.find(filters).sort("id", 1).skip((page - 1) * per_page).limit(per_page)
    students_page = [student_to_dict(s) for s in students_cursor]
    
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "students": students_page
    })

@students_bp.route("/api/students/<int:student_id>", methods=["GET"])
@login_required
def get_student_detail(student_id):
    user = get_current_user()
    if user.role == "team_member":
        return jsonify({"error": "Access forbidden for Placement Team Members."}), 403

    db = get_db()
    student = db.students.find_one({"id": student_id})
    if not student:
        return jsonify({"error": "Student not found"}), 404
        
    data = student_to_dict(student)
    
    # Related collections
    registrations = list(db.placement_registrations.find({"student_id": student_id}))
    attendances = list(db.placement_attendance.find({"student_id": student_id}))
    offers = list(db.offers.find({"student_id": student_id}))
    ats_history = list(db.ats_analyses.find({"student_id": student_id}))
    
    for item in registrations + attendances + offers + ats_history:
        if "_id" in item:
            item["_id"] = str(item["_id"])
        else:
            item["_id"] = str(item.get("id", ""))
        
    data["registrations"] = registrations
    data["attendances"] = attendances
    data["offers"] = offers
    data["ats_history"] = ats_history
    
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
    dept_code = data.get("department_code", "CSE")
    email = data.get("email", "").strip()
    mobile = data.get("mobile_no", "").strip()
    
    if not roll_no or not name or not email or not mobile:
        return jsonify({"error": "Roll No, Name, Department, Email, and Mobile No are required."}), 400
        
    db = get_db()
    if db.students.find_one({"roll_no": roll_no}):
        return jsonify({"error": f"Student with Roll No {roll_no} already exists."}), 400
    if db.students.find_one({"email": email}):
        return jsonify({"error": f"Student with Email {email} already exists."}), 400
        
    next_id = get_next_sequence("student_id")
    
    dept_doc = db.departments.find_one({"id": dept_id}) if dept_id else db.departments.find_one({"code": dept_code})
    if dept_doc:
        dept_id = dept_doc["id"]
        dept_code = dept_doc["code"]
        dept_name = dept_doc["name"]
    else:
        dept_name = dept_code
        
    student_doc = {
        "id": next_id,
        "roll_no": roll_no,
        "name": name,
        "department_id": dept_id,
        "department_code": dept_code,
        "department_name": dept_name,
        "gender": data.get("gender", "Male"),
        "residency_type": data.get("residency_type", "Day Scholar"),
        "sslc_percent": float(data.get("sslc_percent", 0)),
        "hsc_percent": float(data.get("hsc_percent", 0)),
        "ug_percent": float(data.get("ug_percent", 0)),
        "pg_percent": float(data.get("pg_percent")) if data.get("pg_percent") else None,
        "degree": data.get("degree", "B.E / B.Tech"),
        "grad_year_10th": data.get("grad_year_10th", 2020),
        "grad_year_12th": data.get("grad_year_12th", 2022),
        "grad_year_ug": data.get("grad_year_ug", 2026),
        "grad_year_pg": data.get("grad_year_pg"),
        "email": email,
        "mobile_no": mobile,
        "github_url": data.get("github_url", ""),
        "linkedin_url": data.get("linkedin_url", ""),
        "portfolio_url": data.get("portfolio_url", ""),
        "resume_url": data.get("resume_url", ""),
        "self_intro_url": data.get("self_intro_url", ""),
        "photo_url": data.get("photo_url", ""),
        "drive_links": data.get("drive_links", ""),
        "placement_status": "YET TO BE PLACED",
        "created_at": datetime.utcnow()
    }
    
    db.students.insert_one(student_doc)
    log_activity(user.id, "CREATE_STUDENT", "Student", next_id, f"Created student {name} ({roll_no})")
    
    return jsonify({"message": "Student created successfully", "student": student_to_dict(student_doc)}), 201

@students_bp.route("/api/students/<int:student_id>", methods=["PUT"])
@login_required
def update_student(student_id):
    user = get_current_user()
    if user.role not in ["admin", "manager"]:
        return jsonify({"error": "Unauthorized. Only Admin and Manager can edit students."}), 403
        
    db = get_db()
    student = db.students.find_one({"id": student_id})
    if not student:
        return jsonify({"error": "Student not found"}), 404
        
    data = request.get_json() or {}
    update_fields = {}
    
    for key in [
        "roll_no", "name", "gender", "residency_type", "degree", "email", "mobile_no",
        "github_url", "linkedin_url", "portfolio_url", "resume_url",
        "self_intro_url", "photo_url", "drive_links", "placement_status"
    ]:
        if key in data:
            update_fields[key] = data[key]
            
    if "department_id" in data and data["department_id"]:
        try:
            dept = db.departments.find_one({"id": int(data["department_id"])})
            if dept:
                update_fields["department_id"] = dept["id"]
                update_fields["department_code"] = dept["code"]
                update_fields["department_name"] = dept["name"]
        except Exception:
            pass
    elif "department_code" in data:
        dept = db.departments.find_one({"code": data["department_code"]})
        if dept:
            update_fields["department_id"] = dept["id"]
            update_fields["department_code"] = dept["code"]
            update_fields["department_name"] = dept["name"]
            
    for num_key in ["sslc_percent", "hsc_percent", "ug_percent", "pg_percent"]:
        if num_key in data and data[num_key] is not None:
            update_fields[num_key] = float(data[num_key])
            
    for yr_key in ["grad_year_10th", "grad_year_12th", "grad_year_ug", "grad_year_pg"]:
        if yr_key in data and data[yr_key] is not None:
            update_fields[yr_key] = int(data[yr_key])
            
    db.students.update_one({"id": student_id}, {"$set": update_fields})
    log_activity(user.id, "UPDATE_STUDENT", "Student", student_id, f"Updated profile of {student.get('name')} ({student.get('roll_no')})")
    
    updated_doc = db.students.find_one({"id": student_id})
    return jsonify({"message": "Student updated successfully", "student": student_to_dict(updated_doc)})

@students_bp.route("/api/students/<int:student_id>", methods=["DELETE"])
@login_required
def delete_student(student_id):
    user = get_current_user()
    if user.role not in ["admin", "manager"]:
        return jsonify({"error": "Unauthorized. Only Admin and Manager can delete students."}), 403
        
    db = get_db()
    student = db.students.find_one({"id": student_id})
    if not student:
        return jsonify({"error": "Student not found"}), 404
        
    roll = student.get("roll_no")
    name = student.get("name")
    
    db.students.delete_one({"id": student_id})
    db.offers.delete_many({"student_id": student_id})
    
    log_activity(user.id, "DELETE_STUDENT", "Student", student_id, f"Deleted student {name} ({roll})")
    return jsonify({"message": f"Student {name} ({roll}) deleted successfully"})
