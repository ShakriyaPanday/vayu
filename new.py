import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import requests
import plotly.graph_objs as go
from datetime import datetime
import dash_leaflet as dl
import plotly.express as px
import pandas as pd


# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
app.title = "VayuDrishti Dashboard"
server = app.server

# Load pollution data from CSV
dmap = pd.read_csv("/kaggle/input/global-air-pollution-dataset/global air pollution dataset.csv")
# Footer
footer = dbc.Container(
    html.Footer(
        [
            html.Div(
                [
                    html.P(
                        "Made in Nepal for the Earth 🌍",
                        className="text-center mb-2",
                        style={"font-weight": "bold", "font-size": "16px", "color": "#007BFF"}
                    ),
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.A(
                                            "Facebook",
                                            href="https://facebook.com/vayudrishti",
                                            target="_blank",
                                            className="btn btn-primary btn-sm mx-1"
                                        ),
                                        width="auto"
                                    ),
                                    dbc.Col(
                                        html.A(
                                            "Instagram",
                                            href="https://instagram.com/vayudrishti",
                                            target="_blank",
                                            className="btn btn-danger btn-sm mx-1"
                                        ),
                                        width="auto"
                                    ),
                                    dbc.Col(
                                        html.A(
                                            "LinkedIn",
                                            href="https://linkedin.com/company/vayudrishti",
                                            target="_blank",
                                            className="btn btn-info btn-sm mx-1"
                                        ),
                                        width="auto"
                                    ),
                                ],
                                justify="center",
                                align="center"
                            )
                        ]
                    ),
                    html.P(
                        "© 2025 VayuDrishti. All Rights Reserved.",
                        className="text-center mt-3",
                        style={"font-size": "14px", "color": "#6c757d"}
                    ),
                ],
                className="text-center py-3",
                style={
                    "background-color": "#f8f9fa",
                    "border-top": "1px solid #e9ecef"
                }
            )
        ],
        className="mt-4"
    )
)

# API URL
API_URL = "https://api.airgradient.com/public/api/v1/world/locations/58525/measures/current"
data = [
    {"date": "2025-01-16", "pm25": 85.2},
    {"date": "2025-01-17", "pm25": 78.4},
    {"date": "2025-01-18", "pm25": 90.1},
    {"date": "2025-01-19", "pm25": 88.7},
    {"date": "2025-01-20", "pm25": 92.3},
    {"date": "2025-01-21", "pm25": 95.5},
    {"date": "2025-01-22", "pm25": 89.8},
]
df = pd.DataFrame(data)

# Function to fetch data from the API
def fetch_api_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Calculate US AQI using PM2.5
def calculate_usaqi(pm25):
    breakpoints = [
        {'low': 0, 'high': 12.0, 'aqi_low': 0, 'aqi_high': 50},
        {'low': 12.1, 'high': 35.4, 'aqi_low': 51, 'aqi_high': 100},
        {'low': 35.5, 'high': 55.4, 'aqi_low': 101, 'aqi_high': 150},
        {'low': 55.5, 'high': 150.4, 'aqi_low': 151, 'aqi_high': 200},
        {'low': 150.5, 'high': 250.4, 'aqi_low': 201, 'aqi_high': 300},
        {'low': 250.5, 'high': 500.4, 'aqi_low': 301, 'aqi_high': 500},
    ]
    for bp in breakpoints:
        if bp['low'] <= pm25 <= bp['high']:
            return ((bp['aqi_high'] - bp['aqi_low']) / (bp['high'] - bp['low'])) * (pm25 - bp['low']) + bp['aqi_low']
    return None  # Out of range

# Calculate cigarette equivalent
def calculate_cigarette_equivalent(pm25, hours_exposed):
    if pm25 is not None:
        return round((pm25 / 22) * (hours_exposed / 24), 2)
    return "No data"

