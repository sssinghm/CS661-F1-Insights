"""
Championship Evolution Page
Displays cumulative points and rank movement over seasons.
"""

from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_data, get_seasons, get_drivers, get_constructors, column_exists
from src.filter import apply_filters

logger = logging.getLogger(__name__)

# ============================================================
# LOAD DATA
# ============================================================
df = load_data()
seasons = get_seasons(df)
drivers = get_drivers(df)
constructors = get_constructors(df)


# ============================================================
# LAYOUT
# ============================================================
def create_layout():
    """Create the Championship Evolution page layout."""
    default_season = seasons[0] if seasons else 2024
    default_rounds = sorted(df[df['year'] == default_season]['round'].unique()) if 'year' in df.columns else []

    return html.Div([
        html.Div([
            html.H1("🏆 Championship Evolution"),
            html.P("Track how championship battles evolved race by race", className="page-description")
        ], className="page-header"),

        html.Div([
            html.Div([
                html.Label("Season"),
                dcc.Dropdown(
                    id='champ-season',
                    options=[{'label': str(s), 'value': s} for s in seasons],
                    value=default_season,
                    clearable=False
                )
            ], className="filter-group"),

            html.Div([
                html.Label("Driver"),
                dcc.Dropdown(
                    id='champ-driver',
                    options=[{'label': 'All Drivers', 'value': 'All'}] +
                            [{'label': d, 'value': d} for d in drivers[:20]],
                    value='All'
                )
            ], className="filter-group"),

            html.Div([
                html.Label("Constructor"),
                dcc.Dropdown(
                    id='champ-constructor',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': c, 'value': c} for c in constructors],
                    value='All'
                )
            ], className="filter-group"),

            html.Div([
                html.Label("Race Round"),
                dcc.Dropdown(
                    id='champ-round',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': f"Round {r}", 'value': r} for r in default_rounds],
                    value='All'
                )
            ], className="filter-group"),
        ], className="filters-bar"),

        html.Div(id='champ-kpi-cards', className="kpi-grid"),

        html.Div([
            html.Div([
                html.H3("📈 Cumulative Championship Points", className="chart-title"),
                dcc.Loading(
                    type="circle",
                    children=dcc.Graph(
                        id='champ-points-chart',
                        config={'displayModeBar': True, 'displaylogo': False, 'responsive': True}
                    )
                )
            ], className="chart-card"),

            html.Div([
                html.H3("📊 Championship Rank Movement", className="chart-title"),
                dcc.Loading(
                    type="circle",
                    children=dcc.Graph(
                        id='champ-rank-chart',
                        config={'displayModeBar': True, 'displaylogo': False, 'responsive': True}
                    )
                )
            ], className="chart-card"),
        ], className="charts-grid"),

        html.Div([
            html.Div([
                html.Span("💡", className="insights-icon"),
                html.H3("Key Insights")
            ], className="insights-header"),
            html.Div(id='champ-insights', className="insights-grid")
        ], className="insights-section"),

    ], className="page-content")


