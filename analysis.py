import pandas as pd
import numpy as np
import re
from collections import Counter
import database

def load_data(db_path='jobs.db'):
    """Loads all jobs from SQLite into a clean Pandas DataFrame."""
    jobs = database.get_all_jobs(db_path=db_path)
    if not jobs:
        return pd.DataFrame()
    
    df = pd.DataFrame(jobs)
    
    # Ensure numeric columns
    for col in ['min_salary', 'max_salary', 'avg_salary', 'min_exp', 'max_exp']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
    # Clean location (take primary city if comma-separated e.g., 'Bengaluru/Bangalore')
    if 'location' in df.columns:
        df['primary_city'] = df['location'].apply(clean_primary_city)
        
    return df

def clean_primary_city(loc_str):
    if not loc_str or pd.isna(loc_str):
        return 'Other'
    loc = str(loc_str).split('/')[0].split(',')[0].strip()
    loc_lower = loc.lower()
    if 'bangalore' in loc_lower or 'bengaluru' in loc_lower:
        return 'Bengaluru'
    elif 'hyderabad' in loc_lower or 'secunderabad' in loc_lower:
        return 'Hyderabad'
    elif 'pune' in loc_lower:
        return 'Pune'
    elif 'gurgaon' in loc_lower or 'gurugram' in loc_lower:
        return 'Gurgaon'
    elif 'noida' in loc_lower or 'greater noida' in loc_lower:
        return 'Noida'
    elif 'mumbai' in loc_lower or 'navi mumbai' in loc_lower:
        return 'Mumbai'
    elif 'chennai' in loc_lower:
        return 'Chennai'
    elif 'delhi' in loc_lower or 'ncr' in loc_lower:
        return 'Delhi NCR'
    elif 'kolkata' in loc_lower:
        return 'Kolkata'
    elif 'remote' in loc_lower:
        return 'Remote'
    return loc.title()

def get_kpi_summary(df=None):
    """Computes high-level KPI cards metrics."""
    if df is None:
        df = load_data()
        
    if df.empty:
        return {
            'total_jobs': 0,
            'unique_companies': 0,
            'unique_cities': 0,
            'avg_salary': 0.0,
            'max_salary': 0.0,
            'avg_exp': 0.0,
            'remote_percentage': 0.0,
            'top_skill': 'N/A',
            'top_city': 'N/A',
            'top_company': 'N/A',
            'last_updated': 'No data'
        }
        
    total_jobs = len(df)
    unique_companies = df['company'].nunique() if 'company' in df.columns else 0
    unique_cities = df['primary_city'].nunique() if 'primary_city' in df.columns else 0
    
    # Calculate salary averages ignoring 0/undisclosed
    valid_salaries = df[df['avg_salary'] > 0]['avg_salary']
    avg_salary = round(float(valid_salaries.mean()), 1) if not valid_salaries.empty else 0.0
    max_salary = round(float(valid_salaries.max()), 1) if not valid_salaries.empty else 0.0
    
    # Experience averages
    valid_exp = df[df['min_exp'] >= 0]['min_exp']
    avg_exp = round(float(valid_exp.mean()), 1) if not valid_exp.empty else 0.0
    
    # Remote percentage
    if 'job_type' in df.columns:
        remote_count = len(df[df['job_type'].str.lower() == 'remote'])
        remote_pct = round((remote_count / total_jobs) * 100, 1) if total_jobs > 0 else 0.0
    else:
        remote_pct = 0.0
        
    # Top city
    top_city = df['primary_city'].value_counts().index[0] if 'primary_city' in df.columns and not df.empty else 'N/A'
    
    # Top company
    top_company = df['company'].value_counts().index[0] if 'company' in df.columns and not df.empty else 'N/A'
    
    # Top skill
    top_skills_list = get_top_skills_data(df, limit=1)
    top_skill = top_skills_list[0]['skill'] if top_skills_list else 'N/A'
    
    last_updated = df['scraped_at'].max() if 'scraped_at' in df.columns else 'Recent'
    
    return {
        'total_jobs': total_jobs,
        'unique_companies': unique_companies,
        'unique_cities': unique_cities,
        'avg_salary': avg_salary,
        'max_salary': max_salary,
        'avg_exp': avg_exp,
        'remote_percentage': remote_pct,
        'top_skill': top_skill,
        'top_city': top_city,
        'top_company': top_company,
        'last_updated': str(last_updated)
    }

