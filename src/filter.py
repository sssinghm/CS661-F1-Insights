"""
Global Filter Module for F1 Visual Analytics Dashboard
Provides reusable filtering functions for all pages.
"""

import logging

logger = logging.getLogger(__name__)


def filter_by_season(df, season):
    """Filter DataFrame by season/year."""
    if season is None or str(season).upper() == 'ALL':
        return df

    try:
        season = int(season)
        if 'year' in df.columns:
            return df[df['year'] == season]
        elif 'season' in df.columns:
            return df[df['season'] == season]
        return df
    except ValueError:
        return df


def filter_by_driver(df, driver):
    """Filter DataFrame by driver name."""
    if driver is None or str(driver).upper() == 'ALL':
        return df

    if 'driver_name' in df.columns:
        return df[df['driver_name'] == driver]
    elif 'driver' in df.columns:
        return df[df['driver'] == driver]
    return df


def filter_by_constructor(df, constructor):
    """Filter DataFrame by constructor name."""
    if constructor is None or str(constructor).upper() == 'ALL':
        return df

    if 'constructor_name' in df.columns:
        return df[df['constructor_name'] == constructor]
    elif 'constructor' in df.columns:
        return df[df['constructor'] == constructor]
    return df


def filter_by_circuit(df, circuit):
    """Filter DataFrame by circuit name."""
    if circuit is None or str(circuit).upper() == 'ALL':
        return df

    if 'circuit_name' in df.columns:
        return df[df['circuit_name'] == circuit]
    elif 'circuit' in df.columns:
        return df[df['circuit'] == circuit]
    return df


def filter_by_round(df, race_round):
    """Filter DataFrame by round number."""
    if race_round is None or str(race_round).upper() == 'ALL':
        return df

    try:
        race_round = int(race_round)
        if 'round' in df.columns:
            return df[df['round'] == race_round]
        return df
    except ValueError:
        return df


def apply_filters(df, season=None, driver=None, constructor=None,
                  circuit=None, race_round=None):
    """Apply multiple filters to the DataFrame."""
    filtered = df.copy()
    filtered = filter_by_season(filtered, season)
    filtered = filter_by_driver(filtered, driver)
    filtered = filter_by_constructor(filtered, constructor)
    filtered = filter_by_circuit(filtered, circuit)
    filtered = filter_by_round(filtered, race_round)
    return filtered


def get_filter_options(df):
    """Get all available filter options from the dataset."""
    from src.data_loader import get_seasons, get_drivers, get_constructors, get_circuits, get_rounds

    return {
        'seasons': get_seasons(df),
        'drivers': get_drivers(df),
        'constructors': get_constructors(df),
        'circuits': get_circuits(df),
        'rounds': get_rounds(df)
    }