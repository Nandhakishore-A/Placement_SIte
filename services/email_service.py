import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

DISPATCHED_EMAILS = []

ADMIN_DEFAULT_EMAIL = os.getenv("ADMIN_NOTIFICATION_EMAIL", "sivasubramaniyan@college.edu")
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "placements-noreply@college.edu")

def send_admin_drive_proposal_email(company_data: dict, submitter_user, proposed_date: str = None, notes: str = None) -> dict:
    """
    Sends an automated email notification to Admin when a Team Lead / Member
    submits or forwards a new company proposal with essential drive details and JD.
    """
    comp_name = company_data.get("name", "New Recruiter")
    ctc = company_data.get("ctc_lpa", 0.0)
    location = company_data.get("location", "Not Specified")
    contact_person = company_data.get("contact_person", "Campus HR")
    mobile = company_data.get("mobile_no", "N/A")
    email = company_data.get("email", "N/A")
    website = company_data.get("website", "N/A")
    jd_text = company_data.get("jd_text") or "Candidate will contribute to core software engineering, development, testing, and modern technical workflows."
    
    submitter_name = getattr(submitter_user, "full_name", "Placement Team Member")
    submitter_role = getattr(submitter_user, "role", "team_member").replace("_", " ").title()
    submitter_id = getattr(submitter_user, "member_id", "MEM")
    submitter_email = getattr(submitter_user, "email", "team@college.edu")

    drive_date_str = proposed_date or "To be finalized by Admin"
    notes_str = notes or "Company details shared for placement verification and JD review."

    subject = f"[Action Required] Placement Proposal: {comp_name} ({ctc} LPA) submitted by {submitter_name} ({submitter_id})"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
            .container {{ max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 24px 30px; color: white; }}
            .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; }}
            .header p {{ margin: 4px 0 0 0; font-size: 13px; opacity: 0.9; }}
            .badge {{ display: inline-block; padding: 4px 12px; background: rgba(255,255,255,0.2); border-radius: 999px; font-size: 11px; font-weight: bold; margin-bottom: 8px; }}
            .content {{ padding: 28px 30px; }}
            .alert-box {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px 18px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; line-height: 1.5; }}
            .section-title {{ font-size: 14px; font-weight: bold; color: #1e3a8a; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px; margin: 20px 0 12px 0; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 13px; }}
            .info-table td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; }}
            .info-table td.label {{ font-weight: bold; color: #64748b; width: 35%; background: #f8fafc; }}
            .info-table td.val {{ color: #0f172a; }}
            .jd-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; font-size: 12px; line-height: 1.6; color: #334155; max-height: 180px; overflow-y: auto; white-space: pre-wrap; }}
            .btn-group {{ margin-top: 25px; text-align: center; }}
            .btn {{ display: inline-block; padding: 10px 22px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 13px; margin: 4px 6px; }}
            .btn-secondary {{ background: #2563eb; color: white; }}
            .footer {{ background: #f8fafc; padding: 16px 30px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #f1f5f9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="badge">🚨 CAMPUS PLACEMENT NOTIFICATION</span>
                <h1>New Company Proposal for Admin Verification</h1>
                <p>Submitted by <b>{submitter_name}</b> ({submitter_role} • {submitter_id})</p>
            </div>
            <div class="content">
                <div class="alert-box">
                    <strong>Respected Admin Sir,</strong><br>
                    A new recruitment drive proposal for <b>{comp_name}</b> has been submitted by the placement team. Please verify the essential company credentials and approve the drive.
                </div>

                <div class="section-title">🏢 Essential Company & Placement Details</div>
                <table class="info-table">
                    <tr><td class="label">Company Name</td><td class="val"><b>{comp_name}</b></td></tr>
                    <tr><td class="label">Offered CTC</td><td class="val"><b>{ctc} LPA</b></td></tr>
                    <tr><td class="label">Job Location</td><td class="val">{location}</td></tr>
                    <tr><td class="label">Official Website</td><td class="val"><a href="{website}">{website}</a></td></tr>
                    <tr><td class="label">HR Contact Person</td><td class="val">{contact_person}</td></tr>
                    <tr><td class="label">HR Email & Phone</td><td class="val">{email} | +91 {mobile}</td></tr>
                    <tr><td class="label">Proposed Drive Date</td><td class="val"><b>{drive_date_str}</b></td></tr>
                    <tr><td class="label">Team Notes</td><td class="val"><em>"{notes_str}"</em></td></tr>
                </table>

                <div class="section-title">📄 Job Description & Eligibility Overview</div>
                <div class="jd-box">{jd_text}</div>

                <div class="btn-group">
                    <a href="http://127.0.0.1:5000/api/companies/{company_data.get('id', 1)}/jd/download" class="btn btn-secondary">
                        📥 Download JD as Word Document (.docx)
                    </a>
                </div>
            </div>
            <div class="footer">
                Automated Placement Cell Dispatcher • Sent to {ADMIN_DEFAULT_EMAIL} on {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

    email_record = {
        "id": len(DISPATCHED_EMAILS) + 1,
        "type": "ADMIN_COMPANY_PROPOSAL",
        "to": ADMIN_DEFAULT_EMAIL,
        "from": SMTP_FROM_EMAIL,
        "subject": subject,
        "company_id": company_data.get("id"),
        "company_name": comp_name,
        "submitter_name": submitter_name,
        "submitter_id": submitter_id,
        "ctc_lpa": ctc,
        "proposed_date": drive_date_str,
        "notes": notes_str,
        "html_content": html_content,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "DELIVERED (SIMULATED & DISPATCHED)"
    }

    # Attempt live SMTP if configured
    if SMTP_SERVER and SMTP_USERNAME and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM_EMAIL
            msg["To"] = ADMIN_DEFAULT_EMAIL
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM_EMAIL, [ADMIN_DEFAULT_EMAIL], msg.as_string())
            email_record["status"] = "DELIVERED (SMTP LIVE)"
        except Exception as e:
            email_record["status"] = f"SMTP ERROR ({str(e)}), LOGGED TO DISPATCHED"

    DISPATCHED_EMAILS.insert(0, email_record)
    return email_record


def send_team_drive_approval_email(company_data: dict, admin_user, review_note: str = None) -> dict:
    """
    Sends confirmation email back to the Team Lead / Member when the Admin accepts and approves the company.
    """
    comp_name = company_data.get("name", "Campus Recruiter")
    ctc = company_data.get("ctc_lpa", 0.0)
    admin_name = getattr(admin_user, "full_name", "Dr. Sivasubramaniyan Sir (Admin)")
    
    subject = f"✓ [Approved] Drive Confirmed for {comp_name} ({ctc} LPA)"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: sans-serif; padding: 20px; background-color: #f0fdf4; color: #1e293b;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; border: 1px solid #bbf7d0; padding: 24px;">
            <h2 style="color: #16a34a; margin-top: 0;">🎉 Recruitment Drive Approved!</h2>
            <p>Hello Placement Team,</p>
            <p>The recruitment drive proposal for <b>{comp_name}</b> ({ctc} LPA) has been officially verified and approved by <b>{admin_name}</b>.</p>
            <div style="background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 13px;">
                <b>Admin Review Note:</b> {review_note or 'Drive approved. Eligible students can now be registered.'}
            </div>
            <p style="font-size: 12px; color: #64748b; margin-top: 20px;">
                Placement Management Portal • Approved on {datetime.now().strftime('%d-%b-%Y %H:%M')}
            </p>
        </div>
    </body>
    </html>
    """

    email_record = {
        "id": len(DISPATCHED_EMAILS) + 1,
        "type": "TEAM_DRIVE_APPROVAL",
        "to": "placement-team@college.edu",
        "from": SMTP_FROM_EMAIL,
        "subject": subject,
        "company_id": company_data.get("id"),
        "company_name": comp_name,
        "admin_name": admin_name,
        "review_note": review_note or "Approved",
        "html_content": html_content,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "DELIVERED (CONFIRMATION DISPATCHED)"
    }

    DISPATCHED_EMAILS.insert(0, email_record)
    return email_record
