"""
Inline verification: compute all statistics from the CSV data we have.
This replicates verify_numbers.py but with embedded data analysis.
"""
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

print("="*80)
print("RUNNING FULL ANALYSIS PIPELINE ON CURRENT DATA")
print("="*80)

# Load data
state_table = pd.read_csv('output/state_table.csv')
state_table_cdc_epa = pd.read_csv('output/state_table_cdc_epa.csv')

print("\nData loaded:")
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

print("\nSummary statistics:")
print(q1_df.describe().round(4))

q1_hormone_mean = q1_df['hormone_rate'].mean()
q1_hormone_std = q1_df['hormone_rate'].std()
q1_hormone_min = q1_df['hormone_rate'].min()
q1_hormone_q1 = q1_df['hormone_rate'].quantile(0.25)
q1_hormone_med = q1_df['hormone_rate'].median()
q1_hormone_q3 = q1_df['hormone_rate'].quantile(0.75)
q1_hormone_max = q1_df['hormone_rate'].max()

q1_pesticide_mean = q1_df['pesticide_intensity'].mean()
q1_pesticide_std = q1_df['pesticide_intensity'].std()
q1_pesticide_min = q1_df['pesticide_intensity'].min()
q1_pesticide_q1 = q1_df['pesticide_intensity'].quantile(0.25)
q1_pesticide_med = q1_df['pesticide_intensity'].median()
q1_pesticide_q3 = q1_df['pesticide_intensity'].quantile(0.75)
q1_pesticide_max = q1_df['pesticide_intensity'].max()

print("\n>>> Q1 KEY DESCRIPTIVE STATS:")
print(
    f"hormone_rate     mean={q1_hormone_mean:.2f} (report: 52.67), "
    f"max={q1_hormone_max:.2f} (report: 61.37)"
)
print(
    f"pesticide_intensity mean={q1_pesticide_mean:.3f} (report: 0.706), "
    f"max={q1_pesticide_max:.3f}"
)

r, p_pearson = stats.pearsonr(
    q1_df['pesticide_intensity'], q1_df['hormone_rate']
)
rho, p_spearman = stats.spearmanr(
    q1_df['pesticide_intensity'], q1_df['hormone_rate']
)

print("\n>>> Q1 CORRELATIONS:")
print(f"Pearson r={r:.4f}, p={p_pearson:.4f}")
print(f"Spearman rho={rho:.4f}, p={p_spearman:.4f}")

x = q1_df[['pesticide_intensity']].values
y = q1_df['hormone_rate'].values
q1_model = LinearRegression().fit(x, y)
q1_r2 = q1_model.score(x, y)
print(
    f"Regression: slope={q1_model.coef_[0]:.4f}, "
    f"intercept={q1_model.intercept_:.4f}, R²={q1_r2:.4f}"
)

# ============================================================================
# Q2: OVERALL RATE vs PESTICIDE + NITRATE (48 states)
# ============================================================================
print("\n" + "="*80)
print("Q2 ANALYSIS: Overall rate vs Pesticide + Nitrate")
print("="*80)

q2_df = state_table[
    ['overall_rate', 'pesticide_intensity', 'nitrate_rate_per_system']
].dropna()
q2_df = q2_df.replace([np.inf, -np.inf], np.nan).dropna()
print(f"Q2 rows (no missing): {len(q2_df)}")

print("\nSummary statistics:")
print(q2_df.describe().round(4))

q2_overall_mean = q2_df['overall_rate'].mean()
q2_overall_std = q2_df['overall_rate'].std()
q2_overall_min = q2_df['overall_rate'].min()
q2_overall_q1 = q2_df['overall_rate'].quantile(0.25)
q2_overall_med = q2_df['overall_rate'].median()
q2_overall_q3 = q2_df['overall_rate'].quantile(0.75)
q2_overall_max = q2_df['overall_rate'].max()

q2_pesticide_mean = q2_df['pesticide_intensity'].mean()
q2_pesticide_std = q2_df['pesticide_intensity'].std()
q2_pesticide_min = q2_df['pesticide_intensity'].min()
q2_pesticide_q1 = q2_df['pesticide_intensity'].quantile(0.25)
q2_pesticide_med = q2_df['pesticide_intensity'].median()
q2_pesticide_q3 = q2_df['pesticide_intensity'].quantile(0.75)
q2_pesticide_max = q2_df['pesticide_intensity'].max()

q2_nitrate_mean = q2_df['nitrate_rate_per_system'].mean()
q2_nitrate_std = q2_df['nitrate_rate_per_system'].std()
q2_nitrate_min = q2_df['nitrate_rate_per_system'].min()
q2_nitrate_q1 = q2_df['nitrate_rate_per_system'].quantile(0.25)
q2_nitrate_med = q2_df['nitrate_rate_per_system'].median()
q2_nitrate_q3 = q2_df['nitrate_rate_per_system'].quantile(0.75)
q2_nitrate_max = q2_df['nitrate_rate_per_system'].max()

