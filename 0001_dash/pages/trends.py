from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import dcc, html, register_page

register_page(__name__, path='/trends', name='Trends')

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'complaints.csv'
df = pd.read_csv(DATA_PATH)
df['date'] = pd.to_datetime(df['date'])

monthly = df.groupby(df['date'].dt.to_period('M')).agg(total=('customer', 'count'), avg_days=('days_open', 'mean')).reset_index()
monthly['Month'] = monthly['date'].astype(str)
monthly = monthly.drop(columns=['date'])

trend_chart = px.line(monthly, x='Month', y='total', markers=True, title='Complaint Volume Trend')
pareto_data = df['complaint_type'].value_counts().rename_axis('Complaint Type').reset_index(name='Count').head(8)
pareto = px.bar(
    pareto_data,
    x='Complaint Type',
    y='Count',
    title='Top Complaint Categories',
    color='Complaint Type',
)

layout = html.Div(
    [
        html.H3('Quality Trends', style={'marginBottom': '16px'}),
        html.Div(
            [
                dcc.Graph(figure=trend_chart.update_layout(template='plotly_white'), style={'height': '360px'}),
                dcc.Graph(figure=pareto.update_layout(template='plotly_white'), style={'height': '360px'}),
            ],
            style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}
        ),
    ]
)
