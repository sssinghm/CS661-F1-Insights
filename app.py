# app.py
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context, ctx, no_update
from dash import dash_table
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import logging
import os
from datetime import datetime
from functools import lru_cache

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

# ============================================================
# CONSTANTS & THEME
# ============================================================
SURFACE = "#15181D"
SURFACE_RAISED = "#1D2129"
INPUT_BG = "#0f131b"
BORDER = "#2A2E37"
TEXT_PRIMARY = "#F5F6F7"
TEXT_MUTED = "#9AA0AA"
ACCENT_RED = "#E10600"
ACCENT_CYAN = "#00d2ff"
ACCENT_CYAN_ALPHA = "rgba(0, 210, 255, 0.08)"
HOVER_BG = "rgba(0, 210, 255, 0.1)"
DRIVER1_COLOR = '#00E5FF'
DRIVER2_COLOR = '#FF8A3D'
FONT_FAMILY = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"
AMBER = '#FFB100'
AMBER_DIM = 'rgba(255,177,0,0.18)'
CARBON = '#15171C'
PANEL = '#1B1E26'
INK = '#FFFFFF'
MUTED = '#C7CCD6'
HAIRLINE = 'rgba(237,233,225,0.10)'
GRID_LINE = 'rgba(237,233,225,0.06)'

# F1 Team Colors
F1_TEAM_COLORS = {
    'Ferrari': '#DC0000', 'Red Bull': '#3671C6', 'Mercedes': '#27F4D2',
    'McLaren': '#FF8000', 'Aston Martin': '#00A19C', 'Alpine F1 Team': '#FF87BC',
    'Renault': '#FFF500', 'Racing Point': '#F596C8', 'AlphaTauri': '#5E8FAA',
    'Toro Rosso': '#469BFF', 'Sauber': '#52E252', 'RB F1 Team': '#6692FF',
    'Alfa Romeo': '#C92D4B', 'Williams': '#64C4FF', 'Haas F1 Team': '#B6BABD'
}

_PALETTE = (px.colors.qualitative.Set2 + px.colors.qualitative.Set1 + px.colors.qualitative.Pastel)
COLOR_MAP = {c: _PALETTE[i % len(_PALETTE)] for i, c in enumerate(sorted(F1_TEAM_COLORS.keys()))}


