"""Merges the cleaned CDC, USGS, USDA, and EPA state-level tables into
one analysis table (one row per state) and writes it to
output/state_table.csv.
"""
from clean_cdc import clean_cdc_data
from clean_usgs import clean_usgs_data
from clean_usda import clean_usda_data
from clean_epa import clean_epa_data

OUTPUT_PATH = 'output/state_table.csv'


def build_state_table():
    cdc = clean_cdc_data()
    usgs = clean_usgs_data()
    usda = clean_usda_data()
    epa = clean_epa_data()

    usgs = usgs.merge(usda, on='state_postal', how='inner')
    usgs['pesticide_intensity'] = usgs['avg_pesticide_kg'] / usgs['ag_land_acres']

    table = cdc.merge(
        usgs[['state_fips', 'avg_pesticide_kg', 'ag_land_acres', 'pesticide_intensity']],
        on='state_fips', how='inner'
    )
    table = table.merge(
        epa[['state_fips', 'nitrate_rate_per_system', 'nitrate_rate_per_100k_capita']],
        on='state_fips', how='inner'
    )
    return table


def main():
    table = build_state_table()
    print(f'Merged table: {table.shape[0]} states, {table.shape[1]} columns')
    print(table.isna().sum())
    table.to_csv(OUTPUT_PATH, index=False)
    print(f'Wrote {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
