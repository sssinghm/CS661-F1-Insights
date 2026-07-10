"""
Data Loader Module for F1 Visual Analytics Dashboard
Automatically detects and loads the F1 dataset.
"""

import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)


def load_data(file_path=None):
    """
    Load the F1 dataset from CSV file.

    Parameters
    ----------
    file_path : str, optional
        Path to the CSV file. If None, attempts to find it.

    Returns
    -------
    pandas.DataFrame
        Loaded DataFrame with F1 race data.
    """
    if file_path is None:
        possible_paths = [
            'data/master_f1_final_dnf_fixed.csv',
            'data/derived_f1_metrics.csv',
            'data/cleaned_f1.csv',
            '../data/master_f1_final_dnf_fixed.csv',
            '../data/derived_f1_metrics.csv',
            '../data/cleaned_f1.csv'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break

    if file_path and os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            logger.info(f"✅ Loaded {len(df):,} records from {file_path}")
            logger.info(f"   Columns: {list(df.columns)}")
            return df
        except Exception as e:
            logger.error(f"❌ Error loading {file_path}: {e}")
            return create_sample_data()

    logger.warning("⚠️ No data file found. Using sample data.")
    return create_sample_data()


def create_sample_data():
    """Create sample F1 data for testing."""
    logger.info("📊 Generating sample F1 data...")

    data = []
    seasons = [2021, 2022, 2023, 2024]
    drivers = ['Verstappen', 'Hamilton', 'Leclerc', 'Norris', 'Perez', 'Sainz', 'Russell']

    for season in seasons:
        for driver in drivers:
            points = 0
            wins = 0
            podiums = 0
            for r in range(1, 23):
                import hashlib
                hash_val = int(hashlib.md5(f"{driver}{season}{r}".encode()).hexdigest()[:4], 16) % 15
                base_points = 25 if driver == 'Verstappen' and season >= 2022 else 18
                if season == 2021 and driver in ['Verstappen', 'Hamilton']:
                    base_points = 20
                race_points = max(0, base_points + hash_val - 5)
                points += race_points
                if race_points >= 20:
                    wins += 1
                if race_points >= 15:
                    podiums += 1
                data.append({
                    'year': season,
                    'round': r,
                    'driver_name': driver,
                    'championship_points': points,
                    'constructor_name': 'Red Bull' if driver in ['Verstappen', 'Perez'] else
                    'Mercedes' if driver in ['Hamilton', 'Russell'] else
                    'Ferrari' if driver in ['Leclerc', 'Sainz'] else 'McLaren',
                    'wins': wins,
                    'podiums': podiums,
                    'championship_leader': 1 if driver == 'Verstappen' and points > 100 else 0
                })

    df = pd.DataFrame(data)
    logger.info(f"✅ Generated {len(df):,} sample records")
    return df


def column_exists(df, column_name):
    """Check if a column exists in the DataFrame."""
    return column_name in df.columns


def get_seasons(df):
    """Get sorted list of unique seasons (descending)."""
    if column_exists(df, 'year'):
        return sorted(df['year'].unique(), reverse=True)
    if column_exists(df, 'season'):
        return sorted(df['season'].unique(), reverse=True)
    return []


def get_drivers(df):
    """Get sorted list of unique drivers."""
    if column_exists(df, 'driver_name'):
        return sorted(df['driver_name'].unique())
    if column_exists(df, 'driver'):
        return sorted(df['driver'].unique())
    return []


def get_constructors(df):
    """Get sorted list of unique constructors."""
    if column_exists(df, 'constructor_name'):
        return sorted(df['constructor_name'].unique())
    if column_exists(df, 'constructor'):
        return sorted(df['constructor'].unique())
    return []


def get_circuits(df):
    """Get sorted list of unique circuits."""
    if column_exists(df, 'circuit_name'):
        return sorted(df['circuit_name'].unique())
    if column_exists(df, 'circuit'):
        return sorted(df['circuit'].unique())
    return []


def get_rounds(df, season=None):
    """Get sorted list of rounds for a given season."""
    if not column_exists(df, 'round'):
        return []

    if season is not None:
        if column_exists(df, 'year'):
            mask = df['year'] == season
        elif column_exists(df, 'season'):
            mask = df['season'] == season
        else:
            return sorted(df['round'].unique())
        return sorted(df[mask]['round'].unique())

    return sorted(df['round'].unique())


def print_data_summary(df):
    """Print a human-readable summary of the dataset."""
    print("\n" + "=" * 50)
    print("   📊 F1 DATASET SUMMARY")
    print("=" * 50)
    print(f"   Total Records:  {len(df):,}")
    print(f"   Seasons:        {len(get_seasons(df))}")
    print(f"   Drivers:        {len(get_drivers(df))}")
    print(f"   Constructors:   {len(get_constructors(df))}")
    print(f"   Circuits:       {len(get_circuits(df))}")
    print("-" * 50)
    print("   Columns:")
    for col in list(df.columns)[:15]:
        print(f"     • {col}")
    if len(df.columns) > 15:
        print(f"     ... and {len(df.columns) - 15} more columns")
    print("=" * 50 + "\n")