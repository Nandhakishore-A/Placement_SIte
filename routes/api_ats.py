from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from db_mongo import get_db, get_next_sequence
from services.gemini_service import analyze_resume_ats, analyze_raw_resume_text, extract_text_from_file, get_category_for_score
from auth import login_required, get_current_user, log_activity

ats_bp = Blueprint("ats_bp", __name__)

def ats_to_dict(doc):
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

@ats_bp.route("/api/ats/upload-and-analyze", methods=["POST"])
@login_required
def upload_and_analyze_resume():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin can access the Gemini ATS Engine."}), 403

    resume_text = ""
    file_name = ""
    json_data = request.get_json(silent=True) or {}
    
    if "resume_file" in request.files:
        file = request.files["resume_file"]
        if file and file.filename != "":
            file_name = secure_filename(file.filename)
            resume_text = extract_text_from_file(file, file_name)
            
    if not resume_text:
        resume_text = request.form.get("pasted_resume_text", "").strip() or json_data.get("pasted_resume_text", "").strip()
        
    if not resume_text:
        return jsonify({"error": "Please upload a resume file (PDF/DOCX/TXT) or paste your resume content."}), 400

    company_id = request.form.get("company_id", type=int) or json_data.get("company_id")
    student_id = request.form.get("student_id", type=int) or json_data.get("student_id")
    jd_text = (request.form.get("jd_text", "") or json_data.get("jd_text", "")).strip()
    role_name = (request.form.get("role_name", "") or json_data.get("role_name", "")).strip()

    db = get_db()
    company = db.companies.find_one({"id": int(company_id)}) if company_id else None
    if not jd_text:
        if company and company.get("jd_text"):
            jd_text = company["jd_text"]
        else:
            jd_text = "Software Engineer / Developer position requiring strong problem solving, coding proficiency, algorithms, web technologies, and database design."

    if not role_name and company:
        role_name = f"Role at {company.get('name')}"

    candidate_label = file_name if file_name else "Uploaded Candidate"
    student = None
    if student_id:
        student = db.students.find_one({"id": int(student_id)})
        if student:
            candidate_label = f"{student.get('name')} ({student.get('roll_no')})"

    analysis_res = analyze_raw_resume_text(resume_text, jd_text, role_name, candidate_label)

    # Save to database if student_id is provided
    if student_id and student:
        next_id = get_next_sequence("ats_id")
        db.ats_analyses.update_one(
            {"student_id": int(student_id), "company_id": int(company_id) if company_id else None},
            {
                "$set": {
                    "id": next_id,
                    "student_id": int(student_id),
                    "student_roll_no": student.get("roll_no"),
                    "student_name": student.get("name"),
                    "department_code": student.get("department_code"),
                    "company_id": int(company_id) if company_id else None,
                    "company_name": company.get("name") if company else "General Drive",
                    "ats_score": analysis_res["ats_score"],
                    "category": analysis_res["category"],
                    "matched_skills": ",".join(analysis_res["matched_skills"]),
                    "missing_skills": ",".join(analysis_res["missing_skills"]),
                    "summary": analysis_res["summary"],
                    "analyzed_by_id": user.id,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    log_activity(
        user.id,
        "ATS_RESUME_UPLOAD",
        "ATSAnalysis",
        student_id or 0,
        f"Uploaded resume evaluated for {candidate_label}. ATS Score: {analysis_res['ats_score']}% [{analysis_res['category']}]"
    )

    analysis_res["candidate_label"] = candidate_label
    analysis_res["file_name"] = file_name
    analysis_res["company_name"] = company.get("name") if company else "General Drive"
    analysis_res["role_name"] = role_name
    analysis_res["high_match_popup"] = {
        "trigger_popup": analysis_res["is_high_match"],
        "name": candidate_label,
        "score": analysis_res["ats_score"],
        "category": analysis_res["category"]
    }

    return jsonify(analysis_res)

@ats_bp.route("/api/ats/analyze", methods=["POST"])
@login_required
def analyze_ats():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin can access the Gemini ATS Engine."}), 403
        
    data = request.get_json() or {}
    student_id = data.get("student_id")
    company_id = data.get("company_id")
    drive_id = data.get("drive_id")
    jd_text = data.get("jd_text", "").strip()
    role_name = data.get("role_name", "").strip()
    
    if not student_id:
        return jsonify({"error": "student_id is required."}), 400
        
    db = get_db()
    student = db.students.find_one({"id": int(student_id)})
    if not student:
        return jsonify({"error": "Student not found"}), 404
        
    company = db.companies.find_one({"id": int(company_id)}) if company_id else None
    
    if not jd_text:
        if company and company.get("jd_text"):
            jd_text = company["jd_text"]
        else:
            jd_text = "Software Engineer / Developer position requiring strong problem solving, coding proficiency, algorithms, web technologies, and database design."
            
    if not role_name and company:
        role_name = f"Role at {company.get('name')}"
        
    student_dict = dict(student)
    analysis_res = analyze_resume_ats(student_dict, jd_text, role_name)
    
    next_id = get_next_sequence("ats_id")
    ats_doc = {
        "id": next_id,
        "student_id": int(student_id),
        "student_roll_no": student.get("roll_no"),
        "student_name": student.get("name"),
        "department_code": student.get("department_code"),
        "company_id": int(company_id) if company_id else None,
        "company_name": company.get("name") if company else "Campus Drive",
        "drive_id": int(drive_id) if drive_id else None,
        "ats_score": analysis_res["ats_score"],
        "category": analysis_res["category"],
        "matched_skills": ",".join(analysis_res["matched_skills"]),
        "missing_skills": ",".join(analysis_res["missing_skills"]),
        "summary": analysis_res["summary"],
        "analyzed_by_id": user.id,
        "created_at": datetime.utcnow()
    }
    
    db.ats_analyses.update_one(
        {"student_id": int(student_id), "company_id": int(company_id) if company_id else None},
        {"$set": ats_doc},
        upsert=True
    )
    
    log_activity(
        user.id,
        "ATS_ANALYSIS",
        "ATSAnalysis",
        next_id,
        f"ATS scan for {student.get('name')} ({student.get('roll_no')}) scored {analysis_res['ats_score']}% [{analysis_res['category']}]"
    )
    
    response_data = ats_to_dict(ats_doc)
    if ats_doc["ats_score"] >= 91:
        response_data["high_match_popup"] = {
            "trigger_popup": True,
            "roll_no": student.get("roll_no"),
            "name": student.get("name"),
            "department": student.get("department_code", ""),
            "score": ats_doc["ats_score"],
            "category": "91-100 (HIGH MATCH)"
        }
    else:
        response_data["high_match_popup"] = {"trigger_popup": False}
        
    return jsonify(response_data)

@ats_bp.route("/api/ats/batch-analyze", methods=["POST"])
@login_required
def batch_analyze_ats():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin can access the Gemini ATS Engine."}), 403
        
    data = request.get_json() or {}
    company_id = data.get("company_id")
    dept_code = data.get("department_code", "ALL")
    limit = int(data.get("limit", 20))
    jd_text = data.get("jd_text", "").strip()
    
    db = get_db()
    company = db.companies.find_one({"id": int(company_id)}) if company_id else None
    if not jd_text and company:
        jd_text = company.get("jd_text") or f"Recruitment for {company.get('name')}"
        
    filters = {}
    if dept_code != "ALL":
        filters["department_code"] = dept_code
        
    students_cursor = db.students.find(filters).limit(limit)
    results = []
    high_matches = []
    
    for s in students_cursor:
        s_dict = dict(s)
        res = analyze_resume_ats(s_dict, jd_text, company.get("name") if company else "Campus Drive")
        next_id = get_next_sequence("ats_id")
        
        ats_doc = {
            "id": next_id,
            "student_id": s.get("id"),
            "student_roll_no": s.get("roll_no"),
            "student_name": s.get("name"),
            "department_code": s.get("department_code"),
            "company_id": int(company_id) if company_id else None,
            "company_name": company.get("name") if company else "Campus Drive",
            "ats_score": res["ats_score"],
            "category": res["category"],
            "matched_skills": ",".join(res["matched_skills"]),
            "missing_skills": ",".join(res["missing_skills"]),
            "summary": res["summary"],
            "analyzed_by_id": user.id,
            "created_at": datetime.utcnow()
        }
        
        db.ats_analyses.update_one(
            {"student_id": s.get("id"), "company_id": int(company_id) if company_id else None},
            {"$set": ats_doc},
            upsert=True
        )
        
        results.append(ats_to_dict(ats_doc))
        if res["is_high_match"]:
            high_matches.append({
                "roll_no": s.get("roll_no"),
                "name": s.get("name"),
                "department": s.get("department_code", ""),
                "score": res["ats_score"]
            })
            
    log_activity(user.id, "BATCH_ATS_SCAN", "ATSAnalysis", len(results), f"Completed batch ATS evaluation for {len(results)} students")
    
    return jsonify({
        "total_analyzed": len(results),
        "high_matches_count": len(high_matches),
        "high_matches_list": high_matches,
        "results": results
    })

@ats_bp.route("/api/ats/results", methods=["GET"])
@login_required
def get_ats_results():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin can access ATS results."}), 403
        
    category = request.args.get("category", "").strip()
    company_id = request.args.get("company_id", type=int)
    
    db = get_db()
    filters = {}
    if category and category != "ALL":
        filters["category"] = category
    if company_id:
        filters["company_id"] = company_id
        
    records_cursor = db.ats_analyses.find(filters).sort("ats_score", -1).limit(100)
    records = [ats_to_dict(r) for r in records_cursor]
    return jsonify(records)