# Navigation Bar
navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand("VayuDrishti", href="/"),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Dashboard", href="/")),
            dbc.NavItem(dbc.NavLink("Learn", href="/learn")),
            dbc.NavItem(dbc.NavLink("About Us", href="/about")),
            dbc.NavItem(dbc.NavLink("Map", href="/map")),
            dbc.NavItem(dbc.NavLink("AQI Calculator", href="/calculator")),
        ], className="ml-auto", navbar=True),
    ]),
    color="primary",
    dark=True,
    className="mb-4"
)

# Layout for the Dashboard page
def dashboard_layout():
    return dbc.Container([
        dcc.Interval(id='update-interval', interval=30 * 1000, n_intervals=0),  # Update every 30 seconds

        html.Div([
            html.H5("LIVE", className='text-center text-danger', style={'font-weight': 'bold'}),
            html.H1("Nepal Air Quality Index (AQI) | Air Pollution", className='text-center my-2', style={'color': '#007BFF'}),
            html.H4("Real-time Air Pollution Levels in Nepal", className='text-center my-2'),
            html.Div(id='last-updated', className='text-center my-2', style={'font-size': '16px', 'font-weight': 'bold'})
        ], className='mb-4'),

        html.Div(id='location-name', className='text-center mb-4', style={'font-size': '18px'}),

        # AQI Card
        dbc.Card([
            dbc.CardBody([
                html.H4("Air Quality Index (AQI)", className='text-center'),
                html.H2(id='aqi-value', className='text-center'),
                html.Div(id='health-advice', className='text-center mt-2', style={'font-size': '16px'}),
                html.Div(id='cigarette-equivalent', className='text-center mt-2', style={'font-size': '16px'}),
            ])
        ], className='mb-4', style={'border-radius': '10px', 'border': '2px solid #007BFF'}),

        # Data Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("PM2.5", className='text-center'),
                        html.H2(id='pm02-value', className='text-center'),
                    ])
                ], id='pm02-card', style={'border-radius': '10px'}),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("PM10", className='text-center'),
                        html.H2(id='pm10-value', className='text-center'),
                    ])
                ], id='pm10-card', style={'border-radius': '10px'}),
            ], width=6),
        ], className='mb-4'),

        # Environmental Data
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Temperature (°C)", className='text-center'),
                        html.H2(id='temperature-value', className='text-center'),
                    ])
                ], style={'border-radius': '10px'}),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Humidity (%)", className='text-center'),
                        html.H2(id='humidity-value', className='text-center'),
                    ])
                ], style={'border-radius': '10px'}),
            ], width=6),
        ], className='mb-4'),

        # Live Graph
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(id='live-graph', style={'height': '400px'})
            ])
        ], className='mb-4'),

        # OpenStreetMap
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    dl.Map(
                        id='map',
                        style={'width': '100%', 'height': '400px'},
                        center=[27.727502,85.330135],  # Default to Kathmandu, Nepal
                        zoom=30,
                        children=[
                            dl.TileLayer(),  # Default OpenStreetMap layer
                            dl.Marker(
                                id='map-marker',
                                position=[27.7172, 85.3240],  # Default position
                                children=[dl.Tooltip("Air Quality Station"), dl.Popup("Station Details")]
                            ),
                        ]
                    )
                ])
            ])
        ]),
    ], fluid=True)

