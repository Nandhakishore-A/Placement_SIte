from datetime import datetime
from flask import Blueprint, request, jsonify
from models import db, PlacementDrive, PlacementRegistration, PlacementAttendance, Shortlist, Offer, Student, Company
from auth import login_required, get_current_user, log_activity

placements_bp = Blueprint("placements_bp", __name__)

@placements_bp.route("/api/drives", methods=["GET"])
@login_required
def get_drives():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    status = request.args.get("status", "").strip()
    query = PlacementDrive.query
    if status and status != "ALL":
        query = query.filter(PlacementDrive.status == status)
        
    drives = query.order_by(PlacementDrive.drive_date.desc()).all()
    return jsonify([d.to_dict() for d in drives])

@placements_bp.route("/api/drives/<int:drive_id>", methods=["GET"])
@login_required
def get_drive_detail(drive_id):
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    drive = PlacementDrive.query.get_or_404(drive_id)
    data = drive.to_dict()
    data["registrations"] = [r.to_dict() for r in drive.registrations]
    data["attendance"] = [a.to_dict() for a in drive.attendances]
    data["shortlists"] = [s.to_dict() for s in drive.shortlists]
    data["offers"] = [o.to_dict() for o in drive.offers]
    return jsonify(data)

@placements_bp.route("/api/drives", methods=["POST"])
@login_required
def create_drive():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    data = request.get_json() or {}
    company_id = data.get("company_id")
    role_name = data.get("role_name", "").strip()
    ctc = float(data.get("ctc_lpa", 0.0))
    drive_date_str = data.get("drive_date", "")
    
    if not company_id or not role_name or not drive_date_str:
        return jsonify({"error": "Company, Role Name, and Drive Date are required."}), 400
        
    try:
        drive_date = datetime.strptime(drive_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        
    drive = PlacementDrive(
        company_id=company_id,
        role_name=role_name,
        job_description=data.get("job_description", ""),
        ctc_lpa=ctc,
        drive_date=drive_date,
        min_sslc_percent=float(data.get("min_sslc_percent", 60.0)),
        min_hsc_percent=float(data.get("min_hsc_percent", 60.0)),
        min_ug_percent=float(data.get("min_ug_percent", 60.0)),
        eligible_departments=data.get("eligible_departments", "ALL"),
        status=data.get("status", "SCHEDULED"),
        created_by_id=user.id
    )
    
    db.session.add(drive)
    db.session.commit()
    
    comp = Company.query.get(company_id)
    comp_name = comp.name if comp else f"ID {company_id}"
    log_activity(user.id, "CREATE_DRIVE", "PlacementDrive", drive.id, f"Created drive for {comp_name} ({role_name})")
    
    return jsonify({"message": "Drive scheduled successfully", "drive": drive.to_dict()}), 201

@placements_bp.route("/api/drives/<int:drive_id>/eligible-students", methods=["GET"])
@login_required
def get_eligible_students(drive_id):
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    drive = PlacementDrive.query.get_or_404(drive_id)
    query = Student.query.filter(
        Student.sslc_percent >= drive.min_sslc_percent,
        Student.hsc_percent >= drive.min_hsc_percent,
        Student.ug_percent >= drive.min_ug_percent
    )
    
    if drive.eligible_departments and drive.eligible_departments != "ALL":
        dept_codes = [d.strip().upper() for d in drive.eligible_departments.split(",")]
        query = query.join(Student.department).filter(Student.department.has(db.func.upper(db.text("departments.code")).in_(dept_codes)))
        
    students = query.order_by(Student.roll_no.asc()).all()
    reg_student_ids = {r.student_id for r in drive.registrations}
    
    result = []
    for s in students:
        s_dict = s.to_dict()
        s_dict["is_registered"] = s.id in reg_student_ids
        result.append(s_dict)
        
    return jsonify({
        "drive_id": drive.id,
        "eligible_count": len(result),
        "students": result
    })

@placements_bp.route("/api/drives/<int:drive_id>/register", methods=["POST"])
@login_required
def register_student(drive_id):
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    drive = PlacementDrive.query.get_or_404(drive_id)
    data = request.get_json() or {}
    student_id = data.get("student_id")
    
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400
        
    # Check duplicate
    existing = PlacementRegistration.query.filter_by(drive_id=drive_id, student_id=student_id).first()
    if existing:
        return jsonify({"error": "Student is already registered for this drive."}), 400
        
    reg = PlacementRegistration(drive_id=drive_id, student_id=student_id)
    db.session.add(reg)
    db.session.commit()
    
    student = Student.query.get(student_id)
    log_activity(user.id, "REGISTER_STUDENT", "PlacementRegistration", reg.id, f"Registered {student.name} ({student.roll_no}) for Drive #{drive_id}")
    
    return jsonify({"message": "Student registered successfully", "registration": reg.to_dict()}), 201

@placements_bp.route("/api/drives/<int:drive_id>/attendance", methods=["POST"])
@login_required
def mark_attendance(drive_id):
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    drive = PlacementDrive.query.get_or_404(drive_id)
    data = request.get_json() or {}
    # Array of { student_id: int, is_present: bool }
    attendance_records = data.get("records", [])
    
    updated_count = 0
    for rec in attendance_records:
        s_id = rec.get("student_id")
        is_pres = bool(rec.get("is_present", False))
        
        att = PlacementAttendance.query.filter_by(drive_id=drive_id, student_id=s_id).first()
        if not att:
            att = PlacementAttendance(
                drive_id=drive_id,
                student_id=s_id,
                is_present=is_pres,
                marked_by_id=user.id
            )
            db.session.add(att)
        else:
            att.is_present = is_pres
            att.marked_by_id = user.id
            att.marked_at = datetime.utcnow()
        updated_count += 1
        
    db.session.commit()
    log_activity(user.id, "MARK_ATTENDANCE", "PlacementAttendance", drive_id, f"Marked attendance for {updated_count} students in Drive #{drive_id}")
    
    return jsonify({"message": f"Attendance recorded for {updated_count} candidates."})

@placements_bp.route("/api/offers", methods=["GET"])
@login_required
def get_offers():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    offers = Offer.query.order_by(Offer.offer_date.desc()).all()
    return jsonify([o.to_dict() for o in offers])

@placements_bp.route("/api/offers", methods=["POST"])
@login_required
def create_offer():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin has access to Placement Drives, Attendance, and Offers."}), 403
        
    data = request.get_json() or {}
    student_id = data.get("student_id")
    company_id = data.get("company_id")
    role = data.get("role", "").strip()
    ctc = float(data.get("ctc_lpa", 0.0))
    drive_id = data.get("drive_id")
    offer_date_str = data.get("offer_date", "")
    
    if not student_id or not company_id or not role or not ctc:
        return jsonify({"error": "Student, Company, Role, and CTC (LPA) are required."}), 400
        
    offer_date = datetime.strptime(offer_date_str, "%Y-%m-%d").date() if offer_date_str else datetime.utcnow().date()
    
    offer = Offer(
        student_id=student_id,
        company_id=company_id,
        drive_id=drive_id,
        role=role,
        ctc_lpa=ctc,
        offer_date=offer_date,
        offer_letter_url=data.get("offer_letter_url", ""),
        created_by_id=user.id
    )
    
    db.session.add(offer)
    
    # Automatically update Student overall placement status to 'PLACED'
    student = Student.query.get(student_id)
    if student:
        student.placement_status = "PLACED"
        
    # Increment company offers count
    company = Company.query.get(company_id)
    if company:
        company.total_offers_count = (company.total_offers_count or 0) + 1
        
    db.session.commit()
    
    log_activity(user.id, "CREATE_OFFER", "Offer", offer.id, f"Recorded offer for {student.name} ({student.roll_no}) at {company.name} with CTC {ctc} LPA")
    
    return jsonify({"message": "Placement offer recorded successfully!", "offer": offer.to_dict()}), 201
