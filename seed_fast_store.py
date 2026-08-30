import os
import sys
import csv
import json
from datetime import datetime
import db_mongo
from fast_store import FastDatabase

JD_FOLDER_URL = "https://drive.google.com/drive/folders/1gRwKWhM8tWiPA4fAJOXtjqvXSux8kqdw"

def build_fast_store():
    db = FastDatabase("placement_local_db.json")
    
    # 1. Users
    users_data = [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@placement.edu",
            "role": "admin",
            "member_id": "ADM001",
            "full_name": "Dr. Sivasubramaniyan (Head - T&P)",
            "password_hash": "scrypt:32768:8:1$uH2XwM2B6Xw$a7bc341b5d1297e68225e836df3ecab1ecb683cf9c98bc01d102dc897bf124619a9aa8cb0191834927f8a7e2efcd37fc53dfebaf58169970966f1030e4663e00",
            "created_at": datetime.utcnow()
        },
        {
            "id": 2,
            "username": "manager",
            "email": "manager@placement.edu",
            "role": "manager",
            "member_id": "MGR001",
            "full_name": "Dr. Jeyakannan (Dean Academic)",
            "password_hash": "scrypt:32768:8:1$uH2XwM2B6Xw$a7bc341b5d1297e68225e836df3ecab1ecb683cf9c98bc01d102dc897bf124619a9aa8cb0191834927f8a7e2efcd37fc53dfebaf58169970966f1030e4663e00",
            "created_at": datetime.utcnow()
        },
        {
            "id": 3,
            "username": "lead",
            "email": "lead@placement.edu",
            "role": "team_member",
            "member_id": "MEM001",
            "full_name": "Kishore N (Placement Team Lead)",
            "password_hash": "scrypt:32768:8:1$uH2XwM2B6Xw$a7bc341b5d1297e68225e836df3ecab1ecb683cf9c98bc01d102dc897bf124619a9aa8cb0191834927f8a7e2efcd37fc53dfebaf58169970966f1030e4663e00",
            "created_at": datetime.utcnow()
        }
    ]
    for i in range(2, 11):
        mem_code = f"MEM{i:03d}"
        users_data.append({
            "id": i + 2,
            "username": f"mem{i:03d}".lower(),
            "email": f"member{i:03d}@placement.edu",
            "role": "team_member",
            "member_id": mem_code,
            "full_name": f"Placement Officer {i:02d}",
            "password_hash": "scrypt:32768:8:1$uH2XwM2B6Xw$a7bc341b5d1297e68225e836df3ecab1ecb683cf9c98bc01d102dc897bf124619a9aa8cb0191834927f8a7e2efcd37fc53dfebaf58169970966f1030e4663e00",
            "created_at": datetime.utcnow()
        })
    db.users.docs = users_data

    # 2. Departments
    departments_data = [
        {"id": 1, "code": "BCY", "name": "Cyber Security", "description": "B.Sc / B.E Cyber Security & Ethical Hacking"},
        {"id": 2, "code": "BCS", "name": "Computer Science", "description": "B.Sc / B.E Computer Science and Engineering"},
        {"id": 3, "code": "BIT", "name": "Information Technology", "description": "B.Sc / B.Tech Information Technology & Cloud"},
        {"id": 4, "code": "AIDS", "name": "BSC CS WITH AI INTEL", "description": "B.Sc Computer Science with Artificial Intelligence & Data Science"},
        {"id": 5, "code": "BEC", "name": "Electronics and Communication", "description": "B.E Electronics and Communication Engineering & IoT"},
        {"id": 6, "code": "BBA", "name": "Business Administration", "description": "Bachelor of Business Administration, Analytics & FinTech"}
    ]
    db.departments.docs = departments_data

    # 3. Companies
    with open("scratch_companies.csv", "r", encoding="utf-8") as f:
        c_reader = list(csv.reader(f))
    
    companies_data = []
    for i, row in enumerate(c_reader[1:], start=1):
        if not row or not any(row) or not row[0].strip():
            continue
        c_name = row[0].strip()
        hr_name = row[1].strip()
        hr_email = row[2].strip()
        hr_mobile = row[3].strip()
        status = row[4].strip().upper() or "COLD"
        ctc_str = row[5].strip() if len(row) > 5 else "8.0"
        jd_link = row[6].strip() if len(row) > 6 else ""
        job_role = row[7].strip() if len(row) > 7 else "Software Engineer"
        
        try:
            ctc_val = float(ctc_str.replace("LPA", "").replace("₹", "").strip())
        except ValueError:
            ctc_val = 8.0
            
        companies_data.append({
            "id": i,
            "name": c_name,
            "hr_name": hr_name,
            "hr_email": hr_email,
            "hr_mobile": hr_mobile,
            "status": status,
            "ctc": ctc_val,
            "jd_link": jd_link or f"https://example.com/jd/{c_name.lower().replace(' ', '-')}-2026.pdf",
            "drive_links": JD_FOLDER_URL,
            "job_role": job_role,
            "assigned_to": 3,
            "is_approved": True,
            "forwarded_to_admin": True,
            "created_at": datetime.utcnow()
        })
    db.companies.docs = companies_data

    # 4. Students
    dept_map = {
        "Cyber Security": ("BCY", 1),
        "Computer Science": ("BCS", 2),
        "Information Technology": ("BIT", 3),
        "BSC CS WITH AI INTEL": ("AIDS", 4),
        "Electronics and Communication": ("BEC", 5),
        "Business Administration": ("BBA", 6)
    }

    with open("scratch_students.csv", "r", encoding="utf-8") as f:
        s_reader = list(csv.reader(f))

    s_header_idx = -1
    for i, row in enumerate(s_reader):
        if len(row) > 0 and "Roll No" in row[0]:
            s_header_idx = i
            break

    def clean_float(val, default=75.0):
        try:
            clean = val.replace("%", "").strip()
            return float(clean) if clean else default
        except ValueError:
            return default

    students_data = []
    male_idx = 1
    female_idx = 1

    for student_id, row in enumerate(s_reader[s_header_idx+1:], start=1):
        if not row or not any(row) or not row[0].strip():
            continue
        roll = row[0].strip()
        name = row[1].strip()
        dept_name = row[2].strip()
        gender = row[3].strip()
        residency = row[4].strip()
        sslc = clean_float(row[5])
        hsc = clean_float(row[6])
        ug = clean_float(row[7])
        pg = clean_float(row[8]) if row[8].strip() else None
        github = row[9].strip()
        resume = row[10].strip()
        linkedin = row[11].strip()
        grad_date = row[12].strip() or "2027-05-31"
        portfolio = row[13].strip()
        p_email = row[14].strip()
        c_email = row[15].strip()
        mobile = row[16].strip()
        photo = row[17].strip()
        raw_status = row[18].strip().upper()
        
        placement_status = "PLACED" if "PLACED" in raw_status and "YET" not in raw_status else "YET TO BE PLACED"
        dept_code, dept_id = dept_map.get(dept_name, ("BCS", 2))

        grad_year_ug = 2027
        if grad_date:
            try:
                grad_year_ug = int(grad_date.split("-")[0])
            except (ValueError, IndexError):
                grad_year_ug = 2027
                
        if "1fmkUGuUs" in photo:
            final_photo = f"https://drive.google.com/thumbnail?id=1fmkUGuUsnWnFfZ_lppA7jv9YFWjNuV7Y&sz=w200"
        elif gender == "Female":
            final_photo = f"https://randomuser.me/api/portraits/women/{female_idx}.jpg"
            female_idx += 1
        else:
            final_photo = f"https://randomuser.me/api/portraits/men/{male_idx}.jpg"
            male_idx += 1

        students_data.append({
            "id": student_id,
            "roll_no": roll,
            "name": name,
            "department_id": dept_id,
            "department_code": dept_code,
            "department_name": dept_name,
            "gender": gender,
            "residency_type": residency,
            "sslc_percent": sslc,
            "hsc_percent": hsc,
            "ug_percent": ug,
            "pg_percent": pg,
            "degree": "B.E / B.Tech / B.Sc / BBA",
            "grad_year_10th": grad_year_ug - 6,
            "grad_year_12th": grad_year_ug - 4,
            "grad_year_ug": grad_year_ug,
            "grad_date": grad_date,
            "email": c_email or p_email or f"{roll.lower()}@rathinam.in",
            "personal_email": p_email,
            "college_email": c_email,
            "mobile_no": mobile,
            "github_url": github,
            "linkedin_url": linkedin,
            "portfolio_url": portfolio,
            "resume_url": resume,
            "photo_url": final_photo,
            "drive_links": JD_FOLDER_URL,
            "placement_status": placement_status,
            "latest_offer": None,
            "created_at": datetime.utcnow()
        })
    db.students.docs = students_data

    # 5. Drives & Offers
    drives_data = []
    offers_data = []
    offer_id = 1
    
    for comp in companies_data:
        drive_doc = {
            "id": comp["id"],
            "company_id": comp["id"],
            "company_name": comp["name"],
            "drive_date": "2026-03-15",
            "job_role": comp.get("job_role", "Software Engineer"),
            "ctc_lpa": comp.get("ctc", 10.0),
            "status": "COMPLETED" if comp["status"] == "DRIVE COMPLETED" else "SCHEDULED",
            "eligible_departments": ["BCY", "BCS", "BIT", "AIDS", "BEC", "BBA"],
            "min_ug_percent": 70.0,
            "venue": "Placement Cell Campus Center / Online Assessment",
            "created_at": datetime.utcnow()
        }
        drives_data.append(drive_doc)
        
    db.placement_drives.docs = drives_data

    # Match placed students to companies
    placed_studs = [s for s in students_data if s["placement_status"] == "PLACED"]
    comp_list = [c for c in companies_data if c["status"] == "DRIVE COMPLETED"] or companies_data
    
    for i, s in enumerate(placed_studs):
        comp = comp_list[i % len(comp_list)]
        off = {
            "id": offer_id,
            "student_id": s["id"],
            "student_name": s["name"],
            "student_roll": s["roll_no"],
            "company_id": comp["id"],
            "company_name": comp["name"],
            "role": comp.get("job_role", "Associate Engineer"),
            "ctc_lpa": comp.get("ctc", 10.0),
            "offer_date": "2026-03-20",
            "created_at": datetime.utcnow()
        }
        s["latest_offer"] = off
        offers_data.append(off)
        offer_id += 1

    db.offers.docs = offers_data
    db.save_to_disk()
    print(f"[OK] High performance fast store initialized! Seeded {len(students_data)} students, {len(companies_data)} companies, {len(offers_data)} offers.")

if __name__ == "__main__":
    build_fast_store()