print("\n>>> Q2 KEY DESCRIPTIVE STATS:")
print(
    f"overall_rate     mean={q2_overall_mean:.2f} (report: 469.24), "
    f"max={q2_overall_max:.2f}"
)
print(
    f"pesticide_intensity mean={q2_pesticide_mean:.3f} (report: 0.706), "
    f"max={q2_pesticide_max:.3f}"
)
print(
    f"nitrate_rate (per-system) mean={q2_nitrate_mean:.4f} "
    f"(report: 0.887), max={q2_nitrate_max:.4f}"
)

# Fit all three models
y = q2_df['overall_rate'].values
X1 = sm.add_constant(q2_df[['pesticide_intensity']])
X2 = sm.add_constant(q2_df[['nitrate_rate_per_system']])

q2_df_copy = q2_df.copy()
q2_df_copy['interaction'] = (
    q2_df_copy['pesticide_intensity'] * q2_df_copy['nitrate_rate_per_system']
)
X3 = sm.add_constant(
    q2_df_copy[
        ['pesticide_intensity', 'nitrate_rate_per_system', 'interaction']
    ]
)

m1 = sm.OLS(y, X1).fit()
m2 = sm.OLS(y, X2).fit()
m3 = sm.OLS(y, X3).fit()

print("\n>>> Q2 MODEL RESULTS:")
print(
    f"Model 1 (pesticide only): R² = {m1.rsquared:.4f}, "
    f"slope = {m1.params['pesticide_intensity']:.4f}, "
    f"p = {m1.pvalues['pesticide_intensity']:.4f}"
)
print(
    f"Model 2 (nitrate only): R² = {m2.rsquared:.4f}, "
    f"slope = {m2.params['nitrate_rate_per_system']:.4f}, "
    f"p = {m2.pvalues['nitrate_rate_per_system']:.4f}"
)
print(f"Model 3 (combined): R² = {m3.rsquared:.4f}")
print(
    f"  pesticide: slope = {m3.params['pesticide_intensity']:.4f}, "
    f"p = {m3.pvalues['pesticide_intensity']:.4f}"
)
print(
    f"  nitrate: slope = {m3.params['nitrate_rate_per_system']:.4f}, "
    f"p = {m3.pvalues['nitrate_rate_per_system']:.4f}"
)
print(
    f"  interaction: slope = {m3.params['interaction']:.4f}, "
    f"p = {m3.pvalues['interaction']:.4f}"
)

# ============================================================================
# Q3: COLORECTAL & STOMACH vs NITRATE (51 states + DC)
# ============================================================================
print("\n" + "="*80)
print("Q3 ANALYSIS: Colorectal & Stomach rates vs Nitrate")
print("="*80)

q3_df = state_table_cdc_epa[
    ['colorectal_rate', 'stomach_rate', 'nitrate_rate_per_system']
].dropna()
print(f"Q3 rows (no missing): {len(q3_df)}")

print("\nSummary statistics:")
print(q3_df.describe().round(4))

q3_colorectal_mean = q3_df['colorectal_rate'].mean()
q3_colorectal_std = q3_df['colorectal_rate'].std()
q3_colorectal_min = q3_df['colorectal_rate'].min()
q3_colorectal_q1 = q3_df['colorectal_rate'].quantile(0.25)
q3_colorectal_med = q3_df['colorectal_rate'].median()
q3_colorectal_q3 = q3_df['colorectal_rate'].quantile(0.75)
q3_colorectal_max = q3_df['colorectal_rate'].max()

q3_stomach_mean = q3_df['stomach_rate'].mean()
q3_stomach_std = q3_df['stomach_rate'].std()
q3_stomach_min = q3_df['stomach_rate'].min()
q3_stomach_q1 = q3_df['stomach_rate'].quantile(0.25)
q3_stomach_med = q3_df['stomach_rate'].median()
q3_stomach_q3 = q3_df['stomach_rate'].quantile(0.75)
q3_stomach_max = q3_df['stomach_rate'].max()

print("\n>>> Q3 KEY DESCRIPTIVE STATS:")
print(
    f"colorectal_rate mean={q3_colorectal_mean:.2f} (report: 43.32), "
    f"max={q3_colorectal_max:.2f}"
)
print(
    f"stomach_rate    mean={q3_stomach_mean:.2f} (report: 6.40), "
    f"max={q3_stomach_max:.2f}"
)