# Layout for the About page
def about_layout():
    return dbc.Container([
        html.H1("About VayuDrishti", className='text-center my-4', style={'color': '#007BFF'}),

        html.P(
            "At VayuDrishti, we believe in the power of data to bring about change. Our mission is to empower communities, "
            "policymakers, and individuals with actionable insights to combat air pollution and improve public health.",
            style={'font-size': '18px'}
        ),

        html.P(
            "Founded in Nepal, VayuDrishti was born out of a passion for tackling one of the most pressing challenges of our time—air quality. "
            "We leverage cutting-edge technology and innovation to create a world where everyone can breathe cleaner, healthier air.",
            style={'font-size': '18px'}
        ),

        html.H2("What We Do", className='text-center my-4', style={'color': '#007BFF'}),
        html.Ul([
            html.Li(
                "Develop low-cost, accurate air quality monitoring devices to measure PM2.5, PM10, temperature, humidity, and more.",
                style={'font-size': '16px'}
            ),
            html.Li(
                "Provide real-time air quality data through an interactive dashboard and visualizations.",
                style={'font-size': '16px'}
            ),
            html.Li(
                "Educate communities and schools through hands-on workshops and air quality literacy programs.",
                style={'font-size': '16px'}
            ),
            html.Li(
                "Collaborate with environmental organizations, government agencies, and academic institutions to drive meaningful impact.",
                style={'font-size': '16px'}
            ),
            html.Li(
                "Raise awareness about the health impacts of air pollution and encourage data-driven decision-making.",
                style={'font-size': '16px'}
            )
        ]),

        html.H2("Our Vision", className='text-center my-4', style={'color': '#007BFF'}),
        html.P(
            "Our vision is a world where clean air is a right, not a privilege. By providing affordable, accessible, "
            "and reliable air quality data, we aim to spark community-level and global actions that drive sustainable solutions to air pollution.",
            style={'font-size': '18px'}
        ),

        html.H2("Our Journey", className='text-center my-4', style={'color': '#007BFF'}),
        html.P(
            "Since our inception, VayuDrishti has evolved from a simple idea into a movement. What began as a project to measure air pollution "
            "in Nepal has grown into a platform that combines data, technology, and human action. Along the way, we’ve partnered with "
            "renowned organizations like USAID Clean Air, academic institutions, and local communities to expand our reach and refine our solutions.",
            style={'font-size': '18px'}
        ),

        html.H2("Our Achievements", className='text-center my-4', style={'color': '#007BFF'}),
        html.Ul([
            html.Li(
                "Designed and deployed one of the most affordable air quality monitoring systems in South Asia.",
                style={'font-size': '16px'}
            ),
            html.Li(
                "Hosted air quality literacy workshops reaching hundreds of students and educators.",
                style={'font-size': '16px'}
            ),
            html.Li(
                "Collected and analyzed 30 years of satellite and ground-based air pollution data for research.",
                style={'font-size': '16px'}
            ),
            html.Li(
                "Collaborated with international experts in air quality and environmental sciences.",
                style={'font-size': '16px'}
            )
        ]),

        html.H2("Why VayuDrishti?", className='text-center my-4', style={'color': '#007BFF'}),
        html.P(
            "What sets us apart is our commitment to accessibility and innovation. We are more than just an air quality monitoring system—we are "
            "a catalyst for change. By integrating real-time data, interactive tools, and community engagement, we aim to make air quality monitoring "
            "a part of everyday life. Together, we can build a healthier, more sustainable future for everyone.",
            style={'font-size': '18px'}
        ),

        html.H2("Join Us", className='text-center my-4', style={'color': '#007BFF'}),
        html.P(
            "Be a part of our journey to create a cleaner, greener world. Follow us on social media, attend our workshops, "
            "and use our data to make informed decisions for your health and the environment.",
            style={'font-size': '18px'}
        ),
    ], fluid=True)

