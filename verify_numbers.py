"""Verification script: re-run all analyses and extract numbers that must match report prose.

This script:
1. Loads the current state_table.csv and state_table_cdc_epa.csv
2. Runs Q1, Q2, Q3 analyses
3. Extracts summary stats and test statistics
4. Compares against what's written in the report narrative
5. Flags discrepancies so you can update prose before submission
"""
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
import numpy as np

print("="*80)
print("RUNNING FULL ANALYSIS PIPELINE ON CURRENT DATA")
print("="*80)

# ============================================================================
# LOAD DATA
# ============================================================================
state_table = pd.read_csv('output/state_table.csv')
state_table_cdc_epa = pd.read_csv('output/state_table_cdc_epa.csv')

print(f"\nData loaded:")
print(f"  state_table.csv: {state_table.shape[0]} rows")
print(f"  state_table_cdc_epa.csv: {state_table_cdc_epa.shape[0]} rows")

# ============================================================================
# Q1: HORMONE RATE vs PESTICIDE INTENSITY (48 states)
# ============================================================================
print("\n" + "="*80)
print("Q1 ANALYSIS: Hormone rate vs Pesticide intensity")
print("="*80)

q1_df = state_table[['hormone_rate', 'pesticide_intensity']].dropna()
print(f"Q1 rows (no missing): {len(q1_df)}")

print("\nSummary statistics (Q1 table):")
print(q1_df.describe())

q1_hormone_mean = q1_df['hormone_rate'].mean()
q1_hormone_max = q1_df['hormone_rate'].max()
q1_pesticide_mean = q1_df['pesticide_intensity'].mean()

print(f"\nKey Q1 descriptive stats to check:")
print(f"  hormone_rate mean: {q1_hormone_mean:.2f} (report says: 52.67)")
print(f"  hormone_rate max: {q1_hormone_max:.2f} (report says: 61.37)")
print(f"  pesticide_intensity mean: {q1_pesticide_mean:.3f} (report says: 0.706)")

r, p_pearson = stats.pearsonr(q1_df['pesticide_intensity'], q1_df['hormone_rate'])
rho, p_spearman = stats.spearmanr(q1_df['pesticide_intensity'], q1_df['hormone_rate'])
print(f"\nQ1 Correlations:")
print(f"  Pearson r = {r:.4f}, p = {p_pearson:.4f}")
print(f"  Spearman rho = {rho:.4f}, p = {p_spearman:.4f}")

x = q1_df[['pesticide_intensity']].values
y = q1_df['hormone_rate'].values
q1_model = LinearRegression().fit(x, y)
q1_r2 = q1_model.score(x, y)
print(f"  Regression: slope={q1_model.coef_[0]:.4f}, intercept={q1_model.intercept_:.4f}, R²={q1_r2:.4f}")

# ============================================================================
# Q2: OVERALL RATE vs PESTICIDE + NITRATE (48 states, using per-system rate)
# ============================================================================
print("\n" + "="*80)
print("Q2 ANALYSIS: Overall rate vs Pesticide + Nitrate")
print("="*80)

q2_df = state_table[['overall_rate', 'pesticide_intensity', 'nitrate_rate_per_system']].dropna()
q2_df = q2_df.replace([np.inf, -np.inf], np.nan).dropna()
print(f"Q2 rows (no missing): {len(q2_df)}")

print("\nSummary statistics (Q2 table):")
print(q2_df.describe())

q2_overall_mean = q2_df['overall_rate'].mean()
q2_pesticide_mean = q2_df['pesticide_intensity'].mean()
q2_nitrate_mean = q2_df['nitrate_rate_per_system'].mean()

print(f"\nKey Q2 descriptive stats to check:")
print(f"  overall_rate mean: {q2_overall_mean:.2f} (report says: 469.24)")
print(f"  pesticide_intensity mean: {q2_pesticide_mean:.3f} (report says: 0.706)")
print(f"  nitrate_rate (per-system) mean: {q2_nitrate_mean:.4f} (report says: 0.887)")

