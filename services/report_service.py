import io
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_overall_placement_excel(students: list) -> io.BytesIO:
    """
    Generates Excel for All Students:
    Shows Roll No, Name, Department, SSLC %, HSC %, UG %, Status (PLACED / YET TO BE PLACED), Company, Role, CTC (LPA)
    If yet to be placed, CTC is '-' and Company/Role is '-'.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Overall Placement Report"
    
    # Styles
    title_font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    bold_data_font = Font(name="Calibri", size=10, bold=True)
    
    title_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Dark Blue
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")  # Blue
    placed_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")  # Light Green
    unplaced_fill = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid") # Light Red
    
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )
    
    # Title Block
    ws.merge_cells("A1:J1")
    title_cell = ws["A1"]
    title_cell.value = "CAMPUS PLACEMENT MANAGEMENT SYSTEM — OVERALL PLACEMENT REPORT"
    title_cell.font = title_font
    title_cell.fill = title_fill
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 40
    
    # Metadata Subtitle
    ws.merge_cells("A2:J2")
    sub_cell = ws["A2"]
    sub_cell.value = f"Generated On: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')} | Total Students: {len(students)}"
    sub_cell.font = Font(name="Calibri", size=10, italic=True, color="4B5563")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20
    
    # Headers
    headers = [
        "S.No", "Roll No", "Student Name", "Department", "UG %",
        "Gender", "Status", "Company Placed", "Job Role", "CTC (LPA)"
    ]
    
    ws.append([]) # Row 3 blank
    ws.append(headers) # Row 4
    ws.row_dimensions[4].height = 26
    
    for col_idx, _ in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
        
    # Data Rows
    row_num = 5
    for idx, s in enumerate(students, 1):
        is_placed = (s.get("placement_status") == "PLACED")
        latest_offer = s.get("latest_offer") or {}
        
        company_name = latest_offer.get("company_name", "-") if is_placed else "-"
        role_name = latest_offer.get("role", "-") if is_placed else "-"
        ctc = f"{latest_offer.get('ctc_lpa')} LPA" if is_placed and latest_offer.get('ctc_lpa') else "-"
        
        row_data = [
            idx,
            s.get("roll_no", ""),
            s.get("name", ""),
            s.get("department_code", ""),
            f"{s.get('ug_percent', 0)}%",
            s.get("gender", ""),
            s.get("placement_status", "YET TO BE PLACED"),
            company_name,
            role_name,
            ctc
        ]
        
        ws.append(row_data)
        ws.row_dimensions[row_num].height = 20
        
        status_color = placed_fill if is_placed else unplaced_fill
        
        for col_idx in range(1, len(row_data) + 1):
            c = ws.cell(row=row_num, column=col_idx)
            c.font = bold_data_font if col_idx in [2, 7, 10] else data_font
            c.border = thin_border
            if col_idx == 7:
                c.fill = status_color
            c.alignment = Alignment(
                horizontal="center" if col_idx in [1, 2, 4, 5, 6, 7, 10] else "left",
                vertical="center"
            )
            
        row_num += 1
        
    # Adjust column widths
    column_widths = {
        "A": 8, "B": 16, "C": 26, "D": 14, "E": 12,
        "F": 12, "G": 20, "H": 26, "I": 24, "J": 14
    }
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def generate_offers_excel(offers: list) -> io.BytesIO:
    """
    Generates Offers Report:
    S.No, Roll No, Name, Dept, Role, Company Name, CTC (LPA), Offer Date
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Offers Summary"
    
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid") # Emerald green
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )
    
    # Title
    ws.merge_cells("A1:H1")
    t_cell = ws["A1"]
    t_cell.value = "CAMPUS PLACEMENT MANAGEMENT SYSTEM — CANDIDATE OFFERS REPORT"
    t_cell.font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    t_cell.fill = PatternFill(start_color="064E3B", end_color="064E3B", fill_type="solid")
    t_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36
    
    headers = ["S.No", "Roll No", "Student Name", "Department", "Company Name", "Job Role", "CTC (LPA)", "Offer Date"]
    ws.append([])
    ws.append(headers)
    ws.row_dimensions[3].height = 24
    
    for col_idx, _ in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
        
    for idx, o in enumerate(offers, 1):
        row_data = [
            idx,
            o.get("student_roll_no", ""),
            o.get("student_name", ""),
            o.get("department_code", ""),
            o.get("company_name", ""),
            o.get("role", ""),
            f"{o.get('ctc_lpa', 0)} LPA",
            o.get("offer_date", "")
        ]
        ws.append(row_data)
        current_row = idx + 3
        for col_idx in range(1, len(row_data) + 1):
            c = ws.cell(row=current_row, column=col_idx)
            c.font = Font(name="Calibri", size=10)
            c.border = thin_border
            c.alignment = Alignment(
                horizontal="center" if col_idx in [1, 2, 4, 7, 8] else "left",
                vertical="center"
            )
            
    widths = {"A": 8, "B": 16, "C": 26, "D": 14, "E": 26, "F": 24, "G": 14, "H": 16}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def generate_company_stage_excel(companies: list, filter_stage: str = "ALL") -> io.BytesIO:
    """
    Generates Company Status / Stage Report with:
    S.No, Company Name, Location, Status (Cold, Warm, Hot, Drive Completed), CTC (LPA),
    Website, Contact Person, Mobile, Email, Added By Member, Date Added, Admin Approved (Y/N)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Company Pipeline Report"
    
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4338CA", end_color="4338CA", fill_type="solid") # Indigo
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )
    
    ws.merge_cells("A1:K1")
    t_cell = ws["A1"]
    t_cell.value = f"COMPANY STAGE & CRM REPORT — [{filter_stage.upper()}]"
    t_cell.font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    t_cell.fill = PatternFill(start_color="312E81", end_color="312E81", fill_type="solid")
    t_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36
    
    headers = [
        "S.No", "Company Name", "Location", "Status / Stage", "CTC (LPA)",
        "Contact Person", "Mobile No", "Email", "Added By Member", "Date Added", "Approved (Y/N)"
    ]
    ws.append([])
    ws.append(headers)
    ws.row_dimensions[3].height = 24
    
    for col_idx, _ in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
        
    for idx, c_item in enumerate(companies, 1):
        row_data = [
            idx,
            c_item.get("name", ""),
            c_item.get("location", ""),
            c_item.get("status", ""),
            f"{c_item.get('ctc_lpa', 0)} LPA",
            c_item.get("contact_person", ""),
            c_item.get("mobile_no", ""),
            c_item.get("email", ""),
            c_item.get("added_by_member", "N/A"),
            c_item.get("created_at", ""),
            "Y" if c_item.get("is_approved") else "N"
        ]
        ws.append(row_data)
        curr = idx + 3
        for col_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=curr, column=col_idx)
            cell.font = Font(name="Calibri", size=10)
            cell.border = thin_border
            cell.alignment = Alignment(
                horizontal="center" if col_idx in [1, 4, 5, 7, 9, 10, 11] else "left",
                vertical="center"
            )
            
    widths = {"A": 8, "B": 24, "C": 18, "D": 18, "E": 12, "F": 20, "G": 16, "H": 24, "I": 16, "J": 14, "K": 14}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def generate_overall_placement_pdf(students: list) -> io.BytesIO:
    """
    Generates Corporate PDF Placement Report via ReportLab
    """
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1, # Center
        spaceAfter=6
    )
    
    sub_style = ParagraphStyle(
        name='SubStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4B5563'),
        alignment=1,
        spaceAfter=14
    )
    
    elements = []
    
    # Title Block
    elements.append(Paragraph("<b>CAMPUS PLACEMENT MANAGEMENT SYSTEM</b>", title_style))
    elements.append(Paragraph(f"Official Placement & Candidate Status Report — Generated on {datetime.now().strftime('%d-%b-%Y %H:%M')}", sub_style))
    
    # Summary stats
    placed_count = sum(1 for s in students if s.get("placement_status") == "PLACED")
    unplaced_count = len(students) - placed_count
    pct = round((placed_count / len(students) * 100), 1) if students else 0
    
    summary_text = f"<b>Total Candidates:</b> {len(students)} | <b>Placed:</b> {placed_count} ({pct}%) | <b>Yet To Be Placed:</b> {unplaced_count}"
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 10))
    
    # Table Data (top 150 rows for clean PDF rendering if large, with note)
    table_headers = ["S.No", "Roll No", "Student Name", "Dept", "UG %", "Status", "Company", "Role", "CTC (LPA)"]
    data = [table_headers]
    
    for idx, s in enumerate(students[:150], 1):
        is_placed = (s.get("placement_status") == "PLACED")
        latest = s.get("latest_offer") or {}
        comp = latest.get("company_name", "-") if is_placed else "-"
        role = latest.get("role", "-") if is_placed else "-"
        ctc = f"{latest.get('ctc_lpa')} LPA" if is_placed and latest.get('ctc_lpa') else "-"
        
        row = [
            str(idx),
            s.get("roll_no", ""),
            s.get("name", "")[:20],
            s.get("department_code", ""),
            f"{s.get('ug_percent', 0)}%",
            s.get("placement_status", "YET TO BE PLACED"),
            comp[:18],
            role[:16],
            ctc
        ]
        data.append(row)
        
    t = Table(data, colWidths=[35, 80, 140, 50, 50, 110, 110, 100, 75])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    
    elements.append(t)
    doc.build(elements)
    output.seek(0)
    return output

def generate_jd_docx(company_data: dict) -> io.BytesIO:
    """
    Generates a professionally formatted Word Document (.docx) for a Company Job Description.
    """
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import qn, nsdecls

    doc = docx.Document()

    # Page Margins (0.75 in)
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    comp_name = company_data.get("name", "Campus Recruiter")
    location = company_data.get("location", "Not Specified")
    ctc = company_data.get("ctc_lpa", 0.0)
    contact_person = company_data.get("contact_person", "Campus HR")
    mobile = company_data.get("mobile_no", "N/A")
    email = company_data.get("email", "N/A")
    website = company_data.get("website", "N/A")
    status = company_data.get("status", "HOT")
    jd_text = company_data.get("jd_text") or "Candidate will contribute to core software engineering, development, testing, and modern technical workflows."

    # Title Header
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title_p.add_run("CAMPUS RECRUITMENT DRIVE 2026")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(30, 58, 138) # Dark Blue

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub_p.add_run("OFFICIAL JOB DESCRIPTION & ELIGIBILITY CRITERIA")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(11)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(75, 85, 99)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 1. Company Overview Table
    h1 = doc.add_heading("1. Corporate Overview & Drive Profile", level=2)
    for run in h1.runs:
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(37, 99, 235)

    table = doc.add_table(rows=6, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    info_rows = [
        ("Company Name", comp_name),
        ("Job Location", location),
        ("CTC Package (Annual)", f"{ctc} LPA" if ctc else "Best in Industry"),
        ("Official Website", website),
        ("HR Contact Details", f"{contact_person} | Email: {email} | Ph: +91 {mobile}"),
        ("Recruitment Stage", f"{status} (Campus Placement 2026)")
    ]

    for idx, (label, val) in enumerate(info_rows):
        row = table.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        
        # Format label cell
        p_lbl = cell_lbl.paragraphs[0]
        r_lbl = p_lbl.add_run(label)
        r_lbl.font.bold = True
        r_lbl.font.size = Pt(10)
        r_lbl.font.name = "Arial"
        cell_lbl.width = Inches(2.2)

        # Format value cell
        p_val = cell_val.paragraphs[0]
        r_val = p_val.add_run(str(val))
        r_val.font.size = Pt(10)
        r_val.font.name = "Arial"
        cell_val.width = Inches(4.8)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # 2. Detailed Job Description & Responsibilities
    h2 = doc.add_heading("2. Job Description & Core Responsibilities", level=2)
    for run in h2.runs:
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(37, 99, 235)

    p_jd = doc.add_paragraph()
    r_jd = p_jd.add_run(jd_text)
    r_jd.font.name = "Arial"
    r_jd.font.size = Pt(10.5)
    p_jd.paragraph_format.line_spacing = 1.2
    p_jd.paragraph_format.space_after = Pt(12)

    # 3. Eligibility Criteria & Qualifications
    h3 = doc.add_heading("3. Candidate Eligibility Criteria", level=2)
    for run in h3.runs:
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(37, 99, 235)

    eligibility_points = [
        "Degree & Branches: B.E / B.Tech / M.E in CSE, IT, AI&DS, AIML, ECE, EEE, Mechanical, Civil.",
        "Academic Cut-off: Minimum 60.0% (6.0 CGPA) in 10th, 12th, and UG with No Standing Arrears.",
        "Core Skills: Strong foundation in Data Structures, Algorithms, Problem Solving, and Database Design.",
        "Technical Stack: Proficiency in at least one modern language (Python, Java, C++, JavaScript/TypeScript, SQL).",
        "Communication: Professional English verbal and written communication competencies."
    ]

    for pt in eligibility_points:
        doc.add_paragraph(pt, style='List Bullet')

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # 4. Selection Process Rounds
    h4 = doc.add_heading("4. Campus Recruitment Selection Rounds", level=2)
    for run in h4.runs:
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(37, 99, 235)

    rounds = [
        "Round 1: Online Aptitude, Logical Reasoning & Core Coding Assessment.",
        "Round 2: Technical Interview 1 — Data Structures, Projects, System Design & Live Coding.",
        "Round 3: Technical Interview 2 / Managerial Evaluation — Problem Solving & Domain Fitment.",
        "Round 4: Corporate HR Discussion & Final Offer Letter Rollout."
    ]
    for r in rounds:
        doc.add_paragraph(r, style='List Number')

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Footer note
    footer_p = doc.add_paragraph()
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_foot = footer_p.add_run(f"Department of Training & Placement Cell • Document generated on {datetime.now().strftime('%d-%b-%Y')}")
    r_foot.font.italic = True
    r_foot.font.size = Pt(8.5)
    r_foot.font.color.rgb = RGBColor(156, 163, 175)

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