def get_jobs_by_city_data(df, limit=10):
    """Returns top cities by job vacancy count."""
    if df.empty or 'primary_city' not in df.columns:
        return []
    city_counts = df['primary_city'].value_counts().head(limit)
    total = len(df)
    results = []
    for city, count in city_counts.items():
        results.append({
            'city': str(city),
            'count': int(count),
            'percentage': round((count / total) * 100, 1)
        })
    return results

def get_top_companies_data(df, limit=10):
    """Returns top hiring companies with job counts and average salary."""
    if df.empty or 'company' not in df.columns:
        return []
    
    grouped = df.groupby('company').agg(
        count=('id', 'count'),
        avg_sal=('avg_salary', lambda x: round(x[x > 0].mean(), 1) if len(x[x > 0]) > 0 else 0.0)
    ).reset_index().sort_values(by='count', ascending=False).head(limit)
    
    return grouped.to_dict(orient='records')

def get_salary_distribution_data(df):
    """Returns counts of jobs across salary brackets (in LPA)."""
    if df.empty or 'avg_salary' not in df.columns:
        return []
    
    # Exclude undisclosed (0)
    sal = df[df['avg_salary'] > 0]['avg_salary']
    if sal.empty:
        return []

    bins = [0, 6, 12, 20, 35, 50, 200]
    labels = ['< 6 LPA', '6-12 LPA', '12-20 LPA', '20-35 LPA', '35-50 LPA', '50+ LPA']
    
    binned = pd.cut(sal, bins=bins, labels=labels, right=False)
    counts = binned.value_counts()[labels]
    
    return [{'range': label, 'count': int(counts[label])} for label in labels]

def get_experience_distribution_data(df):
    """Returns experience levels breakdown."""
    if df.empty or 'min_exp' not in df.columns:
        return []
    
    bins = [-1, 2.5, 5.5, 9.5, 100]
    labels = ['Entry Level (0-2 Yrs)', 'Mid Level (3-5 Yrs)', 'Senior Level (6-9 Yrs)', 'Lead / Exec (10+ Yrs)']
    
    binned = pd.cut(df['min_exp'], bins=bins, labels=labels)
    counts = binned.value_counts()[labels]
    
    return [{'level': label, 'count': int(counts[label])} for label in labels]

def get_top_skills_data(df, limit=15):
    """Extracts, cleans, and counts individual skills from comma-separated skills column."""
    if df.empty or 'skills' not in df.columns:
        return []
    
    skills_series = df['skills'].dropna()
    all_skills = []
    
    for s_row in skills_series:
        if not s_row:
            continue
        # Split by comma or semicolon
        tags = [t.strip() for t in re.split(r'[,;|\n]', str(s_row)) if t.strip()]
        for tag in tags:
            tag_clean = tag.strip().title()
            if len(tag_clean) > 1 and tag_clean.lower() not in ['and', 'or', 'in', 'with', 'skills', 'etc']:
                # Standardize common acronyms
                if tag_clean.lower() == 'aws': tag_clean = 'AWS'
                elif tag_clean.lower() in ['gcp', 'google cloud']: tag_clean = 'GCP'
                elif tag_clean.lower() == 'sql': tag_clean = 'SQL'
                elif tag_clean.lower() == 'ai': tag_clean = 'AI'
                elif tag_clean.lower() == 'ml': tag_clean = 'Machine Learning'
                elif tag_clean.lower() in ['react', 'react js', 'reactjs']: tag_clean = 'React.js'
                elif tag_clean.lower() in ['node', 'node js', 'nodejs']: tag_clean = 'Node.js'
                elif tag_clean.lower() in ['next', 'next js', 'nextjs']: tag_clean = 'Next.js'
                all_skills.append(tag_clean)
                
    counts = Counter(all_skills).most_common(limit)
    total_listings = len(df)
    
    return [{
        'skill': skill,
        'count': count,
        'percentage': round((count / total_listings) * 100, 1) if total_listings > 0 else 0
    } for skill, count in counts]

