"""Cleans the USGS county-level pesticide-use files into a state-level
average annual pesticide-use total (2013-2017).

Leaves avg_pesticide_kg as a raw average -- dividing by ag land area
to get pesticide_intensity happens later, once merged with USDA.
"""
import pandas as pd

from state_lookup import STATE_LOOKUP

PESTICIDE_PATHS = [
    'EPest.county.estimates.2013.txt',
    'EPest.county.estimates.2014.txt',
    '2015PreliminaryEstimates/EPest.county.estimates.2015.txt',
    '2106PreliminaryEstimates/EPest.county.estimates.2016.txt',
    '2017PreliminaryEstimatesNoCA/EPest.county.estimates_noCA.2017.txt',
]


def load_state_year_total(path):
    df = pd.read_csv(
        path, sep='\t', usecols=['STATE_FIPS_CODE', 'EPEST_HIGH_KG']
    )
    df['STATE_FIPS_CODE'] = df['STATE_FIPS_CODE'].astype(str).str.zfill(2)
    return df.groupby('STATE_FIPS_CODE', as_index=False)['EPEST_HIGH_KG'].sum()


def clean_usgs_data(paths=PESTICIDE_PATHS):
    yearly_totals = pd.concat(
        [load_state_year_total(p) for p in paths], ignore_index=True
    )
    avg = yearly_totals.groupby(
        'STATE_FIPS_CODE', as_index=False
    )['EPEST_HIGH_KG'].mean()
    avg = avg.rename(columns={
        'STATE_FIPS_CODE': 'state_fips', 'EPEST_HIGH_KG': 'avg_pesticide_kg'
    })
    return STATE_LOOKUP.merge(avg, on='state_fips', how='inner')


def main():
    usgs = clean_usgs_data()
    print(usgs.describe())
    print(f'States with pesticide data: {usgs.shape[0]}')
    usgs.to_csv('usgs_state_table.csv', index=False)


if __name__ == '__main__':
    main()
