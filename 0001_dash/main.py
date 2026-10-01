from dash import Dash, html, dcc
import dash

app = Dash(
    __name__,
    use_pages=True,
    title='Kostal AQC Client Complaint Dashboard',
    suppress_callback_exceptions=True,
)
server = app.server

nav_items = [
    ('Overview', '/'),
    ('Complaints', '/complaints'),
    ('Daily Work', '/daily-work'),
    ('Trends', '/trends'),
]

app.layout = html.Div(
    [
        html.Div(
            [
                html.H2('Kostal AQC Operations', style={'margin': '0', 'color': '#0b1f3a'}),
                html.Div(
                    [
                        dcc.Link(label, href=path, style={'marginRight': '18px', 'color': '#0b1f3a', 'fontWeight': '600', 'textDecoration': 'none'})
                        for label, path in nav_items
                    ],
                    style={'display': 'flex', 'gap': '18px', 'alignItems': 'center', 'flexWrap': 'wrap'}
                ),
            ],
            style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'padding': '18px 28px',
                'backgroundColor': '#dfeaf9',
                'borderBottom': '1px solid #c8d9ef',
                'flexWrap': 'wrap',
            },
        ),
        html.Div(dash.page_container, style={'padding': '24px'}),
    ],
    style={'fontFamily': 'Segoe UI, Arial, sans-serif', 'backgroundColor': '#f4f7fb', 'minHeight': '100vh'}
)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
