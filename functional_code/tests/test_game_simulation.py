"""
Tests for baseball game simulation
"""

import pytest
import pandas as pd
import numpy as np
from ..monte_carlo.game_simulation import BaseballGameSimulation
from ..data_processing.data_fetcher import BaseballDataFetcher
from ..data_processing.load_prepared_data import get_team_stats

def test_game_simulation_initialization():
    """Test game simulation initialization"""
    # Create sample team stats
    home_stats = pd.DataFrame({
        'BA': [0.275],
        'OBP': [0.350],
        'SLG': [0.450],
        'HR': [100],
        'AB': [5000]
    })
    
    away_stats = pd.DataFrame({
        'BA': [0.265],
        'OBP': [0.340],
        'SLG': [0.430],
        'HR': [90],
        'AB': [5000]
    })
    
    sim = BaseballGameSimulation(home_stats, away_stats, n_iterations=100)
    assert sim.n_iterations == 100
    assert sim.home_offense['ba'] == 0.275
    assert sim.away_offense['ba'] == 0.265

def test_plate_appearance_simulation():
    """Test plate appearance simulation"""
    home_stats = pd.DataFrame({
        'BA': [0.300],
        'OBP': [0.400],
        'SLG': [0.500],
        'HR': [40],
        'AB': [600]
    })
    
    away_stats = pd.DataFrame({
        'BA': [0.250],
        'OBP': [0.320],
        'SLG': [0.400],
        'HR': [20],
        'AB': [600]
    })
    
    sim = BaseballGameSimulation(home_stats, away_stats, random_seed=42)
    
    # Test multiple plate appearances
    results = [sim._simulate_plate_appearance(sim.home_offense) for _ in range(1000)]
    
    # Calculate observed rates
    hits = sum(1 for r in results if r['hit'])
    walks = sum(1 for r in results if r['walk'])
    homers = sum(1 for r in results if r['home_run'])
    
    # Check if rates are within reasonable bounds
    assert abs(hits/1000 - 0.300) < 0.05  # Within 5% of expected BA
    assert abs((hits + walks)/1000 - 0.400) < 0.05  # Within 5% of expected OBP
    assert abs(homers/1000 - (40/600)) < 0.05  # Within 5% of expected HR rate

def test_inning_simulation():
    """Test inning simulation"""
    home_stats = pd.DataFrame({
        'BA': [0.250],
        'OBP': [0.330],
        'SLG': [0.400],
        'HR': [30],
        'AB': [600]
    })
    
    away_stats = pd.DataFrame({
        'BA': [0.250],
        'OBP': [0.330],
        'SLG': [0.400],
        'HR': [30],
        'AB': [600]
    })
    
    sim = BaseballGameSimulation(home_stats, away_stats, random_seed=42)
    
    # Simulate multiple innings
    results = [sim._simulate_inning(sim.home_offense) for _ in range(1000)]
    
    # Calculate average runs per inning
    avg_runs = sum(r['runs'] for r in results) / 1000
    
    # MLB teams average around 0.5 runs per inning
    assert 0.3 <= avg_runs <= 0.7

def test_game_simulation():
    """Test full game simulation"""
    home_stats = pd.DataFrame({
        'BA': [0.260],
        'OBP': [0.330],
        'SLG': [0.420],
        'HR': [35],
        'AB': [600]
    })
    
    away_stats = pd.DataFrame({
        'BA': [0.260],
        'OBP': [0.330],
        'SLG': [0.420],
        'HR': [35],
        'AB': [600]
    })
    
    sim = BaseballGameSimulation(home_stats, away_stats, n_iterations=100, random_seed=42)
    results = sim.run_sequential()
    
    # Check basic game properties
    for result in results:
        assert result['home_runs'] >= 0
        assert result['away_runs'] >= 0
        assert result['home_runs'] != result['away_runs']  # No ties (extra innings)
        assert result['home_win'] == (result['home_runs'] > result['away_runs'])
        
    # Calculate average runs per game
    avg_total_runs = sum(r['total_runs'] for r in results) / len(results)
    
    # MLB games average around 9 runs per game
    assert 7 <= avg_total_runs <= 11

@pytest.mark.integration
def test_with_prepared_data():
    """Test using prepared 2023 data"""
    # Get Yankees vs Red Sox data
    yankees_stats = get_team_stats('NYY', 2023)
    red_sox_stats = get_team_stats('BOS', 2023)
    
    assert yankees_stats is not None, "Failed to load Yankees stats"
    assert red_sox_stats is not None, "Failed to load Red Sox stats"
    
    # Run simulation
    sim = BaseballGameSimulation(red_sox_stats, yankees_stats, n_iterations=1000)
    results = sim.run_sequential()
    
    # Basic validation
    assert len(results) == 1000
    
    # Calculate statistics
    home_wins = sum(1 for r in results if r['home_win'])
    win_pct = home_wins / len(results)
    
    # Red Sox (home) vs Yankees (away) should be competitive
    assert 0.35 <= win_pct <= 0.65
    
    # Calculate run statistics
    total_runs = [r['total_runs'] for r in results]
    avg_runs = np.mean(total_runs)
    
    # Average runs should be reasonable (MLB average varies between 6-10 runs per game)
    assert 6 <= avg_runs <= 10
    
    # Get confidence intervals
    ci = sim.calculate_confidence_interval('total_runs')
    assert ci[0] < ci[1]
    assert 4 <= ci[0] <= ci[1] <= 12  # Reasonable range for total runs

@pytest.mark.integration
def test_parallel_simulation():
    """Test parallel simulation execution"""
    braves_stats = get_team_stats('ATL', 2023)
    phillies_stats = get_team_stats('PHI', 2023)
    
    assert braves_stats is not None, "Failed to load Braves stats"
    assert phillies_stats is not None, "Failed to load Phillies stats"
    
    # Run simulation in parallel
    sim = BaseballGameSimulation(braves_stats, phillies_stats, n_iterations=1000)
    results = sim.run_parallel(n_processes=4)
    
    assert len(results) == 1000
    
    # Basic validation
    for result in results:
        assert isinstance(result, dict)
        assert all(key in result for key in ['home_runs', 'away_runs', 'home_win', 'total_runs'])
        
    # Performance should reflect Braves' strong offense
    home_wins = sum(1 for r in results if r['home_win'])
    win_pct = home_wins / len(results)
    
    # Braves should have good win probability at home
    assert 0.45 <= win_pct <= 0.75 