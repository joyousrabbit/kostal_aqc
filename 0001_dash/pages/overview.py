from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import dcc, html, register_page

register_page(__name__, path='/', name='Overview')

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'complaints.csv'
df = pd.read_csv(DATA_PATH)
df['date'] = pd.to_datetime(df['date'])

open_cases = int((df['status'] != 'Closed').sum())
critical_cases = int((df['severity'] == 'Critical').sum())
avg_days_open = round(df['days_open'].mean(), 1)
monthly_total = df.groupby(df['date'].dt.to_period('M')).size().reset_index()
monthly_total.columns = ['Month', 'Complaints']
monthly_total['Month'] = monthly_total['Month'].astype(str)

severity_counts = df['severity'].value_counts().rename_axis('Severity').reset_index(name='Count')
severity_chart = px.bar(
    severity_counts,
    x='Severity',
    y='Count',
    color='Severity',
    title='Complaints by Severity',
    color_discrete_sequence=['#ff7f0e', '#ffbb78', '#2ca02c', '#1f77b4'],
)

region_counts = df['region'].value_counts().rename_axis('Region').reset_index(name='Count')
region_chart = px.pie(
    region_counts,
    names='Region',
    values='Count',
    title='Complaints by Region',
    color_discrete_sequence=['#4e79a7', '#f28e2b', '#e15759', '#76b7b2'],
)

layout = html.Div(
    [
        html.H3('Operations Overview', style={'marginBottom': '16px'}),
        html.Div(
            [
                html.Div([
                    html.Div('Open cases', style={'fontSize': '14px', 'color': '#5c6f8b'}),
                    html.Div(str(open_cases), style={'fontSize': '34px', 'fontWeight': '700', 'marginTop': '4px'})
                ], style={'flex': '1', 'backgroundColor': '#ffffff', 'padding': '18px 20px', 'borderRadius': '12px', 'boxShadow': '0 1px 4px rgba(0,0,0,0.08)'}),
                html.Div([
                    html.Div('Critical cases', style={'fontSize': '14px', 'color': '#5c6f8b'}),
                    html.Div(str(critical_cases), style={'fontSize': '34px', 'fontWeight': '700', 'marginTop': '4px'})
                ], style={'flex': '1', 'backgroundColor': '#ffffff', 'padding': '18px 20px', 'borderRadius': '12px', 'boxShadow': '0 1px 4px rgba(0,0,0,0.08)'}),
                html.Div([
                    html.Div('Avg. days open', style={'fontSize': '14px', 'color': '#5c6f8b'}),
                    html.Div(f'{avg_days_open} d', style={'fontSize': '34px', 'fontWeight': '700', 'marginTop': '4px'})
                ], style={'flex': '1', 'backgroundColor': '#ffffff', 'padding': '18px 20px', 'borderRadius': '12px', 'boxShadow': '0 1px 4px rgba(0,0,0,0.08)'}),
            ],
            style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap', 'marginBottom': '24px'}
        ),
        html.Div(
            [
                dcc.Graph(figure=px.line(monthly_total, x='Month', y='Complaints', markers=True, title='Monthly Complaint Trend').update_layout(template='plotly_white'), style={'height': '360px'}),
                dcc.Graph(figure=severity_chart.update_layout(template='plotly_white'), style={'height': '360px'}),
            ],
            style={'display': 'grid', 'gridTemplateColumns': '1.5fr 1fr', 'gap': '20px'}
        ),
        html.Div(
            [
                dcc.Graph(figure=region_chart.update_layout(template='plotly_white'), style={'height': '320px'}),
            ],
            style={'marginTop': '20px'}
        ),
    ]
)
