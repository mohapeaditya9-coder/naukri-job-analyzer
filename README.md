# Naukri IT Job Vacancy & Salary Trend Analyzer

A modern full-stack web application designed to scrape IT job listings from Naukri.com, store structured data in SQLite, perform data analysis with Pandas & NumPy, and visualize insights through an interactive LinkedIn-Analytics-style dashboard with Plotly.js.

![Theme](https://img.shields.io/badge/Theme-LinkedIn%20Analytics-0a66c2)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-indigo)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌟 Key Features

- **Automated Web Scraper**: Headless Selenium + BeautifulSoup engine extracting job titles, companies, locations, parsed salaries (in LPA), experience brackets, tech stacks, and job links.
- **LinkedIn Analytics UI Theme**: Professional Blue, White, and Dark Gray palette with animated KPI counters, glassmorphic metric cards, and responsive Bootstrap 5 styling.
- **Complete Dark Mode**: Dark/Light mode switcher with `localStorage` persistence and dynamic Plotly chart re-styling.
- **7 Core Web Pages**:
  1. **Home Page (`/`)**: Hero section, live stats preview, project overview, and feature showcase.
  2. **Job Search Page (`/search`)**: Customizable search inputs with role presets and live scraping progress modal.
  3. **Live Scraping Progress Console**: Real-time progress bar, status tracker, and scrolling log terminal.
  4. **Analytics Dashboard (`/dashboard`)**: KPI metric cards and 7+ interactive Plotly.js charts (City Distribution, Top Companies, Salary Histogram, Experience Donut, Top Skills, Remote vs. On-site, and Salary vs. Experience progression).
  5. **Job Listings Directory (`/jobs`)**: Filterable, searchable, paginated table with sorting, direct Apply links, and CSV / Excel / PDF export options.
  6. **Deep-Dive Analytics (`/analytics`)**: Automated market observations, highest hiring tech hubs, top hiring companies, and skill rankings.
  7. **Database Administration (`/database`)**: Full SQLite CRUD management (Add Job Modal, Inline Edit Modal, Single Delete, Wipe All, and 1-Click Sample Dataset Seeder).
- **Export Capabilities**: Download filtered listings in **CSV**, formatted **Excel (.xlsx)**, or print-ready **PDF report**.

---

## 🏗️ Project Architecture

```
NaukriAnalyzer/
│
├── app.py                 # Flask server, routes, REST APIs, scraping thread manager
├── scraper.py             # Selenium & BeautifulSoup scraper + resilient fallback generator
├── database.py            # SQLite schema, CRUD operations, indexing, and seed utility
├── analysis.py            # Pandas & NumPy analysis, data cleaning, and statistical metrics
├── visualization.py       # Plotly chart figure generator (JSON serialized) & color schemes
├── test_app.py            # Automated unit and integration test suite
├── requirements.txt       # Project dependencies
├── jobs.db                # SQLite database file
├── static/
│   ├── css/
│   │   └── style.css      # Professional LinkedIn-style palette + full Dark Mode support
│   ├── js/
│   │   ├── main.js        # Core UI logic, dark mode, chart re-rendering, stats counter
│   │   ├── scraper_ui.js  # Live scraping progress polling and animations
│   │   └── datatable.js   # Jobs table filtering, pagination, search, and exports
│   └── images/
│       └── logo.svg       # Brand icon & graphics
└── templates/
    ├── base.html          # Responsive base template with Navbar, Theme Toggle, Footer
    ├── index.html         # Modern Hero Home Page + Quick Preview & Feature Cards
    ├── search.html        # Job Search & Scrape Configuration Page with Live Progress Modal
    ├── dashboard.html     # LinkedIn Analytics-style Dashboard with KPI Cards & Plotly Charts
    ├── jobs.html          # Searchable, filterable, sortable Jobs table with Export options
    ├── analytics.html     # In-depth IT Market Insights, Skill Demands, and Salary Trends
    └── database.html      # Database Management table with CRUD (Edit/Delete/Add/Clear/Seed)
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database & Run Tests
```bash
python test_app.py
```

### 3. Start the Flask Web Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 📊 Database Schema (`jobs` table)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY` | Auto-increment unique job identifier |
| `job_title` | `TEXT` | Title of the position (e.g., SDE-2, Data Scientist) |
| `company` | `TEXT` | Hiring company name |
| `location` | `TEXT` | Primary location / tech hub |
| `salary` | `TEXT` | Raw salary text (e.g. "18-32 Lacs PA") |
| `min_salary` | `REAL` | Normalized minimum salary in LPA |
| `max_salary` | `REAL` | Normalized maximum salary in LPA |
| `avg_salary` | `REAL` | Normalized average salary in LPA |
| `experience` | `TEXT` | Experience requirement (e.g. "3-6 Yrs") |
| `min_exp` | `REAL` | Minimum required experience in years |
| `max_exp` | `REAL` | Maximum required experience in years |
| `skills` | `TEXT` | Comma-separated technical skills |
| `posted_date` | `TEXT` | Time or date of posting (e.g., "1 day ago") |
| `job_link` | `TEXT` | Direct apply / posting URL |
| `job_type` | `TEXT` | Work mode: `On-site`, `Hybrid`, `Remote` |
| `scraped_at` | `TIMESTAMP` | Timestamp when record was saved |