# Layout for the Learn About Air Pollution page
def learn_page_layout():
    return dbc.Container([
        html.H1("Learn About Air Pollution", className='text-center my-4', style={'color': '#007BFF'}),

        html.H2("What is Air Pollution?", className='my-3', style={'color': '#007BFF'}),
        html.P(
            "Air pollution refers to the presence of harmful substances in the atmosphere that pose risks to human health, "
            "the environment, and the climate. These pollutants can be gases, particulates, or biological molecules introduced "
            "by natural or human activities.",
            style={'font-size': '18px'}
        ),
        html.P(
            "Common sources of air pollution include vehicle emissions, industrial processes, burning of fossil fuels, "
            "agricultural activities, and natural events such as wildfires and volcanic eruptions.",
            style={'font-size': '18px'}
        ),

        html.H2("Impacts on Health", className='my-3', style={'color': '#007BFF'}),
        html.Ul([
            html.Li("Respiratory diseases such as asthma, bronchitis, and chronic obstructive pulmonary disease (COPD).",
                    style={'font-size': '16px'}),
            html.Li("Cardiovascular diseases, including increased risks of heart attacks and strokes.",
                    style={'font-size': '16px'}),
            html.Li("Impaired lung development in children, leading to long-term health issues.",
                    style={'font-size': '16px'}),
            html.Li("Increased risk of lung cancer and other cancers caused by prolonged exposure to toxic pollutants.",
                    style={'font-size': '16px'}),
            html.Li("Premature mortality: The World Health Organization (WHO) estimates that air pollution causes 7 million deaths annually.",
                    style={'font-size': '16px'})
        ]),

        html.H2("Global Death Toll from Air Pollution", className='my-3', style={'color': '#007BFF'}),
        html.P(
            "Air pollution is a silent killer, causing millions of premature deaths every year. According to the World Health Organization (WHO):",
            style={'font-size': '18px'}
        ),
        html.Ul([
            html.Li("Outdoor air pollution is responsible for 4.2 million deaths annually worldwide.", style={'font-size': '16px'}),
            html.Li("Indoor air pollution from cooking fuels affects 3.2 million people every year, including many women and children in low-income households.",
                    style={'font-size': '16px'}),
            html.Li("Combined, air pollution is linked to over 7 million deaths annually, making it one of the leading risk factors for early death.",
                    style={'font-size': '16px'}),
        ]),
        html.P(
            "The burden of air pollution is disproportionately high in low- and middle-income countries, particularly in South Asia, "
            "where rapid urbanization and reliance on biomass fuels exacerbate the issue.",
            style={'font-size': '18px'}
        ),

        html.H2("Major Pollutants", className='my-3', style={'color': '#007BFF'}),
        html.Ul([
            html.Li("Particulate Matter (PM2.5 and PM10): Tiny particles that penetrate deep into the lungs and bloodstream, causing severe health issues.",
                    style={'font-size': '16px'}),
            html.Li("Nitrogen Dioxide (NO₂): Emitted from vehicles and industrial processes, it irritates the airways and reduces lung function.",
                    style={'font-size': '16px'}),
            html.Li("Sulfur Dioxide (SO₂): Produced by burning coal and oil, it contributes to acid rain and respiratory problems.",
                    style={'font-size': '16px'}),
            html.Li("Ground-Level Ozone (O₃): A secondary pollutant formed by chemical reactions between sunlight and pollutants, it worsens respiratory conditions.",
                    style={'font-size': '16px'}),
            html.Li("Carbon Monoxide (CO): A colorless, odorless gas that reduces oxygen delivery to the body’s tissues and organs.",
                    style={'font-size': '16px'})
        ]),

        html.H2("How is Pollution Measured?", className='my-3', style={'color': '#007BFF'}),
        html.P(
            "Air pollution levels are typically measured using Air Quality Index (AQI), a standardized system that indicates "
            "the severity of pollution. AQI considers concentrations of key pollutants like PM2.5, PM10, NO₂, O₃, SO₂, and CO, "
            "and categorizes air quality from 'Good' to 'Hazardous'.",
            style={'font-size': '18px'}
        ),
        html.P(
            "PM2.5 levels, in particular, are measured in micrograms per cubic meter (µg/m³). Health impacts increase significantly "
            "when PM2.5 levels exceed WHO guidelines of 5 µg/m³ annually or 15 µg/m³ for 24-hour exposure.",
            style={'font-size': '18px'}
        ),

        html.H2("How Can You Help?", className='my-3', style={'color': '#007BFF'}),
        html.Ul([
            html.Li("Use public transportation or carpool to reduce vehicle emissions.", style={'font-size': '16px'}),
            html.Li("Switch to renewable energy sources like solar and wind.", style={'font-size': '16px'}),
            html.Li("Adopt energy-efficient appliances and reduce electricity consumption.", style={'font-size': '16px'}),
            html.Li("Plant trees to absorb carbon dioxide and filter air pollutants.", style={'font-size': '16px'}),
            html.Li("Participate in community clean-up drives and awareness campaigns.", style={'font-size': '16px'})
        ]),

        html.H2("Join the Movement", className='my-3', style={'color': '#007BFF'}),
        html.P(
            "At VayuDrishti, we encourage individuals and organizations to join hands in combating air pollution. "
            "Explore our resources, attend our workshops, and use our tools to make informed decisions for a healthier environment.",
            style={'font-size': '18px'}
        ),
        html.Div(
            dbc.Button("Get Involved", color="primary", href="/about", className="mt-3"),
            className="text-center"
        ),

        html.H2("Facts About Air Pollution", className='my-3', style={'color': '#007BFF'}),
        html.Ul([
            html.Li("Air pollution is the fourth leading risk factor for early death worldwide.", style={'font-size': '16px'}),
            html.Li("Over 90% of the world’s population breathes air that exceeds WHO pollution limits.", style={'font-size': '16px'}),
            html.Li("Indoor air pollution from biomass fuels affects 3 billion people globally.", style={'font-size': '16px'}),
            html.Li("Air pollution costs the global economy an estimated $8 trillion annually.", style={'font-size': '16px'}),
            html.Li("Children and the elderly are most vulnerable to the effects of air pollution.",
                    style={'font-size': '16px'})
        ])
    ], fluid=True)

