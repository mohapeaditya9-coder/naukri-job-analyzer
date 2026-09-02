import os
import io
import csv
import threading
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, Response
import pandas as pd

import database
import scraper
import analysis
import visualization

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'naukri-analyzer-secret-key-2026'

# Ensure database initialized on startup
database.init_db()
# Seed if empty so the app has instant data
database.seed_sample_data()

# Global lock for background thread
scrape_thread = None

@app.route('/')
def index():
    """Home page with hero section, project overview, and quick stats."""
    stats = database.get_database_stats()
    df = analysis.load_data()
    kpis = analysis.get_kpi_summary(df)
    return render_template('index.html', stats=stats, kpis=kpis)

@app.route('/search')
def search_page():
    """Job search and scraping configuration page."""
    stats = database.get_database_stats()
    return render_template('search.html', stats=stats)

@app.route('/api/scrape/start', methods=['POST'])
def start_scraping():
    """Triggers background scraping task with user parameters."""
    global scrape_thread
    
    if scraper.scraper_tracker.is_running:
        return jsonify({
            'status': 'error',
            'message': 'A scraping task is already running. Please wait for it to finish.'
        }), 400

    data = request.get_json() or request.form
    role = data.get('role', 'Software Engineer')
    location = data.get('location', 'Bengaluru')
    experience = data.get('experience', '')
    pages = int(data.get('pages', 1) or 1)

    def run_scraper_worker():
        try:
            logger.info(f"Starting scraping task: role={role}, loc={location}, exp={experience}, pages={pages}")
            jobs = scraper.scrape_naukri_selenium(
                role=role,
                location=location,
                experience=experience,
                pages=pages
            )
            if jobs:
                inserted = database.insert_jobs_bulk(jobs)
                logger.info(f"Successfully inserted {inserted} jobs to database.")
        except Exception as e:
            logger.error(f"Scraper worker exception: {e}", exc_info=True)
            scraper.scraper_tracker.fail(str(e))

    scrape_thread = threading.Thread(target=run_scraper_worker, daemon=True)
    scrape_thread.start()

    return jsonify({
        'status': 'started',
        'message': f"Scraping started for '{role}' in '{location}' across {pages} page(s)."
    })

@app.route('/api/scrape/status')
def scrape_status():
    """Returns current live progress and logs of the scraper."""
    return jsonify(scraper.scraper_tracker.get_state())

@app.route('/dashboard')
def dashboard():
    """Main Analytics Dashboard with interactive Plotly charts and animated metrics."""
    df = analysis.load_data()
    kpis = analysis.get_kpi_summary(df)
    charts = visualization.generate_all_dashboard_charts(df)
    return render_template('dashboard.html', kpis=kpis, charts=charts)

