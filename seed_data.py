import random
from datetime import datetime, timedelta
from faker import Faker
from models import (
    db, User, Department, Student, Company, CompanyStatusHistory,
    PlacementDrive, PlacementRegistration, PlacementAttendance, Shortlist, Offer, ATSAnalysis
)
from auth import hash_password
from config import Config
from flask import Flask

fake = Faker('en_IN')

def seed_database(app):
    with app.app_context():
        db.create_all()
        
        # 1. Check if already seeded
        if User.query.first():
            print("Database already contains data. Skipping initial seeding.")
            return

        print("=== Starting Database Seeding ===")

        # 2. Seed Users
        users_to_add = [
            User(
                username="sivasubramaniyan",
                email="sivasubramaniyan@placement.edu",
                password_hash=hash_password("admin@123"),
                role="admin",
                member_id="ADMIN",
                full_name="Dr. Sivasubramaniyan Sir (Placement Head)"
            ),
            User(
                username="jeyakannan",
                email="jeyakannan@placement.edu",
                password_hash=hash_password("manager@123"),
                role="manager",
                member_id="MANAGER",
                full_name="Dr. Jeyakannan Sir (Dean)"
            )
        ]
        
        # Placement Team MEM001 to MEM010
        team_names = [
            "Aarav Sundaram (Lead)", "Ananya Iyer", "Karthik Raja", "Pooja Hegde",
            "Manoj Kumar", "Divya Krishnan", "Sanjay Verma", "Sneha Nair",
            "Vikram Sethuraman", "Meera Natarajan"
        ]
        for i in range(1, 11):
            mem_code = f"MEM{i:03d}"
            users_to_add.append(User(
                username=f"mem{i:03d}",
                email=f"mem{i:03d}@placement.edu",
                password_hash=hash_password("team123"),
                role="team_member",
                member_id=mem_code,
                full_name=f"{team_names[i-1]}"
            ))
            
        db.session.add_all(users_to_add)
        db.session.commit()
        print(f"[OK] Seeded {len(users_to_add)} Users (Admin, Manager, MEM001-MEM010).")

        # 3. Seed Departments
        dept_data = [
            ("CSE", "Computer Science & Engineering", "Software Engineering, Cloud, & Systems"),
            ("IT", "Information Technology", "Web, Mobile, Enterprise Tech & Networks"),
            ("AIDS", "Artificial Intelligence & Data Science", "Data Analytics, Machine Learning & Big Data"),
            ("AIML", "Artificial Intelligence & Machine Learning", "Deep Learning, Computer Vision & NLP"),
            ("ECE", "Electronics & Communication Engineering", "VLSI, Embedded Systems, IoT & Telecom"),
            ("EEE", "Electrical & Electronics Engineering", "Power Systems, EV Tech & Control"),
            ("MECH", "Mechanical Engineering", "CAD/CAM, Robotics, Thermal & Manufacturing"),
            ("CIVIL", "Civil Engineering", "Structural Design, Construction & GIS")
        ]
        
        departments = []
        for code, name, desc in dept_data:
            dept = Department(code=code, name=name, description=desc)
            departments.append(dept)
            db.session.add(dept)
            
        db.session.commit()
        print(f"[OK] Seeded {len(departments)} Departments.")

        # 4. Seed 3000 Students
        print("[*] Generating 3000 realistic student records...")
        
        students_to_add = []
        total_students = 3000
        dept_codes = [d.code for d in departments]
        
        # Pre-assign department distribution (approx 375 students per dept)
        for i in range(1, total_students + 1):
            dept = departments[(i - 1) % len(departments)]
            gender = "Female" if random.random() < 0.45 else "Male"
            first_name = fake.first_name_female() if gender == "Female" else fake.first_name_male()
            last_name = fake.last_name()
            full_name = f"{first_name} {last_name}"
            
            # Roll no format: 22 + DeptCode + 3-digit sequence
            seq = ((i - 1) // len(departments)) + 1
            roll_no = f"22{dept.code}{seq:03d}"
            
            # Academic Percentages
            sslc = round(random.uniform(70.0, 98.5), 1)
            hsc = round(random.uniform(68.0, 97.5), 1)
            ug = round(random.uniform(62.0, 96.0), 1)
            has_pg = random.random() < 0.08
            pg = round(random.uniform(72.0, 94.0), 1) if has_pg else None
            
            residency = "Hosteller" if random.random() < 0.4 else "Day Scholar"
            
            # Professional profiles
            github_username = f"{first_name.lower()}{last_name.lower()}{random.randint(10, 99)}"
            email = f"{roll_no.lower()}@college.edu.in"
            mobile = f"9{random.randint(100000000, 999999999)}"
            
            student = Student(
                roll_no=roll_no,
                name=full_name,
                department_id=dept.id,
                gender=gender,
                residency_type=residency,
                sslc_percent=sslc,
                hsc_percent=hsc,
                ug_percent=ug,
                pg_percent=pg,
                degree="M.Tech" if has_pg else "B.E / B.Tech",
                grad_year_10th=2020,
                grad_year_12th=2022,
                grad_year_ug=2026,
                grad_year_pg=2028 if has_pg else None,
                email=email,
                mobile_no=mobile,
                github_url=f"https://github.com/{github_username}",
                linkedin_url=f"https://linkedin.com/in/{github_username}",
                portfolio_url=f"https://{github_username}.dev" if random.random() < 0.6 else "",
                resume_url=f"/static/uploads/resumes/{roll_no}_resume.pdf",
                self_intro_url=f"https://youtube.com/watch?v=intro_{roll_no}" if random.random() < 0.4 else "",
                photo_url=f"https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80" if gender == "Female" else f"https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&auto=format&fit=crop&q=80",
                drive_links=f"https://drive.google.com/drive/folders/{roll_no}_certs",
                placement_status="YET TO BE PLACED"
            )
            students_to_add.append(student)
            
            # Batch commit every 500 records
            if len(students_to_add) >= 500:
                db.session.add_all(students_to_add)
                db.session.commit()
                print(f"  ... inserted {i}/{total_students} students")
                students_to_add = []
                
        if students_to_add:
            db.session.add_all(students_to_add)
            db.session.commit()
            
        print(f"[OK] Successfully seeded {total_students} student profiles.")

        # 5. Seed Companies with full stages (COLD, WARM, HOT, DRIVE COMPLETED)
        team_members = User.query.filter_by(role="team_member").all()
        admin_user = User.query.filter_by(role="admin").first()
        
        sample_companies = [
            # COLD Stage
            {
                "name": "Google India",
                "location": "Bangalore, Karnataka",
                "website": "https://careers.google.com",
                "contact_person": "Vikram Adithya (Campus HR)",
                "mobile_no": "9845012345",
                "email": "vadithya@google.com",
                "employee_count": "100,000+",
                "ctc_lpa": 32.5,
                "status": "COLD",
                "is_approved": False,
                "jd_text": "Software Engineering role focusing on distributed systems, algorithms, Python/Go/C++, and massive scale backend infrastructure.",
                "offers": 0
            },
            {
                "name": "Microsoft IDC",
                "location": "Hyderabad, Telangana",
                "website": "https://careers.microsoft.com",
                "contact_person": "Priya Sharma (University Recruiter)",
                "mobile_no": "9845023456",
                "email": "priya.sharma@microsoft.com",
                "employee_count": "100,000+",
                "ctc_lpa": 28.0,
                "status": "COLD",
                "is_approved": False,
                "jd_text": "Software Engineer Azure Cloud: Design and build scalable microservices using C#, Python, Kubernetes, and Azure Architecture.",
                "offers": 0
            },
            {
                "name": "Adobe Systems",
                "location": "Noida, Uttar Pradesh",
                "website": "https://adobe.wd5.myworkdayjobs.com",
                "contact_person": "Rohit Malhotra",
                "mobile_no": "9845034567",
                "email": "rmalhotra@adobe.com",
                "employee_count": "25,000+",
                "ctc_lpa": 24.0,
                "status": "COLD",
                "is_approved": False,
                "jd_text": "Member of Technical Staff: Creative Cloud algorithms, web technologies, JavaScript/TypeScript, React, and GPU graphics rendering.",
                "offers": 0
            },
            # WARM Stage
            {
                "name": "Amazon Web Services",
                "location": "Chennai, Tamil Nadu",
                "website": "https://amazon.jobs",
                "contact_person": "Siddharth Rao",
                "mobile_no": "9845045678",
                "email": "siddrao@amazon.com",
                "employee_count": "500,000+",
                "ctc_lpa": 22.0,
                "status": "WARM",
                "is_approved": True,
                "jd_text": "SDE-1 Cloud Services: Problem solving, Java, Spring Boot, DynamoDB, AWS infrastructure, and high concurrency data structures.",
                "offers": 0
            },
            {
                "name": "Zoho Corporation",
                "location": "Tenkasi / Chennai, Tamil Nadu",
                "website": "https://zoho.com/careers",
                "contact_person": "Rajesh Kannan",
                "mobile_no": "9845056789",
                "email": "rajesh.k@zohocorp.com",
                "employee_count": "15,000+",
                "ctc_lpa": 8.5,
                "status": "WARM",
                "is_approved": True,
                "jd_text": "Software Developer: Strong fundamentals in C/C++, Java, OOPs, Database concepts, and full-stack web application development.",
                "offers": 0
            },
            # HOT Stage
            {
                "name": "Tata Consultancy Services (TCS Digital)",
                "location": "Chennai / Mumbai",
                "website": "https://tcs.com/careers",
                "contact_person": "Meenakshi Sundaram",
                "mobile_no": "9845067890",
                "email": "meenakshi.s@tcs.com",
                "employee_count": "600,000+",
                "ctc_lpa": 7.5,
                "status": "HOT",
                "is_approved": True,
                "jd_text": "Digital Innovator: Modern Full-Stack Web technologies, Python/Java, Machine Learning, Cloud Services, and REST API development.",
                "offers": 0
            },
            {
                "name": "Infosys (Power Programmer)",
                "location": "Bangalore / Mysore",
                "website": "https://infosys.com/careers",
                "contact_person": "Harish Kumar",
                "mobile_no": "9845078901",
                "email": "harish.k@infosys.com",
                "employee_count": "300,000+",
                "ctc_lpa": 9.5,
                "status": "HOT",
                "is_approved": True,
                "jd_text": "Specialist Programmer: Competitive programming, complex algorithmic problem solving, microservices architecture, and DevOps.",
                "offers": 0
            },
            # DRIVE COMPLETED Stage
            {
                "name": "Accenture Technology",
                "location": "Bangalore / Chennai",
                "website": "https://accenture.com/careers",
                "contact_person": "Nandhini Balan",
                "mobile_no": "9845089012",
                "email": "nandhini.b@accenture.com",
                "employee_count": "700,000+",
                "ctc_lpa": 6.5,
                "status": "DRIVE COMPLETED",
                "is_approved": True,
                "jd_text": "Advanced Associate Software Engineer: Application development, testing automation, Java, React, SQL, and agile delivery.",
                "offers": 45
            },
            {
                "name": "Capgemini India",
                "location": "Trichy / Chennai",
                "website": "https://capgemini.com/careers",
                "contact_person": "Arun Prasad",
                "mobile_no": "9845090123",
                "email": "arun.p@capgemini.com",
                "employee_count": "350,000+",
                "ctc_lpa": 5.8,
                "status": "DRIVE COMPLETED",
                "is_approved": True,
                "jd_text": "Software Analyst: Core Java, JavaScript, Python scripting, database management, and enterprise software implementation.",
                "offers": 32
            }
        ]
        
        created_companies = []
        for idx, c_info in enumerate(sample_companies):
            member = team_members[idx % len(team_members)]
            comp = Company(
                name=c_info["name"],
                location=c_info["location"],
                website=c_info["website"],
                contact_person=c_info["contact_person"],
                mobile_no=c_info["mobile_no"],
                email=c_info["email"],
                employee_count=c_info["employee_count"],
                google_maps_link=f"https://www.google.com/maps/search/?api=1&query={c_info['location'].replace(' ', '+')}",
                address=f"Tech Park, Sector {random.randint(1,15)}, {c_info['location']}",
                ctc_lpa=c_info["ctc_lpa"],
                jd_text=c_info["jd_text"],
                jd_file_url=f"/static/uploads/jds/{c_info['name'].lower().replace(' ', '_')}_jd.pdf",
                status=c_info["status"],
                is_approved=c_info["is_approved"],
                approved_by_id=admin_user.id if c_info["is_approved"] else None,
                approved_at=datetime.utcnow() if c_info["is_approved"] else None,
                added_by_id=member.id,
                total_offers_count=c_info["offers"]
            )
            db.session.add(comp)
            created_companies.append(comp)
            
        db.session.commit()
        print(f"[OK] Seeded {len(created_companies)} Companies with complete lifecycle states.")

        # 6. Seed Placement Drives & Historical Offers
        all_students = Student.query.all()
        
        # Completed drive 1: Accenture
        accenture = Company.query.filter_by(name="Accenture Technology").first()
        if accenture:
            drive1 = PlacementDrive(
                company_id=accenture.id,
                role_name="Advanced Associate Software Engineer",
                job_description=accenture.jd_text,
                ctc_lpa=accenture.ctc_lpa,
                drive_date=(datetime.now() - timedelta(days=20)).date(),
                min_sslc_percent=60.0,
                min_hsc_percent=60.0,
                min_ug_percent=65.0,
                eligible_departments="ALL",
                status="COMPLETED",
                created_by_id=team_members[0].id
            )
            db.session.add(drive1)
            db.session.commit()
            
            # Select 45 candidates and issue offers
            placed_candidates = all_students[:45]
            for stud in placed_candidates:
                # Registration
                reg = PlacementRegistration(drive_id=drive1.id, student_id=stud.id)
                db.session.add(reg)
                # Attendance
                att = PlacementAttendance(drive_id=drive1.id, student_id=stud.id, is_present=True, marked_by_id=team_members[0].id)
                db.session.add(att)
                # Shortlist
                short = Shortlist(drive_id=drive1.id, student_id=stud.id, round_name="HR Round", is_shortlisted=True)
                db.session.add(short)
                # Offer
                off = Offer(
                    student_id=stud.id,
                    company_id=accenture.id,
                    drive_id=drive1.id,
                    role="Advanced Associate Software Engineer",
                    ctc_lpa=accenture.ctc_lpa,
                    offer_date=(datetime.now() - timedelta(days=15)).date(),
                    created_by_id=team_members[0].id
                )
                db.session.add(off)
                stud.placement_status = "PLACED"
                
            db.session.commit()
            print(f"[OK] Recorded Drive & Offers for {accenture.name} (45 placed students).")

        # Completed drive 2: Capgemini
        capgemini = Company.query.filter_by(name="Capgemini India").first()
        if capgemini:
            drive2 = PlacementDrive(
                company_id=capgemini.id,
                role_name="Software Analyst",
                job_description=capgemini.jd_text,
                ctc_lpa=capgemini.ctc_lpa,
                drive_date=(datetime.now() - timedelta(days=10)).date(),
                min_sslc_percent=60.0,
                min_hsc_percent=60.0,
                min_ug_percent=60.0,
                eligible_departments="CSE,IT,AIDS,AIML,ECE",
                status="COMPLETED",
                created_by_id=team_members[1].id
            )
            db.session.add(drive2)
            db.session.commit()
            
            placed_candidates2 = all_students[45:77] # 32 candidates
            for stud in placed_candidates2:
                reg = PlacementRegistration(drive_id=drive2.id, student_id=stud.id)
                db.session.add(reg)
                att = PlacementAttendance(drive_id=drive2.id, student_id=stud.id, is_present=True, marked_by_id=team_members[1].id)
                db.session.add(att)
                off = Offer(
                    student_id=stud.id,
                    company_id=capgemini.id,
                    drive_id=drive2.id,
                    role="Software Analyst",
                    ctc_lpa=capgemini.ctc_lpa,
                    offer_date=(datetime.now() - timedelta(days=5)).date(),
                    created_by_id=team_members[1].id
                )
                db.session.add(off)
                stud.placement_status = "PLACED"
                
            db.session.commit()
            print(f"[OK] Recorded Drive & Offers for {capgemini.name} (32 placed students).")

        # 7. Seed Sample ATS Analyses (including 91-100% High Matches for instant testing)
        for s in all_students[77:110]:
            # Simulate a few high matches
            score = random.randint(91, 98) if random.random() < 0.35 else random.randint(58, 89)
            cat = "91-100" if score >= 91 else ("81-90" if score >= 81 else ("71-80" if score >= 71 else ("61-70" if score >= 61 else "0-60")))
            ats = ATSAnalysis(
                student_id=s.id,
                company_id=accenture.id if accenture else None,
                ats_score=score,
                category=cat,
                matched_skills="Python, SQL, React, Algorithms, Data Structures",
                missing_skills="Docker, Kubernetes" if score < 90 else "None",
                summary="Candidate displays exceptional problem solving alignment." if score >= 91 else "Good potential candidate.",
                analyzed_by_id=team_members[0].id
            )
            db.session.add(ats)
            
        db.session.commit()
        print("[OK] Seeded sample ATS candidate analysis records.")
        print("=== Seeding Completed Successfully! ===")
