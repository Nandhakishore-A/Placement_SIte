from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_file
from models import db, Company, CompanyStatusHistory, ActivityLog, User
from auth import login_required, get_current_user, log_activity
from services.report_service import generate_jd_docx

companies_bp = Blueprint("companies_bp", __name__)

@companies_bp.route("/api/companies", methods=["GET"])
@login_required
def get_companies():
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden. Manager role is restricted to Student Management only."}), 403
        
    stage = request.args.get("status", "").strip().upper()  # COLD, WARM, HOT, DRIVE COMPLETED, or ALL
    recruiter_view = request.args.get("recruiter_view", "false").lower() == "true"
    search = request.args.get("search", "").strip()
    
    query = Company.query
    
    if recruiter_view:
        # Recruiters only see WARM, HOT, DRIVE COMPLETED
        query = query.filter(Company.status.in_(["WARM", "HOT", "DRIVE COMPLETED"]))
    elif stage and stage != "ALL":
        query = query.filter(Company.status == stage)
        
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            db.or_(
                Company.name.ilike(search_fmt),
                Company.location.ilike(search_fmt),
                Company.contact_person.ilike(search_fmt),
                Company.email.ilike(search_fmt)
            )
        )
        
    companies = query.order_by(Company.created_at.desc()).all()
    return jsonify([c.to_dict() for c in companies])

