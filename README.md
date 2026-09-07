# Campus Placement Management System (PlacementOS)

A comprehensive, enterprise-grade **Training and Placement Cell Management Portal** built with **Flask, Python, SQLAlchemy, Tailwind CSS, and Google Gemini AI**. 

Designed for higher-education institutions to manage 3,000+ candidate databases, recruitment pipelines, placement drives, automated resume ATS scoring, Microsoft Word (.docx) job description generation, and email-driven administrative approval workflows.

---

##  Key Features & Modules

### 1. ?? Role-Gated Access Control
* **Admin (Placement Head - Dr. Sivasubramaniyan Sir)**: 
  * Full unrestricted access to all 7 modules.
  * Dedicated **Email Verification Field** for team proposals.
  * 1-click drive approvals, JD downloads, and audit logs.
* **Manager (Dean of Academics - Dr. Jeyakannan Sir)**:
  * Overall Analytics Dashboard, 3,000+ Student Directory, Departmental Placement Reports.
* **Team Lead & Placement Members (MEM001 — MEM010)**:
  * Access to **Overall Analytics Dashboard** & **Company Pipeline CRM**.
  * Ability to add company proposals with proposed drive dates, review notes, and job descriptions.

---

### 2.  Gemini AI ATS Resume Matcher
* **Direct File Upload**: Upload resume files directly (.pdf, .docx, .txt) or select from the student database.
* **Autonomous Match Scoring**:
  * **91–100%**: Top Tier Candidate (Auto-alert badge)
  * **75–90%**: High Match Candidate
  * **60–74%**: Moderate Match
  * **40–59%**: Low Match
  * **< 40%**: Poor Match
* **Detailed Breakdown**: Identifies matched skills, missing skills, institutional recommendations, and evaluation summaries.

---

### 3.  Job Description Word Document (.docx) Generator
* 1-click download of formatted **Microsoft Word documents (.docx)** for any company job description.
* Built using python-docx with custom institutional letterheads, corporate tables, eligibility criteria, CTC packages, and selection rounds.

---

### 4.  Company Proposal Sharing & Email Verification Center
* **Team Submission**: Team Leads & Members fill in company details, CTC package, HR contact, proposed drive date, and notes.
* **Automated Admin Notification**: Dispatches a formatted HTML email alert to the Admin mailbox (sivasubramaniyan@college.edu).
* **Admin Verification Field**:
  * Visible on both **Main Dashboard** and **Company CRM**.
  * Admin can **?? Download JD (.docx)**, **? View Sent Email**, and **? Verify & Accept Proposal**.
  * Upon acceptance, an automated confirmation email is dispatched back to the placement team (placement-team@college.edu).

---

### 5.  Real-Time Analytics & Report Generation
* **Live Dashboards**: Placement percentage tracking, highest/average CTC metrics, and departmental placement charts (Chart.js).
* **Multi-Format Exports**:
  * **Excel Spreadsheets**: Formatted .xlsx exports via openpyxl.
  * **PDF Reports**: Formal reports with statistics and candidate summaries via ReportLab.

---

##  Default Credentials Reference

| Role | Username / Member ID | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Admin** | dmin | admin@123 | Full Suite (All 7 Modules + Verification Center) |
| **Manager** | manager | manager@123 | Analytics, Student Directory & Reports |
| **Team Lead** | lead / mem001 | 	eam123 | Overall Dashboard & Company CRM |
| **Team Member 02** | mem002 | 	eam123 | Overall Dashboard & Company CRM |
| **Team Member 03 — 10** | mem003 — mem010 | 	eam123 | Overall Dashboard & Company CRM |

---

##  Tech Stack

* **Backend**: Python 3.12, Flask, Flask-SQLAlchemy, Werkzeug, Gunicorn
* **AI Engine**: Google Gemini AI API (google-genai)
* **Document Processing**: python-docx (.docx generation), pypdf (PDF text extraction)
* **Reporting**: ReportLab (PDF generation), openpyxl (Excel generation)
* **Frontend**: HTML5, Tailwind CSS, JavaScript (ES6+), FontAwesome 6, Chart.js
* **Database**: SQLite / PostgreSQL with automated database seeding

---

##  Local Setup & Installation

### 1. Clone the Repository
`ash
git clone https://github.com/Nandhakishore-A/Placement_SIte.git
cd Placement_SIte
`

### 2. Create and Activate Virtual Environment
`ash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
`

### 3. Install Dependencies
`ash
pip install -r requirements.txt
`

### 4. Run the Application
`ash
python app.py
`
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

##  Deployment on Vercel

This repository is pre-configured for **Vercel Serverless Deployment**:

1. Import the repository into your Vercel account:
   * **https://placement-s-ite-96bk.vercel.app/login**
2. Select **Nandhakishore-A/Placement_SIte**.
3. (Optional) Set Environment Variables:
   * SECRET_KEY: super-secret-placement-key-2026
   * GEMINI_API_KEY: *(your Google Gemini API Key)*
4. Click **Deploy**.

---

##  License
This project is licensed under the MIT License.
