from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import db, Student, Company, PlacementDrive, ATSAnalysis
from services.gemini_service import analyze_resume_ats, analyze_raw_resume_text, extract_text_from_file, get_category_for_score
from auth import login_required, get_current_user, log_activity

ats_bp = Blueprint("ats_bp", __name__)

@ats_bp.route("/api/ats/upload-and-analyze", methods=["POST"])
@login_required
def upload_and_analyze_resume():
    user = get_current_user()
    if user.role != "admin":
        return jsonify({"error": "Access forbidden. Only Admin can access the Gemini ATS Engine."}), 403

    resume_text = ""
    file_name = ""
    json_data = request.get_json(silent=True) or {}
    
    # Check if a file was uploaded
    if "resume_file" in request.files:
        file = request.files["resume_file"]
        if file and file.filename != "":
            file_name = secure_filename(file.filename)
            resume_text = extract_text_from_file(file, file_name)
            
    # Fallback to pasted text if file empty or text provided directly
    if not resume_text:
        resume_text = request.form.get("pasted_resume_text", "").strip() or json_data.get("pasted_resume_text", "").strip()
        
    if not resume_text:
        return jsonify({"error": "Please upload a resume file (PDF/DOCX/TXT) or paste your resume content."}), 400

    company_id = request.form.get("company_id", type=int) or json_data.get("company_id")
    student_id = request.form.get("student_id", type=int) or json_data.get("student_id")
    jd_text = (request.form.get("jd_text", "") or json_data.get("jd_text", "")).strip()
    role_name = (request.form.get("role_name", "") or json_data.get("role_name", "")).strip()

    company = Company.query.get(company_id) if company_id else None
    if not jd_text:
        if company and company.jd_text:
            jd_text = company.jd_text
        else:
            jd_text = "Software Engineer / Developer position requiring strong problem solving, coding proficiency, algorithms, web technologies, and database design."

    if not role_name and company:
        role_name = f"Role at {company.name}"

    candidate_label = file_name if file_name else "Uploaded Candidate"
    if student_id:
        s = Student.query.get(student_id)
        if s:
            candidate_label = f"{s.name} ({s.roll_no})"

    analysis_res = analyze_raw_resume_text(resume_text, jd_text, role_name, candidate_label)

    # Save to database if student_id is provided
    if student_id:
        student = Student.query.get(student_id)
        if student:
            ats_record = ATSAnalysis.query.filter_by(student_id=student.id, company_id=company_id).first()
            if not ats_record:
                ats_record = ATSAnalysis(
                    student_id=student.id,
                    company_id=company_id,
                    ats_score=analysis_res["ats_score"],
                    category=analysis_res["category"],
                    matched_skills=",".join(analysis_res["matched_skills"]),
                    missing_skills=",".join(analysis_res["missing_skills"]),
                    summary=analysis_res["summary"],
                    analyzed_by_id=user.id
                )
                db.session.add(ats_record)
            else:
                ats_record.ats_score = analysis_res["ats_score"]
                ats_record.category = analysis_res["category"]
                ats_record.matched_skills = ",".join(analysis_res["matched_skills"])
                ats_record.missing_skills = ",".join(analysis_res["missing_skills"])
                ats_record.summary = analysis_res["summary"]
                ats_record.analyzed_by_id = user.id
            db.session.commit()

    log_activity(
        user.id,
        "ATS_RESUME_UPLOAD",
        "ATSAnalysis",
        student_id or 0,
        f"Uploaded resume evaluated for {candidate_label}. ATS Score: {analysis_res['ats_score']}% [{analysis_res['category']}]"
    )

    analysis_res["candidate_label"] = candidate_label
    analysis_res["file_name"] = file_name
    analysis_res["company_name"] = company.name if company else "General Drive"
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
        
    student = Student.query.get_or_404(student_id)
    company = Company.query.get(company_id) if company_id else None
    
    if not jd_text:
        if company and company.jd_text:
            jd_text = company.jd_text
        else:
            jd_text = "Software Engineer / Developer position requiring strong problem solving, coding proficiency, algorithms, web technologies, and database design."
            
    if not role_name and company:
        role_name = f"Role at {company.name}"
        
    student_dict = student.to_dict()
    analysis_res = analyze_resume_ats(student_dict, jd_text, role_name)
    
    # Save or update in database
    ats_record = ATSAnalysis.query.filter_by(student_id=student.id, company_id=company_id).first()
    if not ats_record:
        ats_record = ATSAnalysis(
            student_id=student.id,
            company_id=company_id,
            drive_id=drive_id,
            ats_score=analysis_res["ats_score"],
            category=analysis_res["category"],
            matched_skills=",".join(analysis_res["matched_skills"]),
            missing_skills=",".join(analysis_res["missing_skills"]),
            summary=analysis_res["summary"],
            analyzed_by_id=user.id
        )
        db.session.add(ats_record)
    else:
        ats_record.ats_score = analysis_res["ats_score"]
        ats_record.category = analysis_res["category"]
        ats_record.matched_skills = ",".join(analysis_res["matched_skills"])
        ats_record.missing_skills = ",".join(analysis_res["missing_skills"])
        ats_record.summary = analysis_res["summary"]
        ats_record.analyzed_by_id = user.id
        
    db.session.commit()
    
    log_activity(
        user.id,
        "ATS_ANALYSIS",
        "ATSAnalysis",
        ats_record.id,
        f"ATS scan for {student.name} ({student.roll_no}) scored {analysis_res['ats_score']}% [{analysis_res['category']}]"
    )
    
    response_data = ats_record.to_dict()
    # Ensure popup details for 91-100% are prominent
    if ats_record.ats_score >= 91:
        response_data["high_match_popup"] = {
            "trigger_popup": True,
            "roll_no": student.roll_no,
            "name": student.name,
            "department": student.department.code if student.department else "",
            "score": ats_record.ats_score,
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
    
    company = Company.query.get(company_id) if company_id else None
    if not jd_text and company:
        jd_text = company.jd_text or f"Recruitment for {company.name}"
        
    query = Student.query
    if dept_code != "ALL":
        query = query.join(Student.department).filter(Student.department.has(code=dept_code))
        
    students = query.limit(limit).all()
    results = []
    high_matches = []
    
    for s in students:
        s_dict = s.to_dict()
        res = analyze_resume_ats(s_dict, jd_text, company.name if company else "Campus Drive")
        
        ats_rec = ATSAnalysis(
            student_id=s.id,
            company_id=company_id,
            ats_score=res["ats_score"],
            category=res["category"],
            matched_skills=",".join(res["matched_skills"]),
            missing_skills=",".join(res["missing_skills"]),
            summary=res["summary"],
            analyzed_by_id=user.id
        )
        db.session.add(ats_rec)
        
        item = ats_rec.to_dict()
        results.append(item)
        if res["is_high_match"]:
            high_matches.append({
                "roll_no": s.roll_no,
                "name": s.name,
                "department": s.department.code if s.department else "",
                "score": res["ats_score"]
            })
            
    db.session.commit()
    log_activity(user.id, "BATCH_ATS_SCAN", "ATSAnalysis", len(results), f"Completed batch ATS evaluation for {len(results)} students")
    
    return jsonify({
        "total_analyzed": len(results),
        "high_matches_count": len(high_matches),
        "high_matches_list": high_matches, # For special popup listing!
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
    
    query = ATSAnalysis.query
    if category and category != "ALL":
        query = query.filter(ATSAnalysis.category == category)
    if company_id:
        query = query.filter(ATSAnalysis.company_id == company_id)
        
    records = query.order_by(ATSAnalysis.ats_score.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in records])