@companies_bp.route("/api/companies/<int:company_id>", methods=["GET"])
@login_required
def get_company_detail(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    company = Company.query.get_or_404(company_id)
    data = company.to_dict()
    data["history"] = [h.to_dict() for h in company.status_history]
    data["drives"] = [d.to_dict() for d in company.drives]
    return jsonify(data)

@companies_bp.route("/api/companies", methods=["POST"])
@login_required
def create_company():
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden. Manager cannot add companies."}), 403
        
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    location = data.get("location", "").strip()
    contact_person = data.get("contact_person", "").strip()
    mobile = data.get("mobile_no", "").strip()
    email = data.get("email", "").strip()
    
    if not name or not location or not contact_person or not mobile or not email:
        return jsonify({"error": "Name, Location, Contact Person, Mobile, and Email are required."}), 400
        
    status = data.get("status", "COLD").strip().upper()
    if status not in ["COLD", "WARM", "HOT", "DRIVE COMPLETED"]:
        status = "COLD"
        
    ctc = float(data.get("ctc_lpa", 0.0))
    total_offers = int(data.get("total_offers_count", 0)) if status == "DRIVE COMPLETED" else 0
    
    # Auto-build Google Maps search URL if plain address provided
    maps_link = data.get("google_maps_link", "").strip()
    if not maps_link and location:
        maps_link = f"https://www.google.com/maps/search/?api=1&query={location.replace(' ', '+')}"
        
    company = Company(
        name=name,
        location=location,
        website=data.get("website", ""),
        contact_person=contact_person,
        mobile_no=mobile,
        email=email,
        employee_count=data.get("employee_count", ""),
        google_maps_link=maps_link,
        address=data.get("address", ""),
        ctc_lpa=ctc,
        jd_file_url=data.get("jd_file_url", ""),
        jd_text=data.get("jd_text", ""),
        status=status,
        is_approved=(user.role == "admin"), # Auto approved if admin adds it
        added_by_id=user.id,
        total_offers_count=total_offers
    )

    # If submitted by Team Lead / Member, automatically mark for Admin verification
    if user.role != "admin":
        company.forwarded_to_admin = True
        company.forwarded_note = data.get("notes") or data.get("forwarded_note") or f"New company proposed by {user.member_id} ({user.full_name})"
        company.forwarded_by_id = user.id
        company.forwarded_at = datetime.utcnow()
    
    db.session.add(company)
    db.session.commit()
    
    # Initial status history entry
    hist = CompanyStatusHistory(
        company_id=company.id,
        old_status=None,
        new_status=status,
        changed_by_id=user.id,
        remarks=f"Company added by {user.member_id} ({user.full_name})"
    )
    db.session.add(hist)
    db.session.commit()

    # Send Email Notification to Admin if added by Team Member / Lead
    email_res = None
    if user.role != "admin":
        from services.email_service import send_admin_drive_proposal_email
        email_res = send_admin_drive_proposal_email(
            company.to_dict(),
            user,
            proposed_date=data.get("drive_date_proposed") or data.get("proposed_date"),
            notes=company.forwarded_note
        )
    
    log_activity(
        user.id,
        "CREATE_COMPANY",
        "Company",
        company.id,
        f"Added company {company.name} [{status}] (Email sent to Admin: {bool(email_res)})"
    )
    
    return jsonify({
        "message": "Company created successfully! Email notification dispatched to Admin for verification.",
        "company": company.to_dict(),
        "email_sent": bool(email_res)
    }), 201

@companies_bp.route("/api/companies/<int:company_id>/status", methods=["PUT"])
@login_required
def update_company_status(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    company = Company.query.get_or_404(company_id)
    data = request.get_json() or {}
    new_status = data.get("status", "").strip().upper()
    remarks = data.get("remarks", "").strip()
    offers_count = data.get("total_offers_count")
    
    if new_status not in ["COLD", "WARM", "HOT", "DRIVE COMPLETED"]:
        return jsonify({"error": "Invalid status value."}), 400
        
    old_status = company.status
    company.status = new_status
    if new_status == "DRIVE COMPLETED" and offers_count is not None:
        company.total_offers_count = int(offers_count)
        
    history = CompanyStatusHistory(
        company_id=company.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=user.id,
        remarks=remarks or f"Status changed to {new_status}"
    )
    db.session.add(history)
    db.session.commit()
    
    log_activity(user.id, "UPDATE_COMPANY_STATUS", "Company", company.id, f"Status updated from {old_status} to {new_status}")
    
    return jsonify({"message": f"Status updated to {new_status}", "company": company.to_dict()})

@companies_bp.route("/api/companies/<int:company_id>/forward", methods=["POST"])
@login_required
def forward_company_to_admin(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    company = Company.query.get_or_404(company_id)
    data = request.get_json() or {}
    note = data.get("note", f"Forwarded by {user.member_id} for Admin review and drive approval.")
    proposed_date = data.get("drive_date_proposed") or data.get("proposed_date")
    
    company.forwarded_to_admin = True
    company.forwarded_note = note
    company.forwarded_by_id = user.id
    company.forwarded_at = datetime.utcnow()
    db.session.commit()

    # Send Email Notification to Admin
    from services.email_service import send_admin_drive_proposal_email
    email_res = send_admin_drive_proposal_email(company.to_dict(), user, proposed_date=proposed_date, notes=note)
    
    log_activity(
        user.id,
        "FORWARD_ADMIN",
        "Company",
        company.id,
        f"{user.member_id} ({user.full_name}) forwarded {company.name} (CTC: {company.ctc_lpa} LPA) to Admin with Email Alert. Note: {note}"
    )
    
    return jsonify({
        "message": f"Company '{company.name}' forwarded to Admin successfully! Email notification dispatched to Admin.",
        "company": company.to_dict(),
        "email_sent": bool(email_res)
    })

@companies_bp.route("/api/companies/pending-notifications", methods=["GET"])
@login_required
def get_pending_company_notifications():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"count": 0, "companies": []})
        
    pending = Company.query.filter_by(forwarded_to_admin=True, is_approved=False).order_by(Company.forwarded_at.desc()).all()
    return jsonify({
        "count": len(pending),
        "companies": [c.to_dict() for c in pending]
    })

@companies_bp.route("/api/companies/<int:company_id>/approve", methods=["PUT"])
@login_required
def approve_company(company_id):
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Only Admin can approve or reject company drives."}), 403
        
    company = Company.query.get_or_404(company_id)
    data = request.get_json() or {}
    approve_flag = bool(data.get("is_approved", True))
    review_note = data.get("review_note")
    
    company.is_approved = approve_flag
    company.approved_by_id = user.id if approve_flag else None
    company.approved_at = datetime.utcnow() if approve_flag else None
    if approve_flag:
        company.forwarded_to_admin = False # Resolve pending notification once approved
        
    db.session.commit()

    # Send confirmation email back to placement team
    if approve_flag:
        from services.email_service import send_team_drive_approval_email
        send_team_drive_approval_email(company.to_dict(), user, review_note=review_note)
    
    action_text = "APPROVED" if approve_flag else "REJECTED/UNAPPROVED"
    log_activity(user.id, "ADMIN_APPROVAL", "Company", company.id, f"Admin {action_text} company drive for {company.name}")
    
    return jsonify({
        "message": f"Company proposal for '{company.name}' officially {'ACCEPTED & APPROVED' if approve_flag else 'REJECTED'}. Confirmation email sent to team.",
        "company": company.to_dict()
    })

@companies_bp.route("/api/companies/email-logs", methods=["GET"])
@login_required
def get_company_email_logs():
    from services.email_service import DISPATCHED_EMAILS
    return jsonify(DISPATCHED_EMAILS)


@companies_bp.route("/api/companies/<int:company_id>", methods=["PUT"])
@login_required
def update_company(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    company = Company.query.get_or_404(company_id)
    data = request.get_json() or {}
    
    company.name = data.get("name", company.name)
    company.location = data.get("location", company.location)
    company.website = data.get("website", company.website)
    company.contact_person = data.get("contact_person", company.contact_person)
    company.mobile_no = data.get("mobile_no", company.mobile_no)
    company.email = data.get("email", company.email)
    company.employee_count = data.get("employee_count", company.employee_count)
    company.google_maps_link = data.get("google_maps_link", company.google_maps_link)
    company.address = data.get("address", company.address)
    company.ctc_lpa = float(data.get("ctc_lpa", company.ctc_lpa))
    company.jd_file_url = data.get("jd_file_url", company.jd_file_url)
    company.jd_text = data.get("jd_text", company.jd_text)
    if "total_offers_count" in data:
        company.total_offers_count = int(data["total_offers_count"])
        
    db.session.commit()
    log_activity(user.id, "UPDATE_COMPANY", "Company", company.id, f"Updated company details for {company.name}")
    
    return jsonify({"message": "Company updated successfully", "company": company.to_dict()})

@companies_bp.route("/api/companies/<int:company_id>", methods=["DELETE"])
@login_required
def delete_company(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    company = Company.query.get_or_404(company_id)
    name = company.name
    
    db.session.delete(company)
    db.session.commit()
    
    log_activity(user.id, "DELETE_COMPANY", "Company", company_id, f"Deleted company {name}")
    return jsonify({"message": f"Company {name} deleted successfully."})

@companies_bp.route("/api/companies/<int:company_id>/jd/download", methods=["GET"])
@login_required
def download_company_jd_docx(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403

    company = Company.query.get_or_404(company_id)
    doc_io = generate_jd_docx(company.to_dict())
    
    clean_name = "".join(c for c in company.name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"{clean_name}_Job_Description.docx"

    log_activity(user.id, "DOWNLOAD_JD_DOCX", "Company", company.id, f"Downloaded JD Docx for {company.name}")
    
    return send_file(
        doc_io,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )

@companies_bp.route("/api/companies/jd/custom-download", methods=["POST"])
@login_required
def download_custom_jd_docx():
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403

    data = request.get_json() or {}
    company_data = {
        "name": data.get("company_name") or "Campus Placement Drive",
        "location": data.get("location") or "Campus / Pan India",
        "ctc_lpa": float(data.get("ctc_lpa") or 0.0),
        "contact_person": data.get("contact_person") or "Placement Coordinator",
        "email": data.get("email") or "placement@college.edu",
        "mobile_no": data.get("mobile_no") or "9876543210",
        "website": data.get("website") or "https://placement.college.edu",
        "status": data.get("status") or "HOT",
        "jd_text": data.get("jd_text") or "Candidate will work on software development, technical implementation, and system problem solving."
    }

    doc_io = generate_jd_docx(company_data)
    clean_name = "".join(c for c in company_data["name"] if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"{clean_name}_Job_Description.docx"

    log_activity(user.id, "DOWNLOAD_CUSTOM_JD_DOCX", "Company", 0, f"Downloaded custom JD Docx for {company_data['name']}")

    return send_file(
        doc_io,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )

