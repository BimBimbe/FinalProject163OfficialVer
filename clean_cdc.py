"""Cleans the CDC WONDER cancer incidence exports into one state-level
table with overall_rate, hormone_rate, colorectal_rate, and
stomach_rate.

hormone_rate is not a single CDC WONDER query (CDC WONDER does not have
a built-in "hormone-related cancers" category and a combined query was
not obtained in time). Instead it is a pooled rate: total cases across
breast, prostate, ovary, corpus uteri, and thyroid cancer divided by
total population across those same five files, per state. This is a
crude (non age-adjusted) rate, not an average of the five age-adjusted
rates, since age-adjusted rates cannot be validly averaged.
"""
import pandas as pd

from state_lookup import STATE_LOOKUP

OVERALL_PATH = 'cdcoverallcancer.csv'
COLORECTAL_PATH = 'cdccolonandrectum.csv'
STOMACH_PATH = 'cdcstomach.csv'
HORMONE_PATHS = [
    'cdcbreastallgender.csv',
    'CDCProstate.csv',
    'cdcovary.csv',
    'cdcCorpus Uteri.csv',
    'cdcThyroid.csv',
]


def load_cdc_csv(path):
    """Load a raw CDC WONDER export and drop the Total row and the
    citation/caveat footer, which pandas otherwise reads as ragged
    rows with no valid state FIPS code."""
    df = pd.read_csv(path, on_bad_lines='skip', engine='python')
    df['States Code'] = pd.to_numeric(df['States Code'], errors='coerce')
    df = df.dropna(subset=['States Code'])
    df['States Code'] = df['States Code'].astype(int).astype(str).str.zfill(2)
    for col in ['Count', 'Population', 'Age-Adjusted Rate']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.rename(columns={'States': 'state', 'States Code': 'state_fips'})


def load_rate_column(path, rate_col_name):
    df = load_cdc_csv(path)
    df = df.rename(columns={'Age-Adjusted Rate': rate_col_name})
    return df[['state', 'state_fips', rate_col_name]]


def load_pooled_hormone_rate(paths):
    frames = [load_cdc_csv(p) for p in paths]
    combined = pd.concat(frames, ignore_index=True)
    pooled = combined.groupby(
        ['state', 'state_fips'], as_index=False
    )[['Count', 'Population']].sum()
    pooled['hormone_rate'] = pooled['Count'] / pooled['Population'] * 100_000
    return pooled[['state', 'state_fips', 'hormone_rate']]


def clean_cdc_data():
    overall = load_rate_column(OVERALL_PATH, 'overall_rate')
    colorectal = load_rate_column(COLORECTAL_PATH, 'colorectal_rate')
    stomach = load_rate_column(STOMACH_PATH, 'stomach_rate')
    hormone = load_pooled_hormone_rate(HORMONE_PATHS)

    cdc = STATE_LOOKUP.merge(overall[['state_fips', 'overall_rate']], on='state_fips', how='left')
    cdc = cdc.merge(hormone[['state_fips', 'hormone_rate']], on='state_fips', how='left')
    cdc = cdc.merge(colorectal[['state_fips', 'colorectal_rate']], on='state_fips', how='left')
    cdc = cdc.merge(stomach[['state_fips', 'stomach_rate']], on='state_fips', how='left')
    return cdc


def main():
    cdc = clean_cdc_data()
    print(cdc.describe())
    print(f'States with all four rates present: {cdc.dropna().shape[0]}')
    cdc.to_csv('cdc_state_table.csv', index=False)


if __name__ == '__main__':
    main()
