import json
import plotly
import plotly.graph_objects as go
import plotly.express as px
import analysis

# Theme Colors (LinkedIn / Tech Dashboard Style)
PRIMARY_COLOR = '#0a66c2'
SECONDARY_COLOR = '#004182'
ACCENT_COLOR = '#0284c7'
SUCCESS_COLOR = '#10b981'
PURPLE_COLOR = '#8b5cf6'
AMBER_COLOR = '#f59e0b'
CORAL_COLOR = '#f43f5e'

def get_base_layout(custom_margin=None):
    layout = {
        'font': {'family': 'Inter, system-ui, sans-serif', 'size': 12, 'color': '#94a3b8'},
        'margin': custom_margin or {'l': 40, 'r': 20, 't': 45, 'b': 40},
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'hovermode': 'closest',
        'autosize': True
    }
    return layout

def generate_all_dashboard_charts(df=None):
    """Generates all Plotly chart configurations formatted as JSON strings for frontend rendering."""
    if df is None:
        df = analysis.load_data()
        
    charts = {
        'jobs_by_city': create_jobs_by_city_chart(df),
        'top_companies': create_top_companies_chart(df),
        'salary_distribution': create_salary_distribution_chart(df),
        'experience_distribution': create_experience_distribution_chart(df),
        'top_skills': create_top_skills_chart(df),
        'work_mode': create_work_mode_chart(df),
        'salary_vs_exp': create_salary_vs_exp_chart(df),
        'role_benchmarks': create_role_benchmarks_chart(df)
    }
    return charts