@app.route('/jobs')
def jobs_page():
    """Job listings view with search, multi-filter, pagination, and export."""
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    loc_filter = request.args.get('location', '').strip()
    type_filter = request.args.get('job_type', '').strip()
    min_sal = request.args.get('min_salary', '').strip()
    max_sal = request.args.get('max_salary', '').strip()
    sort_by = request.args.get('sort_by', 'id')
    sort_dir = request.args.get('sort_dir', 'DESC')
    
    filters = {
        'search': search_query,
        'role': role_filter,
        'location': loc_filter,
        'job_type': type_filter,
        'min_salary': min_sal,
        'max_salary': max_sal,
        'sort_by': sort_by,
        'sort_dir': sort_dir
    }
    
    jobs = database.get_all_jobs(filters)
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 12))
    total_jobs = len(jobs)
    total_pages = max(1, (total_jobs + per_page - 1) // per_page)
    page = min(page, total_pages)
    
    start_idx = (page - 1) * per_page
    paginated_jobs = jobs[start_idx:start_idx + per_page]

    # Unique locations for filter dropdown
    all_jobs_raw = database.get_all_jobs()
    unique_locations = sorted(list(set([j['location'].split('/')[0].split(',')[0].strip() for j in all_jobs_raw if j['location']])))

    return render_template(
        'jobs.html',
        jobs=paginated_jobs,
        total_jobs=total_jobs,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        filters=filters,
        locations=unique_locations
    )

@app.route('/analytics')
def analytics_page():
    """Deep Dive Analytics Page with salary benchmarks, skill demands, and market insights."""
    df = analysis.load_data()
    kpis = analysis.get_kpi_summary(df)
    charts = visualization.generate_all_dashboard_charts(df)
    top_cities = analysis.get_jobs_by_city_data(df, limit=10)
    top_companies = analysis.get_top_companies_data(df, limit=10)
    top_skills = analysis.get_top_skills_data(df, limit=15)
    role_benchmarks = analysis.get_role_benchmarks(df, limit=10)
    insights = analysis.generate_market_insights(df)

    return render_template(
        'analytics.html',
        kpis=kpis,
        charts=charts,
        top_cities=top_cities,
        top_companies=top_companies,
        top_skills=top_skills,
        role_benchmarks=role_benchmarks,
        insights=insights
    )

@app.route('/database')
def database_page():
    """Database Administration page with full CRUD table, manual add, and reset options."""
    jobs = database.get_all_jobs()
    stats = database.get_database_stats()
    return render_template('database.html', jobs=jobs, stats=stats)

@app.route('/api/jobs', methods=['GET'])
def api_get_jobs():
    """API endpoint to get list of jobs."""
    jobs = database.get_all_jobs(request.args.to_dict())
    return jsonify({'success': True, 'count': len(jobs), 'data': jobs})

@app.route('/api/jobs', methods=['POST'])
def api_add_job():
    """API endpoint to manually add a new job listing."""
    data = request.get_json() or request.form.to_dict()
    if not data.get('job_title') or not data.get('company'):
        return jsonify({'success': False, 'message': 'Job Title and Company are required.'}), 400

    min_sal, max_sal, avg_sal = scraper.parse_salary(data.get('salary', ''))
    min_exp, max_exp = scraper.parse_experience(data.get('experience', ''))
    
    job_payload = {
        'job_title': data.get('job_title'),
        'company': data.get('company'),
        'location': data.get('location', 'Bengaluru'),
        'salary': data.get('salary', 'Not Disclosed'),
        'min_salary': min_sal,
        'max_salary': max_sal,
        'avg_salary': avg_sal,
        'experience': data.get('experience', '2-5 Yrs'),
        'min_exp': min_exp,
        'max_exp': max_exp,
        'skills': data.get('skills', ''),
        'posted_date': data.get('posted_date', 'Today'),
        'job_link': data.get('job_link', 'https://www.naukri.com'),
        'job_type': data.get('job_type', 'On-site')
    }
    
    new_id = database.insert_job(job_payload)
    return jsonify({'success': True, 'id': new_id, 'message': 'Job created successfully!'})

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def api_get_job(job_id):
    """API endpoint to retrieve single job record."""
    job = database.get_job_by_id(job_id)
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    return jsonify({'success': True, 'data': job})

@app.route('/api/jobs/<int:job_id>', methods=['PUT', 'POST'])
def api_update_job(job_id):
    """API endpoint to update existing job record."""
    data = request.get_json() or request.form.to_dict()
    
    min_sal, max_sal, avg_sal = scraper.parse_salary(data.get('salary', ''))
    min_exp, max_exp = scraper.parse_experience(data.get('experience', ''))
    
    update_payload = {
        'job_title': data.get('job_title'),
        'company': data.get('company'),
        'location': data.get('location'),
        'salary': data.get('salary'),
        'min_salary': min_sal,
        'max_salary': max_sal,
        'avg_salary': avg_sal,
        'experience': data.get('experience'),
        'min_exp': min_exp,
        'max_exp': max_exp,
        'skills': data.get('skills'),
        'posted_date': data.get('posted_date'),
        'job_link': data.get('job_link'),
        'job_type': data.get('job_type', 'On-site')
    }
    
    updated = database.update_job(job_id, update_payload)
    if updated:
        return jsonify({'success': True, 'message': 'Job record updated successfully!'})
    return jsonify({'success': False, 'message': 'Job not found or update failed.'}), 400

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def api_delete_job(job_id):
    """API endpoint to delete job record."""
    deleted = database.delete_job(job_id)
    if deleted:
        return jsonify({'success': True, 'message': 'Job deleted successfully!'})
    return jsonify({'success': False, 'message': 'Job not found'}), 404

@app.route('/api/database/clear', methods=['POST', 'DELETE'])
def api_clear_database():
    """Wipes all records from jobs table."""
    database.clear_all_jobs()
    return jsonify({'success': True, 'message': 'All jobs have been cleared.'})

@app.route('/api/database/seed', methods=['POST'])
def api_seed_database():
    """Re-seeds sample realistic data."""
    count = database.seed_sample_data(force=True)
    return jsonify({'success': True, 'message': f'Database populated with {count} sample jobs.'})

@app.route('/api/stats')
def api_stats():
    """Live stats API for real-time dashboard updates."""
    df = analysis.load_data()
    kpis = analysis.get_kpi_summary(df)
    return jsonify(kpis)

@app.route('/api/export/csv')
def export_csv():
    """Exports all or filtered jobs to a downloadable CSV file."""
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    loc_filter = request.args.get('location', '').strip()
    
    filters = {'search': search_query, 'role': role_filter, 'location': loc_filter}
    jobs = database.get_all_jobs(filters)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Job Title', 'Company', 'Location', 'Salary', 'Avg Salary (LPA)',
        'Experience', 'Min Exp', 'Max Exp', 'Skills', 'Job Type', 'Posted Date', 'Apply Link', 'Scraped At'
    ])
    
    for j in jobs:
        writer.writerow([
            j['id'], j['job_title'], j['company'], j['location'], j['salary'],
            j['avg_salary'], j['experience'], j['min_exp'], j['max_exp'],
            j['skills'], j['job_type'], j['posted_date'], j['job_link'], j['scraped_at']
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=naukri_it_jobs.csv"}
    )

@app.route('/api/export/excel')
def export_excel():
    """Exports all or filtered jobs to an Excel (.xlsx) spreadsheet."""
    jobs = database.get_all_jobs()
    if not jobs:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(jobs)
        # Rename columns nicely
        col_rename = {
            'id': 'Job ID',
            'job_title': 'Job Title',
            'company': 'Company',
            'location': 'Location',
            'salary': 'Salary Range',
            'avg_salary': 'Average Salary (LPA)',
            'experience': 'Experience Required',
            'skills': 'Key Skills',
            'job_type': 'Work Mode',
            'posted_date': 'Posted Date',
            'job_link': 'Apply Link',
            'scraped_at': 'Scraped Timestamp'
        }
        cols_to_keep = [k for k in col_rename.keys() if k in df.columns]
        df = df[cols_to_keep].rename(columns=col_rename)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='IT Job Vacancies')
        
    output.seek(0)
    return send_file(
        output,
        download_name="naukri_it_job_market_analysis.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