# ============================================================
# CHART FUNCTIONS
# ============================================================
def create_empty_figure(message):
    """Create an empty figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color='#8888aa')
    )
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=450,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig


def create_points_chart(df_filtered, season, selected_driver=None):
    """Create cumulative championship points line chart."""
    if df_filtered.empty:
        return create_empty_figure("No data available")

    top_drivers = df_filtered.groupby('driver_name')['championship_points'].max().nlargest(10).index.tolist()
    display_drivers = [selected_driver] if selected_driver and selected_driver != 'All' else top_drivers

    plot_df = df_filtered[df_filtered['driver_name'].isin(display_drivers)].sort_values(['driver_name', 'round'])

    fig = px.line(
        plot_df,
        x='round',
        y='championship_points',
        color='driver_name',
        title=f'Cumulative Championship Points - {season}',
        labels={'round': 'Race Round', 'championship_points': 'Cumulative Points', 'driver_name': 'Driver'},
        markers=True,
        line_shape='spline'
    )

    fig.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        xaxis=dict(title='Race Round', dtick=1, gridcolor='#2a2a3e'),
        yaxis=dict(title='Cumulative Points', gridcolor='#2a2a3e'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500,
        margin=dict(l=40, r=20, t=40, b=40)
    )
    return fig


def create_rank_chart(df_filtered, season, selected_driver=None):
    """Create championship rank movement chart."""
    if df_filtered.empty:
        return create_empty_figure("No data available")

    rank_df = df_filtered.copy()
    rank_df['championship_position'] = rank_df.groupby('round')['championship_points'].rank(method='first', ascending=False)

    top_drivers = rank_df.groupby('driver_name')['championship_points'].max().nlargest(10).index.tolist()
    display_drivers = [selected_driver] if selected_driver and selected_driver != 'All' else top_drivers

    plot_df = rank_df[rank_df['driver_name'].isin(display_drivers)].sort_values(['round', 'championship_position'])

    fig = px.line(
        plot_df,
        x='round',
        y='championship_position',
        color='driver_name',
        title=f'Championship Position Movement - {season}',
        labels={'round': 'Race Round', 'championship_position': 'Championship Position', 'driver_name': 'Driver'},
        markers=True,
        line_shape='spline'
    )

    fig.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        xaxis=dict(title='Race Round', dtick=1, gridcolor='#2a2a3e'),
        yaxis=dict(title='Championship Position', autorange='reversed', dtick=1, gridcolor='#2a2a3e'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500,
        margin=dict(l=40, r=20, t=40, b=40)
    )
    return fig


def create_kpi_cards(df_filtered, season):
    """Create KPI cards."""
    if df_filtered.empty:
        return html.Div("No data available", className="text-muted")

    total_drivers = df_filtered['driver_name'].nunique()
    total_races = df_filtered['round'].nunique()

    leader_data = df_filtered.nlargest(1, 'championship_points').iloc[0]
    leader = leader_data.get('driver_name', 'N/A')
    leader_points = leader_data.get('championship_points', 0)

    top_two = df_filtered.nlargest(2, 'championship_points')
    gap = top_two.iloc[0]['championship_points'] - top_two.iloc[1]['championship_points'] if len(top_two) >= 2 else 0
    second = top_two.iloc[1]['driver_name'] if len(top_two) >= 2 else "N/A"

    kpis = [
        {'icon': '🏆', 'value': leader, 'label': 'Championship Leader'},
        {'icon': '⭐', 'value': f"{leader_points:.0f}", 'label': 'Leader Points'},
        {'icon': '📊', 'value': f"{gap:.0f}", 'label': f'Gap to 2nd ({second})'},
        {'icon': '👥', 'value': total_drivers, 'label': 'Drivers in Season'},
        {'icon': '🏁', 'value': total_races, 'label': 'Races Completed'},
    ]

    return html.Div([
        html.Div([
            html.Div(kpi['icon'], className="kpi-icon"),
            html.Div(str(kpi['value']), className="kpi-value"),
            html.Div(kpi['label'], className="kpi-label")
        ], className="kpi-card") for kpi in kpis
    ])


def get_insights(df_filtered, season):
    """Generate insights."""
    if df_filtered.empty:
        return [html.Div("No data available", className="insight-item")]

    insights = []
    leader_data = df_filtered.nlargest(1, 'championship_points').iloc[0]
    leader = leader_data.get('driver_name', 'Unknown')
    points = leader_data.get('championship_points', 0)

    insights.append(
        html.Div(f"🏆 <strong>{leader}</strong> leads with <strong>{points:.0f}</strong> points",
                 className="insight-item")
    )

    top_two = df_filtered.nlargest(2, 'championship_points')
    if len(top_two) >= 2:
        gap = top_two.iloc[0]['championship_points'] - top_two.iloc[1]['championship_points']
        second = top_two.iloc[1]['driver_name']
        insights.append(
            html.Div(f"📈 <strong>{gap:.0f}</strong> point gap to <strong>{second}</strong>",
                     className="insight-item")
        )

    insights.append(
        html.Div(f"👥 <strong>{df_filtered['driver_name'].nunique()}</strong> drivers this season",
                 className="insight-item")
    )

    return insights


# ============================================================
# SINGLE CALLBACK - ALL UPDATES IN ONE PLACE
# ============================================================
@callback(
    [Output('champ-kpi-cards', 'children'),
     Output('champ-points-chart', 'figure'),
     Output('champ-rank-chart', 'figure'),
     Output('champ-insights', 'children'),
     Output('champ-round', 'options')],
    [Input('champ-season', 'value'),
     Input('champ-driver', 'value'),
     Input('champ-constructor', 'value'),
     Input('champ-round', 'value')]
)
def update_championship(season, driver, constructor, race_round):
    """Single callback handles ALL updates."""
    if season is None:
        season = seasons[0] if seasons else 2024

    filtered = apply_filters(df, season, driver, constructor)

    if race_round and race_round != 'All':
        filtered = filtered[filtered['round'] == int(race_round)]

    season_rounds = sorted(df[df['year'] == int(season)]['round'].unique()) if season else []
    round_options = [{'label': 'All', 'value': 'All'}] + \
                    [{'label': f"Round {r}", 'value': r} for r in season_rounds]

    if filtered.empty:
        return (html.Div("No data", className="text-muted"),
                create_empty_figure("No data available"),
                create_empty_figure("No data available"),
                [html.Div("No data", className="insight-item")],
                round_options)

    kpis = create_kpi_cards(filtered, season)
    points_fig = create_points_chart(filtered, season, driver)
    rank_fig = create_rank_chart(filtered, season, driver)
    insights = get_insights(filtered, season)

    return kpis, points_fig, rank_fig, insights, round_options