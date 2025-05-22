"""
Main script to run baseball game simulations
"""

import argparse
import logging
from data_processing.data_fetcher import BaseballDataFetcher
from monte_carlo.game_simulation import BaseballGameSimulation
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def plot_results(results: list, output_dir: str):
    """Create visualizations of simulation results"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Total runs distribution
    plt.figure(figsize=(10, 6))
    total_runs = [r['total_runs'] for r in results]
    sns.histplot(total_runs, kde=True)
    plt.title('Distribution of Total Runs per Game')
    plt.xlabel('Total Runs')
    plt.ylabel('Frequency')
    plt.savefig(f'{output_dir}/total_runs_distribution.png')
    plt.close()
    
    # Win probability
    home_wins = sum(1 for r in results if r['home_win'])
    win_pct = home_wins / len(results)
    plt.figure(figsize=(8, 8))
    plt.pie([win_pct, 1-win_pct], labels=['Home Team', 'Away Team'], 
            autopct='%1.1f%%', colors=['lightblue', 'lightgreen'])
    plt.title('Win Probability Distribution')
    plt.savefig(f'{output_dir}/win_probability.png')
    plt.close()
    
    # Run differential
    run_diff = [r['home_runs'] - r['away_runs'] for r in results]
    plt.figure(figsize=(10, 6))
    sns.histplot(run_diff, kde=True)
    plt.title('Distribution of Run Differential')
    plt.xlabel('Run Differential (Home - Away)')
    plt.ylabel('Frequency')
    plt.savefig(f'{output_dir}/run_differential_distribution.png')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Run baseball game simulations')
    parser.add_argument('--home-team', required=True, help='Home team abbreviation')
    parser.add_argument('--away-team', required=True, help='Away team abbreviation')
    parser.add_argument('--year', type=int, required=True, help='Season year')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of simulations to run')
    parser.add_argument('--output-dir', default='results', help='Output directory for results')
    parser.add_argument('--parallel', action='store_true', help='Run simulations in parallel')
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Fetch team data
        fetcher = BaseballDataFetcher()
        logger.info(f"Fetching data for {args.home_team} and {args.away_team} from {args.year}")
        
        home_stats = fetcher.get_team_stats(args.home_team, args.year)
        away_stats = fetcher.get_team_stats(args.away_team, args.year)
        
        if home_stats is None or away_stats is None:
            logger.error("Failed to fetch team statistics")
            return
        
        # Initialize simulation
        sim = BaseballGameSimulation(
            home_stats,
            away_stats,
            n_iterations=args.iterations
        )
        
        # Run simulations
        logger.info(f"Running {args.iterations} simulations")
        if args.parallel:
            results = sim.run_parallel()
        else:
            results = sim.run_sequential()
            
        # Calculate statistics
        stats = {
            'total_runs': sim.get_summary_statistics('total_runs'),
            'home_runs': sim.get_summary_statistics('home_runs'),
            'away_runs': sim.get_summary_statistics('away_runs'),
            'home_win_pct': sum(1 for r in results if r['home_win']) / len(results)
        }
        
        # Calculate confidence intervals
        ci_total = sim.calculate_confidence_interval('total_runs')
        ci_home = sim.calculate_confidence_interval('home_runs')
        ci_away = sim.calculate_confidence_interval('away_runs')
        
        stats['confidence_intervals'] = {
            'total_runs': {'lower': ci_total[0], 'upper': ci_total[1]},
            'home_runs': {'lower': ci_home[0], 'upper': ci_home[1]},
            'away_runs': {'lower': ci_away[0], 'upper': ci_away[1]}
        }
        
        # Save results
        with open(f'{args.output_dir}/simulation_stats.json', 'w') as f:
            json.dump(stats, f, indent=4)
            
        # Create visualizations
        plot_results(results, args.output_dir)
        
        logger.info(f"Results saved to {args.output_dir}")
        logger.info(f"Home team win probability: {stats['home_win_pct']:.1%}")
        logger.info(f"Average total runs: {stats['total_runs']['mean']:.1f}")
        
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        raise

if __name__ == '__main__':
    main() 