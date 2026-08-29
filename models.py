from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'manager', 'team_member'
    member_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # 'ADMIN', 'MANAGER', 'MEM001'..'MEM010'
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    activity_logs = db.relationship("ActivityLog", backref="user", lazy=True)
    added_companies = db.relationship("Company", foreign_keys="Company.added_by_id", backref="added_by_user", lazy=True)
    approved_companies = db.relationship("Company", foreign_keys="Company.approved_by_id", backref="approved_by_user", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "member_id": self.member_id,
            "full_name": self.full_name,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class Department(db.Model):
    __tablename__ = "departments"
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # CSE, IT, ECE, EEE, MECH, CIVIL, AIDS, AIML
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    students = db.relationship("Student", backref="department", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "student_count": len(self.students) if self.students else 0
        }

class Student(db.Model):
    __tablename__ = "students"
    
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    gender = db.Column(db.String(15), nullable=False)  # Male, Female, Other
    residency_type = db.Column(db.String(20), nullable=False)  # Hosteller, Day Scholar
    
    # Academic percentiles
    sslc_percent = db.Column(db.Float, nullable=False)
    hsc_percent = db.Column(db.Float, nullable=False)
    ug_percent = db.Column(db.Float, nullable=False)
    pg_percent = db.Column(db.Float, nullable=True)  # Optional
    degree = db.Column(db.String(50), default="B.E / B.Tech")
    
    # Graduation Years
    grad_year_10th = db.Column(db.Integer, nullable=True)
    grad_year_12th = db.Column(db.Integer, nullable=True)
    grad_year_ug = db.Column(db.Integer, nullable=False, default=2026)
    grad_year_pg = db.Column(db.Integer, nullable=True)
    
    # Contact & Validation
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_no = db.Column(db.String(15), nullable=False)  # 10 digit format
    
    # Professional Profiles & Links
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    self_intro_url = db.Column(db.String(255), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    drive_links = db.Column(db.Text, nullable=True)
    
    # Computed / Main placement status
    placement_status = db.Column(db.String(30), default="YET TO BE PLACED", index=True)  # 'PLACED', 'YET TO BE PLACED'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship("PlacementRegistration", backref="student", lazy=True, cascade="all, delete-orphan")
    attendances = db.relationship("PlacementAttendance", backref="student", lazy=True, cascade="all, delete-orphan")
    shortlists = db.relationship("Shortlist", backref="student", lazy=True, cascade="all, delete-orphan")
    offers = db.relationship("Offer", backref="student", lazy=True, cascade="all, delete-orphan")
    ats_results = db.relationship("ATSAnalysis", backref="student", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        dept_code = self.department.code if self.department else ""
        dept_name = self.department.name if self.department else ""
        
        # Primary Offer details if placed
        latest_offer = None
        if self.offers:
            first_offer = sorted(self.offers, key=lambda x: x.created_at or datetime.min, reverse=True)[0]
            latest_offer = {
                "company_name": first_offer.company.name if first_offer.company else first_offer.role,
                "role": first_offer.role,
                "ctc_lpa": first_offer.ctc_lpa,
                "offer_date": first_offer.offer_date.strftime("%Y-%m-%d") if first_offer.offer_date else ""
            }

        return {
            "id": self.id,
            "roll_no": self.roll_no,
            "name": self.name,
            "department_id": self.department_id,
            "department_code": dept_code,
            "department_name": dept_name,
            "gender": self.gender,
            "residency_type": self.residency_type,
            "sslc_percent": self.sslc_percent,
            "hsc_percent": self.hsc_percent,
            "ug_percent": self.ug_percent,
            "pg_percent": self.pg_percent,
            "degree": self.degree,
            "grad_year_10th": self.grad_year_10th,
            "grad_year_12th": self.grad_year_12th,
            "grad_year_ug": self.grad_year_ug,
            "grad_year_pg": self.grad_year_pg,
            "email": self.email,
            "mobile_no": self.mobile_no,
            "github_url": self.github_url or "",
            "linkedin_url": self.linkedin_url or "",
            "portfolio_url": self.portfolio_url or "",
            "resume_url": self.resume_url or "",
            "self_intro_url": self.self_intro_url or "",
            "photo_url": self.photo_url or "",
            "drive_links": self.drive_links or "",
            "placement_status": self.placement_status,
            "latest_offer": latest_offer,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None
        }

class Company(db.Model):
    __tablename__ = "companies"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    contact_person = db.Column(db.String(100), nullable=False)
    mobile_no = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    employee_count = db.Column(db.String(50), nullable=True)
    google_maps_link = db.Column(db.String(500), nullable=True)
    address = db.Column(db.Text, nullable=True)
    ctc_lpa = db.Column(db.Float, nullable=False, default=0.0)
    
    # JD and Docs
    jd_file_url = db.Column(db.String(500), nullable=True)
    jd_text = db.Column(db.Text, nullable=True)
    
    # Status Pipeline: COLD, WARM, HOT, DRIVE COMPLETED
    status = db.Column(db.String(30), default="COLD", index=True)
    
    # Admin Approval Workflow & Forward Notification
    is_approved = db.Column(db.Boolean, default=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    forwarded_to_admin = db.Column(db.Boolean, default=False, index=True)
    forwarded_note = db.Column(db.Text, nullable=True)
    forwarded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    forwarded_at = db.Column(db.DateTime, nullable=True)
    
    # Team member who added this
    added_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    total_offers_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    status_history = db.relationship("CompanyStatusHistory", backref="company", lazy=True, cascade="all, delete-orphan")
    drives = db.relationship("PlacementDrive", backref="company", lazy=True, cascade="all, delete-orphan")
    offers = db.relationship("Offer", backref="company", lazy=True)
    ats_results = db.relationship("ATSAnalysis", backref="company", lazy=True)

    def to_dict(self):
        added_by_member = self.added_by_user.member_id if self.added_by_user else "N/A"
        added_by_name = self.added_by_user.full_name if self.added_by_user else "N/A"
        approved_by_name = self.approved_by_user.full_name if self.approved_by_user else None
        
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "website": self.website or "",
            "contact_person": self.contact_person,
            "mobile_no": self.mobile_no,
            "email": self.email,
            "employee_count": self.employee_count or "",
            "google_maps_link": self.google_maps_link or "",
            "address": self.address or "",
            "ctc_lpa": self.ctc_lpa,
            "jd_file_url": self.jd_file_url or "",
            "jd_text": self.jd_text or "",
            "status": self.status,
            "is_approved": self.is_approved,
            "approved_by_name": approved_by_name,
            "approved_at": self.approved_at.strftime("%Y-%m-%d %H:%M") if self.approved_at else None,
            "forwarded_to_admin": bool(self.forwarded_to_admin),
            "forwarded_note": self.forwarded_note or "",
            "forwarded_at": self.forwarded_at.strftime("%Y-%m-%d %H:%M") if self.forwarded_at else None,
            "added_by_id": self.added_by_id,
            "added_by_member": added_by_member,
            "added_by_name": added_by_name,
            "total_offers_count": self.total_offers_count,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None
        }

class CompanyStatusHistory(db.Model):
    __tablename__ = "company_status_history"
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    old_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    changed_by = db.relationship("User", foreign_keys=[changed_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "changed_by": self.changed_by.member_id if self.changed_by else "System",
            "remarks": self.remarks or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None
        }

class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    role_name = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=True)
    ctc_lpa = db.Column(db.Float, nullable=False)
    drive_date = db.Column(db.Date, nullable=False)
    min_sslc_percent = db.Column(db.Float, default=60.0)
    min_hsc_percent = db.Column(db.Float, default=60.0)
    min_ug_percent = db.Column(db.Float, default=60.0)
    eligible_departments = db.Column(db.String(200), default="ALL")  # CSV e.g., "CSE,IT,ECE" or "ALL"
    status = db.Column(db.String(20), default="SCHEDULED")  # SCHEDULED, ONGOING, COMPLETED, CANCELLED
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    registrations = db.relationship("PlacementRegistration", backref="drive", lazy=True, cascade="all, delete-orphan")
    attendances = db.relationship("PlacementAttendance", backref="drive", lazy=True, cascade="all, delete-orphan")
    shortlists = db.relationship("Shortlist", backref="drive", lazy=True, cascade="all, delete-orphan")
    offers = db.relationship("Offer", backref="drive", lazy=True)
    ats_results = db.relationship("ATSAnalysis", backref="drive", lazy=True)

    def to_dict(self):
        registered_count = len(self.registrations) if self.registrations else 0
        present_count = len([a for a in self.attendances if a.is_present]) if self.attendances else 0
        offers_count = len(self.offers) if self.offers else 0
        
        return {
            "id": self.id,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else "N/A",
            "company_location": self.company.location if self.company else "",
            "role_name": self.role_name,
            "job_description": self.job_description or (self.company.jd_text if self.company else ""),
            "ctc_lpa": self.ctc_lpa,
            "drive_date": self.drive_date.strftime("%Y-%m-%d") if self.drive_date else "",
            "min_sslc_percent": self.min_sslc_percent,
            "min_hsc_percent": self.min_hsc_percent,
            "min_ug_percent": self.min_ug_percent,
            "eligible_departments": self.eligible_departments,
            "status": self.status,
            "registered_count": registered_count,
            "present_count": present_count,
            "offers_count": offers_count,
            "created_by": self.created_by.member_id if self.created_by else "System",
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None
        }

class PlacementRegistration(db.Model):
    __tablename__ = "placement_registrations"
    __table_args__ = (db.UniqueConstraint("drive_id", "student_id", name="unique_drive_student_reg"),)
    
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "drive_id": self.drive_id,
            "student_id": self.student_id,
            "student_roll_no": self.student.roll_no if self.student else "",
            "student_name": self.student.name if self.student else "",
            "department_code": self.student.department.code if self.student and self.student.department else "",
            "ug_percent": self.student.ug_percent if self.student else 0,
            "registered_at": self.registered_at.strftime("%Y-%m-%d %H:%M") if self.registered_at else None
        }

class PlacementAttendance(db.Model):
    __tablename__ = "placement_attendance"
    __table_args__ = (db.UniqueConstraint("drive_id", "student_id", name="unique_drive_student_att"),)
    
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    is_present = db.Column(db.Boolean, default=False)
    marked_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    marked_by = db.relationship("User", foreign_keys=[marked_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "drive_id": self.drive_id,
            "student_id": self.student_id,
            "student_roll_no": self.student.roll_no if self.student else "",
            "student_name": self.student.name if self.student else "",
            "department_code": self.student.department.code if self.student and self.student.department else "",
            "is_present": self.is_present,
            "status_text": "Present" if self.is_present else "Absent",
            "marked_by": self.marked_by.member_id if self.marked_by else "System",
            "marked_at": self.marked_at.strftime("%Y-%m-%d %H:%M") if self.marked_at else None
        }

class Shortlist(db.Model):
    __tablename__ = "shortlists"
    
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    round_name = db.Column(db.String(50), default="Aptitude Round")  # Aptitude, Technical, HR
    is_shortlisted = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "drive_id": self.drive_id,
            "student_id": self.student_id,
            "student_roll_no": self.student.roll_no if self.student else "",
            "student_name": self.student.name if self.student else "",
            "department_code": self.student.department.code if self.student and self.student.department else "",
            "round_name": self.round_name,
            "is_shortlisted": self.is_shortlisted,
            "notes": self.notes or ""
        }

class Offer(db.Model):
    __tablename__ = "offers"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=True)
    role = db.Column(db.String(100), nullable=False)
    ctc_lpa = db.Column(db.Float, nullable=False)
    offer_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    offer_letter_url = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_roll_no": self.student.roll_no if self.student else "",
            "student_name": self.student.name if self.student else "",
            "department_code": self.student.department.code if self.student and self.student.department else "",
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else "",
            "drive_id": self.drive_id,
            "role": self.role,
            "ctc_lpa": self.ctc_lpa,
            "offer_date": self.offer_date.strftime("%Y-%m-%d") if self.offer_date else "",
            "offer_letter_url": self.offer_letter_url or "",
            "created_by": self.created_by.member_id if self.created_by else "System"
        }

