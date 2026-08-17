"""Generates summary statistics table for the analysis variables.

Computes mean, SD, min, Q1, median, Q3, and max for:
  - hormone_rate
  - pesticide_intensity
  - overall_rate
  - nitrate_rate (per 100k capita)
  - colorectal_rate
  - stomach_rate

Outputs to output/summary_stats.csv and prints to console.
"""
import pandas as pd
import numpy as np


def compute_summary_stats(table, column):
    """Compute summary statistics for a single column."""
    data = table[column].dropna()
    return {
        'Variable': column,
        'Mean (x̄)': data.mean(),
        'SD': data.std(),
        'Min': data.min(),
        'Q1': data.quantile(0.25),
        'Median': data.median(),
        'Q3': data.quantile(0.75),
        'Max': data.max(),
    }


def main():
    # Load the analysis table (48 states with pesticide data)
    table = pd.read_csv('output/state_table.csv')
    
    # Variables to summarize
    variables = [
        'hormone_rate',
        'pesticide_intensity',
        'overall_rate',
        'nitrate_rate_per_100k_capita',
        'colorectal_rate',
        'stomach_rate',
    ]
    
    # Compute stats for each variable
    stats_list = [compute_summary_stats(table, var) for var in variables]
    stats_df = pd.DataFrame(stats_list)
    
    # Round to reasonable precision for readability
    for col in ['Mean (x̄)', 'SD', 'Min', 'Q1', 'Median', 'Q3', 'Max']:
        stats_df[col] = stats_df[col].round(4)
    
    # Write to CSV
    stats_df.to_csv('output/summary_stats.csv', index=False)
    print('Summary Statistics')
    print('=' * 100)
    print(stats_df.to_string(index=False))
    print('\n' + '=' * 100)
    print(f"Wrote output/summary_stats.csv")
    print(f"\nBased on {table.shape[0]} states from output/state_table.csv")


if __name__ == '__main__':
    main()
