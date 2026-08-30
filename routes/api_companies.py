import re
from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_file
from db_mongo import get_db, get_next_sequence
from auth import login_required, get_current_user, log_activity
from services.report_service import generate_jd_docx

companies_bp = Blueprint("companies_bp", __name__)

def company_to_dict(doc):
    if not doc:
        return {}
    res = dict(doc)
    if "_id" in res:
        res["_id"] = str(res["_id"])
    else:
        res["_id"] = str(res.get("id", ""))
    if isinstance(res.get("created_at"), datetime):
        res["created_at"] = res["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(res.get("forwarded_at"), datetime):
        res["forwarded_at"] = res["forwarded_at"].strftime("%Y-%m-%d %H:%M")
    if isinstance(res.get("approved_at"), datetime):
        res["approved_at"] = res["approved_at"].strftime("%Y-%m-%d %H:%M")
        
    db = get_db()
    if "added_by_id" in res and res["added_by_id"]:
        u = db.users.find_one({"id": res["added_by_id"]})
        if u:
            res["added_by_name"] = u.get("full_name")
            res["added_by_member"] = u.get("member_id")
            
    if "approved_by_id" in res and res["approved_by_id"]:
        u = db.users.find_one({"id": res["approved_by_id"]})
        if u:
            res["approved_by_name"] = u.get("full_name")
            
    return res

@companies_bp.route("/api/companies", methods=["GET"])
@login_required
def get_companies():
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden. Manager role is restricted to Student Management only."}), 403
        
    stage = request.args.get("status", "").strip().upper()
    recruiter_view = request.args.get("recruiter_view", "false").lower() == "true"
    search = request.args.get("search", "").strip()
    
    db = get_db()
    filters = {}
    
    if recruiter_view:
        filters["status"] = {"$in": ["WARM", "HOT", "DRIVE COMPLETED"]}
    elif stage and stage != "ALL":
        filters["status"] = stage
        
    if search:
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        filters["$or"] = [
            {"name": search_regex},
            {"location": search_regex},
            {"contact_person": search_regex},
            {"email": search_regex}
        ]
        
    companies_cursor = db.companies.find(filters).sort("created_at", -1)
    companies = [company_to_dict(c) for c in companies_cursor]
    return jsonify(companies)

@companies_bp.route("/api/companies/<int:company_id>", methods=["GET"])
@login_required
def get_company_detail(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    db = get_db()
    company = db.companies.find_one({"id": company_id})
    if not company:
        return jsonify({"error": "Company not found"}), 404
        
    data = company_to_dict(company)
    
    history_cursor = db.company_status_history.find({"company_id": company_id}).sort("changed_at", -1)
    history = []
    for h in history_cursor:
        if "_id" in h:
            h["_id"] = str(h["_id"])
        else:
            h["_id"] = str(h.get("id", ""))
        if isinstance(h.get("changed_at"), datetime):
            h["changed_at"] = h["changed_at"].strftime("%Y-%m-%d %H:%M")
        history.append(h)
        
    drives_cursor = db.placement_drives.find({"company_id": company_id})
    drives = []
    for d in drives_cursor:
        if "_id" in d:
            d["_id"] = str(d["_id"])
        else:
            d["_id"] = str(d.get("id", ""))
        drives.append(d)
        
    data["history"] = history
    data["drives"] = drives
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
    
    maps_link = data.get("google_maps_link", "").strip()
    if not maps_link and location:
        maps_link = f"https://www.google.com/maps/search/?api=1&query={location.replace(' ', '+')}"
        
    next_id = get_next_sequence("company_id")
    is_admin = (user.role == "admin")
    
    forwarded_note = data.get("notes") or data.get("forwarded_note") or (f"New company proposed by {user.member_id} ({user.full_name})" if not is_admin else "")
    
    company_doc = {
        "id": next_id,
        "name": name,
        "location": location,
        "website": data.get("website", ""),
        "contact_person": contact_person,
        "mobile_no": mobile,
        "email": email,
        "employee_count": data.get("employee_count", ""),
        "google_maps_link": maps_link,
        "address": data.get("address", ""),
        "ctc_lpa": ctc,
        "jd_file_url": data.get("jd_file_url", ""),
        "jd_text": data.get("jd_text", ""),
        "status": status,
        "is_approved": is_admin,
        "approved_by_id": user.id if is_admin else None,
        "approved_at": datetime.utcnow() if is_admin else None,
        "forwarded_to_admin": not is_admin,
        "forwarded_note": forwarded_note,
        "forwarded_by_id": user.id if not is_admin else None,
        "forwarded_at": datetime.utcnow() if not is_admin else None,
        "added_by_id": user.id,
        "total_offers_count": total_offers,
        "created_at": datetime.utcnow()
    }
    
    db = get_db()
    db.companies.insert_one(company_doc)
    
    # Status history
    db.company_status_history.insert_one({
        "company_id": next_id,
        "old_status": None,
        "new_status": status,
        "changed_by": user.full_name,
        "changed_by_id": user.id,
        "remarks": f"Company added by {user.member_id} ({user.full_name})",
        "changed_at": datetime.utcnow()
    })
    
    # Send Email Notification to Admin if added by Team Member / Lead
    email_res = None
    if not is_admin:
        from services.email_service import send_admin_drive_proposal_email
        email_res = send_admin_drive_proposal_email(
            company_to_dict(company_doc),
            user,
            proposed_date=data.get("drive_date_proposed") or data.get("proposed_date"),
            notes=forwarded_note
        )
    
    log_activity(
        user.id,
        "CREATE_COMPANY",
        "Company",
        next_id,
        f"Added company {name} [{status}] (Email sent to Admin: {bool(email_res)})"
    )
    
    return jsonify({
        "message": "Company created successfully! Email notification dispatched to Admin for verification.",
        "company": company_to_dict(company_doc),
        "email_sent": bool(email_res)
    }), 201

@companies_bp.route("/api/companies/<int:company_id>/status", methods=["PUT"])
@login_required
def update_company_status(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    db = get_db()
    company = db.companies.find_one({"id": company_id})
    if not company:
        return jsonify({"error": "Company not found"}), 404
        
    data = request.get_json() or {}
    new_status = data.get("status", "").strip().upper()
    remarks = data.get("remarks", "").strip()
    offers_count = data.get("total_offers_count")
    
    if new_status not in ["COLD", "WARM", "HOT", "DRIVE COMPLETED"]:
        return jsonify({"error": "Invalid status value."}), 400
        
    old_status = company.get("status")
    update_data = {"status": new_status}
    if new_status == "DRIVE COMPLETED" and offers_count is not None:
        update_data["total_offers_count"] = int(offers_count)
        
    db.companies.update_one({"id": company_id}, {"$set": update_data})
    
    db.company_status_history.insert_one({
        "company_id": company_id,
        "old_status": old_status,
        "new_status": new_status,
        "changed_by": user.full_name,
        "changed_by_id": user.id,
        "remarks": remarks or f"Status changed to {new_status}",
        "changed_at": datetime.utcnow()
    })
    
    log_activity(user.id, "UPDATE_COMPANY_STATUS", "Company", company_id, f"Status updated from {old_status} to {new_status}")
    
    updated_doc = db.companies.find_one({"id": company_id})
    return jsonify({"message": f"Status updated to {new_status}", "company": company_to_dict(updated_doc)})

@companies_bp.route("/api/companies/<int:company_id>/forward", methods=["POST"])
@login_required
def forward_company_to_admin(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    db = get_db()
    company = db.companies.find_one({"id": company_id})
    if not company:
        return jsonify({"error": "Company not found"}), 404
        
    data = request.get_json() or {}
    note = data.get("note", f"Forwarded by {user.member_id} for Admin review and drive approval.")
    proposed_date = data.get("drive_date_proposed") or data.get("proposed_date")
    
    db.companies.update_one(
        {"id": company_id},
        {
            "$set": {
                "forwarded_to_admin": True,
                "forwarded_note": note,
                "forwarded_by_id": user.id,
                "forwarded_at": datetime.utcnow()
            }
        }
    )

    updated_company = company_to_dict(db.companies.find_one({"id": company_id}))
    
    from services.email_service import send_admin_drive_proposal_email
    email_res = send_admin_drive_proposal_email(updated_company, user, proposed_date=proposed_date, notes=note)
    
    log_activity(
        user.id,
        "FORWARD_ADMIN",
        "Company",
        company_id,
        f"{user.member_id} ({user.full_name}) forwarded {company.get('name')} to Admin with Email Alert."
    )
    
    return jsonify({
        "message": f"Company '{company.get('name')}' forwarded to Admin successfully! Email notification dispatched to Admin.",
        "company": updated_company,
        "email_sent": bool(email_res)
    })

@companies_bp.route("/api/companies/pending-notifications", methods=["GET"])
@login_required
def get_pending_company_notifications():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"count": 0, "companies": []})
        
    db = get_db()
    pending = list(db.companies.find({"forwarded_to_admin": True, "is_approved": False}).sort("forwarded_at", -1))
    return jsonify({
        "count": len(pending),
        "companies": [company_to_dict(c) for c in pending]
    })

@companies_bp.route("/api/companies/<int:company_id>/approve", methods=["PUT"])
@login_required
def approve_company(company_id):
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Only Admin can approve or reject company drives."}), 403
        
    db = get_db()
    company = db.companies.find_one({"id": company_id})
    if not company:
        return jsonify({"error": "Company not found"}), 404
        
    data = request.get_json() or {}
    approve_flag = bool(data.get("is_approved", True))
    review_note = data.get("review_note")
    
    db.companies.update_one(
        {"id": company_id},
        {
            "$set": {
                "is_approved": approve_flag,
                "approved_by_id": user.id if approve_flag else None,
                "approved_at": datetime.utcnow() if approve_flag else None,
                "forwarded_to_admin": False if approve_flag else company.get("forwarded_to_admin", False)
            }
        }
    )

    updated_company = company_to_dict(db.companies.find_one({"id": company_id}))
    
    if approve_flag:
        from services.email_service import send_team_drive_approval_email
        send_team_drive_approval_email(updated_company, user, review_note=review_note)
    
    action_text = "APPROVED" if approve_flag else "REJECTED/UNAPPROVED"
    log_activity(user.id, "ADMIN_APPROVAL", "Company", company_id, f"Admin {action_text} company drive for {company.get('name')}")
    
    return jsonify({
        "message": f"Company proposal for '{company.get('name')}' officially {'ACCEPTED & APPROVED' if approve_flag else 'REJECTED'}. Confirmation email sent to team.",
        "company": updated_company
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
        
    db = get_db()
    company = db.companies.find_one({"id": company_id})
    if not company:
        return jsonify({"error": "Company not found"}), 404
        
    data = request.get_json() or {}
    update_fields = {}
    
    for key in [
        "name", "location", "website", "contact_person", "mobile_no", "email",
        "employee_count", "google_maps_link", "address", "jd_file_url", "jd_text"
    ]:
        if key in data:
            update_fields[key] = data[key]
            
    if "ctc_lpa" in data:
        update_fields["ctc_lpa"] = float(data["ctc_lpa"])
    if "total_offers_count" in data:
        update_fields["total_offers_count"] = int(data["total_offers_count"])
        
    db.companies.update_one({"id": company_id}, {"$set": update_fields})
    log_activity(user.id, "UPDATE_COMPANY", "Company", company_id, f"Updated company details for {company.get('name')}")
    
    updated_doc = db.companies.find_one({"id": company_id})
    return jsonify({"message": "Company updated successfully", "company": company_to_dict(updated_doc)})

@companies_bp.route("/api/companies/<int:company_id>", methods=["DELETE"])
@login_required
def delete_company(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403
        
    db = get_db()
    company = db.companies.find_one({"id": company_id})
    if not company:
        return jsonify({"error": "Company not found"}), 404
        
    name = company.get("name")
    db.companies.delete_one({"id": company_id})
    db.company_status_history.delete_many({"company_id": company_id})
    db.placement_drives.delete_many({"company_id": company_id})
    
    log_activity(user.id, "DELETE_COMPANY", "Company", company_id, f"Deleted company {name}")
    return jsonify({"message": f"Company {name} deleted successfully."})

@companies_bp.route("/api/companies/<int:company_id>/jd/download", methods=["GET"])
@login_required
def download_company_jd_docx(company_id):
    user = get_current_user()
    if user.role == "manager":
        return jsonify({"error": "Access forbidden for Manager."}), 403

    db = get_db()
    company = db.companies.find_one({"id": company_id})
    if not company:
        return jsonify({"error": "Company not found"}), 404
        
    doc_io = generate_jd_docx(company_to_dict(company))
    
    clean_name = "".join(c for c in company.get("name", "Company") if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"{clean_name}_Job_Description.docx"

    log_activity(user.id, "DOWNLOAD_JD_DOCX", "Company", company_id, f"Downloaded JD Docx for {company.get('name')}")
    
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