# Layout for the AQI Calculator page
def calculator_layout():
    return dbc.Container([
        html.H1("AQI Calculator", className='text-center my-4', style={'color': '#007BFF'}),

        # AQI Table with Color Codes
        html.Div([
            html.H4("AQI Categories and Color Codes", className='text-center mb-3', style={'color': '#007BFF'}),
            dbc.Table(
                [
                    html.Thead(
                        html.Tr([
                            html.Th("AQI Range", className='text-center'),
                            html.Th("Category", className='text-center'),
                            html.Th("Color", className='text-center')
                        ])
                    ),
                    html.Tbody([
                        html.Tr([html.Td("0-50", className='text-center'), html.Td("Good", className='text-center'), html.Td(style={'background-color': '#00e400'})]),
                        html.Tr([html.Td("51-100", className='text-center'), html.Td("Moderate", className='text-center'), html.Td(style={'background-color': '#ffff00'})]),
                        html.Tr([html.Td("101-150", className='text-center'), html.Td("Unhealthy for Sensitive Groups", className='text-center'), html.Td(style={'background-color': '#ff7e00'})]),
                        html.Tr([html.Td("151-200", className='text-center'), html.Td("Unhealthy", className='text-center'), html.Td(style={'background-color': '#ff0000'})]),
                        html.Tr([html.Td("201-300", className='text-center'), html.Td("Very Unhealthy", className='text-center'), html.Td(style={'background-color': '#8f3f97'})]),
                        html.Tr([html.Td("301-500", className='text-center'), html.Td("Hazardous", className='text-center'), html.Td(style={'background-color': '#7e0023'})]),
                    ])
                ],
                bordered=True,
                hover=True,
                responsive=True,
                style={'font-size': '14px'}
            ),
        ], className="mb-4"),

        # Input Fields
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Label("PM2.5 (µg/m³)", className="mb-2"),
                        dcc.Input(id='input-pm25', type='number', placeholder='Enter PM2.5 value',
                                  className="form-control mb-3")
                    ])
                ], width=6),
                dbc.Col([
                    html.Div([
                        dbc.Label("PM10 (µg/m³)", className="mb-2"),
                        dcc.Input(id='input-pm10', type='number', placeholder='Enter PM10 value',
                                  className="form-control mb-3")
                    ])
                ], width=6),
            ], justify="center"),  # Center input fields
        ], className="text-center"),

        # Button and Calculation Output
        html.Div([
            dbc.Button("Calculate AQI", id='calculate-button', color='primary', className='mt-3'),
            html.Div(id='calculation-output', className='mt-4', style={'font-size': '18px'})
        ], className="text-center"),  # Center the button and output
    ], fluid=True)