# ============================================================
# SLOT 1: DATA LOADING
# ============================================================
def load_data():
    """Load the F1 dataset"""
    try:
        df = pd.read_csv('data/master_f1_final_dnf_fixed.csv')
        logger.info(f"✅ Loaded {len(df)} records")
        
        # Convert numeric columns
        numeric_cols = [
            "year", "grid", "positionOrder", "positions_gained",
            "pit_stop_count", "avg_pit_ms", "fastest_pit_ms", "slowest_pit_ms",
            "points", "is_dnf", "championship_points", "fastestLapSpeed", "lat", "lng"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Add derived columns
        df["avg_pit_s"] = df["avg_pit_ms"] / 1000 if "avg_pit_ms" in df.columns else 0
        df["fastest_pit_s"] = df["fastest_pit_ms"] / 1000 if "fastest_pit_ms" in df.columns else 0
        df["slowest_pit_s"] = df["slowest_pit_ms"] / 1000 if "slowest_pit_ms" in df.columns else 0
        
        df["normal_pit_stop"] = (
            (df["pit_stop_count"] > 0) &
            (df["avg_pit_ms"].between(15000, 60000))
        ) if "avg_pit_ms" in df.columns else False
        
        df["valid_grid"] = df["grid"] > 0 if "grid" in df.columns else False
        df["race_label"] = df["year"].astype(int).astype(str) + " - " + df["race_name"].astype(str)
        
        df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
        
        if 'lap_consistency_score' not in df.columns:
            df['lap_consistency_score'] = 1 / (df.get('lap_std', pd.Series(0)).fillna(0) + 1)
        df['is_dnf'] = pd.to_numeric(df.get('is_dnf', pd.Series(0)), errors='coerce').fillna(0).astype(int)
        
        return df
    except FileNotFoundError as e:
        logger.error(f"❌ Data file not found: {e}")
        return create_sample_data()


def create_sample_data():
    """Create sample data for testing"""
    return pd.DataFrame({
        'driver_name': ['Max Verstappen', 'Lewis Hamilton', 'Charles Leclerc', 'Lando Norris', 'Carlos Sainz'],
        'championship_points': [437, 350, 280, 250, 230],
        'constructor_name': ['Red Bull', 'Mercedes', 'Ferrari', 'McLaren', 'Ferrari'],
        'nationality': ['Dutch', 'British', 'Monégasque', 'British', 'Spanish'],
        'year': [2024, 2024, 2024, 2024, 2024],
        'round': [1, 2, 3, 4, 5],
        'race_name': ['Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China'],
        'grid': [1, 2, 3, 4, 5],
        'positionOrder': [2, 3, 1, 5, 4],
        'positions_gained': [-1, -1, 2, -1, 1],
        'pit_stop_count': [2, 3, 2, 3, 2],
        'avg_pit_ms': [22000, 23000, 21000, 24000, 22000],
        'status': ['Finished', 'Finished', 'Finished', 'Finished', 'Finished'],
        'is_dnf': [0, 0, 0, 0, 0],
        'date': ['2024-03-02', '2024-03-09', '2024-03-24', '2024-04-07', '2024-04-21'],
        'circuit_name': ['Bahrain International', 'Jeddah Corniche', 'Albert Park', 'Suzuka', 'Shanghai'],
        'country': ['Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China'],
        'lat': [26.0325, 26.17, -37.8497, 34.8433, 31.3389],
        'lng': [50.5106, 50.08, 144.968, 136.5333, 121.2197],
        'is_winner': [1, 0, 0, 0, 0],
        'is_podium': [1, 0, 1, 0, 0],
        'is_points_finish': [1, 1, 1, 1, 1],
        'lap_consistency_score': [0.85, 0.78, 0.82, 0.75, 0.80],
        'fastestLapSpeed': [320.5, 318.2, 315.7, 312.3, 310.8],
        'location': ['Sakhir', 'Jeddah', 'Melbourne', 'Suzuka', 'Shanghai']
    })


# ============================================================
# SLOT 2: OVERVIEW PAGE
# ============================================================
def create_overview_page(theme='dark', color_scheme='Viridis'):
    """Create the overview page with 4 visualizations + Data Table"""
    df = load_data()
    
    # Theme colors
    if theme == 'dark':
        bg_color, paper_bg, text_color, card_bg, border_color = '#0d0d1a', '#0d0d1a', '#ffffff', 'rgba(26, 26, 46, 0.85)', 'rgba(255, 255, 255, 0.08)'
    else:
        bg_color, paper_bg, text_color, card_bg, border_color = 'rgba(0,0,0,0)', 'rgba(0,0,0,0)', '#1a1a2e', '#ffffff', '#e0e0e0'
    
    # KPI CARDS
    total_seasons = len(df['year'].unique()) if 'year' in df.columns else 0
    total_races = len(df[['year', 'race_name']].drop_duplicates()) if 'year' in df.columns and 'race_name' in df.columns else 0
    total_drivers = len(df['driver_name'].unique()) if 'driver_name' in df.columns else 0
    total_constructors = len(df['constructor_name'].unique()) if 'constructor_name' in df.columns else 0
    
    kpi_cards = html.Div([
        html.Div([html.H3(f"{total_seasons}", className="kpi-number", style={'color': '#ff6b35'}), html.P("🏁 Total Seasons", className="kpi-label")], className="kpi-card"),
        html.Div([html.H3(f"{total_races}", className="kpi-number", style={'color': '#4ecdc4'}), html.P("🏎️ Total Races", className="kpi-label")], className="kpi-card"),
        html.Div([html.H3(f"{total_drivers}", className="kpi-number", style={'color': '#ffe66d'}), html.P("👤 Total Drivers", className="kpi-label")], className="kpi-card"),
        html.Div([html.H3(f"{total_constructors}", className="kpi-number", style={'color': '#ff6b6b'}), html.P("🏭 Total Constructors", className="kpi-label")], className="kpi-card"),
    ], className="kpi-grid")
    
    # PLOT 1: Season Coverage
    if 'year' in df.columns and 'race_name' in df.columns:
        unique_races = df[['year', 'race_name']].drop_duplicates()
        races_per_season = unique_races.groupby('year').size().reset_index(name='Races')
        
        fig1 = px.bar(
            races_per_season,
            x='year',
            y='Races',
            color='Races',
            color_continuous_scale='Viridis',
            text='Races'
        )
        fig1.update_traces(textposition='outside', hovertemplate='<b>%{x}</b><br>Unique Races: %{y}<extra></extra>')
        fig1.update_layout(
            xaxis_title="Season Year",
            yaxis_title="Number of Unique Races",
            plot_bgcolor=bg_color,
            paper_bgcolor=paper_bg,
            font_color=text_color,
            showlegend=False,
            height=350
        )
    else:
        fig1 = go.Figure()
        fig1.add_annotation(text="No season data available", showarrow=False, font=dict(color=text_color, size=16))
        fig1.update_layout(plot_bgcolor=bg_color, paper_bgcolor=paper_bg, height=350)
    
    # PLOT 2: Circuit Distribution Across Countries
    if 'country' in df.columns and 'circuit_name' in df.columns:
        unique_circuits = df[['country', 'circuit_name']].drop_duplicates()
        circuit_counts = unique_circuits.groupby('country').size().reset_index(name='Circuits')
        circuit_counts = circuit_counts.sort_values('Circuits', ascending=True)
        
        fig2 = px.bar(
            circuit_counts,
            x='Circuits',
            y='country',
            orientation='h',
            color='Circuits',
            color_continuous_scale='Viridis',
            text='Circuits'
        )
        fig2.update_traces(
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Unique Circuits: %{x}<extra></extra>'
        )
        fig2.update_layout(
            xaxis_title="Number of Unique Circuits",
            yaxis_title="Country",
            plot_bgcolor=bg_color,
            paper_bgcolor=paper_bg,
            font_color=text_color,
            showlegend=False,
            height=400
        )
    else:
        fig2 = go.Figure()
        fig2.add_annotation(text="No circuit data available", showarrow=False, font=dict(color=text_color, size=16))
        fig2.update_layout(plot_bgcolor=bg_color, paper_bgcolor=paper_bg, height=400)
    
    # LEAFLET MAP
    if 'lat' in df.columns and 'lng' in df.columns and 'circuit_name' in df.columns:
        circuits_df = df[['circuit_name', 'lat', 'lng', 'country']].drop_duplicates()
        
        markers = []
        for _, row in circuits_df.iterrows():
            markers.append(
                dl.Marker(
                    position=[row['lat'], row['lng']],
                    children=[
                        dl.Tooltip(row['circuit_name']),
                        dl.Popup(f"<b>{row['circuit_name']}</b><br>{row['country']}")
                    ]
                )
            )
        
        map_component = dl.Map(
            children=[
                dl.TileLayer(
                    url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                    attribution='© OpenStreetMap contributors',
                    noWrap=True
                ),
                dl.LayerGroup(children=markers, id="circuit-markers"),
                dl.FullScreenControl(position="topleft"),
                dl.ZoomControl(position="bottomright"),
            ],
            center=[20, 0],
            zoom=2,
            minZoom=2,
            maxBounds=[[-90, -180], [90, 180]],
            style={'height': '400px', 'width': '100%', 'borderRadius': '12px'},
            id="circuit-map"
        )
    else:
        map_component = html.Div(
            "No circuit location data available",
            style={'color': text_color, 'textAlign': 'center', 'padding': '50px', 'height': '400px'}
        )
    
    # PLOT 3: Constructor Participation by Season
    if 'year' in df.columns and 'constructor_name' in df.columns:
        participation = df.groupby(['year', 'constructor_name']).size().reset_index(name='Entries')
        pivot_data = participation.pivot(index='constructor_name', columns='year', values='Entries').fillna(0)
        
        fig3 = px.imshow(
            pivot_data,
            color_continuous_scale='Blues',
            aspect='auto',
            text_auto=True,
            labels=dict(x="Season", y="Constructor", color="Entries")
        )
        fig3.update_layout(
            plot_bgcolor=bg_color,
            paper_bgcolor=paper_bg,
            font_color=text_color,
            height=400,
            xaxis=dict(side='top')
        )
        fig3.update_xaxes(tickangle=0)
        fig3.update_yaxes(tickfont=dict(size=10))
    else:
        fig3 = go.Figure()
        fig3.add_annotation(text="No constructor participation data available", showarrow=False, font=dict(color=text_color, size=16))
        fig3.update_layout(plot_bgcolor=bg_color, paper_bgcolor=paper_bg, height=400)
    
    # PLOT 4: Race Calendar Distribution
    if 'date' in df.columns and 'race_name' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['month_name'] = df['date'].dt.strftime('%B')
        
        unique_races_month = df[['month', 'month_name', 'race_name']].drop_duplicates()
        monthly_races = unique_races_month.groupby(['month', 'month_name']).size().reset_index(name='Count')
        monthly_races = monthly_races.sort_values('month')
        
        all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
        month_num = {name: i+1 for i, name in enumerate(all_months)}
        
        for month in all_months:
            if month not in monthly_races['month_name'].values:
                monthly_races = pd.concat([monthly_races, pd.DataFrame({'month': [month_num[month]], 'month_name': [month], 'Count': [0]})])
        
        monthly_races = monthly_races.sort_values('month')
        
        fig4 = px.line(
            monthly_races,
            x='month_name',
            y='Count',
            markers=True,
            line_shape='spline'
        )
        fig4.update_traces(
            line=dict(color='#ff6b35', width=4),
            marker=dict(size=12, color='#ff6b35', line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>Unique Races: %{y}<extra></extra>'
        )
        fig4.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Unique Races",
            plot_bgcolor=bg_color,
            paper_bgcolor=paper_bg,
            font_color=text_color,
            showlegend=False,
            height=350
        )
        fig4.add_trace(go.Scatter(
            x=monthly_races['month_name'],
            y=monthly_races['Count'],
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(255, 107, 53, 0.2)',
            line=dict(color='rgba(255, 107, 53, 0)'),
            showlegend=False,
            hoverinfo='skip'
        ))
    else:
        fig4 = go.Figure()
        fig4.add_annotation(text="No calendar data available", showarrow=False, font=dict(color=text_color, size=16))
        fig4.update_layout(plot_bgcolor=bg_color, paper_bgcolor=paper_bg, height=350)
    
    # DATA TABLE
    table_df = df[['driver_name', 'year', 'championship_points', 'constructor_name', 'nationality', 'race_name', 'round', 'date']].copy()
    table_df = table_df.sort_values(['year', 'driver_name', 'round'])
    table_df['race_points'] = table_df.groupby(['year', 'driver_name'])['championship_points'].diff().fillna(table_df['championship_points'])
    table_df = table_df.sort_values(['year', 'round'], ascending=[True, True])
    
    available_years = sorted(table_df['year'].unique()) if 'year' in table_df.columns else []
    available_constructors = sorted(table_df['constructor_name'].unique()) if 'constructor_name' in table_df.columns else []
    
    table_component = html.Div([
        html.H4("🏎️ Driver Data", style={'color': text_color, 'marginBottom': '15px'}),
        
        html.Div([
            html.Div([
                html.Label("Filter by Year:", style={'color': text_color, 'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='table-year-filter',
                    options=[{'label': 'All Years', 'value': 'All'}] + [{'label': str(y), 'value': y} for y in available_years],
                    value='All',
                    clearable=False,
                    style={'width': '180px', 'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginRight': '20px'}),
            html.Div([
                html.Label("Filter by Constructor:", style={'color': text_color, 'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='table-constructor-filter',
                    options=[{'label': 'All Constructors', 'value': 'All'}] + [{'label': c, 'value': c} for c in available_constructors],
                    value='All',
                    clearable=False,
                    style={'width': '200px', 'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '15px'}),
        
        html.Div([
            dash_table.DataTable(
                id='driver-data-table',
                columns=[
                    {"name": "Driver", "id": "driver_name"},
                    {"name": "Year", "id": "year"},
                    {"name": "Date", "id": "date"},
                    {"name": "Race", "id": "race_name"},
                    {"name": "Round", "id": "round"},
                    {"name": "Points Scored", "id": "race_points"},
                    {"name": "Constructor", "id": "constructor_name"},
                    {"name": "Nationality", "id": "nationality"}
                ],
                data=table_df.to_dict('records'),
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left', 
                    'padding': '8px 12px', 
                    'backgroundColor': card_bg, 
                    'color': text_color,
                    'border': f'1px solid {border_color}',
                    'fontSize': '13px'
                },
                style_header={
                    'backgroundColor': '#2a2a4e',
                    'color': '#ffffff',
                    'fontWeight': 'bold',
                    'padding': '10px',
                    'border': f'1px solid {border_color}'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#22223a' if theme == 'dark' else '#f8f9fa',
                        'color': text_color
                    },
                    {
                        'if': {'column_id': 'race_points'},
                        'color': '#ff6b35',
                        'fontWeight': 'bold'
                    }
                ],
                sort_action='native',
                filter_action='native',
                page_action='native'
            )
        ], id='table-container')
    ], className="table-container", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '20px', 'borderRadius': '12px'})
    
    # BUILD THE OVERVIEW PAGE
    return html.Div([
        html.H2("📊 Dataset Overview", style={'color': text_color, 'marginBottom': '20px'}),
        kpi_cards,
        
        html.Div([
            html.Div([
                html.H4("📅 Season Coverage - Unique Races per Season", style={'color': text_color, 'marginBottom': '10px'}),
                dcc.Graph(figure=fig1, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'})
        ], style={'marginBottom': '20px'}),
        
        html.Div([
            html.Div([
                html.H4("🌍 Global Circuit Distribution", style={'color': text_color, 'marginBottom': '10px'}),
                map_component
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px', 'flex': '2'}),
            html.Div([
                html.H4("🌍 Circuit Distribution Across Countries", style={'color': text_color, 'marginBottom': '10px'}),
                dcc.Graph(figure=fig2, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}),
        
        html.Div([
            html.Div([
                html.H4("🏭 Constructor Participation by Season", style={'color': text_color, 'marginBottom': '10px'}),
                dcc.Graph(figure=fig3, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'}),
            html.Div([
                html.H4("📆 Race Calendar Distribution (Unique Races)", style={'color': text_color, 'marginBottom': '10px'}),
                dcc.Graph(figure=fig4, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'})
        ], className="charts-grid"),
        
        html.Div([
            table_component
        ], style={'marginTop': '20px'}),
    ])


# ============================================================
# SLOT 3: CHAMPIONSHIP PAGE
# ============================================================
def create_championship_page(theme='dark', selected_year=None, selected_team=None):
    """Create the championship evolution page"""
    df = load_data()
    
    # Theme colors
    if theme == 'dark':
        text_color, bg_color, card_bg, border_color, chart_bg = '#ffffff', '#0d0d1a', 'rgba(26, 26, 46, 0.85)', 'rgba(255, 255, 255, 0.08)', 'rgba(0,0,0,0)'
    else:
        text_color, bg_color, card_bg, border_color, chart_bg = '#1a1a2e', '#f8f9fa', '#ffffff', '#e0e0e0', 'rgba(0,0,0,0)'
    
    available_years = sorted(df['year'].unique()) if 'year' in df.columns else [2024]
    if selected_year is None:
        selected_year = available_years[-1] if available_years else 2024
    
    year_df = df[df['year'] == selected_year] if 'year' in df.columns else df
    if selected_team and selected_team != 'All' and 'constructor_name' in year_df.columns:
        filtered_df = year_df[year_df['constructor_name'] == selected_team]
    else:
        filtered_df = year_df
    if filtered_df.empty:
        filtered_df = year_df
    
    # FIGURE 1: Championship Standings
    if 'championship_points' in filtered_df.columns and 'driver_name' in filtered_df.columns:
        temp_df = filtered_df.sort_values('round')
        all_drivers_df = temp_df.groupby('driver_name').last().reset_index()
        all_drivers_df = all_drivers_df[['driver_name', 'championship_points', 'constructor_name', 'nationality']]
        all_drivers_df = all_drivers_df.sort_values('championship_points', ascending=False)
        all_drivers_df['rank'] = range(1, len(all_drivers_df) + 1)
        top_10_df = all_drivers_df.head(10)
        
        fig1 = px.bar(
            top_10_df,
            x='driver_name',
            y='championship_points',
            color='championship_points',
            color_continuous_scale='Viridis',
            text='championship_points'
        )
        fig1.update_traces(
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>🏆 Rank: #%{customdata[0]}<br>🏆 Points: %{y:,.0f}<br>🌍 Country: %{customdata[1]}<br>🏎️ Team: %{customdata[2]}<extra></extra>',
            customdata=top_10_df[['rank', 'nationality', 'constructor_name']].values
        )
        fig1.update_layout(
            xaxis_title="Driver",
            yaxis_title="Points",
            showlegend=False,
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font_color=text_color,
            hoverlabel=dict(bgcolor=card_bg, font_color=text_color),
            height=450,
            title=f'🏆 {selected_year} Championship Standings - Top 10 Drivers'
        )
    else:
        fig1 = go.Figure()
        fig1.add_annotation(text="No championship data available", showarrow=False)
        all_drivers_df = pd.DataFrame()
    
    # FIGURE 2: Championship Progress
    if 'championship_points' in filtered_df.columns and 'round' in filtered_df.columns and 'driver_name' in filtered_df.columns:
        driver_points_total = filtered_df.groupby('driver_name')['championship_points'].max().reset_index()
        driver_points_total = driver_points_total.sort_values('championship_points', ascending=False)
        top5_drivers = driver_points_total.head(5)['driver_name'].tolist()
        top5_data = filtered_df[filtered_df['driver_name'].isin(top5_drivers)]
        
        fig2 = go.Figure()
        colors = px.colors.qualitative.Set1
        for i, driver in enumerate(top5_drivers):
            driver_data = top5_data[top5_data['driver_name'] == driver].sort_values('round')
            fig2.add_trace(go.Scatter(
                x=driver_data['round'],
                y=driver_data['championship_points'],
                mode='lines+markers',
                name=driver,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8),
                hovertemplate='<b>%{text}</b><br>Round %{x}<br>Points: %{y:,.0f}<extra></extra>',
                text=[driver] * len(driver_data)
            ))
        fig2.update_layout(
            title=f'📈 {selected_year} Championship Progress (Top 5 Drivers)',
            xaxis_title="Race Number",
            yaxis_title="Cumulative Points",
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font_color=text_color,
            hovermode='x unified',
            legend=dict(bgcolor=card_bg if theme == 'dark' else 'rgba(255,255,255,0.8)', font_color=text_color),
            xaxis=dict(tickmode='linear', tick0=1, dtick=1),
            height=400
        )
    else:
        fig2 = go.Figure()
        fig2.add_annotation(text="No championship progress data available", showarrow=False)
    
    # FIGURE 3: Year-by-Year Champions
    if 'year' in df.columns and 'championship_points' in df.columns and 'driver_name' in df.columns:
        driver_yearly_points = df.groupby(['year', 'driver_name'])['championship_points'].max().reset_index()
        yearly_champions = driver_yearly_points.loc[driver_yearly_points.groupby('year')['championship_points'].idxmax()]
        yearly_champions = yearly_champions.sort_values('year')
        
        fig3 = px.bar(
            yearly_champions,
            x='year',
            y='championship_points',
            color='driver_name',
            text='championship_points',
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig3.update_traces(
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>🏆 Champion: %{customdata[0]}<br>Points: %{y:,.0f}<extra></extra>',
            customdata=yearly_champions[['driver_name']].values
        )
        fig3.update_layout(
            xaxis_title="Year",
            yaxis_title="Champion's Points",
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font_color=text_color,
            showlegend=True,
            legend=dict(bgcolor=card_bg if theme == 'dark' else 'rgba(255,255,255,0.8)', font_color=text_color),
            title='🏆 Year-by-Year Champions (Winner\'s Points Only)',
            height=400
        )
    else:
        fig3 = go.Figure()
        fig3.add_annotation(text="No year-by-year champion data available", showarrow=False)
    
    # STATS
    total_drivers = len(filtered_df['driver_name'].unique()) if 'driver_name' in filtered_df.columns else 0
    
    if 'championship_points' in filtered_df.columns and not all_drivers_df.empty:
        top_points = all_drivers_df['championship_points'].max() if not all_drivers_df.empty else 0
        avg_points = all_drivers_df['championship_points'].mean() if not all_drivers_df.empty else 0
        max_points = top_points
        top_driver = all_drivers_df.iloc[0]['driver_name'] if not all_drivers_df.empty else 'N/A'
        active_drivers = len(all_drivers_df[all_drivers_df['championship_points'] > 0])
        total_season_points = all_drivers_df['championship_points'].sum()
        gap_to_second = top_points - (all_drivers_df.iloc[1]['championship_points'] if len(all_drivers_df) > 1 else 0)
    else:
        max_points, avg_points, active_drivers, top_points, total_season_points, gap_to_second = 0, 0, 0, 0, 0, 0
        top_driver = 'N/A'
    
    return html.Div([
        html.Div([
            html.H2([html.Span("🏆 "), "Championship Evolution"]),
            html.P("Track the championship battle throughout the season", className="text-muted mb-0"),
        ], id="app-header", style={
            "background": f"linear-gradient(120deg, {SURFACE_RAISED} 0%, {SURFACE} 70%)",
            "borderBottom": f"3px solid {ACCENT_RED}",
            "borderRadius": "14px",
            "padding": "22px 28px",
            "marginTop": "18px",
            "marginBottom": "18px",
            "boxShadow": "0 8px 24px rgba(0,0,0,0.35)"
        }),
        
        html.Div([
            html.Div([
                html.Label("📅 Select Year:", style={'color': text_color, 'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='year-selector',
                    options=[{'label': str(year), 'value': year} for year in available_years],
                    value=selected_year,
                    clearable=False,
                    style={'width': '200px', 'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'flex': '1'}),
            html.Div([
                html.Label("🔍 Filter by Team:", style={'color': text_color, 'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='championship-team-filter',
                    options=[{'label': 'All Teams', 'value': 'All'}] + [{'label': team, 'value': team} for team in df['constructor_name'].unique()],
                    value=selected_team or 'All',
                    clearable=False,
                    style={'width': '200px', 'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'flex': '1'})
        ], style={'display': 'flex', 'gap': '30px', 'marginBottom': '20px', 'flexWrap': 'wrap'}),
        
        html.Div([
            html.Div([html.H3(f"{total_drivers}", className="stat-number", style={'color': '#ff6b35'}), html.P("🏁 Total Drivers", className="stat-label", style={'color': text_color})],
                    className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([html.H3(f"{max_points:,.0f}", className="stat-number", style={'color': '#4ecdc4'}), html.P("⭐ Max Points", className="stat-label", style={'color': text_color})],
                    className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([html.H3(f"{avg_points:.1f}", className="stat-number", style={'color': '#ffe66d'}), html.P("📊 Average Points", className="stat-label", style={'color': text_color})],
                    className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([html.H3(f"{active_drivers}", className="stat-number", style={'color': '#ff6b6b'}), html.P("✅ Active Drivers", className="stat-label", style={'color': text_color})],
                    className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([html.H3(f"{top_driver}", className="stat-number", style={'color': '#ffd93d', 'fontSize': '20px'}), html.P(f"🏆 Leader with {top_points:,.0f} pts", className="stat-label", style={'color': text_color})],
                    className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'})
        ], className="stats-grid"),
        
        html.Div([
            html.Div([dcc.Graph(figure=fig1, config={'displayModeBar': True})], 
                     className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'grid-column': 'span 2'}),
            html.Div([
                dcc.Graph(figure=fig2, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([
                dcc.Graph(figure=fig3, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'})
        ], className="charts-grid", style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}),
        
        html.Div([
            html.H3("🏆 Full Driver Standings", className="insights-title", style={'color': text_color}),
            html.Div([
                dash_table.DataTable(
                    id='top-drivers-table',
                    columns=[
                        {"name": "Rank", "id": "rank"},
                        {"name": "Driver", "id": "driver_name"},
                        {"name": "Cumulative Points", "id": "championship_points"},
                        {"name": "Constructor", "id": "constructor_name"},
                        {"name": "Nationality", "id": "nationality"}
                    ],
                    data=all_drivers_df.to_dict('records') if 'all_drivers_df' in locals() and not all_drivers_df.empty else [],
                    page_size=15,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left', 
                        'padding': '10px', 
                        'backgroundColor': card_bg, 
                        'color': text_color,
                        'border': f'1px solid {border_color}',
                        'fontSize': '14px'
                    },
                    style_header={
                        'backgroundColor': '#2a2a4e',
                        'color': '#ffffff',
                        'fontWeight': 'bold',
                        'padding': '10px',
                        'border': f'1px solid {border_color}'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#22223a' if theme == 'dark' else '#f8f9fa',
                            'color': text_color
                        },
                        {
                            'if': {'column_id': 'championship_points'},
                            'color': '#ff6b35',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'column_id': 'rank', 'filter_query': '{rank} = 1'},
                            'color': '#ffd93d',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'column_id': 'rank', 'filter_query': '{rank} = 2'},
                            'color': '#c0c0c0',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'column_id': 'rank', 'filter_query': '{rank} = 3'},
                            'color': '#cd7f32',
                            'fontWeight': 'bold'
                        }
                    ],
                    sort_action='native'
                )
            ], className="table-container", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '20px', 'borderRadius': '12px'})
        ], style={'marginTop': '20px'}),
        
        html.Div([
            html.H3("💡 Key Insights", className="insights-title", style={'color': text_color}),
            html.Div([
                html.Div([
                    html.Span("🏆 ", style={'fontSize': '20px'}),
                    html.Span(f"{selected_year} Champion: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{top_driver}", style={'color': '#ffd93d', 'fontWeight': 'bold'}),
                    html.Span(f" ({top_points:,.0f} points)", style={'color': text_color})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
                html.Div([
                    html.Span("📊 ", style={'fontSize': '20px'}),
                    html.Span("Total Points in Season: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{total_season_points:,.0f}", style={'color': text_color})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
                html.Div([
                    html.Span("👥 ", style={'fontSize': '20px'}),
                    html.Span("Active Drivers: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{active_drivers} out of {total_drivers}", style={'color': text_color})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
                html.Div([
                    html.Span("📈 ", style={'fontSize': '20px'}),
                    html.Span("Points Gap to 2nd: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{gap_to_second:,.0f} pts", style={'color': text_color})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'})
            ], className="insights-grid")
        ], className="insights-container", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'})
    ])


# ============================================================
# SLOT 4: DRIVER PERFORMANCE PAGE
# ============================================================
class DriverDataEngine:
    def __init__(self, df):
        self.df = df
        self._sanitize_data()

    def _sanitize_data(self):
        required_cols = ['year', 'round', 'grid', 'positionOrder', 'points', 'positions_gained', 'driver_name', 'status']
        for col in ['year', 'round', 'grid', 'positionOrder', 'positions_gained']:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        self.df['points'] = pd.to_numeric(self.df['points'], errors='coerce').fillna(0.0)
        self.df = self.df.dropna(subset=['year', 'round', 'grid', 'positionOrder', 'positions_gained'])
        for col in ['year', 'round', 'grid', 'positionOrder', 'positions_gained']:
            self.df[col] = self.df[col].astype(int)
        if 'status' not in self.df.columns:
            self.df['status'] = "Unknown"
        else:
            self.df['status'] = self.df['status'].fillna("Unknown").astype(str)
        if 'lap_consistency_score' not in self.df.columns:
            self.df['lap_consistency_score'] = 1 / (self.df.get('lap_std', pd.Series(0)).fillna(0) + 1)
        self.df['is_dnf'] = pd.to_numeric(self.df.get('is_dnf', pd.Series(0)), errors='coerce').fillna(0).astype(int)

    def get_unique_drivers(self):
        return sorted(self.df['driver_name'].dropna().unique())

    def get_season_range_label(self):
        years = self.df['year'].unique()
        return f"{int(years.min())}-{int(years.max())}" if len(years) > 0 else "All Seasons"

    def get_available_seasons(self, driver_name=None):
        seasons = self.df[self.df['driver_name'] == driver_name]['year'].unique() if driver_name else self.df['year'].unique()
        return sorted(int(s) for s in seasons)

    def get_historical_trends(self, driver_name, season_filter='all'):
        if not driver_name:
            return pd.DataFrame(columns=['timeline_label', 'grid', 'positionOrder', 'status'])
        driver_df = self.df[self.df['driver_name'] == driver_name].copy()
        if str(season_filter).lower() != 'all':
            driver_df = driver_df[driver_df['year'] == int(season_filter)].sort_values(by='round')
            if not driver_df.empty:
                driver_df['timeline_label'] = "Rd " + driver_df['round'].astype(str) + ": " + driver_df['race_name']
        else:
            driver_df = driver_df.sort_values(by=['year', 'round'])
            if not driver_df.empty:
                driver_df['timeline_label'] = driver_df['year'].astype(str) + " R" + driver_df['round'].astype(str)
        return driver_df

    def get_kpi_summary(self, driver_name, season_filter='all'):
        trends = self.get_historical_trends(driver_name, season_filter)
        if trends.empty:
            return {'pts': '0', 'avg_fin': '-', 'best_fin': '-', 'dnf_rate': '0%'}
        return {
            'pts': f"{trends['points'].sum():g}",
            'avg_fin': f"{trends['positionOrder'].mean():.1f}",
            'best_fin': f"P{int(trends['positionOrder'].min())}",
            'dnf_rate': f"{(trends['is_dnf'].sum() / len(trends)) * 100:.1f}%"
        }

    def get_dnf_summary(self, driver_name, season_filter='all'):
        trends = self.get_historical_trends(driver_name, season_filter)
        total = len(trends)
        return {'total': total, 'dnf_count': int(trends['is_dnf'].sum()), 'dnf_rate': (int(trends['is_dnf'].sum()) / total * 100) if total else 0.0}

    def get_classified_finishes(self, driver_name, season_filter='all'):
        trends = self.get_historical_trends(driver_name, season_filter)
        return trends[trends['is_dnf'] == 0] if not trends.empty else trends

    def generate_normalized_radar_metrics(self, selected_drivers, season_filter='all'):
        working_df = self.df.copy()
        if str(season_filter).lower() != 'all':
            working_df = working_df[working_df['year'] == int(season_filter)]
        if working_df.empty:
            return pd.DataFrame()
        aggregated = working_df.groupby('driver_name').agg(
            avg_grid=('grid', 'mean'), avg_finish=('positionOrder', 'mean'),
            avg_gained=('positions_gained', 'mean'), avg_pts=('points', 'mean'),
            consistency=('lap_consistency_score', 'mean')
        ).reset_index()
        if aggregated.empty:
            return pd.DataFrame()
        max_vals, min_vals = aggregated.max(numeric_only=True), aggregated.min(numeric_only=True)
        def safe_scale(val, col, invert=False):
            if max_vals[col] == min_vals[col]:
                return 50.0
            norm = (val - min_vals[col]) / (max_vals[col] - min_vals[col])
            return (1.0 - norm) * 100 if invert else norm * 100
        return pd.DataFrame([{
            'driver_name': driver,
            'Qualifying Pace': safe_scale(aggregated[aggregated['driver_name']==driver].iloc[0]['avg_grid'], 'avg_grid', True),
            'Race Craft': safe_scale(aggregated[aggregated['driver_name']==driver].iloc[0]['avg_finish'], 'avg_finish', True),
            'Overtaking Efficiency': safe_scale(aggregated[aggregated['driver_name']==driver].iloc[0]['avg_gained'], 'avg_gained'),
            'Scoring Capacity': safe_scale(aggregated[aggregated['driver_name']==driver].iloc[0]['avg_pts'], 'avg_pts'),
            'Lap Consistency': safe_scale(aggregated[aggregated['driver_name']==driver].iloc[0]['consistency'], 'consistency')
        } for driver in selected_drivers if driver in aggregated['driver_name'].values])


def create_driver_performance_page(theme='dark'):
    """Create the Driver Performance page"""
    df = load_data()
    engine = DriverDataEngine(df)
    
    if theme == 'dark':
        text_color, bg_color, card_bg, border_color = '#ffffff', '#0d0d1a', 'rgba(26, 26, 46, 0.85)', 'rgba(255, 255, 255, 0.08)'
        carbon, panel, hairline, ink, muted, amber, amber_dim, grid_line = '#15171C', '#1B1E26', 'rgba(237,233,225,0.10)', '#FFFFFF', '#C7CCD6', '#FFB100', 'rgba(255,177,0,0.18)', 'rgba(237,233,225,0.06)'
    else:
        text_color, bg_color, card_bg, border_color = '#1a1a2e', '#f8f9fa', '#ffffff', '#e0e0e0'
        carbon, panel, hairline, ink, muted, amber, amber_dim, grid_line = '#f8f9fa', '#ffffff', 'rgba(0,0,0,0.10)', '#1a1a2e', '#666666', '#ff6b35', 'rgba(255,107,53,0.18)', 'rgba(0,0,0,0.06)'
    
    unique_drivers = engine.get_unique_drivers()
    season_range_label = engine.get_season_range_label()
    
    # Sidebar Controls
    sidebar_controls = dbc.Card(
        dbc.CardBody([
            html.Div([html.I(className="fa fa-flag-checkered me-2"), "Race Control"], 
                    className="text-uppercase small fw-bold mb-4", 
                    style={"color": ACCENT_RED, "letterSpacing": "1px", "fontSize": "0.85rem", 
                          "borderBottom": f"1px solid {BORDER}", "paddingBottom": "10px"}),
            
            html.H6([html.I(className="fa fa-user me-2", style={"color": ACCENT_CYAN}), "TARGET FOCUS DRIVER"], 
                   className="text-uppercase fw-bold mb-2", 
                   style={"fontSize": "0.75rem", "color": TEXT_PRIMARY}),
            dcc.Dropdown(id='driver-1-select', 
                        options=[{'label': n, 'value': n} for n in unique_drivers], 
                        value='Lewis Hamilton' if 'Lewis Hamilton' in unique_drivers else (unique_drivers[0] if unique_drivers else None),
                        clearable=False),
            html.Br(),
            
            html.H6([html.I(className="fa fa-user-plus me-2", style={"color": ACCENT_CYAN}), "COMPARE DRIVER (OPTIONAL)"], 
                   className="text-uppercase fw-bold mb-2", 
                   style={"fontSize": "0.75rem", "color": TEXT_PRIMARY}),
            dcc.Dropdown(id='driver-2-select', 
                        options=[{'label': '-- None --', 'value': ''}] + [{'label': n, 'value': n} for n in unique_drivers], 
                        value=''),
            html.Br(),
            
            html.H6([html.I(className="fa fa-calendar-alt me-2", style={"color": ACCENT_CYAN}), "ACTIVE SEASON CONSTRAINT"], 
                   className="text-uppercase fw-bold mb-2", 
                   style={"fontSize": "0.75rem", "color": TEXT_PRIMARY}),
            dcc.Dropdown(id='season-select', value='all', clearable=False),
            html.Br(),
            
            html.H6([html.I(className="fa fa-chart-pie me-2", style={"color": ACCENT_CYAN}), "DISTRIBUTION VIEW TYPE"], 
                   className="text-uppercase fw-bold mb-2", 
                   style={"fontSize": "0.75rem", "marginTop": "5px", "color": TEXT_PRIMARY}),
            html.Div(
                dbc.RadioItems(
                    id='distribution-view-toggle',
                    className="btn-group-toggle",
                    inputClassName="btn-check",
                    labelClassName="btn",
                    labelCheckedClassName="active",
                    options=[{'label': 'Box Plot', 'value': 'box'}, {'label': 'Violin Plot', 'value': 'violin'}],
                    value='box',
                )
            )
        ]), className="mb-3", style={
            "background": f"linear-gradient(145deg, {SURFACE_RAISED}, {SURFACE})", 
            "border": f"1px solid {BORDER}", 
            "borderTop": f"4px solid {ACCENT_RED}", 
            "borderRadius": "14px", 
            "boxShadow": "0 10px 30px rgba(0,0,0,0.4)", 
            "zIndex": 50, 
            "overflow": "visible"
        }
    )
    
    def kpi_card(title, id_val, icon):
        return dbc.Col(
            html.Div(className="dash-graph-card", style={'padding': '16px'}, children=[
                html.Div([html.I(className=f"fa {icon} me-2"), title], 
                        className="text-muted small text-uppercase fw-bold mb-1", 
                        style={'letterSpacing': '0.5px', 'color': ACCENT_CYAN}),
                html.H3(id=id_val, className="mb-0 telemetry-value fw-bold")
            ]), width=6, lg=3
        )
    
    return html.Div([
        html.Div([
            html.H2([html.Span("🏎️ "), "Driver Performance Explorer"]),
            html.P("Interactive analysis of driver race execution, consistency, and comparative performance metrics.", 
                   className="text-muted mb-0"),
        ], id="app-header", style={
            "background": f"linear-gradient(120deg, {SURFACE_RAISED} 0%, {SURFACE} 70%)",
            "borderBottom": f"3px solid {ACCENT_RED}",
            "borderRadius": "14px",
            "padding": "22px 28px",
            "marginTop": "18px",
            "marginBottom": "18px",
            "boxShadow": "0 8px 24px rgba(0,0,0,0.35)"
        }),
        
        dbc.Row([
            dbc.Col(sidebar_controls, width=12, lg=3),
            dbc.Col(html.Div(id="driver-main-dashboard-wrapper", children=[
                dbc.Row([
                    kpi_card("Total Pts", "kpi-points", "fa-flag-checkered"),
                    kpi_card("Avg Finish", "kpi-avg-finish", "fa-crosshairs"),
                    kpi_card("Best Finish", "kpi-best-finish", "fa-trophy"),
                    kpi_card("DNF Rate", "kpi-dnf-rate", "fa-car-burst")
                ], className="mb-1"),
                html.Div(className='dash-graph-card', children=[dcc.Graph(id='line-trend-chart', config={'displaylogo': False})]),
                dbc.Row([
                    dbc.Col(html.Div(className='dash-graph-card', children=[dcc.Graph(id='box-consistency-chart', config={'displaylogo': False})]), width=12, lg=7),
                    dbc.Col(html.Div(className='dash-graph-card', children=[dcc.Graph(id='radar-summary-chart', config={'displaylogo': False})]), width=12, lg=5)
                ])
            ]), width=12, lg=9)
        ])
    ])


# ============================================================
# SLOT 5: CONSTRUCTOR EVOLUTION PAGE
# ============================================================
def aggregate_constructor_season(data):
    grouped = (
        data.groupby(["year", "constructor_name"])
        .agg(
            season_points=("points", "sum"),
            races=("raceId", "nunique"),
            entries=("resultId", "count"),
            wins=("is_winner", "sum"),
            podiums=("is_podium", "sum"),
            points_finishes=("is_points_finish", "sum"),
            dnfs=("is_dnf", "sum"),
            finishes=("is_dnf", lambda x: (x == 0).sum()),
            avg_finish=("positionOrder", "mean"),
            avg_grid=("grid", "mean"),
            avg_positions_gained=("positions_gained", "mean"),
        )
        .reset_index()
    )
    grouped["dnf_rate_pct"] = (grouped["dnfs"] / (grouped["dnfs"] + grouped["finishes"]) * 100).round(1)
    grouped["win_rate_pct"] = (grouped["wins"] / grouped["entries"] * 100).round(1)
    grouped["podium_rate_pct"] = (grouped["podiums"] / grouped["entries"] * 100).round(1)
    grouped["points_per_entry"] = (grouped["season_points"] / grouped["entries"]).round(2)
    return grouped


def aggregate_points_share(data):
    season_points = data.groupby(["year", "constructor_name"])["points"].sum().reset_index()
    season_totals = season_points.groupby("year")["points"].transform("sum")
    season_points["points_share_pct"] = (season_points["points"] / season_totals * 100).round(2)
    season_points["season_rank"] = season_points.groupby("year")["points"].rank(method="min", ascending=False).astype(int)
    return season_points


def aggregate_constructor_career(data):
    grouped = (
        data.groupby("constructor_name")
        .agg(
            total_points=("points", "sum"),
            seasons_active=("year", "nunique"),
            total_entries=("resultId", "count"),
            total_wins=("is_winner", "sum"),
            total_podiums=("is_podium", "sum"),
            total_dnfs=("is_dnf", "sum"),
            avg_finish=("positionOrder", "mean"),
            championship_titles=("championship_wins", "sum"),
        )
        .reset_index()
        .sort_values("total_points", ascending=False)
    )
    grouped["win_rate_pct"] = (grouped["total_wins"] / grouped["total_entries"] * 100).round(1)
    grouped["dnf_rate_pct"] = (grouped["total_dnfs"] / grouped["total_entries"] * 100).round(1)
    grouped["points_per_season"] = (grouped["total_points"] / grouped["seasons_active"]).round(1)
    return grouped.round(2)


def aggregate_reliability_by_status(data):
    dnf_only = data[data["is_dnf"] == 1]
    grouped = (
        dnf_only.groupby(["year", "constructor_name", "status"])
        .size()
        .reset_index(name="count")
        .sort_values(["year", "constructor_name", "count"], ascending=[True, True, False])
    )
    return grouped


def aggregate_year_over_year_change(data):
    season_points = aggregate_points_share(data)[["year", "constructor_name", "points"]]
    season_points = season_points.sort_values(["constructor_name", "year"])
    season_points["prev_year_points"] = season_points.groupby("constructor_name")["points"].shift(1)
    season_points["points_delta"] = season_points["points"] - season_points["prev_year_points"]
    prev = season_points["prev_year_points"].astype(float)
    prev_safe = prev.where(prev != 0)
    season_points["pct_change"] = ((season_points["points_delta"].astype(float) / prev_safe) * 100).round(1)
    return season_points.round(2)


def create_constructor_page(theme='dark'):
    """Create the Constructor Evolution page"""
    df = load_data()
    
    # Theme colors
    if theme == 'dark':
        text_color, bg_color, card_bg, border_color = '#ffffff', '#0d0d1a', 'rgba(26, 26, 46, 0.85)', 'rgba(255, 255, 255, 0.08)'
        carbon, panel, hairline, ink, muted, amber, amber_dim, grid_line = '#15171C', '#1B1E26', 'rgba(237,233,225,0.10)', '#FFFFFF', '#C7CCD6', '#FFB100', 'rgba(255,177,0,0.18)', 'rgba(237,233,225,0.06)'
    else:
        text_color, bg_color, card_bg, border_color = '#1a1a2e', '#f8f9fa', '#ffffff', '#e0e0e0'
        carbon, panel, hairline, ink, muted, amber, amber_dim, grid_line = '#f8f9fa', '#ffffff', 'rgba(0,0,0,0.10)', '#1a1a2e', '#666666', '#ff6b35', 'rgba(255,107,53,0.18)', 'rgba(0,0,0,0.06)'
    
    # Pre-aggregate
    constructor_season = aggregate_constructor_season(df)
    points_share = aggregate_points_share(df)
    constructor_career = aggregate_constructor_career(df)
    reliability_by_status = aggregate_reliability_by_status(df)
    year_over_year = aggregate_year_over_year_change(df)
    
    all_constructors = sorted(constructor_season["constructor_name"].unique())
    default_constructors = [c for c in ["Mercedes", "Red Bull", "Ferrari", "McLaren"] if c in all_constructors] or all_constructors[:4]
    year_min, year_max = int(df["year"].min()), int(df["year"].max())
    
    metric_options = [
        {"label": "Season Points", "value": "season_points"},
        {"label": "Cumulative Points", "value": "cumulative"},
        {"label": "Points Share %", "value": "points_share_pct"},
    ]
    
    controls = dbc.Card(
        dbc.CardBody([
            html.Div([html.I(className="fa fa-sliders-h me-2"), "Filters"],
                    className="text-uppercase small fw-bold mb-3",
                    style={"color": ACCENT_RED, "letterSpacing": "0.5px"}),
            html.H6("Constructors", className="text-uppercase text-muted mb-2"),
            dcc.Dropdown(
                id="constructor-select",
                options=[{"label": c, "value": c} for c in all_constructors],
                value=default_constructors,
                multi=True,
                placeholder="Select constructors to compare",
            ),
            html.Br(),
            html.H6("Season Range", className="text-uppercase text-muted mb-2"),
            dcc.RangeSlider(
                id="year-slider-constructor",
                min=year_min,
                max=year_max,
                step=1,
                value=[year_min, year_max],
                marks={y: {"label": str(y), "style": {"color": "#9AA0AA", "fontWeight": "500"}} for y in range(year_min, year_max + 1)},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
            html.Br(),
            html.H6("Metric (line chart)", className="text-uppercase text-muted mb-2"),
            dcc.RadioItems(
                id="metric-radio",
                options=metric_options,
                value="season_points",
                inline=True,
                inputStyle={"marginRight": "6px", "marginLeft": "12px"},
            ),
            html.Br(),
            dbc.ButtonGroup([
                dbc.Button("Reset Filters", id="btn-reset-constructor", color="secondary", size="sm"),
                dbc.Button([html.I(className="fa fa-download me-1"), "Export CSV"],
                           id="btn-download-constructor", color="primary", size="sm"),
            ]),
            dcc.Download(id="download-csv-constructor"),
        ]),
        className="mb-3",
        style={"background": f"linear-gradient(145deg, {SURFACE_RAISED}, {SURFACE})", 
               "border": f"1px solid {BORDER}", 
               "borderTop": f"4px solid {ACCENT_RED}", 
               "borderRadius": "14px", 
               "boxShadow": "0 10px 30px rgba(0,0,0,0.4)"}
    )
    
    def style_fig(fig):
        fig.update_layout(
            template="plotly_dark",
            font=dict(family=FONT_FAMILY, size=13, color="#E6E8EB"),
            title_font=dict(size=17, family=FONT_FAMILY, color="#F5F6F7"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=50, r=30, t=60, b=40),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)"),
            transition={"duration": 400},
        )
        fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER)
        fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER)
        return fig
    
    return html.Div([
        html.Div([
            html.H2([html.Span("🏎️ "), "Constructor Evolution"]),
            html.P("Module owner: Snehasish Haldar — Team improvement, decline, dominance, and reliability.", 
                   className="text-muted mb-0"),
        ], id="app-header", style={
            "background": f"linear-gradient(120deg, {SURFACE_RAISED} 0%, {SURFACE} 70%)",
            "borderBottom": f"3px solid {ACCENT_RED}",
            "borderRadius": "14px",
            "padding": "22px 28px",
            "marginTop": "18px",
            "marginBottom": "18px",
            "boxShadow": "0 8px 24px rgba(0,0,0,0.35)"
        }),
        dbc.Row([
            dbc.Col(controls, width=12, lg=3),
            dbc.Col([
                dcc.Tabs(
                    id="view-tabs-constructor",
                    value="tab-charts",
                    children=[
                        dcc.Tab(label="Charts", value="tab-charts"),
                        dcc.Tab(label="Drilldown", value="tab-drilldown"),
                        dcc.Tab(label="Tables", value="tab-tables"),
                    ],
                ),
                html.Div([
                    html.Div(id="panel-charts-constructor", style={"display": "block"}, children=[
                        html.Div(id="kpi-cards-constructor", className="mb-3"),
                        html.Div(dcc.Loading(dcc.Graph(id="line-chart-constructor", config={"displaylogo": False})), className="dash-graph-card"),
                        html.Div(dcc.Loading(dcc.Graph(id="bar-chart-constructor", config={"displaylogo": False})), className="dash-graph-card"),
                        html.Div(dcc.Loading(dcc.Graph(id="area-chart-constructor", config={"displaylogo": False})), className="dash-graph-card"),
                        dbc.Card(dbc.CardBody(id="insights-constructor"), className="mt-3"),
                    ]),
                    html.Div(id="panel-drilldown-constructor", style={"display": "none"}, children=[
                        html.Div("Click a point on the line chart (Charts tab) to jump straight to it here.", className="text-muted mb-3"),
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(id="drilldown-year-select", options=[{"label": str(y), "value": y} for y in range(year_min, year_max + 1)], placeholder="Select a season"),
                                width=12, lg=4,
                            ),
                            dbc.Col(
                                dcc.Dropdown(id="drilldown-constructor-select", options=[{"label": c, "value": c} for c in all_constructors], placeholder="Select a constructor"),
                                width=12, lg=4,
                            ),
                        ], className="mb-3 g-2"),
                        html.H5(id="drilldown-title", children="No point selected yet"),
                        dbc.Row([
                            dbc.Col(
                                dash_table.DataTable(id="drilldown-table", columns=[{"name": "Year", "id": "year"}, {"name": "Constructor", "id": "constructor_name"}, {"name": "Status", "id": "status"}, {"name": "Count", "id": "count"}], data=[], page_size=10, sort_action="native", filter_action="native", style_table={"overflowX": "auto"}, style_cell={"backgroundColor": SURFACE_RAISED, "color": "white", "border": f"1px solid {BORDER}", "fontFamily": FONT_FAMILY}, style_header={"backgroundColor": SURFACE, "fontWeight": "bold", "border": f"1px solid {BORDER}"}),
                                width=12, lg=6,
                            ),
                            dbc.Col(
                                html.Div(dcc.Loading(dcc.Graph(id="drilldown-pie-constructor", config={"displaylogo": False})), className="dash-graph-card"),
                                width=12, lg=6,
                            ),
                        ])
                    ]),
                    html.Div(id="panel-tables-constructor", style={"display": "none"}, children=[
                        html.H5("All-time Constructor Leaderboard"),
                        dash_table.DataTable(
                            id="career-table",
                            columns=[{"name": c, "id": c} for c in constructor_career.columns],
                            data=constructor_career.to_dict("records"),
                            page_size=10,
                            sort_action="native",
                            filter_action="native",
                            style_table={"overflowX": "auto"},
                            style_cell={"backgroundColor": SURFACE_RAISED, "color": "white", "border": f"1px solid {BORDER}", "fontFamily": FONT_FAMILY},
                            style_header={"backgroundColor": SURFACE, "fontWeight": "bold", "border": f"1px solid {BORDER}"},
                        ),
                        html.Br(),
                        html.H5("Year-over-Year Points Change"),
                        dash_table.DataTable(
                            id="yoy-table-constructor",
                            columns=[{"name": c, "id": c} for c in year_over_year.columns],
                            data=[],
                            page_size=10,
                            sort_action="native",
                            filter_action="native",
                            style_table={"overflowX": "auto"},
                            style_cell={"backgroundColor": SURFACE_RAISED, "color": "white", "border": f"1px solid {BORDER}", "fontFamily": FONT_FAMILY},
                            style_header={"backgroundColor": SURFACE, "fontWeight": "bold", "border": f"1px solid {BORDER}"},
                        ),
                    ]),
                ], className="mt-3"),
            ], width=12, lg=9),
        ]),
        html.Hr(style={"borderColor": BORDER}),
        html.Small(
            "Chart justification: Line charts best convey temporal trends in constructor points. Stacked bars show finish vs DNF composition. Area charts express dominance share continuously.",
            className="text-muted",
        ),
        html.Div(id="resize-trigger-constructor", style={"display": "none"}),
    ])


# ============================================================
# SLOT 6: QUALIFYING VS RACE PAGE - UPDATED WITH FILTERS
# ============================================================
def create_qualifying_page(theme='dark'):
    """Create the Qualifying vs Race page with filters"""
    df = load_data()
    
    # Theme colors
    if theme == 'dark':
        text_color, bg_color, card_bg, border_color = '#ffffff', '#0d0d1a', 'rgba(26, 26, 46, 0.85)', 'rgba(255, 255, 255, 0.08)'
        carbon, panel, hairline, ink, muted, amber, amber_dim, grid_line = '#15171C', '#1B1E26', 'rgba(237,233,225,0.10)', '#FFFFFF', '#C7CCD6', '#FFB100', 'rgba(255,177,0,0.18)', 'rgba(237,233,225,0.06)'
    else:
        text_color, bg_color, card_bg, border_color = '#1a1a2e', '#f8f9fa', '#ffffff', '#e0e0e0'
        carbon, panel, hairline, ink, muted, amber, amber_dim, grid_line = '#f8f9fa', '#ffffff', 'rgba(0,0,0,0.10)', '#1a1a2e', '#666666', '#ff6b35', 'rgba(255,107,53,0.18)', 'rgba(0,0,0,0.06)'
    
    # Get unique values for filters
    available_years = sorted(df['year'].unique()) if 'year' in df.columns else []
    available_teams = sorted(df['constructor_name'].unique()) if 'constructor_name' in df.columns else []
    
    # Clean data for qualifying analysis
    df_clean = df[(df['grid'] >= 1) & (df['grid'] <= 20) &
                  (df['positionOrder'] >= 1) & (df['positionOrder'] <= 20)].copy()
    
    # Add jittered columns for better visualization
    np.random.seed(42)
    df_clean['grid_jittered'] = df_clean['grid'] + np.random.uniform(-0.15, 0.15, len(df_clean))
    df_clean['position_jittered'] = df_clean['positionOrder'] + np.random.uniform(-0.15, 0.15, len(df_clean))
    
    # Customdata for hover
    df_clean['customdata'] = list(np.stack((
        df_clean['year'].astype(str), df_clean['race_name'],
        df_clean['grid'].astype(str), df_clean['positionOrder'].astype(str),
        df_clean['positions_gained'].astype(str), df_clean['status']
    ), axis=-1))
    
    # F1 Team Colors
    f1_team_colors = {
        'Ferrari': '#DC0000', 'Red Bull': '#3671C6', 'Mercedes': '#27F4D2',
        'McLaren': '#FF8000', 'Aston Martin': '#00A19C', 'Alpine F1 Team': '#FF87BC',
        'Renault': '#FFF500', 'Racing Point': '#F596C8', 'AlphaTauri': '#5E8FAA',
        'Toro Rosso': '#469BFF', 'Sauber': '#52E252', 'RB F1 Team': '#6692FF',
        'Alfa Romeo': '#C92D4B', 'Williams': '#64C4FF', 'Haas F1 Team': '#B6BABD'
    }
    
    unique_teams = sorted([team for team in f1_team_colors.keys() if team in df_clean['constructor_name'].unique()])
    min_year, max_year = int(df_clean['year'].min()), int(df_clean['year'].max())
    
    # ============================================================
    # BUILD SCATTER PLOT (with filters applied via callback)
    # ============================================================
    
    # ============================================================
    # BUILD PAGE WITH FILTERS
    # ============================================================
    return html.Div([
        html.Div([
            html.H2([html.Span("⚡ "), "Qualifying vs Race"]),
            html.P("Grid position vs. finishing position — how often does qualifying decide the race?", 
                   className="text-muted mb-0"),
        ], id="app-header", style={
            "background": f"linear-gradient(120deg, {SURFACE_RAISED} 0%, {SURFACE} 70%)",
            "borderBottom": f"3px solid {ACCENT_RED}",
            "borderRadius": "14px",
            "padding": "22px 28px",
            "marginTop": "18px",
            "marginBottom": "18px",
            "boxShadow": "0 8px 24px rgba(0,0,0,0.35)"
        }),
        
        # ============================================================
        # FILTERS
        # ============================================================
        html.Div([
            html.Div([
                html.Label("📅 Season:", style={'color': text_color, 'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='qualifying-year-filter',
                    options=[{'label': 'All Years', 'value': 'all'}] + [{'label': str(y), 'value': y} for y in available_years],
                    value='all',
                    clearable=False,
                    style={'width': '200px', 'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginRight': '20px'}),
            
            html.Div([
                html.Label("🏭 Team:", style={'color': text_color, 'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='qualifying-team-filter',
                    options=[{'label': 'All Teams', 'value': 'all'}] + [{'label': team, 'value': team} for team in available_teams],
                    value='all',
                    clearable=False,
                    style={'width': '250px', 'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '15px', 'marginBottom': '20px'}),
        
        # ============================================================
        # CHARTS - VERTICAL LAYOUT
        # ============================================================
        html.Div([
            # Chart 1: Scatter Plot (Full Width)
            html.Div([
                dcc.Loading(
                    dcc.Graph(id='qualifying-scatter-plot', config={'displayModeBar': True})
                )
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px', 'marginBottom': '20px'}),
            
            # Chart 2: Heatmap (Full Width)
            html.Div([
                dcc.Loading(
                    dcc.Graph(id='qualifying-heatmap', config={'displayModeBar': True})
                )
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px', 'marginBottom': '20px'}),
            
            # Chart 3: Correlation Matrix (Full Width)
            html.Div([
                dcc.Loading(
                    dcc.Graph(id='qualifying-correlation', config={'displayModeBar': True})
                )
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px', 'marginBottom': '20px'})
        ]),
        
        # ============================================================
        # KEY INSIGHTS
        # ============================================================
        html.Div([
            html.H3("💡 Key Insights", className="insights-title", style={'color': text_color}),
            html.Div([
                html.Div(id='qualifying-insight-1', className="insight-item", 
                        style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '12px 15px', 'borderRadius': '8px'}),
                html.Div(id='qualifying-insight-2', className="insight-item", 
                        style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '12px 15px', 'borderRadius': '8px'}),
                html.Div(id='qualifying-insight-3', className="insight-item", 
                        style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '12px 15px', 'borderRadius': '8px'}),
                html.Div(id='qualifying-insight-4', className="insight-item", 
                        style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '12px 15px', 'borderRadius': '8px'})
            ], className="insights-grid")
        ], className="insights-container", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '20px'})
    ])


# ============================================================
# QUALIFYING VS RACE CALLBACKS
# ============================================================
def register_qualifying_callbacks(app):
    
    @app.callback(
        [Output('qualifying-scatter-plot', 'figure'),
         Output('qualifying-heatmap', 'figure'),
         Output('qualifying-correlation', 'figure'),
         Output('qualifying-insight-1', 'children'),
         Output('qualifying-insight-2', 'children'),
         Output('qualifying-insight-3', 'children'),
         Output('qualifying-insight-4', 'children')],
        [Input('qualifying-year-filter', 'value'),
         Input('qualifying-team-filter', 'value')],
        [State('theme-store', 'data')]
    )
    def update_qualifying_charts(year_filter, team_filter, theme):
        df = load_data()
        
        # Theme colors
        if theme == 'dark':
            carbon, panel, grid_line, ink, muted, amber = '#15171C', '#1B1E26', 'rgba(237,233,225,0.06)', '#FFFFFF', '#C7CCD6', '#FFB100'
        else:
            carbon, panel, grid_line, ink, muted, amber = '#f8f9fa', '#ffffff', 'rgba(0,0,0,0.06)', '#1a1a2e', '#666666', '#ff6b35'
        
        # Clean data
        df_clean = df[(df['grid'] >= 1) & (df['grid'] <= 20) &
                      (df['positionOrder'] >= 1) & (df['positionOrder'] <= 20)].copy()
        
        # Apply year filter
        if year_filter != 'all':
            df_clean = df_clean[df_clean['year'] == year_filter]
        
        # Apply team filter
        if team_filter != 'all':
            df_clean = df_clean[df_clean['constructor_name'] == team_filter]
        
        # Add jittered columns
        np.random.seed(42)
        df_clean['grid_jittered'] = df_clean['grid'] + np.random.uniform(-0.15, 0.15, len(df_clean))
        df_clean['position_jittered'] = df_clean['positionOrder'] + np.random.uniform(-0.15, 0.15, len(df_clean))
        
        df_clean['customdata'] = list(np.stack((
            df_clean['year'].astype(str), df_clean['race_name'],
            df_clean['grid'].astype(str), df_clean['positionOrder'].astype(str),
            df_clean['positions_gained'].astype(str), df_clean['status']
        ), axis=-1))
        
        # F1 Team Colors
        f1_team_colors = {
            'Ferrari': '#DC0000', 'Red Bull': '#3671C6', 'Mercedes': '#27F4D2',
            'McLaren': '#FF8000', 'Aston Martin': '#00A19C', 'Alpine F1 Team': '#FF87BC',
            'Renault': '#FFF500', 'Racing Point': '#F596C8', 'AlphaTauri': '#5E8FAA',
            'Toro Rosso': '#469BFF', 'Sauber': '#52E252', 'RB F1 Team': '#6692FF',
            'Alfa Romeo': '#C92D4B', 'Williams': '#64C4FF', 'Haas F1 Team': '#B6BABD'
        }
        
        unique_teams = sorted([team for team in f1_team_colors.keys() if team in df_clean['constructor_name'].unique()])
        
        # ============================================================
        # SCATTER PLOT
        # ============================================================
        fig_scatter = go.Figure()
        fig_scatter.add_shape(type="line", layer="below", x0=1, y0=1, x1=20, y1=20,
                             line=dict(color="rgba(237,233,225,0.22)", width=1.5, dash="dash"))
        
        for team in unique_teams[:10]:
            team_df = df_clean[df_clean['constructor_name'] == team]
            fig_scatter.add_trace(go.Scatter(
                x=team_df['grid_jittered'], y=team_df['position_jittered'],
                mode='markers', name=team,
                marker=dict(color=f1_team_colors.get(team, '#FFFFFF'), size=9, opacity=0.88,
                           line=dict(width=1, color='rgba(237,233,225,0.45)')),
                text=team_df['driver_name'] if not team_df.empty else [],
                customdata=team_df['customdata'].tolist() if not team_df.empty else [],
                hovertemplate="<b>%{text}</b> (%{customdata[0]})<br>Team: " + team +
                              "<br>GP: %{customdata[1]}<br>Started: P%{customdata[2]} | Finished: P%{customdata[3]}" +
                              "<br>Net Change: %{customdata[4]} positions<br>Status: %{customdata[5]}<extra></extra>"
            ))
        
        fig_scatter.update_layout(
            title="Grid Position vs Finish Position",
            xaxis_title="Starting Grid Position",
            yaxis_title="Final Finish Position",
            plot_bgcolor=panel,
            paper_bgcolor=panel,
            font_color=ink,
            height=550,
            xaxis=dict(range=[0.5, 20.5], tickmode='linear', tick0=1, dtick=1, gridcolor=grid_line, zeroline=False),
            yaxis=dict(range=[0.5, 20.5], tickmode='linear', tick0=1, dtick=1, gridcolor=grid_line, zeroline=False),
            legend=dict(title=dict(text='TEAM'), bgcolor='rgba(0,0,0,0)')
        )
        
        # ============================================================
        # HEATMAP
        # ============================================================
        fig_heat = go.Figure(go.Histogram2d(
            x=df_clean['grid'] if not df_clean.empty else [0],
            y=df_clean['positionOrder'] if not df_clean.empty else [0],
            xbins=dict(start=0.5, end=20.5, size=1),
            ybins=dict(start=0.5, end=20.5, size=1),
            colorscale=[[0.0, carbon], [0.4, '#3A404F'], [1.0, amber]],
            showscale=True,
            colorbar=dict(title=dict(text="Frequency", font=dict(color=muted, size=10)), tickfont=dict(color=ink)),
            hovertemplate="Grid: P%{x}<br>Finish: P%{y}<br>Count: %{z}<extra></extra>"
        ))
        fig_heat.add_shape(type="line", layer="above", x0=1, y0=1, x1=20, y1=20,
                          line=dict(color="rgba(237,233,225,0.4)", width=1.5, dash="dash"))
        fig_heat.update_layout(
            title="Position Density Heatmap",
            xaxis_title="Starting Grid Position",
            yaxis_title="Final Finish Position",
            plot_bgcolor=panel,
            paper_bgcolor=panel,
            font_color=ink,
            height=550,
            xaxis=dict(range=[0.5, 20.5], tickmode='linear', tick0=1, dtick=1, gridcolor=grid_line, zeroline=False),
            yaxis=dict(range=[0.5, 20.5], tickmode='linear', tick0=1, dtick=1, gridcolor=grid_line, zeroline=False)
        )
        
        # ============================================================
        # CORRELATION MATRIX
        # ============================================================
        corr_cols = ['grid', 'positionOrder', 'positions_gained']
        labels = ['Grid Position', 'Finish Position', 'Positions Gained']
        
        if not df_clean.empty and len(df_clean) > 1:
            corr_matrix = df_clean[corr_cols].corr()
        else:
            corr_matrix = pd.DataFrame(np.zeros((3, 3)), index=corr_cols, columns=corr_cols)
        
        fig_corr = go.Figure(go.Heatmap(
            z=corr_matrix.values,
            x=labels,
            y=labels,
            zmin=-1, zmax=1,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont=dict(color=ink, size=14),
            colorscale=[[0.0, '#DC0000'], [0.5, carbon], [1.0, amber]],
            showscale=True,
            colorbar=dict(title=dict(text="Pearson Corr.", font=dict(color=muted, size=10)), tickfont=dict(color=ink)),
            hovertemplate="%{x} vs %{y}<br>Correlation: %{z}<extra></extra>"
        ))
        fig_corr.update_layout(
            title="Correlation Matrix",
            plot_bgcolor=panel,
            paper_bgcolor=panel,
            font_color=ink,
            height=450,
            xaxis=dict(side='bottom', gridcolor=grid_line, color=muted),
            yaxis=dict(autorange='reversed', gridcolor=grid_line, color=muted)
        )
        
        # ============================================================
        # INSIGHTS
        # ============================================================
        total_results = len(df_clean)
        avg_gain = df_clean['positions_gained'].mean() if total_results > 0 else 0
        
        if total_results > 0:
            best_row = df_clean.loc[df_clean['positions_gained'].idxmax()]
            best_drive = f"{best_row['driver_name']} +{int(best_row['positions_gained'])}"
        else:
            best_drive = "—"
        
        # Get correlation value
        corr_value = corr_matrix.loc['grid', 'positionOrder'] if 'grid' in corr_matrix.index and 'positionOrder' in corr_matrix.columns else 0
        
        insight1 = html.Div([
            html.Span("🏁 ", style={'fontSize': '20px'}),
            html.Span("Qualifying matters: ", style={'fontWeight': 'bold'}),
            html.Span(f"{corr_value:.2f} correlation between grid and finish position", style={'color': '#ff6b35'})
        ])
        
        insight2 = html.Div([
            html.Span("📈 ", style={'fontSize': '20px'}),
            html.Span("Average position gain: ", style={'fontWeight': 'bold'}),
            html.Span(f"{avg_gain:+.2f} positions per driver", style={'color': '#4ecdc4'})
        ])
        
        insight3 = html.Div([
            html.Span("🏆 ", style={'fontSize': '20px'}),
            html.Span("Most improved: ", style={'fontWeight': 'bold'}),
            html.Span(f"{best_drive}", style={'color': '#ffe66d'})
        ])
        
        insight4 = html.Div([
            html.Span("📊 ", style={'fontSize': '20px'}),
            html.Span("Total results analyzed: ", style={'fontWeight': 'bold'}),
            html.Span(f"{total_results:,}", style={'color': '#ff6b6b'})
        ])
        
        return fig_scatter, fig_heat, fig_corr, insight1, insight2, insight3, insight4


# Register the callback
register_qualifying_callbacks(app)

# ============================================================
# SLOT 7: RACE STRATEGY PAGE - UPDATED WITH NEW JUSTIFICATIONS
# ============================================================
def create_strategy_page(theme='dark'):
    """Create the Race Strategy Analysis page"""
    df = load_data()
    
    # Theme colors
    if theme == 'dark':
        text_color, bg_color, card_bg, border_color = '#ffffff', '#0d0d1a', 'rgba(26, 26, 46, 0.85)', 'rgba(255, 255, 255, 0.08)'
    else:
        text_color, bg_color, card_bg, border_color = '#1a1a2e', '#f8f9fa', '#ffffff', '#e0e0e0'
    
    # CHART THEME CONSTANTS
    ACCENT = "#3987e5"
    TREND = "#eda100"
    GAIN = "#0ca30c"
    LOSS = "#d03b3b"
    NEUTRAL = "#898781"
    
    DENSITY_SCALE = [
        [0.0, "#16233a"],
        [0.35, "#1c5cab"],
        [0.70, "#3987e5"],
        [1.0, "#9ec5f4"],
    ]
    
    CORR_SCALE = [
        [0.0, "#256abf"],
        [0.5, "#3a3a38"],
        [1.0, "#d03b3b"],
    ]
    
    PLOT_LAYOUT = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6e6e6"),
    )
    
    # Prepare data for strategy analysis
    df['avg_pit_s'] = df['avg_pit_ms'] / 1000 if 'avg_pit_ms' in df.columns else 0
    df['fastest_pit_s'] = df['fastest_pit_ms'] / 1000 if 'fastest_pit_ms' in df.columns else 0
    df['slowest_pit_s'] = df['slowest_pit_ms'] / 1000 if 'slowest_pit_ms' in df.columns else 0
    
    df['normal_pit_stop'] = (
        (df['pit_stop_count'] > 0) &
        (df['avg_pit_ms'].between(15000, 60000))
    ) if 'avg_pit_ms' in df.columns else False
    
    df['valid_grid'] = df['grid'] > 0 if 'grid' in df.columns else False
    df['race_label'] = df['year'].astype(int).astype(str) + " - " + df['race_name'].astype(str)
    
    # Get available races for dropdown
    race_options = sorted(df['race_label'].dropna().unique()) if 'race_label' in df.columns else []
    
    # CHART 1: Density Heatmap - Pit-stop Duration vs Positions Gained
    scatter_df = df[df['pit_stop_count'] > 0].copy()
    scatter_df = scatter_df[scatter_df['normal_pit_stop']].copy()
    scatter_df = scatter_df[scatter_df['valid_grid']].copy()
    
    fig1 = go.Figure()
    
    if not scatter_df.empty:
        x = scatter_df['avg_pit_s']
        y = scatter_df['positions_gained']
        
        fig1.add_trace(
            go.Histogram2d(
                x=x,
                y=y,
                colorscale=DENSITY_SCALE,
                nbinsx=40,
                nbinsy=30,
                colorbar=dict(title="Records"),
                hovertemplate=(
                    "Pit duration: %{x:.1f}s<br>"
                    "Positions gained: %{y}<br>"
                    "Records: %{z}<extra></extra>"
                ),
            )
        )
        
        # Binned mean-trend line
        bins = np.linspace(x.min(), min(x.max(), 45), 13)
        band = pd.cut(x, bins=bins)
        trend_data = (
            pd.DataFrame({"pit": x, "gain": y, "band": band})
            .groupby("band", observed=True)
            .agg(mean_gain=("gain", "mean"), n=("gain", "size"))
        )
        trend_data = trend_data[trend_data["n"] >= 15]
        centers = [b.mid for b in trend_data.index]
        
        fig1.add_trace(
            go.Scatter(
                x=centers,
                y=trend_data["mean_gain"],
                mode="lines+markers",
                line=dict(color=TREND, width=3),
                marker=dict(color=TREND, size=8),
                name="Mean positions gained",
                hovertemplate=(
                    "Pit duration ~%{x:.1f}s<br>"
                    "Mean positions gained: %{y:.2f}<extra></extra>"
                ),
            )
        )
        
        fig1.add_hline(
            y=0,
            line_dash="dash",
            line_color=NEUTRAL,
            annotation_text="No position change",
            annotation_position="top left",
        )
        
        fig1.update_layout(
            title="Pit-stop Duration vs Positions Gained (record density + mean trend)",
            xaxis_title="Average pit-stop duration (seconds)",
            yaxis_title="Positions gained",
            xaxis_range=[float(x.min()) - 1, 42],
            height=550,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            **PLOT_LAYOUT,
        )
    
    # CHART 2: Constructor Box Plot
    box_df = df[df['normal_pit_stop']].copy()
    
    if not box_df.empty:
        constructor_order = (
            box_df.groupby("constructor_name")["avg_pit_s"]
            .median()
            .sort_values()
            .index
            .tolist()
        )
        
        fig2 = px.box(
            box_df,
            x="constructor_name",
            y="avg_pit_s",
            category_orders={"constructor_name": constructor_order} if constructor_order else {},
            points="outliers",
            hover_data={
                "driver_name": True,
                "race_name": True,
                "year": True,
                "pit_stop_count": True,
                "avg_pit_s": ":.2f",
            },
            title="Pit-stop Duration Consistency by Constructor (ordered by median)",
            labels={
                "constructor_name": "Constructor",
                "avg_pit_s": "Average pit-stop duration (seconds)",
            },
            color_discrete_sequence=[ACCENT],
        )
        
        overall_median = box_df["avg_pit_s"].median()
        fig2.add_hline(
            y=overall_median,
            line_dash="dash",
            line_color=TREND,
            annotation_text=f"Field median {overall_median:.1f}s",
            annotation_position="top right",
        )
        
        fig2.update_traces(marker=dict(color=ACCENT), line=dict(color=ACCENT))
        fig2.update_layout(
            height=550,
            showlegend=False,
            xaxis_tickangle=-45,
            **PLOT_LAYOUT,
        )
    else:
        fig2 = go.Figure()
        fig2.add_annotation(text="No constructor pit-stop data available", showarrow=False)
        fig2.update_layout(**PLOT_LAYOUT, height=550)
    
    # CHART 3: Pit Duration Histogram
    hist_df = df[df['normal_pit_stop']].copy()
    
    if not hist_df.empty:
        med = hist_df["avg_pit_s"].median()
        q1 = hist_df["avg_pit_s"].quantile(0.25)
        q3 = hist_df["avg_pit_s"].quantile(0.75)
        
        fig3 = px.histogram(
            hist_df,
            x="avg_pit_s",
            nbins=45,
            marginal="box",
            title="Distribution of Average Pit-stop Duration",
            labels={
                "avg_pit_s": "Average pit-stop duration (seconds)",
                "count": "Number of driver-race records",
            },
            color_discrete_sequence=[ACCENT],
        )
        
        fig3.add_vline(x=med, line_dash="dash", line_color=TREND, line_width=2)
        fig3.add_annotation(
            x=med, y=1.0, yref="paper", yanchor="bottom",
            text=f"Median {med:.1f}s  |  IQR {q1:.1f}-{q3:.1f}s",
            showarrow=False, font=dict(color=TREND),
        )
        
        fig3.update_layout(
            height=500,
            bargap=0.05,
            showlegend=False,
            **PLOT_LAYOUT,
        )
    else:
        fig3 = go.Figure()
        fig3.add_annotation(text="No pit-stop duration data available", showarrow=False)
        fig3.update_layout(**PLOT_LAYOUT, height=500)
    
    # CHART 4: Race Dumbbell Chart
    selected_race = race_options[0] if race_options else None
    race_df = df[df['race_label'] == selected_race].copy() if selected_race else pd.DataFrame()
    race_df = race_df[race_df['valid_grid']].copy() if not race_df.empty else pd.DataFrame()
    
    fig4 = go.Figure()
    
    if not race_df.empty:
        race_df = race_df.sort_values("positionOrder", ascending=False)
        drivers = race_df["driver_name"].tolist()
        
        def _delta_group(g):
            if g > 0:
                return "Gained"
            if g < 0:
                return "Lost"
            return "No change"
        
        color_for = {"Gained": GAIN, "Lost": LOSS, "No change": NEUTRAL}
        
        # Connector lines
        for group in ["Gained", "Lost", "No change"]:
            seg = race_df[race_df["positions_gained"].apply(_delta_group) == group]
            xs, ys = [], []
            for _, r in seg.iterrows():
                xs += [r["grid"], r["positionOrder"], None]
                ys += [r["driver_name"], r["driver_name"], None]
            if xs:
                fig4.add_trace(
                    go.Scatter(
                        x=xs, y=ys, mode="lines",
                        line=dict(color=color_for[group], width=3),
                        name=group, legendgroup=group,
                        hoverinfo="skip",
                    )
                )
        
        # Grid markers
        fig4.add_trace(
            go.Scatter(
                x=race_df["grid"], y=race_df["driver_name"], mode="markers",
                marker=dict(symbol="circle-open", size=11, color=NEUTRAL,
                            line=dict(width=2, color=NEUTRAL)),
                name="Grid (start)", hoverinfo="skip",
            )
        )
        
        # Finish markers
        for group in ["Gained", "Lost", "No change"]:
            seg = race_df[race_df["positions_gained"].apply(_delta_group) == group]
            if seg.empty:
                continue
            sizes = 10 + seg["pit_stop_count"].fillna(0) * 4
            symbols = ["x-thin" if d else "circle" for d in seg["is_dnf"].fillna(0)]
            fig4.add_trace(
                go.Scatter(
                    x=seg["positionOrder"], y=seg["driver_name"], mode="markers",
                    marker=dict(size=sizes, color=color_for[group],
                                symbol=symbols, line=dict(width=1.5, color="#141414")),
                    name=f"Finish ({group.lower()})", legendgroup=group,
                    showlegend=False,
                    customdata=np.stack([
                        seg["constructor_name"], seg["grid"], seg["positionOrder"],
                        seg["positions_gained"], seg["pit_stop_count"].fillna(0),
                        seg["status"],
                    ], axis=-1),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Team: %{customdata[0]}<br>"
                        "Grid: P%{customdata[1]}  ->  Finish: P%{customdata[2]}<br>"
                        "Positions gained: %{customdata[3]}<br>"
                        "Pit stops: %{customdata[4]}<br>"
                        "Status: %{customdata[5]}<extra></extra>"
                    ),
                )
            )
        
        fig4.update_layout(
            title="Race-level Strategy: Grid -> Finish (marker size = pit stops)",
            xaxis_title="Position (1 = best)  -  left is better",
            yaxis_title="Driver",
            height=600,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            yaxis=dict(categoryorder="array", categoryarray=drivers),
            **PLOT_LAYOUT,
        )
    else:
        fig4 = go.Figure()
        fig4.add_annotation(text="No race data available", showarrow=False)
        fig4.update_layout(**PLOT_LAYOUT, height=600)
    
    # CHART 5: Correlation Heatmap
    corr_cols = [
        "pit_stop_count", "avg_pit_s", "fastest_pit_s", "slowest_pit_s",
        "positions_gained", "positionOrder", "points", "avg_lap_difference",
        "fastest_lap_difference", "pace_rank"
    ]
    
    display_names = {
        "pit_stop_count": "Pit stop count",
        "avg_pit_s": "Avg pit time",
        "fastest_pit_s": "Fastest pit time",
        "slowest_pit_s": "Slowest pit time",
        "positions_gained": "Positions gained",
        "positionOrder": "Final position",
        "points": "Points",
        "avg_lap_difference": "Avg lap delta",
        "fastest_lap_difference": "Fastest lap delta",
        "pace_rank": "Pace rank",
    }
    
    corr_df = df[df['pit_stop_count'] > 0].copy()
    corr_df = corr_df[corr_df['normal_pit_stop']].copy()
    corr_df = corr_df[corr_df['valid_grid']].copy()
    
    available_cols = [col for col in corr_cols if col in corr_df.columns]
    
    if not corr_df.empty and len(available_cols) > 1:
        corr_matrix = corr_df[available_cols].corr(numeric_only=True)
        corr_matrix = corr_matrix.rename(index=display_names, columns=display_names)
        
        fig5 = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale=CORR_SCALE,
            zmin=-1,
            zmax=1,
            title="Correlation Between Strategy Metrics and Race Outcomes",
            labels={"color": "Correlation"},
        )
        fig5.update_traces(textfont=dict(color="#ffffff", size=11), xgap=2, ygap=2)
        fig5.update_layout(
            height=600,
            xaxis_title="Metric",
            yaxis_title="Metric",
            margin=dict(l=120, r=80, t=80, b=120),
            **PLOT_LAYOUT,
        )
        fig5.update_xaxes(tickangle=-35)
    else:
        fig5 = go.Figure()
        fig5.add_annotation(text="No data available for correlation heatmap", showarrow=False)
        fig5.update_layout(**PLOT_LAYOUT, height=600)
    
    # Calculate stats for display
    total_records = len(scatter_df) if not scatter_df.empty else 0
    avg_pit = scatter_df['avg_pit_s'].mean() if not scatter_df.empty else 0
    avg_gain = scatter_df['positions_gained'].mean() if not scatter_df.empty else 0
    
    # Get fastest constructor
    if not box_df.empty:
        fastest_constructor = (
            box_df.groupby('constructor_name')['avg_pit_s']
            .median()
            .sort_values()
            .index[0] if not box_df.empty else 'N/A'
        )
    else:
        fastest_constructor = 'N/A'
    
    # ============================================================
    # BUILD THE PAGE
    # ============================================================
    return html.Div([
        html.Div([
            html.H2([html.Span("📈 "), "Race Strategy Analysis"]),
            html.P("Analyze how pit-stop count, duration, and strategy relate to race outcomes", 
                   className="text-muted mb-0"),
        ], id="app-header", style={
            "background": f"linear-gradient(120deg, {SURFACE_RAISED} 0%, {SURFACE} 70%)",
            "borderBottom": f"3px solid {ACCENT_RED}",
            "borderRadius": "14px",
            "padding": "22px 28px",
            "marginTop": "18px",
            "marginBottom": "18px",
            "boxShadow": "0 8px 24px rgba(0,0,0,0.35)"
        }),
        
        # Stats cards
        html.Div([
            html.Div([
                html.H3(f"{total_records:,}", className="stat-number", style={'color': '#ff6b35'}),
                html.P("📊 Total Records", className="stat-label", style={'color': text_color})
            ], className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([
                html.H3(f"{avg_pit:.2f}s", className="stat-number", style={'color': '#4ecdc4'}),
                html.P("⏱️ Avg Pit Duration", className="stat-label", style={'color': text_color})
            ], className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([
                html.H3(f"{avg_gain:+.2f}", className="stat-number", style={'color': '#ffe66d'}),
                html.P("📈 Avg Positions Gained", className="stat-label", style={'color': text_color})
            ], className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
            html.Div([
                html.H3(f"{fastest_constructor}", className="stat-number", style={'color': '#ff6b6b', 'fontSize': '20px'}),
                html.P("🏎️ Fastest Constructor", className="stat-label", style={'color': text_color})
            ], className="stat-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'})
        ], className="stats-grid"),
        
        # Race selector for dumbbell chart
        html.Div([
            html.Div([
                html.Label("🏁 Select Race:", style={'color': text_color, 'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='strategy-race-dropdown',
                    options=[{'label': r, 'value': r} for r in race_options],
                    value=selected_race if selected_race else None,
                    clearable=False,
                    style={'width': '300px', 'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'})
        ]),
        
        # Charts
        html.Div([
            # Row 1: Density Heatmap (Full Width)
            html.Div([
                dcc.Graph(figure=fig1, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'}),
            
            # Row 2: Box Plot + Histogram (2 columns)
            html.Div([
                html.Div([
                    dcc.Graph(figure=fig2, config={'displayModeBar': True})
                ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'}),
                html.Div([
                    dcc.Graph(figure=fig3, config={'displayModeBar': True})
                ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'})
            ], className="charts-grid"),
            
            # Row 3: Dumbbell Chart (Full Width)
            html.Div([
                dcc.Graph(figure=fig4, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'}),
            
            # Row 4: Correlation Heatmap (Full Width)
            html.Div([
                dcc.Graph(figure=fig5, config={'displayModeBar': True})
            ], className="chart-card", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '15px', 'borderRadius': '12px'})
        ]),
        
        # Key Insights
        html.Div([
            html.H3("💡 Key Insights", className="insights-title", style={'color': text_color}),
            html.Div([
                html.Div([
                    html.Span("⏱️ ", style={'fontSize': '20px'}),
                    html.Span("Median pit-stop duration: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{box_df['avg_pit_s'].median():.2f}s" if not box_df.empty else "N/A", style={'color': '#ff6b35'})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
                html.Div([
                    html.Span("🏎️ ", style={'fontSize': '20px'}),
                    html.Span("Fastest constructor: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{fastest_constructor}", style={'color': '#4ecdc4'})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
                html.Div([
                    html.Span("📈 ", style={'fontSize': '20px'}),
                    html.Span("Average positions gained: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{avg_gain:+.2f}", style={'color': '#ffe66d'})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),
                html.Div([
                    html.Span("📊 ", style={'fontSize': '20px'}),
                    html.Span("Total records analyzed: ", style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(f"{total_records:,}", style={'color': '#ff6b6b'})
                ], className="insight-item", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'})
            ], className="insights-grid")
        ], className="insights-container", style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}', 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '20px'}),
        
        # ============================================================
        # CHART JUSTIFICATIONS - UPDATED
        # ============================================================
        html.Div([
            html.H3("📋 Chart Justifications", className="insights-title", style={'color': text_color}),
            html.Div([

                html.Div([
                    html.Span("📊 ", style={'fontSize': '20px'}),
                    html.Span("1. Density heatmap + mean trend — Pit-stop duration vs positions gained: ",
                              style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(
                        "With ~2000 driver-race records, a plain scatter overplots into a hairball. "
                        "A 2D density view shows where records actually concentrate, and the overlaid "
                        "mean-trend line reads the (weak) relationship directly instead of forcing the "
                        "eye to guess through overlap.",
                        style={'color': text_color})
                ], className="insight-item",
                style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),

                html.Div([
                    html.Span("📦 ", style={'fontSize': '20px'}),
                    html.Span("2. Box plot — Pit-stop duration by constructor: ",
                              style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(
                        "Compares constructor-wise pit-stop consistency. Drawn in one color and ordered "
                        "by median so the comparison is about position on the axis, not decoding 15 hues; "
                        "the dashed line marks the field median. A box plot beats an average bar because "
                        "it shows spread and outliers.",
                        style={'color': text_color})
                ], className="insight-item",
                style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),

                html.Div([
                    html.Span("📈 ", style={'fontSize': '20px'}),
                    html.Span("3. Histogram — Pit-stop duration distribution: ",
                              style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(
                        "Identifies the normal pit-stop range and long tail stops. Kept single-series "
                        "(the old stacked-by-constructor version hid both the shape and any one team) "
                        "with quartile reference lines.",
                        style={'color': text_color})
                ], className="insight-item",
                style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),

                html.Div([
                    html.Span("🏁 ", style={'fontSize': '20px'}),
                    html.Span("4. Grid → finish dumbbell — Strategy comparison within one race: ",
                              style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(
                        "Shows each driver's movement from grid to finish. Color encodes gained/lost, "
                        "marker size encodes pit-stop count, so strategy and outcome are read together — "
                        "more informative than plotting only the final position colored by team.",
                        style={'color': text_color})
                ], className="insight-item",
                style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'}),

                html.Div([
                    html.Span("🔗 ", style={'fontSize': '20px'}),
                    html.Span("5. Correlation heatmap — Strategy and outcome relationships: ",
                              style={'fontWeight': 'bold', 'color': text_color}),
                    html.Span(
                        "A supporting overview of relationships between strategy and outcome metrics. "
                        "Uses a diverging blue→gray→red scale centered at 0 so positive and negative "
                        "correlations are distinguishable at a glance. It identifies patterns only "
                        "and does not claim causation.",
                        style={'color': text_color})
                ], className="insight-item",
                style={'backgroundColor': card_bg, 'border': f'1px solid {border_color}'})

            ], className="insights-grid")
        ], className="insights-container",
        style={
            'backgroundColor': card_bg,
            'border': f'1px solid {border_color}',
            'padding': '20px',
            'borderRadius': '12px',
            'marginBottom': '20px'
        })
    ])
# ============================================================
# SLOT 8: CIRCUIT INTELLIGENCE PAGE
# ============================================================
# Circuit Intelligence Theme Constants
CIRCUIT_BG_DARK = "#15151E"
CIRCUIT_CARD_BG = "#1F1F2B"
CIRCUIT_GRID_COLOR = "#33333F"
CIRCUIT_TEXT_LIGHT = "#F5F5F5"
CIRCUIT_TEXT_MUTED = "#9A9AA8"
CIRCUIT_ACCENT_RED = "#E10600"
CIRCUIT_ACCENT_GREY = "#4A4A58"
CIRCUIT_FONT_FAMILY = "'Titillium Web', 'Segoe UI', sans-serif"

CIRCUIT_PLOTLY_TEMPLATE = "plotly_dark"

CIRCUIT_CHART_LAYOUT_DEFAULTS = dict(
    template=CIRCUIT_PLOTLY_TEMPLATE,
    paper_bgcolor=CIRCUIT_CARD_BG,
    plot_bgcolor=CIRCUIT_CARD_BG,
    font=dict(family=CIRCUIT_FONT_FAMILY, color=CIRCUIT_TEXT_LIGHT, size=13),
    title_font=dict(size=18, color=CIRCUIT_TEXT_LIGHT),
    margin=dict(l=60, r=30, t=60, b=40),
    hoverlabel=dict(bgcolor="#2A2A38", font_family=CIRCUIT_FONT_FAMILY, font_color=CIRCUIT_TEXT_LIGHT),
)

CIRCUIT_HOVER_TEMPLATE_BAR = "<b>%{y}</b><br>%{x:.2f}<extra></extra>"

CIRCUIT_METRIC_LABELS = {
    "fastestLapSpeed": "Avg Fastest Lap Speed",
    "positions_gained": "Avg Position Gain",
    "is_dnf": "DNF Rate",
}


def load_circuit_data():
    """Load and prepare circuit data"""
    df = load_data()
    return df


def filter_circuit_data(df, year_range, countries, constructors):
    dff = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]
    if countries:
        dff = dff[dff["country"].isin(countries)]
    if constructors:
        dff = dff[dff["constructor_name"].isin(constructors)]
    return dff


def top_bottom_circuit(df_grouped, metric, top_n, direction):
    ascending = direction == "bottom"
    out = df_grouped.sort_values(metric, ascending=ascending)
    if top_n != "all":
        out = out.head(int(top_n))
    return out


def bar_colors_circuit(circuit_list, selected):
    if not selected:
        return [CIRCUIT_ACCENT_RED] * len(circuit_list)
    return [CIRCUIT_ACCENT_RED if c == selected else CIRCUIT_ACCENT_GREY for c in circuit_list]


def build_circuit_bar_fig(dff, metric, title, top_n, direction, selected):
    grouped = dff.groupby("circuit_name", as_index=False)[metric].mean()
    grouped = top_bottom_circuit(grouped, metric, top_n, direction)
    text_values = [f"{v:.2f}" for v in grouped[metric]]
    
    fig = go.Figure(
        go.Bar(
            x=grouped[metric],
            y=grouped["circuit_name"],
            orientation="h",
            marker_color=bar_colors_circuit(grouped["circuit_name"], selected),
            hovertemplate=CIRCUIT_HOVER_TEMPLATE_BAR,
            text=text_values,
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color=CIRCUIT_TEXT_LIGHT, size=11),
        )
    )
    
    min_val = min(grouped[metric].min(), 0)
    max_val = max(grouped[metric].max(), 0)
    span = max_val - min_val
    pad = span * 0.18 if span > 0 else 1
    axis_range = [min_val - pad, max_val + pad]
    
    fig.update_layout(
        title=title,
        yaxis=dict(autorange="reversed", gridcolor=CIRCUIT_GRID_COLOR),
        xaxis=dict(gridcolor=CIRCUIT_GRID_COLOR, title=CIRCUIT_METRIC_LABELS.get(metric, metric), range=axis_range),
        height=460,
        **CIRCUIT_CHART_LAYOUT_DEFAULTS,
    )
    return fig


def build_circuit_map_fig(dff, selected):
    df = load_circuit_data()
    
    circuit_coords = (
        df.groupby(["circuit_name", "country", "location"], as_index=False)[["lat", "lng"]]
        .first()
    )
    
    map_df = (
        dff.groupby(["circuit_name", "country", "location"], as_index=False)
        .agg({"fastestLapSpeed": "mean"})
        .merge(circuit_coords[["circuit_name", "lat", "lng"]], on="circuit_name", how="left")
    )
    
    fig = px.scatter_geo(
        map_df,
        lat="lat",
        lon="lng",
        hover_name="circuit_name",
        hover_data={"country": True, "location": True, "lat": False, "lng": False},
        size="fastestLapSpeed",
        projection="natural earth",
        color_discrete_sequence=[CIRCUIT_ACCENT_RED],
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color=CIRCUIT_TEXT_LIGHT)))
    
    if selected and selected in map_df["circuit_name"].values:
        sel_row = map_df[map_df["circuit_name"] == selected].iloc[0]
        fig.add_trace(
            go.Scattergeo(
                lat=[sel_row["lat"]],
                lon=[sel_row["lng"]],
                mode="markers",
                marker=dict(size=22, color="#FFD400", symbol="star", line=dict(width=1, color="black")),
                name="Selected",
                hoverinfo="skip",
                showlegend=False,
            )
        )
    
    fig.update_geos(
        bgcolor=CIRCUIT_CARD_BG,
        showland=True, landcolor="#22222E",
        showocean=True, oceancolor=CIRCUIT_BG_DARK,
        showcountries=True, countrycolor=CIRCUIT_GRID_COLOR,
        showframe=False,
    )
    fig.update_layout(title="🌍 Formula 1 Circuits Around the World", height=480, **CIRCUIT_CHART_LAYOUT_DEFAULTS)
    return fig


def build_circuit_heatmap_fig(dff, sort_metric, selected):
    heatmap_df = dff.groupby("circuit_name", as_index=False).agg(
        {"fastestLapSpeed": "mean", "positions_gained": "mean", "is_dnf": "mean"}
    )
    
    raw_norm = heatmap_df.copy()
    for col in ["fastestLapSpeed", "positions_gained", "is_dnf"]:
        min_val, max_val = raw_norm[col].min(), raw_norm[col].max()
        if max_val != min_val:
            raw_norm[col] = (raw_norm[col] - min_val) / (max_val - min_val)
    
    raw_norm = raw_norm.sort_values(sort_metric, ascending=False)
    circuits_order = raw_norm["circuit_name"].tolist()
    
    display_norm = raw_norm.copy()
    display_norm["is_dnf"] = 1 - display_norm["is_dnf"]
    
    z = display_norm.set_index("circuit_name")[["fastestLapSpeed", "positions_gained", "is_dnf"]].T
    actual = heatmap_df.set_index("circuit_name").loc[circuits_order][
        ["fastestLapSpeed", "positions_gained", "is_dnf"]
    ].T
    z_labels = [f"{CIRCUIT_METRIC_LABELS[m]} ({'higher=better' if m != 'is_dnf' else 'lower=better'})" for m in z.index]
    
    fig = go.Figure(
        go.Heatmap(
            z=z.values,
            x=circuits_order,
            y=z_labels,
            customdata=actual.values,
            colorscale="RdYlGn",
            hovertemplate="<b>%{x}</b><br>%{y}<br>Actual value: %{customdata:.2f}<extra></extra>",
            colorbar=dict(title="Performance<br>(green = better)", tickvals=[0, 1], ticktext=["Worse", "Better"]),
        )
    )
    
    if selected and selected in circuits_order:
        idx = circuits_order.index(selected)
        fig.add_shape(
            type="rect",
            x0=idx - 0.5, x1=idx + 0.5, y0=-0.5, y1=2.5,
            line=dict(color="#FFD400", width=3),
        )
    
    fig.update_layout(
        title=f"🔥 Circuit Performance Heatmap (sorted by {CIRCUIT_METRIC_LABELS[sort_metric]})",
        xaxis=dict(tickangle=45, gridcolor=CIRCUIT_GRID_COLOR),
        yaxis=dict(gridcolor=CIRCUIT_GRID_COLOR),
        height=430,
        **CIRCUIT_CHART_LAYOUT_DEFAULTS,
    )
    return fig


def build_circuit_bubble_fig(dff, selected):
    bubble_df = dff.groupby("circuit_name", as_index=False).agg(
        {"fastestLapSpeed": "mean", "positions_gained": "mean", "is_dnf": "mean", "country": "first"}
    )
    
    fig = px.scatter(
        bubble_df,
        x="fastestLapSpeed",
        y="positions_gained",
        size="is_dnf",
        color="is_dnf",
        color_continuous_scale="RdYlGn_r",
        hover_name="circuit_name",
        hover_data={"country": True, "fastestLapSpeed": ":.1f", "positions_gained": ":.2f", "is_dnf": ":.2f"},
        size_max=40,
        labels={
            "fastestLapSpeed": CIRCUIT_METRIC_LABELS["fastestLapSpeed"],
            "positions_gained": CIRCUIT_METRIC_LABELS["positions_gained"],
            "is_dnf": CIRCUIT_METRIC_LABELS["is_dnf"],
        },
    )
    fig.update_traces(marker=dict(line=dict(width=1, color=CIRCUIT_CARD_BG)))
    fig.update_layout(coloraxis_colorbar=dict(title="DNF Rate<br>(green=better)"))
    
    if selected and selected in bubble_df["circuit_name"].values:
        sel_row = bubble_df[bubble_df["circuit_name"] == selected].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=[sel_row["fastestLapSpeed"]],
                y=[sel_row["positions_gained"]],
                mode="markers",
                marker=dict(size=28, color="rgba(0,0,0,0)", line=dict(width=3, color="#FFD400")),
                name="Selected",
                hoverinfo="skip",
                showlegend=False,
            )
        )
    
    fig.update_layout(
        title="🟢 Circuit Speed vs Overtaking vs Reliability (bubble size = DNF rate)",
        xaxis=dict(gridcolor=CIRCUIT_GRID_COLOR),
        yaxis=dict(gridcolor=CIRCUIT_GRID_COLOR),
        height=480,
        **CIRCUIT_CHART_LAYOUT_DEFAULTS,
    )
    return fig


def build_circuit_insights(dff):
    grouped = dff.groupby("circuit_name", as_index=False).agg(
        {"fastestLapSpeed": "mean", "positions_gained": "mean", "is_dnf": "mean"}
    )
    if grouped.empty:
        return [html.Li("No data available for the current filter selection.")]
    
    fastest = grouped.loc[grouped["fastestLapSpeed"].idxmax()]
    lowest_gain = grouped.loc[grouped["positions_gained"].idxmin()]
    highest_dnf = grouped.loc[grouped["is_dnf"].idxmax()]
    most_overtaking = grouped.loc[grouped["positions_gained"].idxmax()]
    
    insights = [
        f"🏎️ {fastest['circuit_name']} records the highest average fastest lap speed in the selected data "
        f"({fastest['fastestLapSpeed']:.1f} km/h), reinforcing it as a high-speed circuit.",
        f"📈 {most_overtaking['circuit_name']} shows the greatest average position gain "
        f"({most_overtaking['positions_gained']:+.2f}), suggesting strong overtaking opportunities.",
        f"🐌 {lowest_gain['circuit_name']} has the lowest average position gain "
        f"({lowest_gain['positions_gained']:+.2f}), highlighting how difficult overtaking is there.",
        f"⚠️ {highest_dnf['circuit_name']} records the highest DNF rate ({highest_dnf['is_dnf'] * 100:.1f}%), "
        f"suggesting greater reliability or driving challenges at this circuit.",
    ]
    return [html.Li(text) for text in insights]


def build_circuit_kpis(dff):
    total_circuits = dff["circuit_name"].nunique()
    total_countries = dff["country"].nunique()
    avg_speed = round(dff["fastestLapSpeed"].mean(), 2) if not dff.empty else 0
    avg_dnf = round(dff["is_dnf"].mean() * 100, 2) if not dff.empty else 0
    return total_circuits, total_countries, avg_speed, avg_dnf


def circuit_kpi_card(icon_label, value_id):
    return html.Div(
        [html.H4(icon_label, style={"color": CIRCUIT_TEXT_MUTED, "fontWeight": "400", "marginBottom": "6px"}),
         html.H2(id=value_id, style={"color": CIRCUIT_TEXT_LIGHT, "margin": "0"})],
        style={
            "flex": "1", "backgroundColor": CIRCUIT_CARD_BG, "padding": "18px",
            "textAlign": "center", "borderRadius": "10px",
            "borderTop": f"3px solid {CIRCUIT_ACCENT_RED}",
        },
    )


def circuit_chart_card(children, width="49%"):
    return html.Div(children, style={
        "width": width, "backgroundColor": CIRCUIT_CARD_BG, "borderRadius": "10px",
        "padding": "10px", "boxSizing": "border-box",
    })


def circuit_filter_label(text):
    return html.Label(text, style={"color": CIRCUIT_TEXT_MUTED, "fontSize": "13px", "marginBottom": "4px", "display": "block"})


CIRCUIT_DROPDOWN_STYLE = {"color": "#111", "backgroundColor": "#fff"}


def create_circuit_page(theme='dark'):
    """Create the Circuit Intelligence page"""
    df = load_circuit_data()
    
    YEAR_MIN, YEAR_MAX = int(df["year"].min()), int(df["year"].max())
    ALL_COUNTRIES = sorted(df["country"].dropna().unique().tolist())
    ALL_CONSTRUCTORS = sorted(df["constructor_name"].dropna().unique().tolist())
    
    # Theme colors
    if theme == 'dark':
        bg_color, text_color, card_bg = CIRCUIT_BG_DARK, CIRCUIT_TEXT_LIGHT, CIRCUIT_CARD_BG
    else:
        bg_color, text_color, card_bg = '#f8f9fa', '#1a1a2e', '#ffffff'
    
    return html.Div([
        dcc.Store(id="selected-circuit-store", data=None),
        
        # Header
        html.Div([
            html.H1("🏎️ Circuit Intelligence", style={
                "color": text_color, "fontSize": "38px", "margin": "0", "fontWeight": "700",
            }),
            html.P("An interactive visual analytics system for exploring Formula 1 circuit performance",
                   style={"color": CIRCUIT_TEXT_MUTED, "marginTop": "4px"}),
        ], style={"marginBottom": "20px"}),
        
        # Filter Bar
        html.Div([
            html.Div([
                circuit_filter_label("Season Range"),
                dcc.RangeSlider(
                    id="circuit-year-slider", min=YEAR_MIN, max=YEAR_MAX, step=1,
                    value=[YEAR_MIN, YEAR_MAX],
                    marks={y: str(y) for y in range(YEAR_MIN, YEAR_MAX + 1)},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], style={"flex": "2", "minWidth": "260px", "padding": "0 15px"}),
            
            html.Div([
                circuit_filter_label("Country"),
                dcc.Dropdown(id="circuit-country-filter", options=[{"label": c, "value": c} for c in ALL_COUNTRIES],
                             multi=True, placeholder="All countries", style=CIRCUIT_DROPDOWN_STYLE),
            ], style={"flex": "2", "minWidth": "200px", "padding": "0 15px"}),
            
            html.Div([
                circuit_filter_label("Constructor"),
                dcc.Dropdown(id="circuit-constructor-filter", options=[{"label": c, "value": c} for c in ALL_CONSTRUCTORS],
                             multi=True, placeholder="All constructors", style=CIRCUIT_DROPDOWN_STYLE),
            ], style={"flex": "2", "minWidth": "200px", "padding": "0 15px"}),
            
            html.Div([
                circuit_filter_label("Show"),
                dcc.Dropdown(id="circuit-topn-filter",
                             options=[{"label": f"Top {n}", "value": str(n)} for n in [5, 10, 15, 20]] + [{"label": "All", "value": "all"}],
                             value="10", clearable=False, style=CIRCUIT_DROPDOWN_STYLE),
            ], style={"flex": "1", "minWidth": "120px", "padding": "0 15px"}),
            
            html.Div([
                circuit_filter_label("Rank Direction"),
                dcc.RadioItems(
                    id="circuit-direction-filter",
                    options=[{"label": " Top", "value": "top"}, {"label": " Bottom", "value": "bottom"}],
                    value="top", inline=True, style={"color": text_color},
                    labelStyle={"marginRight": "12px"},
                ),
            ], style={"flex": "1", "minWidth": "140px", "padding": "0 15px"}),
            
            html.Div([
                html.Button("✕ Clear Selection", id="circuit-reset-selection-btn", n_clicks=0, style={
                    "backgroundColor": CIRCUIT_ACCENT_RED, "color": "white", "border": "none",
                    "borderRadius": "6px", "padding": "10px 16px", "cursor": "pointer",
                    "fontFamily": CIRCUIT_FONT_FAMILY, "marginTop": "18px",
                }),
            ], style={"padding": "0 15px"}),
            
        ], style={
            "display": "flex", "flexWrap": "wrap", "alignItems": "flex-start",
            "backgroundColor": card_bg, "borderRadius": "10px", "padding": "20px 5px",
            "marginBottom": "20px",
        }),
        
        html.Div(id="circuit-selection-banner", style={"color": "#FFD400", "marginBottom": "10px", "fontWeight": "600"}),
        
        # KPI Cards
        html.Div([
            circuit_kpi_card("🏁 Circuits Shown", "circuit-kpi-circuits"),
            circuit_kpi_card("🌍 Countries", "circuit-kpi-countries"),
            circuit_kpi_card("⚡ Avg Speed (km/h)", "circuit-kpi-speed"),
            circuit_kpi_card("⚠ Avg DNF Rate", "circuit-kpi-dnf"),
        ], style={"display": "flex", "gap": "20px", "marginBottom": "25px"}),
        
        # Map
        html.Div([
            circuit_chart_card([dcc.Graph(id="circuit-fig-map", config={"displayModeBar": False})], width="100%"),
        ], style={"marginBottom": "20px"}),
        
        # Ranked Bars
        html.Div([
            circuit_chart_card([dcc.Graph(id="circuit-fig-speed", config={"displayModeBar": False})], width="32.5%"),
            circuit_chart_card([dcc.Graph(id="circuit-fig-gain", config={"displayModeBar": False})], width="32.5%"),
            circuit_chart_card([dcc.Graph(id="circuit-fig-dnf", config={"displayModeBar": False})], width="32.5%"),
        ], style={"display": "flex", "justifyContent": "space-between", "gap": "1%", "marginBottom": "20px"}),
        
        # Heatmap + Bubble
        html.Div([
            html.Div([
                circuit_filter_label("Heatmap sort metric"),
                dcc.Dropdown(
                    id="circuit-heatmap-sort-metric",
                    options=[{"label": v, "value": k} for k, v in CIRCUIT_METRIC_LABELS.items()],
                    value="fastestLapSpeed", clearable=False, style={**CIRCUIT_DROPDOWN_STYLE, "width": "260px"},
                ),
            ], style={"marginBottom": "10px"}),
            html.Div([
                circuit_chart_card([dcc.Graph(id="circuit-fig-heatmap", config={"displayModeBar": False})], width="49%"),
                circuit_chart_card([dcc.Graph(id="circuit-fig-bubble", config={"displayModeBar": False})], width="49%"),
            ], style={"display": "flex", "justifyContent": "space-between", "gap": "2%"}),
        ], style={"marginBottom": "25px"}),
        
        # Insights
        html.Div([
            html.H2("💡 Circuit Insights", style={"color": text_color}),
            html.P("Automatically generated from the currently filtered dataset — not static text.",
                   style={"color": CIRCUIT_TEXT_MUTED, "fontSize": "13px"}),
            html.Ul(id="circuit-insights-list", style={"color": text_color, "lineHeight": "1.8"}),
        ], style={"backgroundColor": card_bg, "borderRadius": "10px", "padding": "20px"}),
        
        html.P(
            "Click any circuit on the map, a bar in the rankings, a heatmap column, or a bubble to highlight it "
            "across every visualization on this page.",
            style={"color": CIRCUIT_TEXT_MUTED, "fontSize": "12px", "marginTop": "15px", "textAlign": "center"},
        ),
        
    ], style={
        "backgroundColor": bg_color, "padding": "30px", "fontFamily": CIRCUIT_FONT_FAMILY,
        "minHeight": "100vh",
    })


# ============================================================
# SLOT 9: APP LAYOUT
# ============================================================
app.layout = html.Div([
    dcc.Store(id='theme-store', data='dark'),
    dcc.Store(id='color-scheme-store', data='Viridis'),
    dcc.Store(id='year-store', data=None),
    dcc.Store(id='team-store', data='All'),
    dcc.Store(id='points-range-store', data=None),
    dcc.Store(id='current-page', data='overview'),
    dcc.Store(id='constructor-year-store', data=None),
    dcc.Store(id='constructor-team-store', data=None),
    dcc.Store(id="selected-circuit-store", data=None),
    
    html.Div(
        id='sidebar',
        className='sidebar',
        children=[
            html.H2("🏎️ F1 Insights", className="sidebar-title"),
            html.Hr(className="sidebar-divider"),
            html.Div([
                html.A("📊 Overview", href="#", className="nav-link active", id="nav-overview"),
                html.A("🏆 Championship", href="#", className="nav-link", id="nav-championship"),
                html.A("🏎️ Drivers", href="#", className="nav-link", id="nav-drivers"),
                html.A("🏭 Constructors", href="#", className="nav-link", id="nav-constructors"),
                html.A("🏁 Circuits", href="#", className="nav-link", id="nav-circuits"),
                html.A("📈 Race Strategy", href="#", className="nav-link", id="nav-strategy"),
                html.A("⚡ Qualifying vs Race", href="#", className="nav-link", id="nav-qualifying"),
            ], className="nav-menu"),
            html.Hr(className="sidebar-divider"),
            
            html.Div([
                html.P("🎨 THEME", className="sidebar-label"),
                html.Div([
                    html.Button("☀️ Light", id="theme-light-btn", className="theme-btn", n_clicks=0),
                    html.Button("🌙 Dark", id="theme-dark-btn", className="theme-btn active", n_clicks=0),
                ], className="theme-toggle-group"),
            ], className="sidebar-section"),
            
            html.Div([
                html.P("🎨 COLOR SCHEME", className="sidebar-label"),
                dcc.Dropdown(
                    id='sidebar-color-scheme',
                    options=[
                        {'label': '🌈 Viridis', 'value': 'Viridis'},
                        {'label': '🌋 Plasma', 'value': 'Plasma'},
                        {'label': '🎯 Turbo', 'value': 'Turbo'},
                        {'label': '🌈 Rainbow', 'value': 'Rainbow'},
                        {'label': '🌡️ RdBu', 'value': 'RdBu'},
                        {'label': '🎨 Spectral', 'value': 'Spectral'}
                    ],
                    value='Viridis',
                    clearable=False,
                    style={'backgroundColor': '#ffffff', 'color': '#000000', 'border': '1px solid #cccccc', 'borderRadius': '4px'}
                )
            ], className="sidebar-section"),
            
            html.Hr(className="sidebar-divider"),
            html.Div([
                html.P("📊 Data sourced from F1 records", className="footer-text"),
                html.P("© 2024 F1 Analytics v2.0", className="footer-text")
            ], className="sidebar-footer")
        ]
    ),
    
    html.Div(id='sidebar-overlay', className='sidebar-overlay hidden'),
    
    html.Div(
        id='main-content',
        className='main-content',
        children=[
            html.Div([
                html.Button("☰", id="toggle-sidebar-btn", className="menu-toggle"),
                html.H1("F1 Dashboard", className="page-title"),
                html.Div(id="page-title", children="Dashboard Overview", className="page-title-text"),
                html.Div(id="page-breadcrumb", children="Overview", className="page-breadcrumb"),
                html.Div(id="filter-summary", children="All data", className="filter-summary")
            ], className="top-bar"),
            
            html.Div(id='page-content', children=[
                html.Div("Loading...")
            ])
        ]
    )
])


# ============================================================
# SLOT 10: CSS + JAVASCRIPT
# ============================================================
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&family=Titillium+Web:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            /* Global Styles */
            html, body {
                background-color: #15181D !important;
                font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
            }
            
            * { font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif; }
            .brand-font { font-family: 'Inter', sans-serif !important; }
            .mono { font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important; }
            
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: #15181D; }
            ::-webkit-scrollbar-thumb { background: #2A2E37; border-radius: 4px; }
            
            /* App Header */
            #app-header {
                background: linear-gradient(120deg, #1D2129 0%, #15181D 70%);
                border-bottom: 3px solid #E10600;
                border-radius: 14px;
                padding: 22px 28px;
                margin-top: 18px;
                margin-bottom: 18px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.35);
            }
            #app-header h2 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 4px; color: #F5F6F7; }
            
            /* Cards */
            .dash-graph-card {
                background-color: #1D2129;
                border: 1px solid #2A2E37;
                border-radius: 14px;
                padding: 12px 10px 4px 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.25);
                transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease, border-color 0.3s ease;
            }
            .dash-graph-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 28px rgba(0, 210, 255, 0.15);
                border-color: rgba(0, 210, 255, 0.4);
            }
            
            .stat-card {
                background-color: #1D2129;
                border: 1px solid #2A2E37;
                border-radius: 14px;
                padding: 20px;
                text-align: center;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                box-shadow: 0 4px 14px rgba(0,0,0,0.25);
            }
            .stat-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            }
            
            .stat-number { font-size: 28px; font-weight: 800; margin: 0; color: #F5F6F7; }
            .stat-label { color: #9AA0AA; font-size: 13px; margin: 5px 0 0; }
            
            .telemetry-value {
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                color: #ffffff;
                letter-spacing: -0.5px;
            }
            
            /* KPI Cards */
            .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
            .kpi-card { background: rgba(26, 26, 46, 0.85); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px; text-align: center; transition: all 0.3s ease; box-shadow: 0 8px 32px rgba(0,0,0,0.2); }
            .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 12px 48px rgba(255,107,53,0.15); border-color: rgba(255,107,53,0.3); }
            .kpi-number { font-size: 32px; font-weight: 800; margin: 0; }
            .kpi-label { color: #aaaaaa; font-size: 14px; margin: 5px 0 0; }
            
            .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px; }
            .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
            .insights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
            
            .chart-card { background: rgba(26, 26, 46, 0.85); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 15px; transition: all 0.3s ease; }
            .chart-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
            
            .insight-item { padding: 12px 15px; border-radius: 8px; }
            .insights-container { padding: 20px; border-radius: 12px; margin-bottom: 20px; }
            .insights-title { margin-top: 0; margin-bottom: 15px; color: #F5F6F7; }
            .table-container { border-radius: 12px; margin-bottom: 20px; }
            
            .sidebar { background-color: #1a1a2e !important; }
            .sidebar-title { color: #ff6b35 !important; }
            .nav-link { color: #aaaaaa !important; transition: all 0.2s ease; }
            .nav-link:hover { background-color: #2a2a4e !important; color: #ffffff !important; }
            .nav-link.active { background-color: #ff6b35 !important; color: #ffffff !important; }
            .sidebar-label { color: #aaaaaa !important; }
            .footer-text { color: #666666 !important; }
            .theme-btn { transition: all 0.3s ease !important; }
            .theme-btn.active { background-color: #ff6b35 !important; border-color: #ff6b35 !important; color: #ffffff !important; }
            
            .top-bar { background: rgba(26, 26, 46, 0.6) !important; backdrop-filter: blur(10px) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 12px !important; }
            .menu-toggle { background: rgba(255,107,53,0.2) !important; color: #ff6b35 !important; border: 1px solid rgba(255,107,53,0.3) !important; }
            .menu-toggle:hover { background: #ff6b35 !important; color: #ffffff !important; }
            
            .leaflet-container { border-radius: 12px !important; z-index: 1 !important; }
            
            /* Dropdown Fixes */
            .Select-control { background-color: #ffffff !important; border-color: #cccccc !important; border-radius: 4px !important; min-height: 38px !important; }
            .Select-value-label { color: #000000 !important; font-weight: 500 !important; }
            .Select-placeholder { color: #666666 !important; }
            .Select-arrow-zone { color: #000000 !important; }
            .Select-clear-zone { color: #000000 !important; }
            .Select-menu-outer { background-color: #ffffff !important; border-color: #cccccc !important; border-radius: 4px !important; margin-top: 2px !important; z-index: 99999 !important; }
            .Select-option { background-color: #ffffff !important; color: #000000 !important; padding: 10px 15px !important; cursor: pointer !important; }
            .Select-option.is-focused { background-color: #f0f0f0 !important; color: #000000 !important; }
            .Select-option.is-selected { background-color: #ff6b35 !important; color: #ffffff !important; }
            .Select-option:hover { background-color: #f0f0f0 !important; color: #000000 !important; }
            .is-open .Select-control { background-color: #ffffff !important; border-color: #ff6b35 !important; }
            .has-value .Select-control { background-color: #ffffff !important; }
            
            .rc-slider-track { background-color: #ff6b35 !important; }
            .rc-slider-handle { border-color: #ff6b35 !important; background-color: #ff6b35 !important; }
            .rc-slider-handle:hover { border-color: #ff6b35 !important; background-color: #ff6b35 !important; }
            .rc-slider-handle:active { border-color: #ff6b35 !important; background-color: #ff6b35 !important; box-shadow: 0 0 0 5px rgba(255,107,53,0.3) !important; }
            .rc-slider-dot-active { border-color: #ff6b35 !important; }
            .rc-slider-rail { background-color: #e0e0e0 !important; }
            .rc-slider-dot { border-color: #cccccc !important; }
            
            .rc-slider-tooltip-inner { background-color: #ffffff !important; color: #000000 !important; border: 2px solid #ff6b35 !important; font-weight: bold !important; padding: 6px 12px !important; border-radius: 6px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important; }
            .rc-slider-tooltip-arrow { border-top-color: #ffffff !important; }
            
            /* Responsive */
            @media (max-width: 768px) { 
                .kpi-grid { grid-template-columns: repeat(2, 1fr); } 
                .stats-grid { grid-template-columns: repeat(2, 1fr); }
                .charts-grid { grid-template-columns: 1fr !important; } 
                .insights-grid { grid-template-columns: 1fr !important; } 
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <script>
            function updateSliderColors() {
                var marks = document.querySelectorAll('.rc-slider-mark-text');
                marks.forEach(function(mark) {
                    var text = mark.textContent.trim();
                    if (text === '0' || text === '585') {
                        mark.style.color = '#000000';
                        mark.style.fontWeight = '900';
                        mark.style.fontSize = '14px';
                        mark.style.backgroundColor = '#ffffff';
                        mark.style.padding = '2px 8px';
                        mark.style.borderRadius = '4px';
                        mark.style.border = '2px solid #ff6b35';
                    } else {
                        mark.style.color = '#00cc66';
                        mark.style.fontWeight = '700';
                        mark.style.fontSize = '13px';
                        mark.style.backgroundColor = 'transparent';
                        mark.style.border = 'none';
                        mark.style.padding = '0';
                    }
                });
            }
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(updateSliderColors, 500);
            });
            setInterval(updateSliderColors, 1000);
            document.addEventListener('DOMContentLoaded', function() {
                var observer = new MutationObserver(function() { updateSliderColors(); });
                var target = document.getElementById('page-content');
                if (target) { observer.observe(target, { childList: true, subtree: true }); }
            });
        </script>
    </body>
</html>
'''


# ============================================================
# SLOT 11: CALLBACKS
# ============================================================
from dash import callback_context, html, dcc, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

# Callback 1: Toggle Theme
@app.callback(
    [Output('theme-store', 'data'),
     Output('theme-light-btn', 'className'),
     Output('theme-dark-btn', 'className'),
     Output('main-content', 'style')],
    [Input('theme-light-btn', 'n_clicks'),
     Input('theme-dark-btn', 'n_clicks')],
    [State('theme-store', 'data')]
)
def toggle_theme(light_clicks, dark_clicks, current_theme):
    ctx = callback_context
    if not ctx.triggered:
        return 'dark', 'theme-btn', 'theme-btn active', {'backgroundColor': '#0d0d1a', 'color': '#ffffff'}
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'theme-light-btn':
        return 'light', 'theme-btn active', 'theme-btn', {'backgroundColor': '#f8f9fa'}
    elif trigger_id == 'theme-dark-btn':
        return 'dark', 'theme-btn', 'theme-btn active', {'backgroundColor': '#0d0d1a', 'color': '#ffffff'}
    return current_theme, 'theme-btn active', 'theme-btn', {'backgroundColor': '#0d0d1a', 'color': '#ffffff'}


# Callback 2: MASTER NAVIGATION & PAGE ROUTER
@app.callback(
    [Output('page-content', 'children'),
     Output('page-title', 'children'),
     Output('page-breadcrumb', 'children'),
     Output('filter-summary', 'children'),
     Output('nav-overview', 'className'),
     Output('nav-championship', 'className'),
     Output('nav-drivers', 'className'),
     Output('nav-constructors', 'className'),
     Output('nav-circuits', 'className'),
     Output('nav-strategy', 'className'),
     Output('nav-qualifying', 'className')],
    [Input('nav-overview', 'n_clicks'),
     Input('nav-championship', 'n_clicks'),
     Input('nav-drivers', 'n_clicks'),
     Input('nav-constructors', 'n_clicks'),
     Input('nav-circuits', 'n_clicks'),
     Input('nav-strategy', 'n_clicks'),
     Input('nav-qualifying', 'n_clicks'),
     Input('theme-store', 'data'),
     Input('sidebar-color-scheme', 'value')],
    [State('nav-overview', 'className'),
     State('nav-championship', 'className'),
     State('nav-drivers', 'className'),
     State('nav-constructors', 'className'),
     State('nav-circuits', 'className'),
     State('nav-strategy', 'className'),
     State('nav-qualifying', 'className')]
)
def master_page_router(nav_ov, nav_ch, nav_dr, nav_co, nav_ci, nav_st, nav_qu,
                       theme, color_scheme,
                       st_ov, st_ch, st_dr, st_co, st_ci, st_st, st_qu):
    ctx = callback_context
    
    # Set fallback values
    theme = theme or 'dark'
    color_scheme = color_scheme or 'Viridis'
    
    # Identify what triggered the callback
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    active_nav = 'nav-overview'  # Default active page
    
    # If a nav button was explicitly clicked, use that.
    if trigger_id and trigger_id.startswith('nav-'):
        active_nav = trigger_id
    else:
        # If triggered by a theme/filter change or initial load, maintain current active page
        if st_ch and 'active' in st_ch:
            active_nav = 'nav-championship'
        elif st_dr and 'active' in st_dr:
            active_nav = 'nav-drivers'
        elif st_co and 'active' in st_co:
            active_nav = 'nav-constructors'
        elif st_ci and 'active' in st_ci:
            active_nav = 'nav-circuits'
        elif st_st and 'active' in st_st:
            active_nav = 'nav-strategy'
        elif st_qu and 'active' in st_qu:
            active_nav = 'nav-qualifying'

    # Build nav classes
    inactive = "nav-link"
    active = "nav-link active"
    
    nav_classes = {
        'nav-overview': inactive, 'nav-championship': inactive,
        'nav-drivers': inactive, 'nav-constructors': inactive,
        'nav-circuits': inactive, 'nav-strategy': inactive,
        'nav-qualifying': inactive
    }
    nav_classes[active_nav] = active

    # Route to the correct layout function
    if active_nav == 'nav-overview':
        page = create_overview_page(theme=theme, color_scheme=color_scheme)
        title, breadcrumb, summary = "Dashboard Overview", "Overview", "All data"
        
    elif active_nav == 'nav-championship':
        page = create_championship_page(theme=theme)
        title, breadcrumb, summary = "Championship Evolution", "Championship", "Season data"
        
    elif active_nav == 'nav-drivers':
        page = create_driver_performance_page(theme=theme)
        title, breadcrumb, summary = "Driver Performance", "Drivers", "Driver data"
        
    elif active_nav == 'nav-constructors':
        page = create_constructor_page(theme=theme)
        title, breadcrumb, summary = "Constructor Evolution", "Constructors", "Constructor data"
        
    elif active_nav == 'nav-circuits':
        page = create_circuit_page(theme=theme)
        title, breadcrumb, summary = "Circuit Intelligence", "Circuits", "Circuit data"
        
    elif active_nav == 'nav-strategy':
        page = create_strategy_page(theme=theme)
        title, breadcrumb, summary = "Race Strategy", "Strategy", "Strategy data"
        
    elif active_nav == 'nav-qualifying':
        page = create_qualifying_page(theme=theme)
        title, breadcrumb, summary = "Qualifying vs Race", "Qualifying vs Race", "Session data"
        
    else:
        page = create_overview_page(theme=theme, color_scheme=color_scheme)
        title, breadcrumb, summary = "Dashboard Overview", "Overview", "All data"

    return (page, title, breadcrumb, summary,
            nav_classes['nav-overview'], nav_classes['nav-championship'], 
            nav_classes['nav-drivers'], nav_classes['nav-constructors'], 
            nav_classes['nav-circuits'], nav_classes['nav-strategy'], 
            nav_classes['nav-qualifying'])
    
# Callback 3: Driver Data Table
@app.callback(
    Output('driver-data-table', 'data'),
    [Input('table-year-filter', 'value'),
     Input('table-constructor-filter', 'value')]
)
def update_table(year_filter, constructor_filter):
    df = load_data()
    table_df = df[['driver_name', 'year', 'championship_points', 'constructor_name', 'nationality', 'race_name', 'round', 'date']].copy()
    table_df = table_df.sort_values(['year', 'driver_name', 'round'])
    table_df['race_points'] = table_df.groupby(['year', 'driver_name'])['championship_points'].diff().fillna(table_df['championship_points'])
    table_df = table_df.sort_values(['year', 'round'], ascending=[True, True])
    if year_filter != 'All':
        table_df = table_df[table_df['year'] == year_filter]
    if constructor_filter != 'All':
        table_df = table_df[table_df['constructor_name'] == constructor_filter]
    return table_df.to_dict('records')


# Callback 4: Driver Performance - Season Dropdown
@app.callback(
    [Output('season-select', 'options'), Output('season-select', 'value')],
    Input('driver-1-select', 'value'),
    State('season-select', 'value')
)
def update_season_dropdown(driver, current_season):
    df = load_data()
    engine = DriverDataEngine(df)
    seasons = engine.get_available_seasons(driver)
    options = [{'label': f'Career ({engine.get_season_range_label()})', 'value': 'all'}] + [{'label': str(yr), 'value': str(yr)} for yr in seasons]
    return options, current_season if current_season in {'all'} | {str(yr) for yr in seasons} else 'all'


# Callback 5: Driver Performance - Driver 2 Options
@app.callback(
    Output('driver-2-select', 'options'),
    Input('driver-1-select', 'value')
)
def update_driver_two_options(driver):
    df = load_data()
    engine = DriverDataEngine(df)
    return [{'label': '-- None --', 'value': ''}] + [{'label': n, 'value': n} for n in engine.get_unique_drivers() if n != driver]


# Callback 6: Driver Performance - Main Dashboard
@app.callback(
    [Output('kpi-points', 'children'), Output('kpi-avg-finish', 'children'),
     Output('kpi-best-finish', 'children'), Output('kpi-dnf-rate', 'children'),
     Output('line-trend-chart', 'figure'), Output('box-consistency-chart', 'figure'), Output('radar-summary-chart', 'figure')],
    [Input('driver-1-select', 'value'), Input('driver-2-select', 'value'),
     Input('season-select', 'value'), Input('distribution-view-toggle', 'value')]
)
def update_driver_dashboard(d1, d2, season, view_type):
    df = load_data()
    engine = DriverDataEngine(df)
    
    if not d1:
        empty_fig = go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis={'visible': False}, yaxis={'visible': False},
            annotations=[{'text': 'Select a driver', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 15, 'color': '#9AA0AA'}}],
            margin=dict(t=40, b=40, l=40, r=40)
        )
        return ["-"] * 4 + [empty_fig] * 3
    
    kpis = engine.get_kpi_summary(d1, season)
    trends1 = engine.get_historical_trends(d1, season)
    trends2 = engine.get_historical_trends(d2, season) if d2 else pd.DataFrame()
    
    # Line Chart
    line_fig = go.Figure()
    if not trends1.empty:
        custom_data_1 = trends1[['grid', 'points', 'status']]
        line_fig.add_trace(go.Scatter(
            x=trends1['timeline_label'], y=trends1['positionOrder'], mode='lines+markers', 
            name=f'{d1} - Finish', line=dict(width=3, color='#00E5FF'),
            fill='tozeroy', fillcolor='rgba(0, 210, 255, 0.08)',
            customdata=custom_data_1,
            hovertemplate=(
                "<b style='font-size:14px'>%{x}</b><br><br>"
                "<b>START:</b> P%{customdata[0]}<br>"
                "<b>FINISH:</b> P%{y}<br>"
                "<b>POINTS:</b> %{customdata[1]}<br>"
                "<b style='color:#00d2ff'>STATUS:</b> %{customdata[2]}"
                "<extra></extra>"
            )
        ))
        if d2 and not trends2.empty:
            custom_data_2 = trends2[['grid', 'points', 'status']]
            line_fig.add_trace(go.Scatter(
                x=trends2['timeline_label'], y=trends2['positionOrder'], mode='lines+markers', 
                name=f'{d2} - Finish', line=dict(width=2, color='#FF8A3D'),
                customdata=custom_data_2,
                hovertemplate=(
                    "<b style='font-size:14px'>%{x}</b><br><br>"
                    "<b>START:</b> P%{customdata[0]}<br>"
                    "<b>FINISH:</b> P%{y}<br>"
                    "<b>POINTS:</b> %{customdata[1]}<br>"
                    "<b style='color:#FF8A3D'>STATUS:</b> %{customdata[2]}"
                    "<extra></extra>"
                )
            ))
        combined = pd.concat([trends1, trends2]) if not trends2.empty else trends1
        line_fig.update_layout(
            title="Telemetry Progression",
            xaxis={'title': '', 'tickangle': -45, 'categoryorder': 'array', 'categoryarray': combined.sort_values(by=['year', 'round'])['timeline_label'].unique()},
            yaxis={'title': 'Classification', 'autorange': 'reversed', 'dtick': 2},
            legend=dict(orientation="h", y=-0.55, x=0.5, xanchor='center'),
            hoverlabel=dict(bgcolor='rgba(0, 210, 255, 0.1)', bordercolor='#00d2ff', font_size=13),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F5F6F7'), margin=dict(t=50, b=160, l=40, r=20)
        )
        line_fig.update_xaxes(gridcolor='#2A2E37', zeroline=False)
        line_fig.update_yaxes(gridcolor='#2A2E37', zeroline=False)
    else:
        line_fig = go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            annotations=[{'text': 'No data available.', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 15, 'color': '#9AA0AA'}}],
            margin=dict(t=40, b=40, l=40, r=40)
        )
    
    # Box/Violin Chart
    box_fig = go.Figure()
    class1, dnf1 = engine.get_classified_finishes(d1, season), engine.get_dnf_summary(d1, season)
    if not class1.empty:
        is_violin = (view_type == 'violin')
        def add_dist(fig, data, name, color):
            if is_violin:
                fig.add_trace(go.Violin(y=data, name=name, box_visible=True, meanline_visible=True, points='all', jitter=0.3, marker_color=color, line_color=color, fillcolor=color, opacity=0.5))
            else:
                fig.add_trace(go.Box(y=data, name=name, boxpoints='all', jitter=0.3, marker_color=color, line=dict(color=color)))
        add_dist(box_fig, class1['positionOrder'], d1, '#00E5FF')
        dnf_text = [f"{d1}: {dnf1['dnf_count']}/{dnf1['total']} DNFs ({dnf1['dnf_rate']:.0f}%)"]
        if d2:
            class2, dnf2 = engine.get_classified_finishes(d2, season), engine.get_dnf_summary(d2, season)
            if not class2.empty:
                add_dist(box_fig, class2['positionOrder'], d2, '#FF8A3D')
                dnf_text.append(f"{d2}: {dnf2['dnf_count']}/{dnf2['total']} DNFs ({dnf2['dnf_rate']:.0f}%)")
        box_fig.update_layout(
            title=f"Distribution Floor ({view_type.title()})",
            yaxis={'title': 'Classification (Lower is Better)', 'autorange': 'reversed', 'dtick': 2},
            annotations=[{'text': " | ".join(dnf_text), 'xref': 'paper', 'yref': 'paper', 'x': 0.5, 'y': 1.10, 'yanchor': 'bottom', 'showarrow': False, 'font': {'size': 11, 'color': '#00d2ff'}}],
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F5F6F7')
        )
        box_fig.update_xaxes(gridcolor='#2A2E37')
        box_fig.update_yaxes(gridcolor='#2A2E37')
    else:
        box_fig = go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            annotations=[{'text': 'No data available.', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 15, 'color': '#9AA0AA'}}],
            margin=dict(t=40, b=40, l=40, r=40)
        )
    
    # Radar Chart
    radar_fig = go.Figure()
    radar_df = engine.generate_normalized_radar_metrics([d1, d2] if d2 else [d1], season)
    if not radar_df.empty:
        dims = ['Qualifying Pace', 'Race Craft', 'Overtaking Efficiency', 'Scoring Capacity', 'Lap Consistency']
        for idx, driver_name in enumerate([d1, d2] if d2 else [d1]):
            row = radar_df[radar_df['driver_name'] == driver_name]
            if not row.empty:
                radar_fig.add_trace(go.Scatterpolar(r=[row.iloc[0][d] for d in dims], theta=dims, fill='toself', name=driver_name, line=dict(color='#00E5FF' if idx == 0 else '#FF8A3D')))
        radar_fig.update_layout(
            title="Diagnostic Fingerprint",
            polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, range=[0, 100], gridcolor='#2A2E37', linecolor='#2A2E37', color='#9AA0AA'), angularaxis=dict(gridcolor='#2A2E37', linecolor='#2A2E37', color='#F5F6F7')),
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor='center'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F5F6F7'), margin=dict(t=50, b=80, l=40, r=40)
        )
    else:
        radar_fig = go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            annotations=[{'text': 'No data available.', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 15, 'color': '#9AA0AA'}}],
            margin=dict(t=40, b=40, l=40, r=40)
        )
    
    return kpis['pts'], kpis['avg_fin'], kpis['best_fin'], kpis['dnf_rate'], line_fig, box_fig, radar_fig


# Callback 7: Constructor Page - Tab Visibility
@app.callback(
    [Output("panel-charts-constructor", "style"),
     Output("panel-drilldown-constructor", "style"),
     Output("panel-tables-constructor", "style")],
    Input("view-tabs-constructor", "value")
)
def switch_constructor_panel(tab):
    hidden = {"display": "none"}
    visible = {"display": "block"}
    return (
        visible if tab == "tab-charts" else hidden,
        visible if tab == "tab-drilldown" else hidden,
        visible if tab == "tab-tables" else hidden,
    )


# Callback 8: Constructor Page - Reset Filters
@app.callback(
    [Output("constructor-select", "value"),
     Output("year-slider-constructor", "value"),
     Output("metric-radio", "value")],
    Input("btn-reset-constructor", "n_clicks"),
    prevent_initial_call=True
)
def reset_constructor_filters(n_clicks):
    df = load_data()
    constructor_season = aggregate_constructor_season(df)
    all_constructors = sorted(constructor_season["constructor_name"].unique())
    default_constructors = [c for c in ["Mercedes", "Red Bull", "Ferrari", "McLaren"] if c in all_constructors] or all_constructors[:4]
    year_min, year_max = int(df["year"].min()), int(df["year"].max())
    return default_constructors, [year_min, year_max], "season_points"


# Callback 9: Constructor Page - Main Charts
@app.callback(
    [Output("line-chart-constructor", "figure"),
     Output("bar-chart-constructor", "figure"),
     Output("area-chart-constructor", "figure"),
     Output("insights-constructor", "children"),
     Output("kpi-cards-constructor", "children")],
    [Input("constructor-select", "value"),
     Input("year-slider-constructor", "value"),
     Input("metric-radio", "value")]
)
def update_constructor_charts(selected_constructors, year_range, metric):
    df = load_data()
    constructor_season = aggregate_constructor_season(df)
    points_share = aggregate_points_share(df)
    
    if not selected_constructors:
        empty = go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            title="Select at least one constructor", font=dict(color='#F5F6F7'),
            annotations=[{'text': 'Select at least one constructor from the sidebar.', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 14, 'color': '#9AA0AA'}}]
        )
        warning = dbc.Alert("Select at least one constructor from the sidebar.", color="warning")
        return empty, empty, empty, warning, warning
    
    y0, y1 = year_range
    filtered = constructor_season[
        constructor_season["constructor_name"].isin(selected_constructors) &
        constructor_season["year"].between(y0, y1)
    ]
    filtered_share = points_share[
        points_share["constructor_name"].isin(selected_constructors) &
        points_share["year"].between(y0, y1)
    ]
    
    # Line Chart
    def build_metric_frame(filtered_season, filtered_share, metric):
        if metric == "points_share_pct":
            d = filtered_share.rename(columns={"points_share_pct": "value"}).copy()
            ylabel = "Points Share (%)"
        elif metric == "cumulative":
            d = filtered_season.sort_values(["constructor_name", "year"]).copy()
            d["value"] = d.groupby("constructor_name")["season_points"].cumsum()
            ylabel = "Cumulative Points"
        else:
            d = filtered_season.copy()
            d["value"] = d["season_points"]
            ylabel = "Season Points"
        return d, ylabel
    
    line_df, ylabel = build_metric_frame(filtered, filtered_share, metric)
    hover_cols = ["wins", "podiums", "dnf_rate_pct"]
    line_df = line_df.drop(columns=[c for c in hover_cols if c in line_df.columns])
    line_df = line_df.merge(
        filtered[["year", "constructor_name"] + hover_cols],
        on=["year", "constructor_name"],
        how="left",
    )
    
    color_map = {c: _PALETTE[i % len(_PALETTE)] for i, c in enumerate(selected_constructors)}
    
    fig_line = px.line(
        line_df,
        x="year",
        y="value",
        color="constructor_name",
        markers=True,
        custom_data=["constructor_name", "wins", "podiums", "dnf_rate_pct"],
        color_discrete_map=color_map,
        labels={"value": ylabel, "year": "Season", "constructor_name": "Constructor"},
        title="Constructor Points by Season",
    )
    fig_line.update_traces(
        line=dict(width=3),
        marker=dict(size=9, line=dict(width=1, color='#15181D')),
        hovertemplate=(
            "<b>%{customdata[0]}</b> — %{x}<br>"
            + ylabel + ": %{y:.1f}<br>"
            "Wins: %{customdata[1]} | Podiums: %{customdata[2]}<br>"
            "DNF rate: %{customdata[3]:.1f}%<extra></extra>"
        ),
    )
    fig_line.update_layout(
        hovermode="closest",
        legend_title_text="Constructor",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#F5F6F7'),
        margin=dict(l=50, r=30, t=60, b=40)
    )
    fig_line.update_xaxes(gridcolor='#2A2E37', zerolinecolor='#2A2E37')
    fig_line.update_yaxes(gridcolor='#2A2E37', zerolinecolor='#2A2E37')
    
    # Bar Chart
    reliability_long = filtered.melt(
        id_vars=["year", "constructor_name"],
        value_vars=["finishes", "dnfs"],
        var_name="outcome",
        value_name="count",
    )
    reliability_long["outcome"] = reliability_long["outcome"].map({"finishes": "Finished", "dnfs": "DNF"})
    n_facets = max(len(selected_constructors), 1)
    fig_bar = px.bar(
        reliability_long,
        x="year",
        y="count",
        color="outcome",
        facet_col="constructor_name",
        facet_col_wrap=min(n_facets, 4),
        barmode="stack",
        color_discrete_map={"Finished": "#2ECC71", "DNF": "#E10600"},
        labels={"count": "Entries", "year": "Season"},
        title="Finish vs DNF Composition by Constructor and Season",
    )
    fig_bar.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#F5F6F7'),
        margin=dict(l=50, r=30, t=60, b=40)
    )
    fig_bar.update_xaxes(gridcolor='#2A2E37', zerolinecolor='#2A2E37')
    fig_bar.update_yaxes(gridcolor='#2A2E37', zerolinecolor='#2A2E37')
    
    # Area Chart
    fig_area = px.area(
        filtered_share,
        x="year",
        y="points_share_pct",
        color="constructor_name",
        color_discrete_map=color_map,
        labels={"points_share_pct": "Share of Total Season Points (%)", "year": "Season"},
        title="Constructor Points Share — Dominance Across Seasons",
    )
    fig_area.update_traces(
        line=dict(width=1.5),
        hovertemplate="<b>%{fullData.name}</b> — %{x}<br>Share: %{y:.1f}%<extra></extra>",
    )
    fig_area.update_layout(
        legend_title_text="Constructor",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#F5F6F7'),
        margin=dict(l=50, r=30, t=60, b=40)
    )
    fig_area.update_xaxes(gridcolor='#2A2E37', zerolinecolor='#2A2E37')
    fig_area.update_yaxes(gridcolor='#2A2E37', zerolinecolor='#2A2E37')
    
    # Insights
    insights = []
    trend = (
        filtered.sort_values("year")
        .groupby("constructor_name")
        .agg(first_points=("season_points", "first"), last_points=("season_points", "last"))
    )
    trend["delta"] = trend["last_points"] - trend["first_points"]
    best_improver = worst_decline = None
    if not trend.empty:
        best_improver = trend["delta"].idxmax()
        worst_decline = trend["delta"].idxmin()
        insights.append(
            f"{best_improver} showed the strongest improvement, gaining "
            f"{trend.loc[best_improver, 'delta']:.0f} points from {y0} to {y1}."
        )
        if trend.loc[worst_decline, "delta"] < 0:
            insights.append(
                f"{worst_decline} declined the most, losing "
                f"{abs(trend.loc[worst_decline, 'delta']):.0f} points over the same period."
            )
    avg_share = filtered_share.groupby("constructor_name")["points_share_pct"].mean()
    dominant = avg_share.idxmax() if not avg_share.empty else None
    if dominant is not None:
        insights.append(
            f"{dominant} was the most dominant constructor in the selected range, "
            f"averaging a {avg_share.loc[dominant]:.1f}% share of total season points."
        )
    reliability_avg = filtered.groupby("constructor_name")["dnf_rate_pct"].mean()
    most_reliable = None
    if not reliability_avg.empty:
        most_reliable = reliability_avg.idxmin()
        least_reliable = reliability_avg.idxmax()
        insights.append(
            f"{most_reliable} was the most reliable, with only "
            f"{reliability_avg.loc[most_reliable]:.1f}% average DNF rate, while "
            f"{least_reliable} struggled most with a {reliability_avg.loc[least_reliable]:.1f}% average DNF rate."
        )
    
    insights_children = [html.H5("📌 Constructor Insights", className="mb-3", style={'color': '#F5F6F7'})] + [
        html.Div(
            [html.Span(className="kpi-accent", style={'width': '4px', 'borderRadius': '4px', 'background': '#E10600', 'display': 'inline-block', 'height': '34px', 'marginRight': '10px', 'verticalAlign': 'middle'}), html.Span(text)],
            className="mb-2 d-flex align-items-center",
            style={'color': '#F5F6F7'}
        )
        for text in insights
    ]
    
    # KPI Cards
    total_points = int(filtered["season_points"].sum())
    
    def kpi_card(icon, label, value, sub=""):
        return dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.I(className=f"fa {icon} mb-2", style={"color": "#E10600", "fontSize": "1.1rem"}),
                    html.Div(label, className="text-uppercase text-muted small", style={'color': '#9AA0AA'}),
                    html.H4(value, className="mb-0", style={'color': '#F5F6F7'}),
                    html.Div(sub, className="text-muted small", style={'color': '#9AA0AA'}) if sub else None,
                ]),
                className="text-center kpi-card h-100",
                style={'background': '#1D2129', 'border': '1px solid #2A2E37', 'borderRadius': '14px', 'boxShadow': '0 4px 14px rgba(0,0,0,0.25)'}
            ),
            width=6,
            lg=3,
        )
    
    kpi_children = dbc.Row([
        kpi_card("fa-flag-checkered", "Total Points (selection)", f"{total_points:,}", f"{y0}–{y1}"),
        kpi_card("fa-crown", "Most Dominant", dominant or "—", f"{avg_share.loc[dominant]:.1f}% avg share" if dominant is not None else ""),
        kpi_card("fa-arrow-trend-up", "Best Improver", best_improver or "—", f"+{trend.loc[best_improver, 'delta']:.0f} pts" if best_improver is not None else ""),
        kpi_card("fa-shield-halved", "Most Reliable", most_reliable or "—", f"{reliability_avg.loc[most_reliable]:.1f}% DNF rate" if most_reliable is not None else ""),
    ], className="g-2")
    
    return fig_line, fig_bar, fig_area, insights_children, kpi_children


# Callback 10: Constructor Page - Click to Drilldown
@app.callback(
    [Output("drilldown-year-select", "value"),
     Output("drilldown-constructor-select", "value")],
    Input("line-chart-constructor", "clickData"),
    prevent_initial_call=True
)
def click_to_dropdowns(click_data):
    if not click_data or "points" not in click_data:
        return None, None
    point = click_data["points"][0]
    if "customdata" not in point or not point["customdata"]:
        return None, None
    return point.get("x"), point["customdata"][0]


# Callback 11: Constructor Page - Render Drilldown
@app.callback(
    [Output("drilldown-table", "data"),
     Output("drilldown-title", "children"),
     Output("drilldown-pie-constructor", "figure")],
    [Input("drilldown-year-select", "value"),
     Input("drilldown-constructor-select", "value")]
)
def render_drilldown(clicked_year, clicked_constructor):
    df = load_data()
    reliability_by_status = aggregate_reliability_by_status(df)
    
    if not clicked_year or not clicked_constructor:
        empty_fig = go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis={'visible': False}, yaxis={'visible': False},
            annotations=[{'text': 'Select a season & constructor to view breakdown', 'showarrow': False, 'font': {'size': 14, 'color': '#9AA0AA'}}]
        )
        return [], "No point selected yet", empty_fig
    
    subset = reliability_by_status[
        (reliability_by_status["year"] == clicked_year) &
        (reliability_by_status["constructor_name"] == clicked_constructor)
    ]
    title = f"DNF causes — {clicked_constructor}, {clicked_year}"
    if subset.empty:
        empty_fig = go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis={'visible': False}, yaxis={'visible': False},
            annotations=[{'text': 'No DNFs recorded', 'showarrow': False, 'font': {'size': 14, 'color': '#9AA0AA'}}]
        )
        return [], title + " (no DNFs recorded)", empty_fig
    
    fig_pie = px.pie(
        subset,
        names="status",
        values="count",
        hole=0.5,
        title=f"DNF Cause Breakdown — {clicked_constructor}, {clicked_year}",
        color_discrete_sequence=px.colors.sequential.Reds_r,
    )
    fig_pie.update_traces(textinfo="label+percent", marker=dict(line=dict(color='#1D2129', width=2)))
    fig_pie.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#F5F6F7')
    )
    return subset.to_dict("records"), title, fig_pie


# Callback 12: Constructor Page - Year-over-Year Table
@app.callback(
    Output("yoy-table-constructor", "data"),
    [Input("constructor-select", "value"),
     Input("year-slider-constructor", "value")]
)
def update_yoy_table(selected_constructors, year_range):
    df = load_data()
    year_over_year = aggregate_year_over_year_change(df)
    if not selected_constructors:
        return []
    y0, y1 = year_range
    filtered = year_over_year[
        year_over_year["constructor_name"].isin(selected_constructors) &
        year_over_year["year"].between(y0, y1)
    ]
    return filtered.to_dict("records")


# Callback 13: Constructor Page - CSV Export
@app.callback(
    Output("download-csv-constructor", "data"),
    Input("btn-download-constructor", "n_clicks"),
    [State("constructor-select", "value"),
     State("year-slider-constructor", "value")],
    prevent_initial_call=True
)
def export_csv(n_clicks, selected_constructors, year_range):
    df = load_data()
    constructor_season = aggregate_constructor_season(df)
    y0, y1 = year_range
    filtered = constructor_season[
        constructor_season["constructor_name"].isin(selected_constructors or []) &
        constructor_season["year"].between(y0, y1)
    ]
    return dcc.send_data_frame(filtered.to_csv, "constructor_evolution_filtered.csv", index=False)


# Callback 14: Toggle Sidebar
@app.callback(
    [Output('sidebar', 'className'),
     Output('sidebar-overlay', 'className')],
    [Input('toggle-sidebar-btn', 'n_clicks'),
     Input('sidebar-overlay', 'n_clicks')],
    [State('sidebar', 'className')]
)
def toggle_sidebar(btn_clicks, overlay_clicks, current_class):
    ctx = callback_context
    if not ctx.triggered:
        return current_class or 'sidebar', 'sidebar-overlay hidden'
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id in ['toggle-sidebar-btn', 'sidebar-overlay']:
        if current_class and 'open' in current_class:
            return 'sidebar', 'sidebar-overlay hidden'
        else:
            return 'sidebar open', 'sidebar-overlay visible'
    return current_class or 'sidebar', 'sidebar-overlay hidden'


# ============================================================
# CIRCUIT INTELLIGENCE CALLBACKS
# ============================================================

@app.callback(
    Output("selected-circuit-store", "data"),
    Input("circuit-fig-map", "clickData"),
    Input("circuit-fig-speed", "clickData"),
    Input("circuit-fig-gain", "clickData"),
    Input("circuit-fig-dnf", "clickData"),
    Input("circuit-fig-heatmap", "clickData"),
    Input("circuit-fig-bubble", "clickData"),
    Input("circuit-reset-selection-btn", "n_clicks"),
    State("selected-circuit-store", "data"),
    prevent_initial_call=True,
)
def update_circuit_selection(map_click, speed_click, gain_click, dnf_click,
                              heatmap_click, bubble_click, reset_clicks, current):
    trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "circuit-reset-selection-btn":
        return None
    
    clicked_circuit = None
    try:
        if trigger_id == "circuit-fig-map" and map_click:
            clicked_circuit = map_click["points"][0].get("hovertext")
        elif trigger_id in ("circuit-fig-speed", "circuit-fig-gain", "circuit-fig-dnf"):
            click = {"circuit-fig-speed": speed_click, "circuit-fig-gain": gain_click, "circuit-fig-dnf": dnf_click}[trigger_id]
            if click:
                clicked_circuit = click["points"][0].get("y")
        elif trigger_id == "circuit-fig-heatmap" and heatmap_click:
            clicked_circuit = heatmap_click["points"][0].get("x")
        elif trigger_id == "circuit-fig-bubble" and bubble_click:
            clicked_circuit = bubble_click["points"][0].get("hovertext")
    except (KeyError, IndexError, TypeError):
        clicked_circuit = None
    
    if not clicked_circuit:
        return no_update
    
    if clicked_circuit == current:
        return None
    return clicked_circuit


@app.callback(
    [Output("circuit-fig-map", "figure"),
     Output("circuit-fig-speed", "figure"),
     Output("circuit-fig-gain", "figure"),
     Output("circuit-fig-dnf", "figure"),
     Output("circuit-fig-heatmap", "figure"),
     Output("circuit-fig-bubble", "figure"),
     Output("circuit-kpi-circuits", "children"),
     Output("circuit-kpi-countries", "children"),
     Output("circuit-kpi-speed", "children"),
     Output("circuit-kpi-dnf", "children"),
     Output("circuit-insights-list", "children"),
     Output("circuit-selection-banner", "children")],
    [Input("circuit-year-slider", "value"),
     Input("circuit-country-filter", "value"),
     Input("circuit-constructor-filter", "value"),
     Input("circuit-topn-filter", "value"),
     Input("circuit-direction-filter", "value"),
     Input("circuit-heatmap-sort-metric", "value"),
     Input("selected-circuit-store", "data")]
)
def update_circuit_dashboard(year_range, countries, constructors, top_n, direction,
                              heatmap_metric, selected):
    df = load_circuit_data()
    dff = filter_circuit_data(df, year_range, countries, constructors)
    
    fig_map = build_circuit_map_fig(dff, selected)
    fig_speed = build_circuit_bar_fig(dff, "fastestLapSpeed", "🏎️ Fastest Circuits", top_n, direction, selected)
    fig_gain = build_circuit_bar_fig(dff, "positions_gained", "📈 Position Change by Circuit", top_n, direction, selected)
    fig_dnf = build_circuit_bar_fig(dff, "is_dnf", "⚠️ DNF Rate by Circuit", top_n, direction, selected)
    fig_heatmap = build_circuit_heatmap_fig(dff, heatmap_metric, selected)
    fig_bubble = build_circuit_bubble_fig(dff, selected)
    
    total_circuits, total_countries, avg_speed, avg_dnf = build_circuit_kpis(dff)
    insights = build_circuit_insights(dff)
    
    banner = f"🔎 Highlighting: {selected}" if selected else ""
    
    return (fig_map, fig_speed, fig_gain, fig_dnf, fig_heatmap, fig_bubble,
            f"{total_circuits}", f"{total_countries}", f"{avg_speed}", f"{avg_dnf}%",
            insights, banner)


# ============================================================
# RUN THE APP
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, port=8050)
