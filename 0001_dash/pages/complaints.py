from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html, register_page, dash_table

register_page(__name__, path='/complaints', name='Complaints')

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'complaints.csv'
df = pd.read_csv(DATA_PATH)
df['date'] = pd.to_datetime(df['date'])

layout = html.Div(
    [
        html.H3('Complaint Register', style={'marginBottom': '16px'}),
        html.Div(
            [
                html.Div(
                    [
                        html.Label('Region'),
                        dcc.Dropdown(
                            options=[{'label': r, 'value': r} for r in sorted(df['region'].unique())],
                            value='Europe',
                            id='region-filter',
                            clearable=False,
                        ),
                    ],
                    style={'flex': '1'}
                ),
                html.Div(
                    [
                        html.Label('Severity'),
                        dcc.Dropdown(
                            options=[{'label': s, 'value': s} for s in ['Critical', 'High', 'Medium', 'Low']],
                            value='High',
                            id='severity-filter',
                            clearable=False,
                        ),
                    ],
                    style={'flex': '1'}
                ),
            ],
            style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}
        ),
        html.Div(
            [
                dcc.Graph(id='complaint-type-chart', style={'height': '320px'}),
                dash_table.DataTable(
                    id='complaint-table',
                    columns=[{'name': c, 'id': c} for c in ['date', 'customer', 'region', 'complaint_type', 'severity', 'status', 'days_open']],
                    style_table={'overflowX': 'auto'},
                    page_size=10,
                    style_cell={'padding': '8px 10px', 'textAlign': 'left'},
                ),
            ],
            style={'display': 'grid', 'gridTemplateColumns': '1.1fr 1.6fr', 'gap': '20px'}
        ),
    ]
)


@callback(
    Output('complaint-type-chart', 'figure'),
    Output('complaint-table', 'data'),
    Input('region-filter', 'value'),
    Input('severity-filter', 'value'),
)
def update_report(region, severity):
    filtered = df[(df['region'] == region) & (df['severity'] == severity)].copy()

    complaint_counts = filtered['complaint_type'].value_counts().rename_axis('Complaint Type').reset_index(name='Count')
    chart = px.bar(
        complaint_counts,
        x='Complaint Type',
        y='Count',
        title=f'{severity} complaints in {region}',
        color='Complaint Type',
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    chart.update_layout(template='plotly_white')

    table_data = filtered[['date', 'customer', 'region', 'complaint_type', 'severity', 'status', 'days_open']].to_dict('records')
    for row in table_data:
        row['date'] = row['date'].strftime('%Y-%m-%d')

    return chart, table_data
