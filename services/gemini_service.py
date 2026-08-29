import os
import io
import json
import re
from config import Config

def get_category_for_score(score: int) -> str:
    if score <= 60:
        return "0-60"
    elif score <= 70:
        return "61-70"
    elif score <= 80:
        return "71-80"
    elif score <= 90:
        return "81-90"
    else:
        return "91-100"

def extract_text_from_file(file_storage, filename: str = "") -> str:
    """
    Extracts plain text from PDF, DOCX, or TXT file uploads.
    """
    if not filename and hasattr(file_storage, 'filename'):
        filename = file_storage.filename or ""
        
    ext = os.path.splitext(filename)[1].lower()
    content = file_storage.read()
    
    # Reset stream pointer
    if hasattr(file_storage, 'seek'):
        file_storage.seek(0)
        
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text_pages = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_pages.append(t)
            return "\n".join(text_pages).strip()
        except Exception as e:
            print(f"Error parsing PDF with pypdf: {e}")
            return ""
            
    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()
        except Exception as e:
            print(f"Error parsing DOCX: {e}")
            return ""
            
    else: # Default text / txt
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1", errors="ignore")

def analyze_raw_resume_text(resume_text: str, jd_text: str, role_name: str = "", candidate_name: str = "Candidate") -> dict:
    """
    Evaluates uploaded resume text against Job Description using Gemini 2.5 Flash AI or intelligent heuristic engine.
    """
    if not resume_text or not resume_text.strip():
        return {
            "ats_score": 0,
            "category": "0-60",
            "matched_skills": [],
            "missing_skills": ["No readable text found in resume"],
            "summary": "The uploaded resume was empty or unreadable.",
            "recommendations": ["Please upload a standard PDF or DOCX file with readable text."],
            "is_high_match": False,
            "extracted_preview": ""
        }

    gemini_key = Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            
            prompt = f"""
You are an expert AI Applicant Tracking System (ATS) and Resume Auditor.
Analyze the following Candidate Resume against the specified Job Description for the role: "{role_name or 'Software Engineer'}".

CANDIDATE RESUME CONTENT:
\"\"\"
{resume_text[:4000]}
\"\"\"

JOB DESCRIPTION (REQUIREMENTS):
\"\"\"
{jd_text}
\"\"\"

Evaluate with realistic recruiter ATS standards:
1. Identify matched skills, tools, frameworks, and qualifications present in the resume.
2. Identify missing or weak requirements mentioned in the JD.
3. Calculate an overall ATS match score between 0 and 100.
4. Provide a 2-3 sentence executive evaluation.
5. Provide 2-3 specific recommendations for improving this resume for the role.

Return your response in EXACT JSON format with these keys:
{{
  "ats_score": <integer 0-100>,
  "matched_skills": [<list of matched skills found in resume>],
  "missing_skills": [<list of missing or desired skills from JD>],
  "summary": "<2-3 sentence executive summary>",
  "recommendations": [<list of 2-3 specific improvement points>]
}}
Return ONLY raw JSON, no markdown wrappers.
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text_resp = response.text.strip()
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:]
            if text_resp.startswith("```"):
                text_resp = text_resp[3:]
            if text_resp.endswith("```"):
                text_resp = text_resp[:-3]
                
            res = json.loads(text_resp.strip())
            score = max(0, min(100, int(res.get("ats_score", 70))))
            return {
                "ats_score": score,
                "category": get_category_for_score(score),
                "matched_skills": res.get("matched_skills", []),
                "missing_skills": res.get("missing_skills", []),
                "summary": res.get("summary", "Resume evaluated by Gemini ATS AI."),
                "recommendations": res.get("recommendations", ["Tailor keywords directly to the target JD."]),
                "is_high_match": score >= 91,
                "extracted_preview": resume_text[:350].strip() + ("..." if len(resume_text) > 350 else "")
            }
        except Exception as e:
            print(f"Gemini API invocation error: {e}, falling back to intelligent heuristic parser.")

    # Intelligent Heuristic Fallback for Raw Resume Text
    return _smart_heuristic_resume_eval(resume_text, jd_text, role_name, candidate_name)

def _smart_heuristic_resume_eval(resume_text: str, jd_text: str, role_name: str, candidate_name: str) -> dict:
    resume_lower = resume_text.lower()
    jd_lower = (jd_text + " " + role_name).lower()
    
    # Comprehensive lexicon
    skills_lexicon = [
        "python", "java", "c++", "c#", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "nodejs", "express", "flask", "django", "fastapi", "spring boot", "sql", "postgresql",
        "mysql", "mongodb", "redis", "aws", "azure", "gcp", "docker", "kubernetes", "git", "github",
        "rest api", "graphql", "html", "html5", "css", "css3", "tailwind", "bootstrap", "machine learning",
        "deep learning", "nlp", "data structures", "algorithms", "problem solving", "communication",
        "agile", "scrum", "ci/cd", "linux", "testing", "unit test", "cybersecurity", "analytics"
    ]
    
    jd_skills = [s for s in skills_lexicon if re.search(r'\b' + re.escape(s) + r'\b', jd_lower)]
    if not jd_skills:
        jd_skills = ["python", "problem solving", "data structures", "sql", "git", "communication"]
        
    matched = [s for s in jd_skills if re.search(r'\b' + re.escape(s) + r'\b', resume_lower)]
    missing = [s for s in jd_skills if s not in matched]
    
    # Additional resume skills detected
    extra_skills = [s for s in skills_lexicon if s not in jd_skills and re.search(r'\b' + re.escape(s) + r'\b', resume_lower)]
    
    # Word count and structure check
    word_count = len(resume_text.split())
    structure_bonus = 10 if word_count >= 150 else (5 if word_count >= 60 else 0)
    
    # Match ratio
    match_ratio = len(matched) / len(jd_skills) if jd_skills else 0.5
    raw_score = (match_ratio * 70) + structure_bonus + (len(extra_skills) * 2)
    score = int(max(35, min(98, raw_score)))
    
    if len(matched) >= len(jd_skills) * 0.85 and word_count >= 120:
        score = max(92, score)
        
    category = get_category_for_score(score)
    summary = f"Resume analysis identified {len(matched)} matched core skills against the target job requirements. Word count: {word_count} words."
    if score >= 91:
        summary = f"🔥 Exceptional match ({score}%)! The uploaded resume is highly aligned with {len(matched)} key requirements for {role_name or 'the role'}."
        
    recs = []
    if missing:
        recs.append(f"Incorporate missing target competencies: {', '.join([m.capitalize() for m in missing[:3]])}.")
    if word_count < 150:
        recs.append("Expand project details, quantitative metrics, and technology impact.")
    recs.append("Ensure standard section headers (Experience, Projects, Skills, Education) for optimal parsing.")
    
    return {
        "ats_score": score,
        "category": category,
        "matched_skills": [m.capitalize() for m in matched],
        "missing_skills": [m.capitalize() for m in missing],
        "summary": summary,
        "recommendations": recs,
        "is_high_match": score >= 91,
        "extracted_preview": resume_text[:350].strip() + ("..." if len(resume_text) > 350 else "")
    }

def analyze_resume_ats(student_data: dict, jd_text: str, role_name: str = "") -> dict:
    """
    Analyzes student database profile against Job Description.
    """
    resume_combined = f"""
    Name: {student_data.get('name')}
    Roll No: {student_data.get('roll_no')}
    Department: {student_data.get('department_code')} ({student_data.get('department_name')})
    Academic UG: {student_data.get('ug_percent')}%
    Profiles: {student_data.get('github_url')} {student_data.get('linkedin_url')} {student_data.get('portfolio_url')}
    Skills & Projects: {student_data.get('resume_text', 'Proficient in modern software engineering, data structures, algorithms, and practical projects.')}
    """
    return analyze_raw_resume_text(resume_combined, jd_text, role_name, student_data.get('name', 'Student'))