def create_jobs_by_city_chart(df):
    data = analysis.get_jobs_by_city_data(df, limit=8)
    if not data:
        return empty_chart_json("No City Data Available")
        
    cities = [d['city'] for d in data]
    counts = [d['count'] for d in data]
    percentages = [f"{d['percentage']}%" for d in data]
    
    fig = go.Figure(go.Bar(
        x=cities,
        y=counts,
        text=percentages,
        textposition='outside',
        marker=dict(
            color=counts,
            colorscale=[[0, '#38bdf8'], [1, '#0062cc']],
            showscale=False,
            line=dict(color='rgba(255,255,255,0.25)', width=1)
        ),
        hovertemplate="<b>%{x}</b><br>Vacancies: %{y}<br>Share: %{text}<extra></extra>"
    ))
    
    layout = get_base_layout()
    layout.update(dict(
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)', title="Job Count"),
        title=dict(text="IT Job Vacancies by Top Cities", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def create_top_companies_chart(df):
    data = analysis.get_top_companies_data(df, limit=8)
    if not data:
        return empty_chart_json("No Company Data Available")
        
    data = list(reversed(data))
    companies = [d['company'] for d in data]
    counts = [d['count'] for d in data]
    avg_sals = [f"Avg ₹{d['avg_sal']} LPA" if d['avg_sal'] > 0 else "Salary N/A" for d in data]
    
    fig = go.Figure(go.Bar(
        y=companies,
        x=counts,
        orientation='h',
        text=avg_sals,
        textposition='auto',
        marker=dict(
            color='#0284c7',
            line=dict(color='#38bdf8', width=1)
        ),
        hovertemplate="<b>%{y}</b><br>Openings: %{x}<br>%{text}<extra></extra>"
    ))
    
    layout = get_base_layout(custom_margin={'l': 140, 'r': 20, 't': 45, 'b': 30})
    layout.update(dict(
        xaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)', title="Active Openings"),
        yaxis=dict(showgrid=False, title=""),
        title=dict(text="Top Hiring Companies", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def create_salary_distribution_chart(df):
    data = analysis.get_salary_distribution_data(df)
    if not data:
        return empty_chart_json("No Salary Records Available")
        
    ranges = [d['range'] for d in data]
    counts = [d['count'] for d in data]
    
    colors = ['#38bdf8', '#0284c7', '#2563eb', '#1d4ed8', '#1e40af', '#172554']
    
    fig = go.Figure(go.Bar(
        x=ranges,
        y=counts,
        text=counts,
        textposition='outside',
        marker=dict(color=colors[:len(ranges)], line=dict(color='rgba(255,255,255,0.2)', width=1)),
        hovertemplate="<b>Bracket: %{x}</b><br>Jobs: %{y}<extra></extra>"
    ))
    
    layout = get_base_layout()
    layout.update(dict(
        xaxis=dict(showgrid=False, title="Salary Bracket (Lakhs PA)"),
        yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)', title="Count"),
        title=dict(text="Salary Distribution (in LPA)", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def create_experience_distribution_chart(df):
    data = analysis.get_experience_distribution_data(df)
    if not data:
        return empty_chart_json("No Experience Data Available")
        
    labels = [d['level'] for d in data]
    values = [d['count'] for d in data]
    
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=['#38bdf8', '#0284c7', '#6366f1', '#a855f7']),
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
    ))
    
    layout = get_base_layout()
    layout.update(dict(
        showlegend=False,
        title=dict(text="Experience Requirement Split", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def create_top_skills_chart(df):
    data = analysis.get_top_skills_data(df, limit=10)
    if not data:
        return empty_chart_json("No Skills Data Available")
        
    data = list(reversed(data))
    skills = [d['skill'] for d in data]
    counts = [d['count'] for d in data]
    percentages = [f"{d['percentage']}% of jobs" for d in data]
    
    fig = go.Figure(go.Bar(
        y=skills,
        x=counts,
        orientation='h',
        text=percentages,
        textposition='outside',
        marker=dict(
            color='#0284c7',
            line=dict(color='rgba(255,255,255,0.25)', width=1)
        ),
        hovertemplate="<b>%{y}</b><br>Demand: %{x} listings (%{text})<extra></extra>"
    ))
    
    layout = get_base_layout(custom_margin={'l': 110, 'r': 70, 't': 45, 'b': 30})
    layout.update(dict(
        xaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)', title="Mentions"),
        yaxis=dict(showgrid=False, title=""),
        title=dict(text="Top In-Demand Technical Skills", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def create_work_mode_chart(df):
    data = analysis.get_work_mode_data(df)
    if not data:
        return empty_chart_json("No Work Mode Data Available")
        
    labels = [d['mode'] for d in data]
    values = [d['count'] for d in data]
    
    colors_map = {
        'On-site': '#0284c7',
        'Hybrid': '#38bdf8',
        'Remote': '#10b981'
    }
    colors = [colors_map.get(lbl, '#64748b') for lbl in labels]
    
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors),
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>Openings: %{value}<br>Ratio: %{percent}<extra></extra>"
    ))
    
    layout = get_base_layout()
    layout.update(dict(
        showlegend=False,
        title=dict(text="Remote vs. Hybrid vs. On-site", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def create_salary_vs_exp_chart(df):
    data = analysis.get_salary_vs_exp_data(df)
    if not data:
        return empty_chart_json("No Salary vs Experience Data Available")
        
    exp_years = [d['experience_years'] for d in data]
    mean_sal = [d['mean_salary'] for d in data]
    median_sal = [d['median_salary'] for d in data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=exp_years,
        y=mean_sal,
        mode='lines+markers',
        name='Average Salary',
        line=dict(color='#38bdf8', width=3),
        marker=dict(size=8, color='#0284c7'),
        hovertemplate="Exp: %{x} Yrs<br>Avg Salary: ₹%{y} LPA<extra></extra>"
    ))
    
    fig.add_trace(go.Scatter(
        x=exp_years,
        y=median_sal,
        mode='lines+markers',
        name='Median Salary',
        line=dict(color='#34d399', width=2, dash='dash'),
        marker=dict(size=6, color='#10b981'),
        hovertemplate="Exp: %{x} Yrs<br>Median Salary: ₹%{y} LPA<extra></extra>"
    ))
    
    layout = get_base_layout()
    layout.update(dict(
        xaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)', title="Min Experience (Years)"),
        yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)', title="Salary (LPA)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title=dict(text="Salary Progression by Experience Level", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def create_role_benchmarks_chart(df):
    data = analysis.get_role_benchmarks(df, limit=7)
    if not data:
        return empty_chart_json("No Role Benchmark Data")
        
    categories = [d['category'] for d in data]
    avg_sals = [d['avg_salary'] for d in data]
    counts = [d['count'] for d in data]
    
    fig = go.Figure(go.Bar(
        x=categories,
        y=avg_sals,
        text=[f"₹{s} LPA ({c} jobs)" for s, c in zip(avg_sals, counts)],
        textposition='outside',
        marker=dict(
            color='#c084fc',
            line=dict(color='#a855f7', width=1)
        ),
        hovertemplate="<b>%{x}</b><br>Avg Compensation: ₹%{y} LPA<extra></extra>"
    ))
    
    layout = get_base_layout()
    layout.update(dict(
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)', title="Avg Salary (LPA)"),
        title=dict(text="Role-wise Average Salary Benchmark", font=dict(size=14))
    ))
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

def empty_chart_json(title_text):
    fig = go.Figure()
    fig.add_annotation(
        text=title_text,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="#94a3b8")
    )
    layout = get_base_layout()
    fig.update_layout(**layout)
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