print("\n>>> Q3 CORRELATIONS & REGRESSIONS:")
for cancer_col in ['colorectal_rate', 'stomach_rate']:
    r, p_pearson = stats.pearsonr(
        q3_df['nitrate_rate_per_system'], q3_df[cancer_col]
    )
    rho, p_spearman = stats.spearmanr(
        q3_df['nitrate_rate_per_system'], q3_df[cancer_col]
    )
    x = q3_df[['nitrate_rate_per_system']].values
    y = q3_df[cancer_col].values
    q3_model = LinearRegression().fit(x, y)
    r2 = q3_model.score(x, y)

    print(f"\n{cancer_col}:")
    print(f"  Pearson r={r:.4f}, p={p_pearson:.4f}")
    print(f"  Spearman rho={rho:.4f}, p={p_spearman:.4f}")
    print(f"  Regression: slope={q3_model.coef_[0]:.4f}, R²={r2:.4f}")

# ============================================================================
# CORRECTED SUMMARY TABLE
# ============================================================================
print("\n" + "="*80)
print("CORRECTED SUMMARY STATISTICS TABLE FOR YOUR REPORT")
print("="*80)

table_data = {
    'Variable': [
        'hormone_rate', 'pesticide_intensity', 'overall_rate',
        'nitrate_rate', 'colorectal_rate', 'stomach_rate',
    ],
    'Mean': [
        q1_hormone_mean, q1_pesticide_mean, q2_overall_mean,
        q2_nitrate_mean, q3_colorectal_mean, q3_stomach_mean,
    ],
    'SD': [
        q1_hormone_std, q1_pesticide_std, q2_overall_std,
        q2_nitrate_std, q3_colorectal_std, q3_stomach_std,
    ],
    'Min': [
        q1_hormone_min, q1_pesticide_min, q2_overall_min,
        q2_nitrate_min, q3_colorectal_min, q3_stomach_min,
    ],
    'Q1': [
        q1_hormone_q1, q1_pesticide_q1, q2_overall_q1,
        q2_nitrate_q1, q3_colorectal_q1, q3_stomach_q1,
    ],
    'Median': [
        q1_hormone_med, q1_pesticide_med, q2_overall_med,
        q2_nitrate_med, q3_colorectal_med, q3_stomach_med,
    ],
    'Q3': [
        q1_hormone_q3, q1_pesticide_q3, q2_overall_q3,
        q2_nitrate_q3, q3_colorectal_q3, q3_stomach_q3,
    ],
    'Max': [
        q1_hormone_max, q1_pesticide_max, q2_overall_max,
        q2_nitrate_max, q3_colorectal_max, q3_stomach_max,
    ],
}

summary_table = pd.DataFrame(table_data)
print("\n" + summary_table.to_string(index=False))

# ============================================================================
# MARKDOWN TABLE FOR REPORT
# ============================================================================
print("\n" + "="*80)
print("MARKDOWN TABLE (copy-paste into your report):")
print("="*80)

print("\n| Variable | x̄ | SD | min | Q1 | median | Q3 | max |")
print("|---|---:|---:|---:|---:|---:|---:|---:|")
for _, row in summary_table.iterrows():
    print(
        f"| {row['Variable']} | {row['Mean']:.2f} | {row['SD']:.2f} | "
        f"{row['Min']:.2f} | {row['Q1']:.2f} | {row['Median']:.2f} | "
        f"{row['Q3']:.2f} | {row['Max']:.2f} |"
    )

# ============================================================================
# DISCREPANCY REPORT
# ============================================================================
print("\n" + "="*80)
print("DISCREPANCY CHECK: Report prose vs. newly computed values")
print("="*80)

discrepancies = [
    ("Q1 hormone_rate mean", 52.67, q1_hormone_mean),
    ("Q1 hormone_rate max", 61.37, q1_hormone_max),
    ("Q1 pesticide_intensity mean", 0.706, q1_pesticide_mean),
    ("Q2 overall_rate mean", 469.24, q2_overall_mean),
    ("Q2 pesticide_intensity mean", 0.706, q2_pesticide_mean),
    ("Q2 nitrate_rate mean", 0.887, q2_nitrate_mean),
    ("Q3 colorectal_rate mean", 43.32, q3_colorectal_mean),
    ("Q3 stomach_rate mean", 6.40, q3_stomach_mean),
]

print("\nStatus legend:")
print("  ✓ MATCH (within ±0.5 for rates, ±0.05 for intensity)")
print("  ✗ NEEDS UPDATE (difference exceeds tolerance)")
print()

for name, reported, computed in discrepancies:
    diff = abs(reported - computed)
    if name.endswith('_intensity mean'):
        tolerance = 0.05
    else:
        tolerance = 0.5
    status = "✓ MATCH" if diff <= tolerance else "✗ UPDATE"
    print(
        f"{status:12s} {name:35s}: reported={reported:8.4f}, "
        f"computed={computed:8.4f}, diff={diff:8.4f}"
    )

print("\n" + "="*80)
print("END VERIFICATION REPORT")
print("="*80)