class ATSAnalysis(db.Model):
    __tablename__ = "ats_analysis"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=True)
    ats_score = db.Column(db.Integer, nullable=False)  # 0 to 100
    category = db.Column(db.String(30), nullable=False)  # '0-60', '61-70', '71-80', '81-90', '91-100'
    matched_skills = db.Column(db.Text, nullable=True)  # Comma separated or JSON string
    missing_skills = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    analyzed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    analyzed_by = db.relationship("User", foreign_keys=[analyzed_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "roll_no": self.student.roll_no if self.student else "",
            "student_name": self.student.name if self.student else "",
            "department_code": self.student.department.code if self.student and self.student.department else "",
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else "Generic JD",
            "drive_id": self.drive_id,
            "ats_score": self.ats_score,
            "category": self.category,
            "matched_skills": [s.strip() for s in self.matched_skills.split(",") if s.strip()] if self.matched_skills else [],
            "missing_skills": [s.strip() for s in self.missing_skills.split(",") if s.strip()] if self.missing_skills else [],
            "summary": self.summary or "",
            "is_high_match": self.ats_score >= 91,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None
        }

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)  # CREATE_COMPANY, UPDATE_STATUS, FORWARD_ADMIN, ATS_SCAN, etc.
    target_entity = db.Column(db.String(50), nullable=False)  # Company, Student, Drive, Offer
    target_id = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else "System",
            "member_id": self.user.member_id if self.user else "SYS",
            "action_type": self.action_type,
            "target_entity": self.target_entity,
            "target_id": self.target_id or "",
            "description": self.description,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