# Callback for AQI Calculator
@app.callback(
    Output('calculation-output', 'children'),
    [Input('calculate-button', 'n_clicks')],
    [dash.dependencies.State('input-pm25', 'value'),
     dash.dependencies.State('input-pm10', 'value')]
)
def calculate_aqi(n_clicks, pm25, pm10):
    if n_clicks is None or pm25 is None or pm10 is None:
        return ""

    # Calculate AQI for PM2.5
    aqi_pm25 = calculate_usaqi(pm25)
    # Calculate AQI for PM10
    aqi_pm10 = calculate_usaqi(pm10)

    # Determine the higher AQI value as the final AQI
    aqi_final = max(aqi_pm25, aqi_pm10) if aqi_pm25 and aqi_pm10 else None

    if aqi_final:
        # Determine the AQI category
        if aqi_final <= 50:
            category = "Good"
            color = "Green"
        elif aqi_final <= 100:
            category = "Moderate"
            color = "Yellow"
        elif aqi_final <= 150:
            category = "Unhealthy for Sensitive Groups"
            color = "Orange"
        elif aqi_final <= 200:
            category = "Unhealthy"
            color = "Red"
        elif aqi_final <= 300:
            category = "Very Unhealthy"
            color = "Purple"
        else:
            category = "Hazardous"
            color = "Maroon"

        return html.Div([
            html.P(f"Calculated AQI: {aqi_final:.2f}", style={'font-weight': 'bold', 'font-size': '20px'}),
            html.P(f"Category: {category}", style={'color': color.lower(), 'font-size': '18px'}),
            html.P(f"PM2.5 AQI: {aqi_pm25:.2f}, PM10 AQI: {aqi_pm10:.2f}", style={'font-size': '16px'}),
        ], className="text-center")
    else:
        return html.P("Unable to calculate AQI. Please enter valid inputs.", className="text-center")

def choropleth_page_layout():
    return dbc.Container([
        html.H1("Global Air Quality Map", className='text-center my-4', style={'color': '#007BFF'}),
        
        html.Div([
            html.Label("Select Pollutant to Display:", style={'font-size': '18px'}),
            dcc.Dropdown(
                id='pollutant-dropdown',
                options=[
                    {"label": "AQI Value", "value": "AQI Value"},
                    {"label": "CO AQI Value", "value": "CO AQI Value"},
                    {"label": "Ozone AQI Value", "value": "Ozone AQI Value"},
                    {"label": "NO2 AQI Value", "value": "NO2 AQI Value"},
                    {"label": "PM2.5 AQI Value", "value": "PM2.5 AQI Value"}
                ],
                value="AQI Value",
                clearable=False,
                className="mb-4"
            ),
        ], style={'width': '50%', 'margin': '0 auto'}),

        dcc.Graph(id='choropleth-map', style={'height': '600px'}),
        
        html.Div("Data Source: NASA", className='text-center mt-4', style={'font-size': '14px', 'color': '#6c757d'}),
    ], fluid=True)

@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('pollutant-dropdown', 'value')]
)
def update_choropleth_map(selected_pollutant):
    fig = px.choropleth(
        dmap,
        locations="Country",
        locationmode="country names",
        color=selected_pollutant,
        hover_name="City",
        title=f"Heat Map of {selected_pollutant}",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular'),
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
    )
    return fig

# App Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content'),
    footer 
])

