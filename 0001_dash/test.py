from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

# Load a sample dataset
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

# Initialize the app
app = Dash()

# Define the layout
app.layout = [
    html.H1(children='Mini Dash Demo', style={'textAlign': 'center'}),
    dcc.Dropdown(df.City.unique(), 'SF', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
]

# Add a callback to connect user input to the graph
@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    filtered_df = df[df.City == value]
    return px.bar(filtered_df, x='Fruit', y='Amount', title=f'Fruit Sales in {value}')

# Run the server
if __name__ == '__main__':
    app.run(debug=True)