# Fit all three models
y = q2_df['overall_rate'].values
X1 = sm.add_constant(q2_df[['pesticide_intensity']])
X2 = sm.add_constant(q2_df[['nitrate_rate_per_system']])
q2_df['interaction'] = q2_df['pesticide_intensity'] * q2_df['nitrate_rate_per_system']
X3 = sm.add_constant(q2_df[['pesticide_intensity', 'nitrate_rate_per_system', 'interaction']])

m1 = sm.OLS(y, X1).fit()
m2 = sm.OLS(y, X2).fit()
m3 = sm.OLS(y, X3).fit()

print(f"\nQ2 Model Results:")
print(f"\nModel 1 (pesticide only):")
print(f"  R² = {m1.rsquared:.4f}")
print(f"  slope = {m1.params['pesticide_intensity']:.4f}")
print(f"  p-value = {m1.pvalues['pesticide_intensity']:.4f}")

print(f"\nModel 2 (nitrate only):")
print(f"  R² = {m2.rsquared:.4f}")
print(f"  slope = {m2.params['nitrate_rate_per_system']:.4f}")
print(f"  p-value = {m2.pvalues['nitrate_rate_per_system']:.4f}")

print(f"\nModel 3 (combined):")
print(f"  R² = {m3.rsquared:.4f}")
print(f"  slope (pesticide) = {m3.params['pesticide_intensity']:.4f}")
print(f"  p-value (pesticide) = {m3.pvalues['pesticide_intensity']:.4f}")
print(f"  slope (nitrate) = {m3.params['nitrate_rate_per_system']:.4f}")
print(f"  p-value (nitrate) = {m3.pvalues['nitrate_rate_per_system']:.4f}")
print(f"  slope (interaction) = {m3.params['interaction']:.4f}")

# ============================================================================
# Q3: COLORECTAL & STOMACH vs NITRATE (51 states + DC)
# ============================================================================
print("\n" + "="*80)
print("Q3 ANALYSIS: Colorectal & Stomach rates vs Nitrate")
print("="*80)

q3_df = state_table_cdc_epa[['colorectal_rate', 'stomach_rate', 'nitrate_rate_per_system']].dropna()
print(f"Q3 rows (no missing): {len(q3_df)}")

print("\nSummary statistics (Q3 table):")
print(q3_df.describe())

q3_colorectal_mean = q3_df['colorectal_rate'].mean()
q3_colorectal_max = q3_df['colorectal_rate'].max()
q3_stomach_mean = q3_df['stomach_rate'].mean()
q3_stomach_max = q3_df['stomach_rate'].max()

print(f"\nKey Q3 descriptive stats to check:")
print(f"  colorectal_rate mean: {q3_colorectal_mean:.2f} (report says: 43.32)")
print(f"  colorectal_rate max: {q3_colorectal_max:.2f}")
print(f"  stomach_rate mean: {q3_stomach_mean:.2f} (report says: 6.40)")
print(f"  stomach_rate max: {q3_stomach_max:.2f}")

for cancer_col in ['colorectal_rate', 'stomach_rate']:
    r, p_pearson = stats.pearsonr(q3_df['nitrate_rate_per_system'], q3_df[cancer_col])
    rho, p_spearman = stats.spearmanr(q3_df['nitrate_rate_per_system'], q3_df[cancer_col])
    x = q3_df[['nitrate_rate_per_system']].values
    y = q3_df[cancer_col].values
    q3_model = LinearRegression().fit(x, y)
    r2 = q3_model.score(x, y)
    
    print(f"\n{cancer_col}:")
    print(f"  Pearson r = {r:.4f}, p = {p_pearson:.4f}")
    print(f"  Spearman rho = {rho:.4f}, p = {p_spearman:.4f}")
    print(f"  Regression: slope={q3_model.coef_[0]:.4f}, R²={r2:.4f}")

