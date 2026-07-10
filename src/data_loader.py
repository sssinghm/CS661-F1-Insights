"""
Data Loader Module for F1 Visual Analytics Dashboard
Automatically detects and loads the F1 dataset.
"""

import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
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
        # Try multiple paths
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
    """
    Create sample F1 data for testing when real data is unavailable.
    
    Returns
    -------
    pandas.DataFrame
        Sample F1 data.
    """
    logger.info("📊 Generating sample F1 data...")
    
    data = []
    seasons = [2021, 2022, 2023, 2024]
    drivers = ['Verstappen', 'Hamilton', 'Leclerc', 'Norris', 'Perez', 'Sainz', 'Russell']
    
    for season in seasons:
        for driver in drivers:
            points = 0
            for r in range(1, 23):
                # Simulate points accumulation
                base_points = 25 if driver == 'Verstappen' and season >= 2022 else 18
                if season == 2021 and driver in ['Verstappen', 'Hamilton']:
                    base_points = 20
                
                # Add some randomness
                import hashlib
                hash_val = int(hashlib.md5(f"{driver}{season}{r}".encode()).hexdigest()[:4], 16) % 15
                race_points = max(0, base_points + hash_val - 5)
                points += race_points
                
                data.append({
                    'year': season,
                    'round': r,
                    'driver_name': driver,
                    'championship_points': points,
                    'constructor_name': 'Red Bull' if driver in ['Verstappen', 'Perez'] else 
                                       'Mercedes' if driver in ['Hamilton', 'Russell'] else 
                                       'Ferrari' if driver in ['Leclerc', 'Sainz'] else 'McLaren',
                    'championship_leader': 1 if driver == 'Verstappen' and points > 100 else 0
                })
    
    df = pd.DataFrame(data)
    logger.info(f"✅ Generated {len(df):,} sample records")
    return df


def get_columns(df):
    """Get all column names from the DataFrame."""
    return list(df.columns)


def column_exists(df, column_name):
    """Check if a column exists in the DataFrame."""
    return column_name in df.columns


def get_seasons(df):
    """Get sorted list of unique seasons (descending)."""
    if column_exists(df, 'year'):
        return sorted(df['year'].unique(), reverse=True)
    if column_exists(df, 'season'):
        return sorted(df['season'].unique(), reverse=True)
    logger.warning("⚠️ No 'year' or 'season' column found.")
    return []


def get_drivers(df):
    """Get sorted list of unique drivers."""
    if column_exists(df, 'driver_name'):
        return sorted(df['driver_name'].unique())
    if column_exists(df, 'driver'):
        return sorted(df['driver'].unique())
    logger.warning("⚠️ No 'driver_name' or 'driver' column found.")
    return []


def get_constructors(df):
    """Get sorted list of unique constructors."""
    if column_exists(df, 'constructor_name'):
        return sorted(df['constructor_name'].unique())
    if column_exists(df, 'constructor'):
        return sorted(df['constructor'].unique())
    logger.warning("⚠️ No constructor column found.")
    return []


def get_circuits(df):
    """Get sorted list of unique circuits."""
    if column_exists(df, 'circuit_name'):
        return sorted(df['circuit_name'].unique())
    if column_exists(df, 'circuit'):
        return sorted(df['circuit'].unique())
    logger.warning("⚠️ No circuit column found.")
    return []


def get_rounds(df, season=None):
    """Get sorted list of rounds for a given season."""
    if not column_exists(df, 'round'):
        logger.warning("⚠️ No 'round' column found.")
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


def get_data_summary(df):
    """Get a summary of the dataset."""
    summary = {
        'total_records': len(df),
        'total_seasons': len(get_seasons(df)),
        'total_drivers': len(get_drivers(df)),
        'total_constructors': len(get_constructors(df)),
        'total_circuits': len(get_circuits(df)),
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict()
    }
    
    if get_seasons(df):
        summary['seasons_range'] = f"{min(get_seasons(df))} - {max(get_seasons(df))}"
    
    return summary


def print_data_summary(df):
    """Print a human-readable summary of the dataset."""
    summary = get_data_summary(df)
    
    print("\n" + "=" * 50)
    print("   📊 F1 DATASET SUMMARY")
    print("=" * 50)
    print(f"   Total Records:  {summary['total_records']:,}")
    print(f"   Seasons:        {summary['total_seasons']} ({summary.get('seasons_range', 'N/A')})")
    print(f"   Drivers:        {summary['total_drivers']}")
    print(f"   Constructors:   {summary['total_constructors']}")
    print(f"   Circuits:       {summary['total_circuits']}")
    print("-" * 50)
    print("   Columns:")
    for col in summary['columns'][:10]:  # Show first 10 columns
        print(f"     • {col} ({summary['dtypes'][col]})")
    if len(summary['columns']) > 10:
        print(f"     ... and {len(summary['columns']) - 10} more columns")
    print("=" * 50 + "\n")