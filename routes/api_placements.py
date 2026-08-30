from datetime import datetime
from flask import Blueprint, request, jsonify
from db_mongo import get_db, get_next_sequence
from auth import login_required, get_current_user, log_activity

placements_bp = Blueprint("placements_bp", __name__)

def drive_to_dict(doc):
    if not doc:
        return {}
    res = dict(doc)
    if "_id" in res:
        res["_id"] = str(res["_id"])
    else:
        res["_id"] = str(res.get("id", ""))
    return res

def offer_to_dict(doc):
    if not doc:
        return {}
    res = dict(doc)
    if "_id" in res:
        res["_id"] = str(res["_id"])
    else:
        res["_id"] = str(res.get("id", ""))
    if isinstance(res.get("created_at"), datetime):
        res["created_at"] = res["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    return res

@placements_bp.route("/api/drives", methods=["GET"])
@login_required
def get_drives():
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    status = request.args.get("status", "").strip()
    db = get_db()
    filters = {}
    if status and status != "ALL":
        filters["status"] = status
        
    drives_cursor = db.placement_drives.find(filters).sort("drive_date", -1)
    drives = []
    for d in drives_cursor:
        d_dict = drive_to_dict(d)
        if "registered_count" not in d_dict or d_dict["registered_count"] == 0:
            d_dict["registered_count"] = db.placement_registrations.count_documents({"drive_id": d["id"]})
        if "offers_count" not in d_dict:
            d_dict["offers_count"] = db.offers.count_documents({"drive_id": d["id"]})
        drives.append(d_dict)
    return jsonify(drives)

@placements_bp.route("/api/drives/<int:drive_id>", methods=["GET"])
@login_required
def get_drive_detail(drive_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    db = get_db()
    drive = db.placement_drives.find_one({"id": drive_id})
    if not drive:
        return jsonify({"error": "Drive not found"}), 404
        
    data = drive_to_dict(drive)
    
    registrations = list(db.placement_registrations.find({"drive_id": drive_id}))
    attendances = list(db.placement_attendance.find({"drive_id": drive_id}))
    offers = list(db.offers.find({"drive_id": drive_id}))
    
    for item in registrations + attendances + offers:
        if "_id" in item:
            item["_id"] = str(item["_id"])
        else:
            item["_id"] = str(item.get("id", ""))
        
    data["registrations"] = registrations
    data["attendance"] = attendances
    data["offers"] = offers
    return jsonify(data)

@placements_bp.route("/api/drives", methods=["POST"])
@login_required
def create_drive():
    user = get_current_user()
    if user.role not in ["admin", "team_member"]:
        return jsonify({"error": "Unauthorized."}), 403
        
    data = request.get_json() or {}
    company_id = data.get("company_id")
    role_name = data.get("role_name") or data.get("job_role", "").strip()
    ctc = float(data.get("ctc_lpa", 0.0))
    drive_date_str = data.get("drive_date", "")
    
    if not company_id or not role_name or not drive_date_str:
        return jsonify({"error": "Company, Role Name, and Drive Date are required."}), 400
        
    db = get_db()
    comp = db.companies.find_one({"id": int(company_id)})
    comp_name = comp.get("name") if comp else f"Company #{company_id}"
    
    next_id = get_next_sequence("drive_id")
    drive_doc = {
        "id": next_id,
        "company_id": int(company_id),
        "company_name": comp_name,
        "role_name": role_name,
        "job_role": role_name,
        "job_description": data.get("job_description", ""),
        "ctc_lpa": ctc,
        "drive_date": drive_date_str,
        "min_sslc_percent": float(data.get("min_sslc_percent", 60.0)),
        "min_hsc_percent": float(data.get("min_hsc_percent", 60.0)),
        "min_ug_percent": float(data.get("min_ug_percent", 60.0)),
        "eligible_departments": data.get("eligible_departments", ["BCY", "BCS", "BIT", "AIDS", "BEC", "BBA"]),
        "status": data.get("status", "SCHEDULED"),
        "registered_count": 0,
        "offers_count": 0,
        "created_by_id": user.id,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    db.placement_drives.insert_one(drive_doc)
    log_activity(user.id, "CREATE_DRIVE", "PlacementDrive", next_id, f"Created drive for {comp_name} ({role_name})")
    
    return jsonify({"message": "Drive scheduled successfully", "drive": drive_to_dict(drive_doc)}), 201

@placements_bp.route("/api/drives/<int:drive_id>/eligible-students", methods=["GET"])
@login_required
def get_eligible_students(drive_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    db = get_db()
    drive = db.placement_drives.find_one({"id": drive_id})
    if not drive:
        return jsonify({"error": "Drive not found"}), 404
        
    min_ug = float(drive.get("min_ug_percent", 60.0))
    filters = {"ug_percent": {"$gte": min_ug}}
    
    eligible_depts = drive.get("eligible_departments")
    if isinstance(eligible_depts, list) and eligible_depts and "ALL" not in eligible_depts:
        filters["department_code"] = {"$in": eligible_depts}
    elif isinstance(eligible_depts, str) and eligible_depts != "ALL":
        filters["department_code"] = {"$in": [d.strip().upper() for d in eligible_depts.split(",")]}
        
    students_cursor = db.students.find(filters).sort("roll_no", 1).limit(500)
    
    registrations = list(db.placement_registrations.find({"drive_id": drive_id}))
    reg_student_ids = {r.get("student_id") for r in registrations}
    
    result = []
    for s in students_cursor:
        if "_id" in s:
            s["_id"] = str(s["_id"])
        else:
            s["_id"] = str(s.get("id", ""))
        s["is_registered"] = s.get("id") in reg_student_ids
        result.append(s)
        
    return jsonify({
        "drive_id": drive_id,
        "eligible_count": len(result),
        "students": result
    })

@placements_bp.route("/api/drives/<int:drive_id>/register", methods=["POST"])
@login_required
def register_student(drive_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    data = request.get_json() or {}
    student_id = data.get("student_id")
    
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400
        
    db = get_db()
    existing = db.placement_registrations.find_one({"drive_id": drive_id, "student_id": int(student_id)})
    if existing:
        return jsonify({"error": "Student is already registered for this drive."}), 400
        
    next_id = get_next_sequence("registration_id")
    student = db.students.find_one({"id": int(student_id)})
    
    reg_doc = {
        "id": next_id,
        "drive_id": drive_id,
        "student_id": int(student_id),
        "student_roll_no": student.get("roll_no") if student else "",
        "student_name": student.get("name") if student else "",
        "department_code": student.get("department_code") if student else "",
        "registered_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    db.placement_registrations.insert_one(reg_doc)
    if "_id" in reg_doc:
        reg_doc["_id"] = str(reg_doc["_id"])
    else:
        reg_doc["_id"] = str(reg_doc.get("id", ""))
    
    log_activity(user.id, "REGISTER_STUDENT", "PlacementRegistration", next_id, f"Registered student ID {student_id} for Drive #{drive_id}")
    return jsonify({"message": "Student registered successfully", "registration": reg_doc}), 201

@placements_bp.route("/api/drives/<int:drive_id>/attendance", methods=["POST"])
@login_required
def mark_attendance(drive_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    data = request.get_json() or {}
    attendance_records = data.get("records", [])
    
    db = get_db()
    updated_count = 0
    for rec in attendance_records:
        s_id = int(rec.get("student_id"))
        is_pres = bool(rec.get("is_present", False))
        student = db.students.find_one({"id": s_id})
        
        db.placement_attendance.update_one(
            {"drive_id": drive_id, "student_id": s_id},
            {
                "$set": {
                    "is_present": is_pres,
                    "status": "PRESENT" if is_pres else "ABSENT",
                    "student_name": student.get("name") if student else "",
                    "student_roll_no": student.get("roll_no") if student else "",
                    "department_code": student.get("department_code") if student else "",
                    "marked_by_id": user.id,
                    "marked_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            upsert=True
        )
        updated_count += 1
        
    log_activity(user.id, "MARK_ATTENDANCE", "PlacementAttendance", drive_id, f"Marked attendance for {updated_count} students in Drive #{drive_id}")
    return jsonify({"message": f"Attendance recorded for {updated_count} candidates."})

@placements_bp.route("/api/offers", methods=["GET"])
@login_required
def get_offers():
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    db = get_db()
    offers_cursor = db.offers.find().sort("offer_date", -1).limit(1000)
    offers = [offer_to_dict(o) for o in offers_cursor]
    return jsonify(offers)

@placements_bp.route("/api/offers", methods=["POST"])
@login_required
def create_offer():
    user = get_current_user()
    if user.role not in ["admin", "team_member"]:
        return jsonify({"error": "Unauthorized."}), 403
        
    data = request.get_json() or {}
    student_id = data.get("student_id")
    company_id = data.get("company_id")
    role = data.get("role") or data.get("role_offered", "").strip()
    ctc = float(data.get("ctc_lpa", 0.0))
    drive_id = data.get("drive_id")
    offer_date_str = data.get("offer_date", "") or datetime.utcnow().strftime("%Y-%m-%d")
    
    if not student_id or not company_id or not role or not ctc:
        return jsonify({"error": "Student, Company, Role, and CTC (LPA) are required."}), 400
        
    db = get_db()
    student = db.students.find_one({"id": int(student_id)})
    company = db.companies.find_one({"id": int(company_id)})
    
    next_id = get_next_sequence("offer_id")
    
    offer_doc = {
        "id": next_id,
        "student_id": int(student_id),
        "student_roll_no": student.get("roll_no") if student else "",
        "student_name": student.get("name") if student else "",
        "department_code": student.get("department_code") if student else "",
        "company_id": int(company_id),
        "company_name": company.get("name") if company else f"Company #{company_id}",
        "drive_id": int(drive_id) if drive_id else None,
        "role_offered": role,
        "role": role,
        "ctc_lpa": ctc,
        "offer_date": offer_date_str,
        "offer_letter_url": data.get("offer_letter_url", ""),
        "status": "ACCEPTED",
        "created_by_id": user.id,
        "created_at": datetime.utcnow()
    }
    
    db.offers.insert_one(offer_doc)
    
    # Update Student overall placement status to 'PLACED'
    db.students.update_one(
        {"id": int(student_id)},
        {
            "$set": {
                "placement_status": "PLACED",
                "latest_offer": {
                    "company_name": company.get("name") if company else "",
                    "role": role,
                    "ctc_lpa": ctc,
                    "offer_date": offer_date_str
                }
            }
        }
    )
    
    # Increment company offers count
    db.companies.update_one(
        {"id": int(company_id)},
        {"$inc": {"total_offers_count": 1}}
    )
    
    log_activity(user.id, "CREATE_OFFER", "Offer", next_id, f"Recorded offer for student ID {student_id} at {company.get('name') if company else ''} with CTC {ctc} LPA")
    return jsonify({"message": "Placement offer recorded successfully!", "offer": offer_to_dict(offer_doc)}), 201
