import pandas as pd
import streamlit as st
import plotly.express as px


DATA_PATH = "data/derived_f1_metrics.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, na_values=["\\N"])

    numeric_cols = [
        "year", "grid", "positionOrder", "positions_gained",
        "pit_stop_count", "avg_pit_ms", "fastest_pit_ms", "slowest_pit_ms",
        "points", "is_dnf"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["avg_pit_s"] = df["avg_pit_ms"] / 1000
    df["fastest_pit_s"] = df["fastest_pit_ms"] / 1000
    df["slowest_pit_s"] = df["slowest_pit_ms"] / 1000

    df["normal_pit_stop"] = (
        (df["pit_stop_count"] > 0) &
        (df["avg_pit_ms"].between(15000, 60000))
    )

    df["valid_grid"] = df["grid"] > 0
    df["race_label"] = df["year"].astype(int).astype(str) + " - " + df["race_name"].astype(str)

    return df


def apply_sidebar_filters(df):
    st.sidebar.header("Filters")

    years = sorted(df["year"].dropna().astype(int).unique())
    selected_years = st.sidebar.multiselect(
        "Season",
        years,
        default=years
    )

    filtered = df[df["year"].isin(selected_years)]

    constructors = sorted(filtered["constructor_name"].dropna().unique())
    selected_constructors = st.sidebar.multiselect(
        "Constructor",
        constructors
    )

    if selected_constructors:
        filtered = filtered[filtered["constructor_name"].isin(selected_constructors)]

    drivers = sorted(filtered["driver_name"].dropna().unique())
    selected_drivers = st.sidebar.multiselect(
        "Driver",
        drivers
    )

    if selected_drivers:
        filtered = filtered[filtered["driver_name"].isin(selected_drivers)]

    include_long_pits = st.sidebar.checkbox(
        "Include long pit stops > 60s",
        value=False
    )

    exclude_grid_zero = st.sidebar.checkbox(
        "Exclude grid = 0 rows",
        value=True
    )

    return filtered, include_long_pits, exclude_grid_zero


def build_strategy_scatter(df):
    fig = px.scatter(
        df,
        x="avg_pit_s",
        y="positions_gained",
        size="pit_stop_count",
        color="constructor_name",
        hover_data={
            "driver_name": True,
            "race_name": True,
            "year": True,
            "constructor_name": True,
            "pit_stop_count": True,
            "avg_pit_s": ":.2f",
            "positionOrder": True,
            "positions_gained": True,
            "avg_pit_ms": False,
        },
        title="Pit-stop Duration vs Positions Gained",
        labels={
            "avg_pit_s": "Average pit-stop duration (seconds)",
            "positions_gained": "Positions gained",
            "constructor_name": "Constructor",
            "pit_stop_count": "Pit-stop count",
            "positionOrder": "Final position",
        },
        size_max=18,
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        annotation_text="No position change",
        annotation_position="top left"
    )

    fig.update_layout(
        height=650,
        legend_title_text="Constructor"
    )

    return fig

def build_constructor_boxplot(df):
    constructor_order = (
        df.groupby("constructor_name")["avg_pit_s"]
        .median()
        .sort_values()
        .index
        .tolist()
    )

    fig = px.box(
        df,
        x="constructor_name",
        y="avg_pit_s",
        color="constructor_name",
        category_orders={"constructor_name": constructor_order},
        points="outliers",
        hover_data={
            "driver_name": True,
            "race_name": True,
            "year": True,
            "pit_stop_count": True,
            "avg_pit_s": ":.2f",
            "constructor_name": False,
        },
        title="Pit-stop Duration Consistency by Constructor",
        labels={
            "constructor_name": "Constructor",
            "avg_pit_s": "Average pit-stop duration (seconds)",
        },
    )

    fig.update_layout(
        height=650,
        showlegend=False,
        xaxis_tickangle=-45,
    )

    return fig

def build_pit_duration_histogram(df):
    fig = px.histogram(
        df,
        x="avg_pit_s",
        nbins=35,
        color="constructor_name",
        marginal="box",
        title="Distribution of Average Pit-stop Duration",
        labels={
            "avg_pit_s": "Average pit-stop duration (seconds)",
            "constructor_name": "Constructor",
            "count": "Number of driver-race records",
        },
    )

    fig.update_layout(
        height=600,
        bargap=0.05,
        legend_title_text="Constructor",
    )

    return fig

def build_race_dotplot(df):
    race_df = df.copy()

    race_df = race_df.sort_values("positionOrder", ascending=False)

    fig = px.scatter(
        race_df,
        x="positionOrder",
        y="driver_name",
        size="pit_stop_count",
        color="constructor_name",
        symbol="is_dnf",
        hover_data={
            "driver_name": True,
            "constructor_name": True,
            "grid": True,
            "positionOrder": True,
            "positions_gained": True,
            "pit_stop_count": True,
            "avg_pit_s": ":.2f",
            "status": True,
            "is_dnf": True,
        },
        title="Race-level Strategy Comparison",
        labels={
            "positionOrder": "Final classified position",
            "driver_name": "Driver",
            "constructor_name": "Constructor",
            "pit_stop_count": "Pit-stop count",
            "is_dnf": "DNF",
        },
        size_max=22,
    )

    fig.update_layout(
        height=700,
        yaxis_title="Driver",
        xaxis_title="Final classified position",
        legend_title_text="Constructor / DNF",
    )

    fig.update_xaxes(autorange="reversed")

    return fig

def build_correlation_heatmap(df):
    corr_cols = [
        "pit_stop_count",
        "avg_pit_s",
        "fastest_pit_s",
        "slowest_pit_s",
        "positions_gained",
        "positionOrder",
        "points",
        "avg_lap_difference",
        "fastest_lap_difference",
        "pace_rank",
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

    available_cols = [col for col in corr_cols if col in df.columns]

    corr_df = df[available_cols].copy()
    corr_matrix = corr_df.corr(numeric_only=True)

    corr_matrix = corr_matrix.rename(index=display_names, columns=display_names)

    fig = px.imshow(
        corr_matrix,
        text_auto=".2f",
        aspect="auto",
        range_color=[-1, 1],
        title="Correlation Between Strategy Metrics and Race Outcomes",
        labels={"color": "Correlation"},
    )

    fig.update_layout(
        height=750,
        xaxis_title="Metric",
        yaxis_title="Metric",
        margin=dict(l=120, r=80, t=100, b=140),
    )

    fig.update_xaxes(tickangle=-35)

    return fig

def show_chart_justifications():
    st.subheader("Chart Justifications")

    with st.expander("Why these charts were used"):
        st.markdown(
            """
            **1. Bubble scatter plot — Pit-stop duration vs positions gained**  
            Used to study the relationship between pit-stop execution and race outcome.  
            A scatter plot is better than a bar chart here because both variables are numeric and the goal is to observe relationship patterns.

            **2. Box plot — Pit-stop duration by constructor**  
            Used to compare constructor-wise pit-stop consistency.  
            A box plot is better than an average bar chart because it shows median, spread, and outliers.

            **3. Histogram — Pit-stop duration distribution**  
            Used to identify the normal pit-stop range and unusually long stops.  
            A histogram is suitable because pit duration is a continuous numeric variable.

            **4. Race-level dot plot — Strategy comparison within one race**  
            Used to compare drivers in a selected race by final position, pit count, constructor, and DNF status.  
            A dot plot is clearer than a table because it visually shows strategy and outcome together.

            **5. Correlation heatmap — Strategy and outcome relationships**  
            Used as a supporting overview of relationships between strategy metrics and race outcomes.  
            It is not used to claim causation, only to identify patterns.
            """
        )

def show_key_insights(df):
    st.subheader("Key Insights")

    normal_df = df[df["normal_pit_stop"]].copy()

    if normal_df.empty:
        st.warning("No data available for insights.")
        return

    median_pit = normal_df["avg_pit_s"].median()

    constructor_summary = (
        normal_df.groupby("constructor_name")
        .agg(
            median_pit_s=("avg_pit_s", "median"),
            avg_positions_gained=("positions_gained", "mean"),
            records=("avg_pit_s", "count"),
        )
        .query("records >= 10")
        .sort_values("median_pit_s")
        .reset_index()
    )

    fastest_team = constructor_summary.iloc[0]

    pit_count_summary = (
    df[df["pit_stop_count"] > 0]
    .groupby("pit_stop_count")
    .agg(
        avg_positions_gained=("positions_gained", "mean"),
        records=("positions_gained", "count"),
    )
    .query("records >= 30")
    .sort_values("avg_positions_gained", ascending=False)
)

    best_pit_count = pit_count_summary.index[0]
    best_gain = pit_count_summary.iloc[0]["avg_positions_gained"]
    best_count_records = pit_count_summary.iloc[0]["records"]

    st.markdown(
    f"""
    - The median normal pit-stop duration in the selected data is **{median_pit:.2f} seconds**.
    - **{fastest_team['constructor_name']}** has the fastest median pit-stop duration among constructors with enough records, at **{fastest_team['median_pit_s']:.2f} seconds**.
    - Among pit-stop counts with at least 30 records, **{int(best_pit_count)} stops** has the highest average position gain, with **{best_gain:.2f} positions** across **{int(best_count_records)} records**.
    """
)


def render():
    st.title("Race Strategy Analysis")

    st.write(
        "This page analyzes how pit-stop count, pit-stop duration, and race strategy "
        "relate to race outcomes such as final position and positions gained."
    )

    df = load_data()

    st.subheader("Dataset checks")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total records", len(df))
    c2.metric("Pit stops = 0", int((df["pit_stop_count"] == 0).sum()))
    c3.metric("Long pit stops > 60s", int((df["avg_pit_ms"] > 60000).sum()))
    c4.metric("Grid = 0 rows", int((df["grid"] == 0).sum()))

    st.info(
        "Pit-duration plots exclude zero-stop rows and extreme pit stops by default. "
        "Grid = 0 rows can be excluded because they distort positions gained."
    )

    filtered_df, include_long_pits, exclude_grid_zero = apply_sidebar_filters(df)

    scatter_df = filtered_df[filtered_df["pit_stop_count"] > 0].copy()

    if not include_long_pits:
        scatter_df = scatter_df[scatter_df["normal_pit_stop"]]

    if exclude_grid_zero:
        scatter_df = scatter_df[scatter_df["valid_grid"]]

    st.subheader("Pit-stop execution vs race outcome")

    st.write(
        "This bubble scatter plot compares average pit-stop duration with positions gained. "
        "Bubble size represents pit-stop count. Points above zero indicate drivers who gained positions."
    )

    if scatter_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        fig = build_strategy_scatter(scatter_df)
        st.plotly_chart(fig, use_container_width=True)

        avg_pit = scatter_df["avg_pit_s"].mean()
        avg_gain = scatter_df["positions_gained"].mean()

        c1, c2, c3 = st.columns(3)
        c1.metric("Filtered records", len(scatter_df))
        c2.metric("Average pit duration", f"{avg_pit:.2f}s")
        c3.metric("Average positions gained", f"{avg_gain:.2f}")

    st.subheader("Constructor pit-stop consistency")

    st.write(
        "This box plot compares average pit-stop duration across constructors. "
        "Lower median values indicate faster pit execution, while wider boxes and more outliers indicate inconsistency."
    )

    box_df = filtered_df[filtered_df["normal_pit_stop"]].copy()

    if box_df.empty:
        st.warning("No constructor pit-stop data available for the selected filters.")
    else:
        fig_box = build_constructor_boxplot(box_df)
        st.plotly_chart(fig_box, use_container_width=True)

        constructor_summary = (
            box_df.groupby("constructor_name")
            .agg(
                median_pit_s=("avg_pit_s", "median"),
                avg_pit_s=("avg_pit_s", "mean"),
                pit_records=("avg_pit_s", "count"),
            )
            .sort_values("median_pit_s")
            .reset_index()
        )

        fastest_constructor = constructor_summary.iloc[0]

        st.success(
            f"Fastest median constructor in selected data: "
            f"{fastest_constructor['constructor_name']} "
            f"with median pit duration {fastest_constructor['median_pit_s']:.2f}s."
        )  

    st.subheader("Pit-stop duration distribution")

    st.write(
        "This histogram shows how pit-stop durations are distributed across the selected data. "
        "It helps identify the normal pit-stop range and whether some stops are unusually long."
    )

    hist_df = filtered_df[filtered_df["normal_pit_stop"]].copy()

    if hist_df.empty:
        st.warning("No pit-stop duration data available for the selected filters.")
    else:
        fig_hist = build_pit_duration_histogram(hist_df)
        st.plotly_chart(fig_hist, use_container_width=True)

        median_pit = hist_df["avg_pit_s"].median()
        q1 = hist_df["avg_pit_s"].quantile(0.25)
        q3 = hist_df["avg_pit_s"].quantile(0.75)

        c1, c2, c3 = st.columns(3)
        c1.metric("Median pit duration", f"{median_pit:.2f}s")
        c2.metric("25th percentile", f"{q1:.2f}s")
        c3.metric("75th percentile", f"{q3:.2f}s") 

    st.subheader("Race-level strategy comparison")

    st.write(
        "This dot plot compares all drivers within a selected race. "
        "Final position is shown on the x-axis, driver is on the y-axis, "
        "bubble size represents pit-stop count, and color represents constructor."
    )

    race_options = sorted(filtered_df["race_label"].dropna().unique())

    if not race_options:
        st.warning("No race data available for the selected filters.")
    else:
        selected_race = st.selectbox(
            "Select race for race-level comparison",
            race_options
        )

        race_df = filtered_df[filtered_df["race_label"] == selected_race].copy()

        if exclude_grid_zero:
            race_df = race_df[race_df["valid_grid"]]

        if race_df.empty:
            st.warning("No race-level data available for the selected race.")
        else:
            fig_race = build_race_dotplot(race_df)
            st.plotly_chart(fig_race, use_container_width=True)

            winner = race_df.sort_values("positionOrder").iloc[0]
            most_stops = race_df.sort_values("pit_stop_count", ascending=False).iloc[0]
            best_gain = race_df.sort_values("positions_gained", ascending=False).iloc[0]

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("**Winner**")
                st.markdown(f"### {winner['driver_name']}")

            with c2:
                st.markdown("**Most pit stops**")
                st.markdown(
                f"### {most_stops['driver_name']}"
                f"\n{int(most_stops['pit_stop_count'])} pit stops"
            )

            with c3:
                st.markdown("**Best position gain**")
                gain = int(best_gain["positions_gained"])
                gain_text = f"+{gain}" if gain > 0 else str(gain)
                st.markdown(
                f"### {best_gain['driver_name']}"
                f"\n{gain_text} positions"
                )

    st.subheader("Strategy metric correlation heatmap")

    st.write(
        "This heatmap shows correlation between pit-stop strategy variables and race outcome variables. "
        "Values close to +1 indicate a positive relationship, values close to -1 indicate a negative relationship, "
        "and values close to 0 indicate weak linear relationship."
    )

    st.warning(
        "Correlation does not prove causation. This plot shows patterns only; it does not prove that pit stops directly caused the result."
    )

    corr_df = filtered_df[filtered_df["pit_stop_count"] > 0].copy()

    if not include_long_pits:
        corr_df = corr_df[corr_df["normal_pit_stop"]]

    if exclude_grid_zero:
        corr_df = corr_df[corr_df["valid_grid"]]

    if corr_df.empty:
        st.warning("No data available for correlation heatmap with the selected filters.")
    else:
        fig_corr = build_correlation_heatmap(corr_df)
        st.plotly_chart(fig_corr, use_container_width=True)   

    show_key_insights(filtered_df)
    show_chart_justifications()             

if __name__ == "__main__":
    render()