import os
import sys
import re
import csv
import random
from datetime import datetime, timedelta

# Ensure python finds local modules
sys.path.insert(0, r"c:\Placement_Site")
import db_mongo
from werkzeug.security import generate_password_hash

JD_FOLDER_URL = "https://drive.google.com/drive/folders/1gRwKWhM8tWiPA4fAJOXtjqvXSux8kqdw"

def clean_float(val, default=0.0):
    if not val:
        return default
    val_str = str(val).replace("%", "").replace("₹", "").replace("LPA", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return default

def seed_database():
    db = db_mongo.get_db()
    
    print("=== STEP 1: DROPPING ALL OLD DATA ===", flush=True)
    collections_to_drop = [
        "students", "placement_drives", "companies", "departments",
        "offers", "users", "ats_analyses", "activity_logs",
        "company_status_history", "placement_registrations", "placement_attendance"
    ]
    for coll in collections_to_drop:
        db[coll].drop()
        print(f"Dropped collection: {coll}", flush=True)
        
    db_mongo.init_mongo_indexes()
    
    print("\n=== STEP 2: SEEDING USERS ===", flush=True)
    users_data = [
        {
            "id": 1,
            "username": "admin",
            "email": "placement_head@rathinam.in",
            "password_hash": generate_password_hash("admin@123"),
            "role": "admin",
            "member_id": "ADM001",
            "full_name": "Dr. R. Sivasubramaniyan",
            "created_at": datetime.utcnow()
        },
        {
            "id": 2,
            "username": "manager",
            "email": "dean_academics@rathinam.in",
            "password_hash": generate_password_hash("manager@123"),
            "role": "manager",
            "member_id": "MGR001",
            "full_name": "Dr. S. Jeyakannan",
            "created_at": datetime.utcnow()
        },
        {
            "id": 3,
            "username": "lead",
            "email": "placement.lead@rathinam.in",
            "password_hash": generate_password_hash("team123"),
            "role": "team_member",
            "member_id": "MEM001",
            "full_name": "Karthik Subramanian (Lead)",
            "created_at": datetime.utcnow()
        }
    ]
    
    for i in range(2, 11):
        mem_code = f"MEM{i:03d}"
        users_data.append({
            "id": i + 2,
            "username": mem_code.lower(),
            "email": f"coordinator.{i}@rathinam.in",
            "password_hash": generate_password_hash("team123"),
            "role": "team_member",
            "member_id": mem_code,
            "full_name": f"Coordinator {i}",
            "created_at": datetime.utcnow()
        })
        
    db.users.insert_many(users_data)
    print(f"[OK] Seeded {len(users_data)} users.", flush=True)
    
    print("\n=== STEP 3: SEEDING AVAILABLE DEPARTMENTS ===", flush=True)
    departments_info = [
        {"id": 1, "code": "BCY", "name": "Cyber Security", "description": "B.Sc / B.Tech Cyber Security & Digital Forensics"},
        {"id": 2, "code": "BCS", "name": "Computer Science", "description": "B.E / B.Sc Computer Science & Engineering"},
        {"id": 3, "code": "BIT", "name": "Information Technology", "description": "B.Tech Information Technology & Cloud Systems"},
        {"id": 4, "code": "AIDS", "name": "BSC CS WITH AI INTEL", "description": "B.Sc Computer Science with Artificial Intelligence & Machine Learning"},
        {"id": 5, "code": "BEC", "name": "Electronics and Communication", "description": "B.E Electronics and Communication Engineering"},
        {"id": 6, "code": "BBA", "name": "Business Administration", "description": "Bachelor of Business Administration & Analytics"}
    ]
    db.departments.insert_many(departments_info)
    print(f"[OK] Seeded {len(departments_info)} available departments.", flush=True)
    
    dept_map = {
        "Cyber Security": ("BCY", 1),
        "Computer Science": ("BCS", 2),
        "Information Technology": ("BIT", 3),
        "BSC CS WITH AI INTEL": ("AIDS", 4),
        "Electronics and Communication": ("BEC", 5),
        "Business Administration": ("BBA", 6)
    }

    print("\n=== STEP 4: PARSING & SEEDING 20 COMPANIES ===", flush=True)
    with open(r"c:\Placement_Site\scratch_companies.csv", "r", encoding="utf-8", errors="ignore") as f:
        c_reader = list(csv.reader(f))
        
    c_header_idx = -1
    for i, row in enumerate(c_reader):
        if len(row) > 1 and "Company Name" in row[1]:
            c_header_idx = i
            break
            
    companies_data = []
    company_name_to_id = {}
    
    for row in c_reader[c_header_idx+1:]:
        if not row or not any(row) or not row[0].strip() or "Overall Average" in row[0]:
            continue
        try:
            c_id = int(row[0].strip())
        except ValueError:
            continue
            
        c_name = row[1].strip()
        c_role = row[2].strip()
        c_ctc = clean_float(row[3])
        c_loc = row[4].strip()
        c_opp_status = row[5].strip().upper()
        c_job_status = row[6].strip().upper()
        c_placed_count = int(clean_float(row[7]))
        c_placed_details = row[8].strip()
        c_jd_summary = row[9].strip()
        c_jd_link = row[10].strip() or JD_FOLDER_URL
        c_careers_link = row[11].strip()
        c_email = row[12].strip()
        c_mobile = row[13].strip()
        
        if "COMPLETED" in c_opp_status:
            status_norm = "DRIVE COMPLETED"
        elif "WARM" in c_opp_status:
            status_norm = "WARM"
        elif "HOT" in c_opp_status:
            status_norm = "HOT"
        else:
            status_norm = "COLD"
            
        is_appr = (c_job_status == "APPROVED" or status_norm == "DRIVE COMPLETED")
        
        comp_doc = {
            "id": c_id,
            "name": c_name,
            "job_role": c_role,
            "ctc_lpa": c_ctc,
            "location": c_loc,
            "status": status_norm,
            "is_approved": is_appr,
            "approved_by_id": 1 if is_appr else None,
            "approved_at": datetime.utcnow() - timedelta(days=20) if is_appr else None,
            "contact_person": "Campus University Relations Manager",
            "email": c_email,
            "mobile_no": c_mobile,
            "website": c_careers_link,
            "jd_file_url": c_jd_link,
            "jd_folder_url": JD_FOLDER_URL,
            "jd_text": c_jd_summary,
            "total_offers_count": c_placed_count,
            "placed_students_summary": c_placed_details,
            "google_maps_link": f"https://www.google.com/maps/search/?api=1&query={c_loc.replace(' ', '+')}",
            "added_by_id": 1,
            "forwarded_to_admin": not is_appr,
            "forwarded_note": "Proposed campus drive" if not is_appr else None,
            "created_at": datetime.utcnow() - timedelta(days=45)
        }
        companies_data.append(comp_doc)
        company_name_to_id[c_name.lower()] = c_id
        
    db.companies.insert_many(companies_data)
    print(f"[OK] Seeded {len(companies_data)} companies.", flush=True)

    print("\n=== STEP 5: PARSING & SEEDING STUDENTS ===", flush=True)
    with open(r"c:\Placement_Site\scratch_students.csv", "r", encoding="utf-8", errors="ignore") as f:
        s_reader = list(csv.reader(f))
        
    s_header_idx = -1
    for i, row in enumerate(s_reader):
        if len(row) > 0 and "Roll No" in row[0]:
            s_header_idx = i
            break
            
    students_data = []
    student_id = 1
    male_idx = 1
    female_idx = 1
    
    for row in s_reader[s_header_idx+1:]:
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

        stud_doc = {
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
        }
        students_data.append(stud_doc)
        student_id += 1
        
    db.students.insert_many(students_data)
    print(f"[OK] Seeded {len(students_data)} students.", flush=True)

    print("\n=== STEP 6: SEEDING PLACEMENT DRIVES & OFFERS ===", flush=True)
    drives_data = []
    offers_data = []
    offer_id = 1
    
    # 1. Create Drives for all 20 companies
    for comp in companies_data:
        drive_doc = {
            "id": comp["id"],
            "company_id": comp["id"],
            "company_name": comp["name"],
            "role_name": comp["job_role"],
            "job_role": comp["job_role"],
            "job_description": comp["jd_text"],
            "ctc_lpa": comp["ctc_lpa"],
            "drive_date": (datetime.utcnow() - timedelta(days=random.randint(10, 40))).strftime("%Y-%m-%d"),
            "min_sslc_percent": 60.0,
            "min_hsc_percent": 60.0,
            "min_ug_percent": 65.0,
            "eligible_departments": ["BCY", "BCS", "BIT", "AIDS", "BEC", "BBA"],
            "status": "COMPLETED" if comp["status"] == "DRIVE COMPLETED" else "SCHEDULED",
            "created_by_id": 1,
            "created_at": comp["created_at"]
        }
        drives_data.append(drive_doc)
        
    db.placement_drives.insert_many(drives_data)
    print(f"[OK] Seeded {len(drives_data)} placement drives.", flush=True)

    # 2. Match Placed Students to Offers
    placed_student_roll_map = {}
    for comp in companies_data:
        p_details = comp.get("placed_students_summary", "")
        if p_details and "Upcoming" not in p_details:
            rolls_found = re.findall(r"(RCAS\w+|RTC\w+)", p_details)
            for r in rolls_found:
                placed_student_roll_map[r.upper()] = comp

    completed_comps = [c for c in companies_data if c["status"] == "DRIVE COMPLETED"]
    comp_cycle_idx = 0
    
    for student in students_data:
        if student["placement_status"] == "PLACED":
            roll = student["roll_no"].upper()
            target_comp = placed_student_roll_map.get(roll)
            if not target_comp and completed_comps:
                target_comp = completed_comps[comp_cycle_idx % len(completed_comps)]
                comp_cycle_idx += 1
                
            if target_comp:
                offer_doc = {
                    "id": offer_id,
                    "student_id": student["id"],
                    "student_roll_no": student["roll_no"],
                    "student_name": student["name"],
                    "department_code": student["department_code"],
                    "company_id": target_comp["id"],
                    "company_name": target_comp["name"],
                    "drive_id": target_comp["id"],
                    "role_offered": target_comp["job_role"],
                    "role": target_comp["job_role"],
                    "ctc_lpa": target_comp["ctc_lpa"],
                    "offer_date": (datetime.utcnow() - timedelta(days=random.randint(5, 25))).strftime("%Y-%m-%d"),
                    "status": "ACCEPTED",
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(5, 25))
                }
                offers_data.append(offer_doc)
                offer_id += 1
                
                db.students.update_one(
                    {"id": student["id"]},
                    {
                        "$set": {
                            "latest_offer": {
                                "company_name": target_comp["name"],
                                "role": target_comp["job_role"],
                                "ctc_lpa": target_comp["ctc_lpa"],
                                "offer_date": offer_doc["offer_date"]
                            }
                        }
                    }
                )
                
    if offers_data:
        db.offers.insert_many(offers_data)
    print(f"[OK] Seeded {len(offers_data)} placement offers.", flush=True)

    # 3. Status History
    history_data = []
    for c in companies_data:
        history_data.append({
            "company_id": c["id"],
            "old_status": None,
            "new_status": c["status"],
            "changed_by": "Dr. R. Sivasubramaniyan",
            "changed_by_id": 1,
            "remarks": f"Official Campus recruitment drive: {c['job_role']} ({c['ctc_lpa']} LPA)",
            "changed_at": datetime.utcnow() - timedelta(days=random.randint(15, 30))
        })
    db.company_status_history.insert_many(history_data)
    print(f"[OK] Seeded {len(history_data)} company status histories.", flush=True)
    
    print("\n=== COMPLETED SEEDING NEW DATASET! ===", flush=True)

if __name__ == "__main__":
    seed_database()
