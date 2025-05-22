"""
Module for loading prepared baseball data
"""

import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_team_stats(year: int) -> pd.DataFrame:
    """
    Load team statistics from prepared data
    
    Args:
        year: Season year
        
    Returns:
        DataFrame containing team statistics
    """
    try:
        data_path = Path('prepared_data') / str(year) / 'team_stats.csv'
        return pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Error loading team stats for {year}: {e}")
        return None

def get_team_stats(team: str, year: int) -> pd.DataFrame:
    """
    Get statistics for a specific team
    
    Args:
        team: Team abbreviation
        year: Season year
        
    Returns:
        DataFrame containing team statistics
    """
    try:
        all_stats = load_team_stats(year)
        if all_stats is None:
            return None
            
        team_stats = all_stats[all_stats['Team'] == team]
        if len(team_stats) == 0:
            logger.warning(f"No stats found for {team} in {year}")
            return None
            
        return team_stats
    except Exception as e:
        logger.error(f"Error getting stats for {team} {year}: {e}")
        return None 