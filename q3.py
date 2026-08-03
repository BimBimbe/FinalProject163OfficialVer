"""Q3 combo-EDA: CDC colorectal and stomach cancer incidence vs. EPA
nitrate/nitrite drinking-water violation rate. Unlike Q1/Q2, this
combo does not use pesticide data, so it draws on
output/state_table_cdc_epa.csv (50 states + DC, including Alaska and
Hawaii, which the pesticide-restricted table excludes).

Answers RQ3: are states with higher rates of health-based nitrate
violations associated with higher colorectal and stomach cancer
incidence?
"""
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression

from clean_cdc import load_cdc_csv, OVERALL_PATH

DATA_PATH = 'output/state_table_cdc_epa.csv'
CANCER_COLS = ['colorectal_rate', 'stomach_rate']
NITRATE_COL = 'nitrate_rate_per_system'
NITRATE_CAPITA_COL = 'nitrate_rate_per_100k_capita'
SMALL_STATE_QUANTILE = 0.10


def load_q3_data(path=DATA_PATH):
    df = pd.read_csv(path, dtype={'state_fips': str})
    cols = (
        ['state', 'state_fips', 'state_postal']
        + CANCER_COLS + [NITRATE_COL, NITRATE_CAPITA_COL]
    )
    return df[cols]


def report_size_and_missingness(df):
    print(f'Q3 table: {df.shape[0]} rows, {df.shape[1]} columns')
    print('Rows = all 50 states + DC. This combo does not use pesticide '
          'data, so unlike Q1/Q2, Alaska, Hawaii, and DC are included.')
    print('Columns = state identifiers, colorectal_rate, stomach_rate, '
          'and two nitrate violation rate measures (per system, per '
          '100,000 population served).')
    print('Missing values per column:')
    print(df.isna().sum())


def summarize(df):
    print(df[CANCER_COLS + [NITRATE_COL, NITRATE_CAPITA_COL]].describe())


def plot_scatter(df, cancer_col, out_path, nitrate_col=NITRATE_COL):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(df[nitrate_col], df[cancer_col], color='#2C6E62')
    label = cancer_col.replace('_', ' ')
    ax.set_xlabel('Nitrate/nitrite violation rate (per water system)')
    ax.set_ylabel(f'{label.capitalize()} (per 100,000)')
    ax.set_title(f'{label.capitalize()} vs. nitrate violation rate, by state')
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'Wrote {out_path}')


def run_correlations(df, cancer_col, nitrate_col=NITRATE_COL):
    r, p_pearson = stats.pearsonr(df[nitrate_col], df[cancer_col])
    rho, p_spearman = stats.spearmanr(df[nitrate_col], df[cancer_col])
    print(
        f'{cancer_col} vs {nitrate_col}: '
        f'Pearson r = {r:.4f} (p={p_pearson:.4f}), '
        f'Spearman rho = {rho:.4f} (p={p_spearman:.4f}), n={len(df)}'
    )
    return r, p_pearson, rho, p_spearman


def run_regression(df, cancer_col, nitrate_col=NITRATE_COL):
    x = df[[nitrate_col]].values
    y = df[cancer_col].values
    model = LinearRegression().fit(x, y)
    r_squared = model.score(x, y)
    print(
        f'{cancer_col} ~ {nitrate_col}: slope={model.coef_[0]:.4f}, '
        f'intercept={model.intercept_:.4f}, R^2={r_squared:.4f}'
    )
    return model.coef_[0], model.intercept_, r_squared


def load_population():
    """Relative state population size, reused from the raw CDC overall-
    cancer export (already parsed by clean_cdc.load_cdc_csv). CDC WONDER
    sums Population across every year in the query window, so this is
    cumulative person-years, not a single-year population -- unusable
    as a real population figure, but states rank correctly by size, so
    it is used only to *rank* states for the small-state exclusion
    below, never printed or reported as a population count."""
    pop = load_cdc_csv(OVERALL_PATH)
    return pop[['state_fips', 'Population']]


def sensitivity_excluding_small_states(df):
    print('\n--- Sensitivity 1: excluding DC and very small states ---')
    pop = load_population()
    merged = df.merge(pop, on='state_fips', how='left')
    threshold = merged['Population'].quantile(SMALL_STATE_QUANTILE)
    excluded = merged[
        (merged['state'] == 'District of Columbia')
        | (merged['Population'] <= threshold)
    ]
    print(f'Excluding DC and the smallest {SMALL_STATE_QUANTILE:.0%} of '
          f'states by population: {", ".join(excluded["state"])}')
    filtered = merged[
        (merged['state'] != 'District of Columbia')
        & (merged['Population'] > threshold)
    ]
    print(f'{len(filtered)} states remain after exclusion '
          f'(of {len(merged)}).')
    for cancer_col in CANCER_COLS:
        run_correlations(filtered, cancer_col)
        run_regression(filtered, cancer_col)


def sensitivity_per_capita(df):
    print('\n--- Sensitivity 2: nitrate rate per 100,000 population '
          'instead of per water system ---')
    for cancer_col in CANCER_COLS:
        run_correlations(df, cancer_col, nitrate_col=NITRATE_CAPITA_COL)
        run_regression(df, cancer_col, nitrate_col=NITRATE_CAPITA_COL)


def main():
    df = load_q3_data()
    report_size_and_missingness(df)
    summarize(df)

    plot_scatter(
        df, 'colorectal_rate', 'output/q3_scatter_colorectal.png'
    )
    plot_scatter(
        df, 'stomach_rate', 'output/q3_scatter_stomach.png'
    )

    print('\n--- Primary analysis: nitrate rate per water system ---')
    for cancer_col in CANCER_COLS:
        run_correlations(df, cancer_col)
        run_regression(df, cancer_col)

    sensitivity_excluding_small_states(df)
    sensitivity_per_capita(df)


if __name__ == '__main__':
    main()
