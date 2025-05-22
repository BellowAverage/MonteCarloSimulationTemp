"""
Base class for Monte Carlo simulations in baseball analysis
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from multiprocessing import Pool
from tqdm import tqdm
import logging
from abc import ABC, abstractmethod
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonteCarloSimulation(ABC):
    """Abstract base class for Monte Carlo simulations"""
    
    def __init__(self, n_iterations: int = 1000, random_seed: Optional[int] = None):
        """
        Initialize Monte Carlo simulation
        
        Args:
            n_iterations: Number of simulation iterations
            random_seed: Random seed for reproducibility
        """
        self.n_iterations = n_iterations
        self.rng = np.random.default_rng(random_seed)
        self.results = []
        
    @abstractmethod
    def single_iteration(self) -> Dict[str, Any]:
        """
        Run a single iteration of the simulation
        
        Returns:
            Dictionary containing results of the iteration
        """
        pass
    
    def _run_iteration(self, iteration: int) -> Dict[str, Any]:
        """
        Helper function for parallel processing
        
        Args:
            iteration: Iteration number (used for random seed)
            
        Returns:
            Dictionary containing results of the iteration
        """
        # Create a new random number generator for each process
        # Use current time and iteration number to create unique seeds
        seed = int(time.time() * 1000) + iteration
        self.rng = np.random.default_rng(seed)
        return self.single_iteration()

    def run_parallel(self, n_processes: int = 4) -> List[Dict[str, Any]]:
        """
        Run simulation iterations in parallel
        
        Args:
            n_processes: Number of parallel processes to use
            
        Returns:
            List of results from all iterations
        """
        try:
            with Pool(n_processes) as pool:
                self.results = list(tqdm(
                    pool.imap(self._run_iteration, range(self.n_iterations)),
                    total=self.n_iterations,
                    desc="Running simulations"
                ))
            return self.results
        except Exception as e:
            logger.error(f"Error in parallel simulation: {e}")
            return []
    
    def run_sequential(self) -> List[Dict[str, Any]]:
        """
        Run simulation iterations sequentially
        
        Returns:
            List of results from all iterations
        """
        try:
            self.results = [
                self.single_iteration() 
                for _ in tqdm(range(self.n_iterations), desc="Running simulations")
            ]
            return self.results
        except Exception as e:
            logger.error(f"Error in sequential simulation: {e}")
            return []
    
    def calculate_confidence_interval(
        self, 
        metric: str, 
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for a metric
        
        Args:
            metric: Name of the metric to analyze
            confidence_level: Confidence level (default: 0.95)
            
        Returns:
            Tuple of (lower bound, upper bound)
        """
        if not self.results:
            logger.warning("No simulation results available")
            return (0.0, 0.0)
        
        try:
            values = [result[metric] for result in self.results if metric in result]
            if not values:
                logger.warning(f"No values found for metric: {metric}")
                return (0.0, 0.0)
                
            mean = np.mean(values)
            std_err = np.std(values, ddof=1) / np.sqrt(len(values))
            z_score = np.abs(np.percentile(np.random.standard_normal(10000), 
                                         (1 - confidence_level) * 100 / 2))
            
            return (mean - z_score * std_err, mean + z_score * std_err)
        except Exception as e:
            logger.error(f"Error calculating confidence interval: {e}")
            return (0.0, 0.0)
    
    def get_summary_statistics(self, metric: str) -> Dict[str, float]:
        """
        Get summary statistics for a metric
        
        Args:
            metric: Name of the metric to analyze
            
        Returns:
            Dictionary of summary statistics
        """
        if not self.results:
            logger.warning("No simulation results available")
            return {}
        
        try:
            values = [result[metric] for result in self.results if metric in result]
            if not values:
                logger.warning(f"No values found for metric: {metric}")
                return {}
                
            return {
                'mean': np.mean(values),
                'median': np.median(values),
                'std': np.std(values, ddof=1),
                'min': np.min(values),
                'max': np.max(values),
                'q25': np.percentile(values, 25),
                'q75': np.percentile(values, 75)
            }
        except Exception as e:
            logger.error(f"Error calculating summary statistics: {e}")
            return {} 