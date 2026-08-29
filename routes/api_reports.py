from flask import Blueprint, request, jsonify, send_file
from models import db, Student, Company, Offer, PlacementDrive, PlacementRegistration, PlacementAttendance
from services.report_service import (
    generate_overall_placement_excel,
    generate_offers_excel,
    generate_company_stage_excel,
    generate_overall_placement_pdf
)
from auth import login_required, get_current_user

reports_bp = Blueprint("reports_bp", __name__)

@reports_bp.route("/api/reports/overall-placement/excel", methods=["GET"])
@login_required
def download_overall_placement_excel():
    user = get_current_user()
    if user.role == "team_member":
        return jsonify({"error": "Access forbidden. Placement Team Members can only access Overall Dashboard and Company CRM."}), 403
        
    dept_code = request.args.get("department", "ALL")
    status = request.args.get("status", "ALL")
    
    query = Student.query
    if dept_code != "ALL":
        query = query.join(Student.department).filter(Student.department.has(code=dept_code))
    if status != "ALL":
        query = query.filter(Student.placement_status == status)
        
    students = [s.to_dict() for s in query.order_by(Student.roll_no.asc()).all()]
    excel_stream = generate_overall_placement_excel(students)
    
    filename = f"Overall_Placement_Report_{dept_code}_{status}.xlsx"
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route("/api/reports/overall-placement/pdf", methods=["GET"])
@login_required
def download_overall_placement_pdf():
    user = get_current_user()
    if user.role == "team_member":
        return jsonify({"error": "Access forbidden. Placement Team Members can only access Overall Dashboard and Company CRM."}), 403
        
    dept_code = request.args.get("department", "ALL")
    status = request.args.get("status", "ALL")
    
    query = Student.query
    if dept_code != "ALL":
        query = query.join(Student.department).filter(Student.department.has(code=dept_code))
    if status != "ALL":
        query = query.filter(Student.placement_status == status)
        
    students = [s.to_dict() for s in query.order_by(Student.roll_no.asc()).all()]
    pdf_stream = generate_overall_placement_pdf(students)
    
    filename = f"Overall_Placement_Report_{dept_code}_{status}.pdf"
    return send_file(
        pdf_stream,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route("/api/reports/offers/excel", methods=["GET"])
@login_required
def download_offers_excel():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin can export offers reports."}), 403
        
    company_id = request.args.get("company_id", type=int)
    query = Offer.query
    if company_id:
        query = query.filter(Offer.company_id == company_id)
        
    offers = [o.to_dict() for o in query.order_by(Offer.offer_date.desc()).all()]
    excel_stream = generate_offers_excel(offers)
    
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Campus_Placement_Offers_Report.xlsx"
    )

@reports_bp.route("/api/reports/companies/excel", methods=["GET"])
@login_required
def download_companies_excel():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin can export company pipeline reports."}), 403
        
    stage = request.args.get("stage", "ALL").upper()
    query = Company.query
    if stage != "ALL":
        query = query.filter(Company.status == stage)
        
    companies = [c.to_dict() for c in query.order_by(Company.created_at.desc()).all()]
    excel_stream = generate_company_stage_excel(companies, filter_stage=stage)
    
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Company_Pipeline_Report_{stage}.xlsx"
    )

@reports_bp.route("/api/reports/stats", methods=["GET"])
@login_required
def get_reports_summary():
    user = get_current_user()
    
    total_students = Student.query.count()
    placed_students = Student.query.filter_by(placement_status="PLACED").count()
    unplaced_students = total_students - placed_students
    
    data = {
        "total_students": total_students,
        "placed_students": placed_students,
        "unplaced_students": unplaced_students,
        "placement_percentage": round((placed_students / total_students * 100), 1) if total_students else 0
    }
    
    # Non-manager gets company & offer stats
    if user.role != "manager":
        data["total_companies"] = Company.query.count()
        data["cold_companies"] = Company.query.filter_by(status="COLD").count()
        data["warm_companies"] = Company.query.filter_by(status="WARM").count()
        data["hot_companies"] = Company.query.filter_by(status="HOT").count()
        data["completed_drives"] = Company.query.filter_by(status="DRIVE COMPLETED").count()
        data["total_offers"] = Offer.query.count()
        
        # Calculate highest & average CTC
        offers = Offer.query.all()
        if offers:
            ctc_vals = [o.ctc_lpa for o in offers if o.ctc_lpa]
            data["highest_ctc"] = max(ctc_vals) if ctc_vals else 0.0
            data["average_ctc"] = round(sum(ctc_vals) / len(ctc_vals), 2) if ctc_vals else 0.0
        else:
            data["highest_ctc"] = 0.0
            data["average_ctc"] = 0.0
            
    return jsonify(data)