# ============================================================================
# SUMMARY TABLE FOR REPORT
# ============================================================================
print("\n" + "="*80)
print("CORRECTED SUMMARY STATISTICS TABLE")
print("="*80)

# Compute for the final table
hormone_stats = state_table['hormone_rate'].describe(percentiles=[.25, .5, .75]).round(2)
pesticide_stats = state_table['pesticide_intensity'].describe(percentiles=[.25, .5, .75]).round(2)
overall_stats = state_table['overall_rate'].describe(percentiles=[.25, .5, .75]).round(2)
nitrate_stats = state_table['nitrate_rate_per_system'].describe(percentiles=[.25, .5, .75]).round(4)
colorectal_stats = state_table_cdc_epa['colorectal_rate'].describe(percentiles=[.25, .5, .75]).round(2)
stomach_stats = state_table_cdc_epa['stomach_rate'].describe(percentiles=[.25, .5, .75]).round(2)

summary_table = pd.DataFrame({
    'Variable': ['hormone_rate', 'pesticide_intensity', 'overall_rate', 'nitrate_rate', 'colorectal_rate', 'stomach_rate'],
    'Mean': [hormone_stats['mean'], pesticide_stats['mean'], overall_stats['mean'], nitrate_stats['mean'], colorectal_stats['mean'], stomach_stats['mean']],
    'SD': [hormone_stats['std'], pesticide_stats['std'], overall_stats['std'], nitrate_stats['std'], colorectal_stats['std'], stomach_stats['std']],
    'Min': [hormone_stats['min'], pesticide_stats['min'], overall_stats['min'], nitrate_stats['min'], colorectal_stats['min'], stomach_stats['min']],
    'Q1': [hormone_stats['25%'], pesticide_stats['25%'], overall_stats['25%'], nitrate_stats['25%'], colorectal_stats['25%'], stomach_stats['25%']],
    'Median': [hormone_stats['50%'], pesticide_stats['50%'], overall_stats['50%'], nitrate_stats['50%'], colorectal_stats['50%'], stomach_stats['50%']],
    'Q3': [hormone_stats['75%'], pesticide_stats['75%'], overall_stats['75%'], nitrate_stats['75%'], colorectal_stats['75%'], stomach_stats['75%']],
    'Max': [hormone_stats['max'], pesticide_stats['max'], overall_stats['max'], nitrate_stats['max'], colorectal_stats['max'], stomach_stats['max']],
})

print("\n" + summary_table.to_string(index=False))

summary_table.to_csv('output/summary_stats_verified.csv', index=False)
print("\nWrote output/summary_stats_verified.csv")

# ============================================================================
# DISCREPANCY REPORT
# ============================================================================
print("\n" + "="*80)
print("DISCREPANCY CHECK: Report prose vs. newly computed values")
print("="*80)

discrepancies = [
    ("Q1 hormone_rate mean", 52.67, q1_hormone_mean, 0.5),
    ("Q1 hormone_rate max", 61.37, q1_hormone_max, 0.5),
    ("Q1 pesticide_intensity mean", 0.706, q1_pesticide_mean, 0.05),
    ("Q2 overall_rate mean", 469.24, q2_overall_mean, 5.0),
    ("Q2 pesticide_intensity mean", 0.706, q2_pesticide_mean, 0.05),
    ("Q2 nitrate_rate mean", 0.887, q2_nitrate_mean, 0.05),
    ("Q3 colorectal_rate mean", 43.32, q3_colorectal_mean, 0.5),
    ("Q3 stomach_rate mean", 6.40, q3_stomach_mean, 0.3),
]

print("\nVariables marked MISMATCH need to be updated in your report:")
for name, reported, computed, tolerance in discrepancies:
    diff = abs(reported - computed)
    status = "✓ OK" if diff <= tolerance else "✗ MISMATCH"
    print(f"{status:8s} {name:30s}: reported={reported:8.4f}, computed={computed:8.4f}, diff={diff:8.4f}")

print("\n" + "="*80)
