from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import dcc, html, register_page

register_page(__name__, path='/daily-work', name='Daily Work')

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'complaints.csv'
df = pd.read_csv(DATA_PATH)

def build_tasks(frame):
    tasks = []
    for _, row in frame.iterrows():
        priority = 'High' if row['severity'] in ['Critical', 'High'] else 'Medium'
        owner = 'AQC Engineer' if row['status'] != 'Closed' else 'QA Lead'
        tasks.append({
            'Customer': row['customer'],
            'Issue': row['issue'],
            'Severity': row['severity'],
            'Priority': priority,
            'Owner': owner,
            'Status': row['status'],
            'Due': f"{row['days_open'] + 2} days",
        })
    return tasks

filtered = df[df['status'] != 'Closed'].copy()
tasks = build_tasks(filtered)

summary = px.bar(
    filtered.groupby('severity').size().reset_index(name='count'),
    x='severity',
    y='count',
    color='severity',
    title='Open Workload by Severity',
    color_discrete_map={'Critical': '#d62728', 'High': '#ff7f0e', 'Medium': '#2ca02c', 'Low': '#1f77b4'},
)

layout = html.Div(
    [
        html.H3('Daily Work Automation', style={'marginBottom': '14px'}),
        html.Div(
            [
                html.Div([
                    html.Div('Priority tasks', style={'fontSize': '14px', 'color': '#5c6f8b'}),
                    html.Div(str(len(tasks)), style={'fontSize': '32px', 'fontWeight': '700'})
                ], style={'flex': '1', 'backgroundColor': '#fff', 'padding': '18px 20px', 'borderRadius': '12px'}),
                html.Div([
                    html.Div('Critical backlog', style={'fontSize': '14px', 'color': '#5c6f8b'}),
                    html.Div(str(int((filtered['severity'] == 'Critical').sum())), style={'fontSize': '32px', 'fontWeight': '700'})
                ], style={'flex': '1', 'backgroundColor': '#fff', 'padding': '18px 20px', 'borderRadius': '12px'}),
                html.Div([
                    html.Div('Automated follow-up', style={'fontSize': '14px', 'color': '#5c6f8b'}),
                    html.Div('8 actions', style={'fontSize': '32px', 'fontWeight': '700'})
                ], style={'flex': '1', 'backgroundColor': '#fff', 'padding': '18px 20px', 'borderRadius': '12px'}),
            ],
            style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap', 'marginBottom': '20px'}
        ),
        html.Div(
            [
                dcc.Graph(figure=summary.update_layout(template='plotly_white'), style={'height': '360px'}),
            ],
            style={'marginBottom': '20px'}
        ),
        html.Div(
            [
                html.H4('Recommended actions', style={'marginBottom': '12px'}),
                html.Table(
                    [
                        html.Thead(
                            html.Tr([
                                html.Th('Customer', style={'padding': '10px', 'backgroundColor': '#eaf1ff'}),
                                html.Th('Issue', style={'padding': '10px', 'backgroundColor': '#eaf1ff'}),
                                html.Th('Priority', style={'padding': '10px', 'backgroundColor': '#eaf1ff'}),
                                html.Th('Owner', style={'padding': '10px', 'backgroundColor': '#eaf1ff'}),
                                html.Th('Due', style={'padding': '10px', 'backgroundColor': '#eaf1ff'}),
                            ])
                        ),
                        html.Tbody([
                            html.Tr([
                                html.Td(task['Customer'], style={'padding': '10px'}),
                                html.Td(task['Issue'], style={'padding': '10px'}),
                                html.Td(task['Priority'], style={'padding': '10px'}),
                                html.Td(task['Owner'], style={'padding': '10px'}),
                                html.Td(task['Due'], style={'padding': '10px'}),
                            ]) for task in tasks
                        ]),
                    ],
                    style={'width': '100%', 'borderCollapse': 'collapse', 'backgroundColor': '#fff'}
                ),
            ],
            style={'backgroundColor': '#fff', 'padding': '18px', 'borderRadius': '12px'}
        ),
    ]
)
