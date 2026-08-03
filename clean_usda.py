"""Cleans the USDA 2017 Census of Agriculture bulk file into
state-level total agricultural land area (acres), the denominator
for pesticide_intensity.

The bulk file has no single "land in farms" row per state, so it's
reconstructed as the sum of its four official land-use components.
"""
import pandas as pd

CENSUS_PATH = 'qs.census2017.txt.gz'
LAND_COMPONENTS = [
    'AG LAND, CROPLAND - ACRES',
    'AG LAND, PASTURELAND, (EXCL CROPLAND & WOODLAND) - ACRES',
    'AG LAND, WOODLAND - ACRES',
    'AG LAND, (EXCL CROPLAND & PASTURELAND & WOODLAND) - ACRES',
]
COLS = ['SHORT_DESC', 'DOMAIN_DESC', 'AGG_LEVEL_DESC', 'STATE_ALPHA', 'VALUE']


def clean_usda_data(path=CENSUS_PATH, chunksize=500_000):
    matches = []
    for chunk in pd.read_csv(
        path, sep='\t', usecols=COLS, chunksize=chunksize, low_memory=False
    ):
        mask = (
            chunk['SHORT_DESC'].isin(LAND_COMPONENTS)
            & (chunk['AGG_LEVEL_DESC'] == 'STATE')
            & (chunk['DOMAIN_DESC'] == 'TOTAL')
        )
        matches.append(chunk[mask])
    result = pd.concat(matches, ignore_index=True)
    result['VALUE'] = pd.to_numeric(
        result['VALUE'].astype(str).str.replace(',', '', regex=False),
        errors='coerce'
    )
    totals = result.groupby('STATE_ALPHA', as_index=False)['VALUE'].sum()
    return totals.rename(
        columns={'STATE_ALPHA': 'state_postal', 'VALUE': 'ag_land_acres'}
    )


def main():
    usda = clean_usda_data()
    print(usda.sort_values('ag_land_acres', ascending=False).head(10))
    print(f'States with agricultural land data: {usda.shape[0]}')
    usda.to_csv('usda_state_table.csv', index=False)


if __name__ == '__main__':
    main()
