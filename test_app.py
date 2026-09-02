import unittest
import json
import database
import scraper
import analysis
import visualization
from app import app

class NaukriAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()
        database.init_db()
        database.seed_sample_data(force=True)

    def test_01_database_crud(self):
        job_id = database.insert_job({
            'job_title': 'Unit Test Python Developer',
            'company': 'UnitTest Corp',
            'location': 'Bengaluru',
            'salary': '20-30 Lacs PA',
            'min_salary': 20.0,
            'max_salary': 30.0,
            'avg_salary': 25.0,
            'experience': '3-6 Yrs',
            'min_exp': 3.0,
            'max_exp': 6.0,
            'skills': 'Python, Flask, PyTest',
            'job_type': 'Remote'
        })
        self.assertIsNotNone(job_id)
        
        job = database.get_job_by_id(job_id)
        self.assertEqual(job['job_title'], 'Unit Test Python Developer')
        self.assertEqual(job['company'], 'UnitTest Corp')

        updated = database.update_job(job_id, {
            'job_title': 'Updated Lead Python Developer',
            'company': 'UnitTest Corp',
            'location': 'Hyderabad',
            'salary': '25-35 Lacs PA',
            'min_salary': 25.0,
            'max_salary': 35.0,
            'avg_salary': 30.0,
            'experience': '5-8 Yrs',
            'min_exp': 5.0,
            'max_exp': 8.0,
            'skills': 'Python, FastAPI, AWS',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com',
            'job_type': 'Hybrid'
        })
        self.assertTrue(updated)
        
        job = database.get_job_by_id(job_id)
        self.assertEqual(job['job_title'], 'Updated Lead Python Developer')

        deleted = database.delete_job(job_id)
        self.assertTrue(deleted)
        self.assertIsNone(database.get_job_by_id(job_id))

    def test_02_scraper_parsers(self):
        min_s, max_s, avg_s = scraper.parse_salary("15-25 Lacs PA")
        self.assertEqual(min_s, 15.0)
        self.assertEqual(max_s, 25.0)
        self.assertEqual(avg_s, 20.0)

        min_e, max_e = scraper.parse_experience("4-8 Yrs")
        self.assertEqual(min_e, 4.0)
        self.assertEqual(max_e, 8.0)

        j_type = scraper.determine_job_type("Senior Remote Engineer", "Bengaluru")
        self.assertEqual(j_type, "Remote")

    def test_03_analysis_module(self):
        df = analysis.load_data()
        self.assertFalse(df.empty)
        
        kpis = analysis.get_kpi_summary(df)
        self.assertGreater(kpis['total_jobs'], 0)
        self.assertGreater(kpis['unique_companies'], 0)
        self.assertGreater(kpis['avg_salary'], 0)

        cities = analysis.get_jobs_by_city_data(df)
        self.assertIsInstance(cities, list)

        skills = analysis.get_top_skills_data(df)
        self.assertIsInstance(skills, list)
        self.assertGreater(len(skills), 0)

    def test_04_visualization_charts(self):
        charts = visualization.generate_all_dashboard_charts()
        expected_keys = [
            'jobs_by_city', 'top_companies', 'salary_distribution',
            'experience_distribution', 'top_skills', 'work_mode',
            'salary_vs_exp', 'role_benchmarks'
        ]
        for key in expected_keys:
            self.assertIn(key, charts)
            self.assertIn('data', charts[key])
            self.assertIn('layout', charts[key])

    def test_05_routes(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/search')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/jobs')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/analytics')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/database')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('total_jobs', data)

        res = self.client.get('/api/export/csv')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')

        res = self.client.get('/api/export/excel')
        self.assertEqual(res.status_code, 200)

    def test_06_api_jobs_crud(self):
        res = self.client.post('/api/jobs', json={
            'job_title': 'API Test Engineer',
            'company': 'Test Co',
            'location': 'Bengaluru',
            'salary': '12-18 Lacs PA',
            'experience': '2-4 Yrs',
            'skills': 'Selenium, Python',
            'job_type': 'On-site'
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        job_id = data['id']

        res = self.client.get(f'/api/jobs/{job_id}')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['data']['job_title'], 'API Test Engineer')

        res = self.client.delete(f'/api/jobs/{job_id}')
        self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(NaukriAppTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("ALL TESTS COMPLETED. Success:", result.wasSuccessful())
