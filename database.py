import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = 'jobs.db'

def get_db_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            min_salary REAL DEFAULT 0.0,
            max_salary REAL DEFAULT 0.0,
            avg_salary REAL DEFAULT 0.0,
            experience TEXT,
            min_exp REAL DEFAULT 0.0,
            max_exp REAL DEFAULT 0.0,
            skills TEXT,
            posted_date TEXT,
            job_link TEXT,
            job_type TEXT DEFAULT 'On-site',
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_avg_salary ON jobs(avg_salary)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_min_exp ON jobs(min_exp)')
    conn.commit()
    conn.close()

def insert_job(job_dict, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO jobs (
            job_title, company, location, salary, min_salary, max_salary, avg_salary,
            experience, min_exp, max_exp, skills, posted_date, job_link, job_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        job_dict.get('job_title', 'Software Engineer'),
        job_dict.get('company', 'Tech Enterprise'),
        job_dict.get('location', 'Bengaluru'),
        job_dict.get('salary', 'Not Disclosed'),
        float(job_dict.get('min_salary', 0.0) or 0.0),
        float(job_dict.get('max_salary', 0.0) or 0.0),
        float(job_dict.get('avg_salary', 0.0) or 0.0),
        job_dict.get('experience', '2-5 Yrs'),
        float(job_dict.get('min_exp', 0.0) or 0.0),
        float(job_dict.get('max_exp', 0.0) or 0.0),
        job_dict.get('skills', ''),
        job_dict.get('posted_date', 'Today'),
        job_dict.get('job_link', 'https://www.naukri.com'),
        job_dict.get('job_type', 'On-site')
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def insert_jobs_bulk(jobs_list, db_path=DB_PATH):
    if not jobs_list:
        return 0
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    inserted_count = 0
    for job_dict in jobs_list:
        try:
            cursor.execute('''
                INSERT INTO jobs (
                    job_title, company, location, salary, min_salary, max_salary, avg_salary,
                    experience, min_exp, max_exp, skills, posted_date, job_link, job_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_dict.get('job_title', 'Software Engineer'),
                job_dict.get('company', 'Tech Enterprise'),
                job_dict.get('location', 'Bengaluru'),
                job_dict.get('salary', 'Not Disclosed'),
                float(job_dict.get('min_salary', 0.0) or 0.0),
                float(job_dict.get('max_salary', 0.0) or 0.0),
                float(job_dict.get('avg_salary', 0.0) or 0.0),
                job_dict.get('experience', '2-5 Yrs'),
                float(job_dict.get('min_exp', 0.0) or 0.0),
                float(job_dict.get('max_exp', 0.0) or 0.0),
                job_dict.get('skills', ''),
                job_dict.get('posted_date', 'Today'),
                job_dict.get('job_link', 'https://www.naukri.com'),
                job_dict.get('job_type', 'On-site')
            ))
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting job {job_dict.get('job_title')}: {e}")
    conn.commit()
    conn.close()
    return inserted_count

def get_all_jobs(filters=None, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = 'SELECT * FROM jobs WHERE 1=1'
    params = []
    
    if filters:
        if filters.get('search'):
            term = f"%{filters['search']}%".lower()
            query += ' AND (LOWER(job_title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(skills) LIKE ? OR LOWER(location) LIKE ?)'
            params.extend([term, term, term, term])
        if filters.get('role'):
            query += ' AND LOWER(job_title) LIKE ?'
            params.append(f"%{filters['role'].lower()}%")
        if filters.get('location'):
            query += ' AND LOWER(location) LIKE ?'
            params.append(f"%{filters['location'].lower()}%")
        if filters.get('job_type'):
            query += ' AND LOWER(job_type) = ?'
            params.append(filters['job_type'].lower())
        if filters.get('min_salary'):
            try:
                query += ' AND avg_salary >= ?'
                params.append(float(filters['min_salary']))
            except (ValueError, TypeError):
                pass
        if filters.get('max_salary'):
            try:
                query += ' AND avg_salary <= ?'
                params.append(float(filters['max_salary']))
            except (ValueError, TypeError):
                pass
        if filters.get('min_exp'):
            try:
                query += ' AND min_exp >= ?'
                params.append(float(filters['min_exp']))
            except (ValueError, TypeError):
                pass
        if filters.get('max_exp'):
            try:
                query += ' AND max_exp <= ?'
                params.append(float(filters['max_exp']))
            except (ValueError, TypeError):
                pass

    sort_col = filters.get('sort_by', 'id') if filters else 'id'
    sort_dir = filters.get('sort_dir', 'DESC') if filters else 'DESC'
    allowed_cols = ['id', 'job_title', 'company', 'location', 'avg_salary', 'min_exp', 'scraped_at', 'posted_date']
    if sort_col not in allowed_cols:
        sort_col = 'id'
    if sort_dir.upper() not in ['ASC', 'DESC']:
        sort_dir = 'DESC'
        
    query += f' ORDER BY {sort_col} {sort_dir}'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    jobs = [dict(row) for row in rows]
    conn.close()
    return jobs

def get_job_by_id(job_id, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_job(job_id, data, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE jobs SET
            job_title = ?,
            company = ?,
            location = ?,
            salary = ?,
            min_salary = ?,
            max_salary = ?,
            avg_salary = ?,
            experience = ?,
            min_exp = ?,
            max_exp = ?,
            skills = ?,
            posted_date = ?,
            job_link = ?,
            job_type = ?
        WHERE id = ?
    ''', (
        data.get('job_title'),
        data.get('company'),
        data.get('location'),
        data.get('salary'),
        float(data.get('min_salary', 0.0) or 0.0),
        float(data.get('max_salary', 0.0) or 0.0),
        float(data.get('avg_salary', 0.0) or 0.0),
        data.get('experience'),
        float(data.get('min_exp', 0.0) or 0.0),
        float(data.get('max_exp', 0.0) or 0.0),
        data.get('skills'),
        data.get('posted_date'),
        data.get('job_link'),
        data.get('job_type', 'On-site'),
        job_id
    ))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_job(job_id, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def clear_all_jobs(db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM jobs')
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='jobs'")
    conn.commit()
    conn.close()
    return True

def get_database_stats(db_path=DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM jobs')
    total = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(DISTINCT company) as total_companies FROM jobs')
    companies = cursor.fetchone()['total_companies']
    cursor.execute('SELECT COUNT(DISTINCT location) as total_locations FROM jobs')
    locations = cursor.fetchone()['total_locations']
    cursor.execute('SELECT MAX(scraped_at) as last_updated FROM jobs')
    last_update = cursor.fetchone()['last_updated']
    conn.close()
    return {
        'total_jobs': total,
        'total_companies': companies,
        'total_locations': locations,
        'last_updated': last_update or 'No data yet'
    }

def seed_sample_data(db_path=DB_PATH, force=False):
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM jobs')
    count = cursor.fetchone()['count']
    conn.close()
    
    if count > 0 and not force:
        return count

    if force:
        clear_all_jobs(db_path)

    sample_jobs = [
        {
            'job_title': 'Senior Software Development Engineer (SDE-2)',
            'company': 'Amazon India',
            'location': 'Bengaluru',
            'salary': '28-45 Lacs PA',
            'min_salary': 28.0, 'max_salary': 45.0, 'avg_salary': 36.5,
            'experience': '4-8 Yrs',
            'min_exp': 4.0, 'max_exp': 8.0,
            'skills': 'Java, Microservices, AWS, Distributed Systems, Spring Boot, DynamoDB, Docker',
            'posted_date': '1 day ago',
            'job_link': 'https://www.naukri.com/job-listings-sde2-amazon-bengaluru-4-to-8-years',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Full Stack Java Developer',
            'company': 'Tata Consultancy Services (TCS)',
            'location': 'Hyderabad',
            'salary': '8-14 Lacs PA',
            'min_salary': 8.0, 'max_salary': 14.0, 'avg_salary': 11.0,
            'experience': '3-6 Yrs',
            'min_exp': 3.0, 'max_exp': 6.0,
            'skills': 'Java, Spring Boot, React.js, Hibernate, RESTful APIs, MySQL, Git',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-full-stack-java-tcs-hyderabad',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Python Backend Engineer',
            'company': 'Swiggy',
            'location': 'Bengaluru',
            'salary': '18-32 Lacs PA',
            'min_salary': 18.0, 'max_salary': 32.0, 'avg_salary': 25.0,
            'experience': '3-7 Yrs',
            'min_exp': 3.0, 'max_exp': 7.0,
            'skills': 'Python, Django, FastAPI, PostgreSQL, Redis, Celery, Kafka, Docker',
            'posted_date': '2 days ago',
            'job_link': 'https://www.naukri.com/job-listings-python-backend-swiggy-bengaluru',
            'job_type': 'Remote'
        },
        {
            'job_title': 'Lead Frontend Engineer (React / Next.js)',
            'company': 'Flipkart',
            'location': 'Bengaluru',
            'salary': '30-48 Lacs PA',
            'min_salary': 30.0, 'max_salary': 48.0, 'avg_salary': 39.0,
            'experience': '6-10 Yrs',
            'min_exp': 6.0, 'max_exp': 10.0,
            'skills': 'React.js, Next.js, TypeScript, Redux Toolkit, Webpack, Performance Optimization, GraphQL',
            'posted_date': 'Just Now',
            'job_link': 'https://www.naukri.com/job-listings-lead-frontend-flipkart',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'DevOps & Cloud Infrastructure Engineer',
            'company': 'Infosys',
            'location': 'Pune',
            'salary': '10-18 Lacs PA',
            'min_salary': 10.0, 'max_salary': 18.0, 'avg_salary': 14.0,
            'experience': '4-7 Yrs',
            'min_exp': 4.0, 'max_exp': 7.0,
            'skills': 'Kubernetes, Docker, AWS, Terraform, CI/CD, Jenkins, Linux, Python',
            'posted_date': '3 days ago',
            'job_link': 'https://www.naukri.com/job-listings-devops-engineer-infosys-pune',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Staff AI/ML Research Engineer',
            'company': 'Microsoft IDC',
            'location': 'Hyderabad',
            'salary': '42-65 Lacs PA',
            'min_salary': 42.0, 'max_salary': 65.0, 'avg_salary': 53.5,
            'experience': '6-12 Yrs',
            'min_exp': 6.0, 'max_exp': 12.0,
            'skills': 'PyTorch, Transformers, LLMs, LangChain, Python, Deep Learning, MLOps, Azure AI',
            'posted_date': '1 day ago',
            'job_link': 'https://www.naukri.com/job-listings-staff-ai-ml-microsoft',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Data Scientist - Predictive Analytics',
            'company': 'Fractal Analytics',
            'location': 'Mumbai',
            'salary': '14-24 Lacs PA',
            'min_salary': 14.0, 'max_salary': 24.0, 'avg_salary': 19.0,
            'experience': '3-6 Yrs',
            'min_exp': 3.0, 'max_exp': 6.0,
            'skills': 'Python, Machine Learning, Pandas, Scikit-Learn, SQL, Tableau, Statistics',
            'posted_date': '2 days ago',
            'job_link': 'https://www.naukri.com/job-listings-data-scientist-fractal',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Senior Data Engineer (Big Data / PySpark)',
            'company': 'Wipro Technologies',
            'location': 'Chennai',
            'salary': '12-22 Lacs PA',
            'min_salary': 12.0, 'max_salary': 22.0, 'avg_salary': 17.0,
            'experience': '5-8 Yrs',
            'min_exp': 5.0, 'max_exp': 8.0,
            'skills': 'PySpark, Hadoop, Apache Spark, SQL, Snowflake, Airflow, Python, GCP',
            'posted_date': '4 days ago',
            'job_link': 'https://www.naukri.com/job-listings-data-engineer-wipro',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Cyber Security Specialist',
            'company': 'HCLTech',
            'location': 'Noida',
            'salary': '11-19 Lacs PA',
            'min_salary': 11.0, 'max_salary': 19.0, 'avg_salary': 15.0,
            'experience': '4-8 Yrs',
            'min_exp': 4.0, 'max_exp': 8.0,
            'skills': 'SIEM, SOC, Penetration Testing, Network Security, Vulnerability Assessment, Splunk',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-cyber-security-hcl',
            'job_type': 'On-site'
        },
        {
            'job_title': 'iOS / Android Mobile App Developer (Flutter)',
            'company': 'Zomato',
            'location': 'Gurgaon',
            'salary': '16-28 Lacs PA',
            'min_salary': 16.0, 'max_salary': 28.0, 'avg_salary': 22.0,
            'experience': '3-6 Yrs',
            'min_exp': 3.0, 'max_exp': 6.0,
            'skills': 'Flutter, Dart, Mobile Architecture, State Management, REST APIs, iOS, Android',
            'posted_date': '2 days ago',
            'job_link': 'https://www.naukri.com/job-listings-mobile-flutter-zomato',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Principal Cloud Architect',
            'company': 'Google India',
            'location': 'Bengaluru',
            'salary': '55-85 Lacs PA',
            'min_salary': 55.0, 'max_salary': 85.0, 'avg_salary': 70.0,
            'experience': '10-16 Yrs',
            'min_exp': 10.0, 'max_exp': 16.0,
            'skills': 'GCP, Enterprise Architecture, Kubernetes, Cloud Migration, Terraform, Microservices',
            'posted_date': '3 days ago',
            'job_link': 'https://www.naukri.com/job-listings-cloud-architect-google',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'QA Automation Lead (Selenium / Cypress)',
            'company': 'Cognizant',
            'location': 'Pune',
            'salary': '9-16 Lacs PA',
            'min_salary': 9.0, 'max_salary': 16.0, 'avg_salary': 12.5,
            'experience': '5-9 Yrs',
            'min_exp': 5.0, 'max_exp': 9.0,
            'skills': 'Selenium, Cypress, Java, TestNG, Jenkins, Cucumber BDD, API Testing',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-qa-automation-cognizant',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Frontend React Developer',
            'company': 'Paytm',
            'location': 'Noida',
            'salary': '12-20 Lacs PA',
            'min_salary': 12.0, 'max_salary': 20.0, 'avg_salary': 16.0,
            'experience': '2-5 Yrs',
            'min_exp': 2.0, 'max_exp': 5.0,
            'skills': 'React.js, JavaScript, HTML5, CSS3, Redux, RESTful APIs, Git',
            'posted_date': '1 day ago',
            'job_link': 'https://www.naukri.com/job-listings-react-paytm-noida',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Junior Python Developer',
            'company': 'Zoho Corporation',
            'location': 'Chennai',
            'salary': '5-9 Lacs PA',
            'min_salary': 5.0, 'max_salary': 9.0, 'avg_salary': 7.0,
            'experience': '0-2 Yrs',
            'min_exp': 0.0, 'max_exp': 2.0,
            'skills': 'Python, Django, SQL, Data Structures, Algorithms, Git, Linux',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-junior-python-zoho',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Golang Backend Microservices Developer',
            'company': 'Razorpay',
            'location': 'Bengaluru',
            'salary': '24-40 Lacs PA',
            'min_salary': 24.0, 'max_salary': 40.0, 'avg_salary': 32.0,
            'experience': '3-7 Yrs',
            'min_exp': 3.0, 'max_exp': 7.0,
            'skills': 'Golang, Microservices, gRPC, PostgreSQL, Redis, Kafka, Distributed Systems',
            'posted_date': '2 days ago',
            'job_link': 'https://www.naukri.com/job-listings-golang-razorpay',
            'job_type': 'Remote'
        },
        {
            'job_title': 'Senior Product Manager - Tech & AI',
            'company': 'MakeMyTrip',
            'location': 'Gurgaon',
            'salary': '28-45 Lacs PA',
            'min_salary': 28.0, 'max_salary': 45.0, 'avg_salary': 36.5,
            'experience': '5-10 Yrs',
            'min_exp': 5.0, 'max_exp': 10.0,
            'skills': 'Product Management, Agile, User Stories, Roadmapping, Data Analytics, Generative AI',
            'posted_date': '3 days ago',
            'job_link': 'https://www.naukri.com/job-listings-pm-makemytrip',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Site Reliability Engineer (SRE)',
            'company': 'PhonePe',
            'location': 'Bengaluru',
            'salary': '20-35 Lacs PA',
            'min_salary': 20.0, 'max_salary': 35.0, 'avg_salary': 27.5,
            'experience': '3-6 Yrs',
            'min_exp': 3.0, 'max_exp': 6.0,
            'skills': 'Kubernetes, Prometheus, Grafana, Linux, Terraform, Python, Incident Management',
            'posted_date': '1 day ago',
            'job_link': 'https://www.naukri.com/job-listings-sre-phonepe',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Database Administrator (PostgreSQL / Oracle)',
            'company': 'Oracle India',
            'location': 'Hyderabad',
            'salary': '14-25 Lacs PA',
            'min_salary': 14.0, 'max_salary': 25.0, 'avg_salary': 19.5,
            'experience': '5-9 Yrs',
            'min_exp': 5.0, 'max_exp': 9.0,
            'skills': 'PostgreSQL, Oracle DB, SQL Performance Tuning, High Availability, Disaster Recovery',
            'posted_date': '5 days ago',
            'job_link': 'https://www.naukri.com/job-listings-dba-oracle',
            'job_type': 'Remote'
        },
        {
            'job_title': 'Senior React Native Developer',
            'company': 'Jio Platforms',
            'location': 'Mumbai',
            'salary': '15-26 Lacs PA',
            'min_salary': 15.0, 'max_salary': 26.0, 'avg_salary': 20.5,
            'experience': '4-7 Yrs',
            'min_exp': 4.0, 'max_exp': 7.0,
            'skills': 'React Native, JavaScript, Redux, Mobile App Lifecycle, iOS, Android, REST APIs',
            'posted_date': '3 days ago',
            'job_link': 'https://www.naukri.com/job-listings-react-native-jio',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Computer Vision Engineer',
            'company': 'Ola Electric',
            'location': 'Bengaluru',
            'salary': '22-38 Lacs PA',
            'min_salary': 22.0, 'max_salary': 38.0, 'avg_salary': 30.0,
            'experience': '3-7 Yrs',
            'min_exp': 3.0, 'max_exp': 7.0,
            'skills': 'OpenCV, PyTorch, C++, Python, Deep Learning, Object Detection, YOLO, Edge AI',
            'posted_date': '4 days ago',
            'job_link': 'https://www.naukri.com/job-listings-cv-ola-electric',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Full Stack MERN Developer',
            'company': 'Lenskart',
            'location': 'Gurgaon',
            'salary': '14-24 Lacs PA',
            'min_salary': 14.0, 'max_salary': 24.0, 'avg_salary': 19.0,
            'experience': '3-6 Yrs',
            'min_exp': 3.0, 'max_exp': 6.0,
            'skills': 'MongoDB, Express.js, React.js, Node.js, JavaScript, AWS, Redis',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-mern-lenskart',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'NLP / LLM Engineer',
            'company': 'Krudrim AI',
            'location': 'Bengaluru',
            'salary': '25-45 Lacs PA',
            'min_salary': 25.0, 'max_salary': 45.0, 'avg_salary': 35.0,
            'experience': '3-8 Yrs',
            'min_exp': 3.0, 'max_exp': 8.0,
            'skills': 'NLP, Python, PyTorch, HuggingFace, RAG, Fine-Tuning, Vector DB, LangChain',
            'posted_date': '1 day ago',
            'job_link': 'https://www.naukri.com/job-listings-nlp-krutrim',
            'job_type': 'Remote'
        },
        {
            'job_title': 'Associate Software Engineer - Fresher',
            'company': 'Tech Mahindra',
            'location': 'Hyderabad',
            'salary': '4-6.5 Lacs PA',
            'min_salary': 4.0, 'max_salary': 6.5, 'avg_salary': 5.25,
            'experience': '0-1 Yrs',
            'min_exp': 0.0, 'max_exp': 1.0,
            'skills': 'Java, C++, Core Java, SQL, Object Oriented Programming, Git',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-fresher-tech-mahindra',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Security Operations Center (SOC) Analyst',
            'company': 'Wipro Technologies',
            'location': 'Bengaluru',
            'salary': '7-12 Lacs PA',
            'min_salary': 7.0, 'max_salary': 12.0, 'avg_salary': 9.5,
            'experience': '2-4 Yrs',
            'min_exp': 2.0, 'max_exp': 4.0,
            'skills': 'SOC, Incident Response, SIEM, Threat Hunting, Splunk, Cyber Security',
            'posted_date': '3 days ago',
            'job_link': 'https://www.naukri.com/job-listings-soc-analyst-wipro',
            'job_type': 'On-site'
        },
        {
            'job_title': 'Salesforce Developer / Technical Consultant',
            'company': 'Accenture India',
            'location': 'Pune',
            'salary': '11-19 Lacs PA',
            'min_salary': 11.0, 'max_salary': 19.0, 'avg_salary': 15.0,
            'experience': '4-7 Yrs',
            'min_exp': 4.0, 'max_exp': 7.0,
            'skills': 'Salesforce, Apex, Lightning Web Components (LWC), SOQL, Salesforce Flow',
            'posted_date': '2 days ago',
            'job_link': 'https://www.naukri.com/job-listings-salesforce-accenture',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Senior Node.js / TypeScript Developer',
            'company': 'Cars24',
            'location': 'Gurgaon',
            'salary': '18-30 Lacs PA',
            'min_salary': 18.0, 'max_salary': 30.0, 'avg_salary': 24.0,
            'experience': '4-8 Yrs',
            'min_exp': 4.0, 'max_exp': 8.0,
            'skills': 'Node.js, TypeScript, Express, PostgreSQL, Microservices, Redis, AWS',
            'posted_date': '1 day ago',
            'job_link': 'https://www.naukri.com/job-listings-nodejs-cars24',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Data Analyst - Business Intelligence & SQL',
            'company': 'Mu Sigma',
            'location': 'Bengaluru',
            'salary': '7-13 Lacs PA',
            'min_salary': 7.0, 'max_salary': 13.0, 'avg_salary': 10.0,
            'experience': '2-5 Yrs',
            'min_exp': 2.0, 'max_exp': 5.0,
            'skills': 'SQL, PowerBI, Excel, Tableau, Python, Data Visualization, Data Cleansing',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-data-analyst-musigma',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Kubernetes & Platform Engineer',
            'company': 'Dell Technologies',
            'location': 'Bengaluru',
            'salary': '22-36 Lacs PA',
            'min_salary': 22.0, 'max_salary': 36.0, 'avg_salary': 29.0,
            'experience': '5-9 Yrs',
            'min_exp': 5.0, 'max_exp': 9.0,
            'skills': 'Kubernetes, Helm, Go, Linux, OpenShift, Terraform, Infrastructure as Code',
            'posted_date': '4 days ago',
            'job_link': 'https://www.naukri.com/job-listings-platform-engineer-dell',
            'job_type': 'Remote'
        },
        {
            'job_title': 'C++ Embedded Software Engineer',
            'company': 'Bosch India',
            'location': 'Bengaluru',
            'salary': '10-18 Lacs PA',
            'min_salary': 10.0, 'max_salary': 18.0, 'avg_salary': 14.0,
            'experience': '3-6 Yrs',
            'min_exp': 3.0, 'max_exp': 6.0,
            'skills': 'C++, Embedded C, RTOS, AUTOSAR, Microcontrollers, CAN protocol, Linux',
            'posted_date': '3 days ago',
            'job_link': 'https://www.naukri.com/job-listings-embedded-bosch',
            'job_type': 'On-site'
        },
        {
            'job_title': 'AI Solutions Architect',
            'company': 'IBM India',
            'location': 'Hyderabad',
            'salary': '35-55 Lacs PA',
            'min_salary': 35.0, 'max_salary': 55.0, 'avg_salary': 45.0,
            'experience': '8-14 Yrs',
            'min_exp': 8.0, 'max_exp': 14.0,
            'skills': 'Enterprise AI, WatsonX, Machine Learning, Python, Generative AI, Cloud Architecture',
            'posted_date': '2 days ago',
            'job_link': 'https://www.naukri.com/job-listings-ai-architect-ibm',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'UI/UX Designer & Frontend Specialist',
            'company': 'Urban Company',
            'location': 'Gurgaon',
            'salary': '12-22 Lacs PA',
            'min_salary': 12.0, 'max_salary': 22.0, 'avg_salary': 17.0,
            'experience': '3-6 Yrs',
            'min_exp': 3.0, 'max_exp': 6.0,
            'skills': 'Figma, UI/UX, HTML5, CSS3, TailwindCSS, JavaScript, Prototyping',
            'posted_date': 'Today',
            'job_link': 'https://www.naukri.com/job-listings-ui-ux-urban-company',
            'job_type': 'Hybrid'
        },
        {
            'job_title': 'Golang Systems Engineer',
            'company': 'Postman',
            'location': 'Bengaluru',
            'salary': '26-44 Lacs PA',
            'min_salary': 26.0, 'max_salary': 44.0, 'avg_salary': 35.0,
            'experience': '4-8 Yrs',
            'min_exp': 4.0, 'max_exp': 8.0,
            'skills': 'Go, High Concurrency, WebSockets, HTTP/2, Distributed Tracing, Docker',
            'posted_date': '1 day ago',
            'job_link': 'https://www.naukri.com/job-listings-systems-postman',
            'job_type': 'Remote'
        }
    ]

    return insert_jobs_bulk(sample_jobs, db_path)

if __name__ == '__main__':
    init_db()
    count = seed_sample_data(force=True)
    print(f"Database initialized with {count} sample records.")
