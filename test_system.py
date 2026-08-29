import unittest
import json
from app import create_app
from models import db, User, Student, Company, PlacementDrive, Offer

class PlacementSystemTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_01_user_logins(self):
        # 1. Admin Demo Login
        res = self.client.post('/api/auth/demo-login', json={'role': 'admin'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['user']['role'], 'admin')

        # 2. Manager Demo Login
        res = self.client.post('/api/auth/demo-login', json={'role': 'manager'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['user']['role'], 'manager')

        # 3. MEM001 Demo Login
        res = self.client.post('/api/auth/demo-login', json={'role': 'mem001'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['user']['member_id'], 'MEM001')

    def test_02_manager_access_restrictions(self):
        # Manager should ONLY have access to students
        self.client.post('/api/auth/demo-login', json={'role': 'manager'})
        
        # Access students: Allowed
        res = self.client.get('/api/students?page=1&per_page=5')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data['students']), 5)
        self.assertEqual(data['total'], 3000)

        # Access companies: Forbidden
        res = self.client.get('/api/companies')
        self.assertEqual(res.status_code, 403)

        # Access drives: Forbidden
        res = self.client.get('/api/drives')
        self.assertEqual(res.status_code, 403)

        # Access ATS: Forbidden
        res = self.client.post('/api/ats/analyze', json={'student_id': 1})
        self.assertEqual(res.status_code, 403)

    def test_03_team_member_company_and_forward(self):
        # Login as MEM003
        self.client.post('/api/auth/demo-login', json={'role': 'mem003'})

        # Add Company
        comp_payload = {
            "name": "Tesla Energy",
            "location": "Bangalore, Karnataka",
            "contact_person": "Elon Musk HR",
            "mobile_no": "9845112233",
            "email": "careers@tesla.com",
            "status": "COLD",
            "ctc_lpa": 18.0,
            "jd_text": "Embedded C++ and Python Battery Management Systems"
        }
        res = self.client.post('/api/companies', json=comp_payload)
        self.assertEqual(res.status_code, 201)
        comp_id = res.get_json()['company']['id']

        # Update Status to WARM
        res = self.client.put(f'/api/companies/{comp_id}/status', json={'status': 'WARM'})
        self.assertEqual(res.status_code, 200)

        # Forward to Admin
        res = self.client.post(f'/api/companies/{comp_id}/forward', json={'note': 'Requesting drive slot approval for Oct 2026'})
        self.assertEqual(res.status_code, 200)

        # Admin Logs in and Approves
        self.client.post('/api/auth/demo-login', json={'role': 'admin'})
        res = self.client.put(f'/api/companies/{comp_id}/approve', json={'is_approved': True})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['company']['is_approved'])

    def test_04_gemini_ats_evaluation(self):
        self.client.post('/api/auth/demo-login', json={'role': 'mem001'})
        
        # Test student 1 ATS Scan
        student = Student.query.first()
        comp = Company.query.first()
        
        res = self.client.post('/api/ats/analyze', json={
            'student_id': student.id,
            'company_id': comp.id,
            'jd_text': comp.jd_text
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('ats_score', data)
        self.assertIn('category', data)
        self.assertIn(data['category'], ['0-60', '61-70', '71-80', '81-90', '91-100'])

    def test_05_reports_generation(self):
        self.client.post('/api/auth/demo-login', json={'role': 'admin'})
        
        # Excel Overall Report
        res = self.client.get('/api/reports/overall-placement/excel?department=ALL&status=ALL')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # PDF Overall Report
        res = self.client.get('/api/reports/overall-placement/pdf?department=ALL&status=ALL')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/pdf')

if __name__ == '__main__':
    unittest.main()
