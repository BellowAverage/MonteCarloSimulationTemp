"""
Monte Carlo simulation for baseball games
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from .simulation_base import MonteCarloSimulation
import logging

logger = logging.getLogger(__name__)

class BaseballGameSimulation(MonteCarloSimulation):
    """Monte Carlo simulation for baseball games"""
    
    def __init__(
        self,
        home_team_stats: pd.DataFrame,
        away_team_stats: pd.DataFrame,
        n_iterations: int = 1000,
        random_seed: Optional[int] = None
    ):
        """
        Initialize baseball game simulation
        
        Args:
            home_team_stats: Statistics for home team
            away_team_stats: Statistics for away team
            n_iterations: Number of simulation iterations
            random_seed: Random seed for reproducibility
        """
        super().__init__(n_iterations, random_seed)
        self.home_team_stats = home_team_stats
        self.away_team_stats = away_team_stats
        self._process_team_stats()
        
    def _process_team_stats(self):
        """Process team statistics for simulation"""
        try:
            # Calculate key offensive metrics
            self.home_offense = {
                'ba': float(self.home_team_stats['BA'].mean()),
                'obp': float(self.home_team_stats['OBP'].mean()),
                'slg': float(self.home_team_stats['SLG'].mean()),
                'hr_rate': float(self.home_team_stats['HR'].sum() / self.home_team_stats['AB'].sum())
            }
            
            self.away_offense = {
                'ba': float(self.away_team_stats['BA'].mean()),
                'obp': float(self.away_team_stats['OBP'].mean()),
                'slg': float(self.away_team_stats['SLG'].mean()),
                'hr_rate': float(self.away_team_stats['HR'].sum() / self.away_team_stats['AB'].sum())
            }
        except Exception as e:
            logger.error(f"Error processing team stats: {e}")
            raise
            
    def _simulate_plate_appearance(self, offense_stats: Dict[str, float]) -> Dict[str, Any]:
        """
        Simulate a single plate appearance
        
        Args:
            offense_stats: Offensive statistics for batting team
            
        Returns:
            Dictionary containing result of plate appearance
        """
        result = {
            'hit': False,
            'out': False,
            'walk': False,
            'home_run': False,
            'bases_advanced': 0
        }
        
        # Generate random number for outcome
        roll = self.rng.random()
        
        # Check for walk
        if roll < (offense_stats['obp'] - offense_stats['ba']):
            result['walk'] = True
            result['bases_advanced'] = 1
        # Check for hit
        elif roll < offense_stats['obp']:
            result['hit'] = True
            # Determine type of hit
            hit_roll = self.rng.random()
            if hit_roll < offense_stats['hr_rate']:
                result['home_run'] = True
                result['bases_advanced'] = 4
            else:
                # Simplified extra-base hit calculation
                slugging_factor = (offense_stats['slg'] - offense_stats['ba']) / offense_stats['ba']
                bases = min(3, 1 + int(self.rng.random() < slugging_factor * 0.5))
                result['bases_advanced'] = bases
        else:
            result['out'] = True
            
        return result
        
    def _simulate_inning(self, offense_stats: Dict[str, float]) -> Dict[str, int]:
        """
        Simulate a single inning
        
        Args:
            offense_stats: Offensive statistics for batting team
            
        Returns:
            Dictionary containing inning results
        """
        outs = 0
        runs = 0
        bases = [False, False, False]  # Runners on 1st, 2nd, 3rd
        
        while outs < 3:
            pa_result = self._simulate_plate_appearance(offense_stats)
            
            if pa_result['out']:
                outs += 1
            elif pa_result['home_run']:
                # Score all runners plus batter
                runs += 1 + sum(1 for base in bases if base)
                bases = [False, False, False]
            else:
                # Advance runners
                advance = pa_result['bases_advanced']
                # Score runners that would advance past third
                for i in range(2, -1, -1):
                    if bases[i]:
                        new_base = i + advance
                        if new_base >= 3:
                            runs += 1
                            bases[i] = False
                        else:
                            bases[i] = False
                            bases[new_base] = True
                
                # Place batter on appropriate base
                if advance > 0 and advance < 4:
                    bases[advance - 1] = True
                    
        return {'runs': runs}
        
    def single_iteration(self) -> Dict[str, Any]:
        """
        Simulate a single game
        
        Returns:
            Dictionary containing game results
        """
        home_runs = 0
        away_runs = 0
        
        # Simulate 9 innings
        for _ in range(9):
            # Away team bats in top of inning
            inning_result = self._simulate_inning(self.away_offense)
            away_runs += inning_result['runs']
            
            # Home team bats in bottom of inning
            inning_result = self._simulate_inning(self.home_offense)
            home_runs += inning_result['runs']
        
        # Extra innings if tied
        while home_runs == away_runs:
            # Away team bats
            inning_result = self._simulate_inning(self.away_offense)
            away_runs += inning_result['runs']
            
            # Home team bats
            inning_result = self._simulate_inning(self.home_offense)
            home_runs += inning_result['runs']
        
        return {
            'home_runs': home_runs,
            'away_runs': away_runs,
            'home_win': home_runs > away_runs,
            'total_runs': home_runs + away_runs
        } 