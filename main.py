"""Merges the cleaned CDC, USGS, USDA, and EPA tables into analysis
tables (one row per state) and writes them to output/.

build_state_table() needs pesticide data, so DC drops out (no
farmland, no pesticide use). build_cdc_epa_table() skips pesticide
data entirely, so it keeps DC for Q3.
"""
from clean_cdc import clean_cdc_data
from clean_usgs import clean_usgs_data
from clean_usda import clean_usda_data
from clean_epa import clean_epa_data

OUTPUT_PATH = 'output/state_table.csv'
CDC_EPA_OUTPUT_PATH = 'output/state_table_cdc_epa.csv'


def build_state_table():
    cdc = clean_cdc_data()
    usgs = clean_usgs_data()
    usda = clean_usda_data()
    epa = clean_epa_data()

    usgs = usgs.merge(usda, on='state_postal', how='inner')
    usgs['pesticide_intensity'] = (
        usgs['avg_pesticide_kg'] / usgs['ag_land_acres']
    )

    pesticide_cols = [
        'state_fips', 'avg_pesticide_kg', 'ag_land_acres',
        'pesticide_intensity'
    ]
    nitrate_cols = [
        'state_fips', 'nitrate_rate_per_system', 'nitrate_rate_per_100k_capita'
    ]
    table = cdc.merge(usgs[pesticide_cols], on='state_fips', how='inner')
    table = table.merge(epa[nitrate_cols], on='state_fips', how='inner')
    return table


def build_cdc_epa_table():
    cdc = clean_cdc_data()
    epa = clean_epa_data()
    nitrate_cols = [
        'state_fips', 'nitrate_rate_per_system', 'nitrate_rate_per_100k_capita'
    ]
    return cdc.merge(epa[nitrate_cols], on='state_fips', how='inner')


def main():
    table = build_state_table()
    print(f'Merged table: {table.shape[0]} states, {table.shape[1]} columns')
    print(table.isna().sum())
    table.to_csv(OUTPUT_PATH, index=False)
    print(f'Wrote {OUTPUT_PATH}')

    cdc_epa_table = build_cdc_epa_table()
    print(
        f'CDC+EPA table: {cdc_epa_table.shape[0]} states, '
        f'{cdc_epa_table.shape[1]} columns'
    )
    print(cdc_epa_table.isna().sum())
    cdc_epa_table.to_csv(CDC_EPA_OUTPUT_PATH, index=False)
    print(f'Wrote {CDC_EPA_OUTPUT_PATH}')


if __name__ == '__main__':
    main()