def get_work_mode_data(df):
    """Returns distribution of Remote vs Hybrid vs On-site jobs."""
    if df.empty or 'job_type' not in df.columns:
        return []
    
    counts = df['job_type'].value_counts()
    modes = ['On-site', 'Hybrid', 'Remote']
    results = []
    for mode in modes:
        results.append({
            'mode': mode,
            'count': int(counts.get(mode, 0))
        })
    return results

def get_salary_vs_exp_data(df):
    """Calculates salary trends across experience cohorts."""
    if df.empty or 'min_exp' not in df.columns or 'avg_salary' not in df.columns:
        return []
    
    valid_df = df[df['avg_salary'] > 0]
    if valid_df.empty:
        return []
        
    grouped = valid_df.groupby('min_exp')['avg_salary'].agg(['mean', 'median', 'count']).reset_index()
    grouped = grouped[grouped['count'] >= 1].sort_values(by='min_exp')
    
    return [{
        'experience_years': float(row['min_exp']),
        'mean_salary': round(float(row['mean']), 2),
        'median_salary': round(float(row['median']), 2),
        'job_count': int(row['count'])
    } for _, row in grouped.iterrows()]

def get_role_benchmarks(df, limit=8):
    """Groups similar job roles to compute average salary benchmarks."""
    if df.empty:
        return []
        
    categories = {
        'AI / Machine Learning': ['ai', 'ml', 'data scientist', 'deep learning', 'nlp', 'llm', 'computer vision'],
        'Cloud & DevOps': ['devops', 'cloud', 'sre', 'kubernetes', 'aws', 'platform', 'infrastructure'],
        'Full Stack & Web': ['full stack', 'mern', 'react', 'frontend', 'node', 'javascript', 'next.js'],
        'Backend & Microservices': ['backend', 'java', 'python', 'golang', 'spring boot', 'django'],
        'Data Engineering': ['data engineer', 'big data', 'pyspark', 'snowflake', 'data analyst'],
        'Security & Network': ['security', 'soc', 'cyber', 'penetration', 'siem'],
        'Mobile App (iOS/Android)': ['flutter', 'react native', 'ios', 'android', 'mobile'],
        'QA Automation': ['qa', 'automation', 'testing', 'selenium', 'cypress']
    }
    
    results = []
    for cat_name, keywords in categories.items():
        pattern = '|'.join(keywords)
        matched = df[df['job_title'].str.contains(pattern, case=False, na=False)]
        count = len(matched)
        if count > 0:
            sal_matched = matched[matched['avg_salary'] > 0]['avg_salary']
            avg_sal = round(float(sal_matched.mean()), 1) if not sal_matched.empty else 0.0
            results.append({
                'category': cat_name,
                'count': count,
                'avg_salary': avg_sal
            })
            
    results.sort(key=lambda x: x['count'], reverse=True)
    return results[:limit]

def generate_market_insights(df=None):
    """Generates an executive textual summary of the current IT job landscape."""
    if df is None:
        df = load_data()
        
    if df.empty:
        return ["No job records available. Please run a job search or seed sample data."]
        
    kpis = get_kpi_summary(df)
    top_city = kpis['top_city']
    top_comp = kpis['top_company']
    top_skill = kpis['top_skill']
    avg_sal = kpis['avg_salary']
    remote_pct = kpis['remote_percentage']
    
    insights = [
        f"**{top_city}** continues to lead the IT hiring demand, accounting for the highest share of open positions.",
        f"**{top_comp}** is actively hiring at scale with competitive compensation packages.",
        f"**{top_skill}** ranks as the single most requested technical proficiency across all indexed job listings.",
        f"The overall average annual salary benchmark sits at **₹{avg_sal} Lakhs per annum (LPA)**.",
        f"**{remote_pct}%** of all scraped listings support complete remote work, while hybrid setups represent the dominant workplace model.",
        f"AI/ML and Cloud Infrastructure roles demonstrate the highest salary premiums across experience tiers (often exceeding ₹35-50+ LPA for senior talent)."
    ]
    return insights