# Callbacks
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/about':
        return about_layout()
    elif pathname == '/calculator':
        return calculator_layout()
    elif pathname == '/learn':
        return learn_page_layout()
    elif pathname == '/map':  
        return choropleth_page_layout()
    elif pathname == '/':
        return dashboard_layout()
    else:
        return dbc.Container(
            html.H1("404: Page Not Found", className='text-center text-danger'),
            fluid=True
        )

@app.callback(
    [Output('location-name', 'children'),
     Output('pm02-value', 'children'),
     Output('pm10-value', 'children'),
     Output('temperature-value', 'children'),
     Output('humidity-value', 'children'),
     Output('aqi-value', 'children'),
     Output('health-advice', 'children'),
     Output('cigarette-equivalent', 'children'),
     Output('live-graph', 'figure'),  # Added Output for live-graph
     Output('map', 'children'),       # Map children
     Output('last-updated', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def update_dashboard(n_intervals):
    data = fetch_api_data()
    if not data:
        return "No data", "No data", "No data", "No data", "No data", "No data", "No data", "No data", {}, {}, "Last Updated: No data"

    location_name = data.get("locationName", "Unknown Location")
    pm25 = data.get("pm02", 0)
    pm10 = data.get("pm10", 0)
    temperature = data.get("atmp", "No data")
    humidity = data.get("rhum", "No data")
    lat = data.get("latitude", 0)
    lon = data.get("longitude", 0)
    timestamp = data.get("timestamp", "No data")
    

    # Calculate AQI
    us_aqi = calculate_usaqi(pm25)

    # Determine health advice and cigarette equivalent
    if us_aqi is not None:
        if us_aqi <= 50:
            health_advice = "Good air quality. No precautions needed."
        elif us_aqi <= 100:
            health_advice = "Moderate air quality. Sensitive groups should limit outdoor activities."
        elif us_aqi <= 150:
            health_advice = "Unhealthy for sensitive groups. Reduce outdoor exertion."
        elif us_aqi <= 200:
            health_advice = "Unhealthy. Everyone should limit outdoor activities."
        elif us_aqi <= 300:
            health_advice = "Very unhealthy. Stay indoors with air filtration."
        else:
            health_advice = "Hazardous. Avoid outdoor activities."
        cigarette_equivalent = f"Equivalent to smoking {calculate_cigarette_equivalent(pm25, 24)} cigarettes per day."
    else:
        health_advice = "No data available for health advice."
        cigarette_equivalent = "No data available for cigarette equivalent."

    # Format timestamp
    if timestamp != "No data":
        last_updated = f"Last Updated: {datetime.fromisoformat(timestamp.replace('Z', '')).strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        last_updated = "Last Updated: No data"

    # Create live graph
    bar_graph_figure = {
    'data': [
        go.Bar(
            x=df['date'], 
            y=df['pm25'], 
            name='PM2.5 Daily Averages', 
            marker=dict(color='#007BFF')
        )
    ],
    'layout': go.Layout(
        title='Past 7 Days PM2.5 Levels',
        xaxis=dict(title='Date'),
        yaxis=dict(title='PM2.5 (µg/m³)'),
        template='plotly_white'
    )
}


    # Create the map with updated marker position
    map_children = [
        dl.TileLayer(),
        dl.Marker(
            position=[lat, lon],
            children=[dl.Tooltip(location_name), dl.Popup(f"PM2.5: {pm25} µg/m³, PM10: {pm10} µg/m³")]
        )
    ]

    return (
    location_name,
    f"{pm25} µg/m³",
    f"{pm10} µg/m³",
    f"{temperature} °C",
    f"{humidity} %",
    f"{us_aqi:.2f}" if us_aqi else "No data",
    health_advice,
    cigarette_equivalent,
    bar_graph_figure,   # For 'live-graph'
    map_children,        # For 'map'
    last_updated         # For 'last-updated'
)


if __name__ == '__main__':
    app.run_server(debug=True)
