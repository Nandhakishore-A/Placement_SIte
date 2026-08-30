from flask import Blueprint, request, jsonify, send_file
from db_mongo import get_db
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
    
    db = get_db()
    filters = {}
    if dept_code != "ALL":
        filters["department_code"] = dept_code
    if status != "ALL":
        filters["placement_status"] = status
        
    students_cursor = db.students.find(filters).sort("roll_no", 1)
    students = []
    for s in students_cursor:
        if "_id" in s:
            s["_id"] = str(s["_id"])
        else:
            s["_id"] = str(s.get("id", ""))
        students.append(s)
        
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
    
    db = get_db()
    filters = {}
    if dept_code != "ALL":
        filters["department_code"] = dept_code
    if status != "ALL":
        filters["placement_status"] = status
        
    students_cursor = db.students.find(filters).sort("roll_no", 1)
    students = []
    for s in students_cursor:
        if "_id" in s:
            s["_id"] = str(s["_id"])
        else:
            s["_id"] = str(s.get("id", ""))
        students.append(s)
        
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
    db = get_db()
    filters = {}
    if company_id:
        filters["company_id"] = company_id
        
    offers_cursor = db.offers.find(filters).sort("offer_date", -1)
    offers = []
    for o in offers_cursor:
        if "_id" in o:
            o["_id"] = str(o["_id"])
        else:
            o["_id"] = str(o.get("id", ""))
        offers.append(o)
        
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
    db = get_db()
    filters = {}
    if stage != "ALL":
        filters["status"] = stage
        
    companies_cursor = db.companies.find(filters).sort("created_at", -1)
    companies = []
    for c in companies_cursor:
        if "_id" in c:
            c["_id"] = str(c["_id"])
        else:
            c["_id"] = str(c.get("id", ""))
        companies.append(c)
        
    excel_stream = generate_company_stage_excel(companies, filter_stage=stage)
    
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Company_Pipeline_Report_{stage}.xlsx"
    )

@reports_bp.route("/api/reports/stats", methods=["GET"])
@reports_bp.route("/api/reports/dashboard-stats", methods=["GET"])
@login_required
def get_reports_summary():
    user = get_current_user()
    db = get_db()
    
    # 1. Fast Student Stats Aggregation (single query)
    student_stats = list(db.students.aggregate([
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "placed": {
                    "$sum": {"$cond": [{"$eq": ["$placement_status", "PLACED"]}, 1, 0]}
                }
            }
        }
    ]))
    
    total_students = student_stats[0]["total"] if student_stats else 0
    placed_students = student_stats[0]["placed"] if student_stats else 0
    unplaced_students = total_students - placed_students
    
    data = {
        "total_students": total_students,
        "placed_students": placed_students,
        "unplaced_students": unplaced_students,
        "placement_percentage": round((placed_students / total_students * 100), 1) if total_students else 0
    }
    
    if user.role != "manager":
        # 2. Fast Company Stats Aggregation (single query)
        comp_stats = {
            item["_id"]: item["count"]
            for item in db.companies.aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ])
        }
        data["total_companies"] = sum(comp_stats.values())
        data["cold_companies"] = comp_stats.get("COLD", 0)
        data["warm_companies"] = comp_stats.get("WARM", 0)
        data["hot_companies"] = comp_stats.get("HOT", 0)
        data["completed_drives"] = comp_stats.get("DRIVE COMPLETED", 0)
        
        # 3. Fast Offers Stats Aggregation (single query)
        offer_stats = list(db.offers.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_offers": {"$sum": 1},
                    "highest_ctc": {"$max": "$ctc_lpa"},
                    "avg_ctc": {"$avg": "$ctc_lpa"}
                }
            }
        ]))
        if offer_stats:
            data["total_offers"] = offer_stats[0].get("total_offers", 0)
            data["highest_ctc"] = round(float(offer_stats[0].get("highest_ctc") or 0.0), 2)
            data["average_ctc"] = round(float(offer_stats[0].get("avg_ctc") or 0.0), 2)
        else:
            data["total_offers"] = 0
            data["highest_ctc"] = 0.0
            data["average_ctc"] = 0.0
            
    return jsonify(data)
