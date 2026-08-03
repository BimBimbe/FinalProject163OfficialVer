"""Assert-based tests for the four clean_*.py modules, run against
small, hand-built fixture files rather than the real project data, so
the cleaning/aggregation logic itself is checked -- not just whatever
the real files happen to contain.

Usage: python test_clean.py
"""
import tempfile
from pathlib import Path

from clean_cdc import load_cdc_csv, load_rate_column, load_pooled_hormone_rate
from clean_usgs import clean_usgs_data
from clean_usda import clean_usda_data
from clean_epa import clean_epa_data


def write(dir_path, name, text):
    path = Path(dir_path) / name
    path.write_text(text)
    return str(path)


def test_load_cdc_csv_drops_suppressed_rows():
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, 'fake_cdc.csv', (
            'States,States Code,Count,Population,Age-Adjusted Rate\n'
            'Alabama,1,100,1000000,45.5\n'
            'Wyoming,56,10,500000,20.0\n'
            'Suppressed State,,5,100,10.0\n'
        ))
        df = load_cdc_csv(path)

        assert df.shape[0] == 2, (
            'expected the suppressed row (blank States Code) to be '
            f'dropped, got {df.shape[0]} rows'
        )
        assert set(df['state_fips']) == {'01', '56'}, (
            'state_fips should be zero-padded 2-digit strings, '
            f'got {sorted(df["state_fips"])}'
        )


def test_load_rate_column_renames_and_selects():
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, 'fake_cdc.csv', (
            'States,States Code,Count,Population,Age-Adjusted Rate\n'
            'Alabama,1,100,1000000,45.5\n'
        ))
        df = load_rate_column(path, 'overall_rate')

        assert list(df.columns) == ['state', 'state_fips', 'overall_rate']
        got = df.loc[df['state'] == 'Alabama', 'overall_rate'].iloc[0]
        assert got == 45.5, f'expected overall_rate 45.5, got {got}'


def test_load_pooled_hormone_rate_pools_across_files():
    with tempfile.TemporaryDirectory() as tmp:
        breast = write(tmp, 'fake_breast.csv', (
            'States,States Code,Count,Population,Age-Adjusted Rate\n'
            'Alabama,1,60,1000000,6.0\n'
        ))
        prostate = write(tmp, 'fake_prostate.csv', (
            'States,States Code,Count,Population,Age-Adjusted Rate\n'
            'Alabama,1,40,1000000,4.0\n'
        ))
        pooled = load_pooled_hormone_rate([breast, prostate])

        # hand-computed: (60 + 40) / (1_000_000 + 1_000_000) * 100_000
        expected = 5.0
        got = pooled.loc[
            pooled['state'] == 'Alabama', 'hormone_rate'
        ].iloc[0]
        assert abs(got - expected) < 1e-9, (
            f'expected pooled hormone_rate {expected}, got {got}'
        )


def test_clean_usgs_data_averages_across_years():
    with tempfile.TemporaryDirectory() as tmp:
        year1 = write(tmp, 'fake_2013.txt', (
            'STATE_FIPS_CODE\tCOUNTY_FIPS_CODE\tEPEST_HIGH_KG\n'
            '01\t001\t100\n'
            '01\t003\t50\n'
            '56\t001\t10\n'
        ))
        year2 = write(tmp, 'fake_2014.txt', (
            'STATE_FIPS_CODE\tCOUNTY_FIPS_CODE\tEPEST_HIGH_KG\n'
            '01\t001\t200\n'
            '01\t003\t100\n'
            '56\t001\t30\n'
        ))
        usgs = clean_usgs_data(paths=[year1, year2])

        # hand-computed: AL totals 150 (year1) and 300 (year2) -> avg 225
        # WY totals 10 (year1) and 30 (year2) -> avg 20
        al = usgs.loc[usgs['state_fips'] == '01', 'avg_pesticide_kg'].iloc[0]
        wy = usgs.loc[usgs['state_fips'] == '56', 'avg_pesticide_kg'].iloc[0]
        assert al == 225, f'expected Alabama avg_pesticide_kg 225, got {al}'
        assert wy == 20, f'expected Wyoming avg_pesticide_kg 20, got {wy}'


def test_clean_usda_data_sums_land_components_and_filters():
    header = 'SHORT_DESC\tDOMAIN_DESC\tAGG_LEVEL_DESC\tSTATE_ALPHA\tVALUE\n'
    rows = (
        'AG LAND, CROPLAND - ACRES\tTOTAL\tSTATE\tAL\t1,000\n'
        'AG LAND, PASTURELAND, (EXCL CROPLAND & WOODLAND) - ACRES'
        '\tTOTAL\tSTATE\tAL\t500\n'
        'AG LAND, WOODLAND - ACRES\tTOTAL\tSTATE\tAL\t300\n'
        'AG LAND, (EXCL CROPLAND & PASTURELAND & WOODLAND) - ACRES'
        '\tTOTAL\tSTATE\tAL\t200\n'
        # should be excluded: wrong aggregation level (county, not state)
        'AG LAND, CROPLAND - ACRES\tTOTAL\tCOUNTY\tAL\t999999\n'
        # should be excluded: wrong domain (not TOTAL)
        'AG LAND, CROPLAND - ACRES\tOWNED\tSTATE\tAL\t999999\n'
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = write(tmp, 'fake_census.txt', header + rows)
        usda = clean_usda_data(path=path)

        # hand-computed: 1000 + 500 + 300 + 200 = 2000 (commas stripped,
        # non-STATE and non-TOTAL rows excluded)
        got = usda.loc[
            usda['state_postal'] == 'AL', 'ag_land_acres'
        ].iloc[0]
        assert got == 2000, f'expected ag_land_acres 2000, got {got}'


def test_clean_epa_data_computes_both_rates_and_fills_missing():
    violations_header = (
        'SUBMISSIONYEARQUARTER,PWSID,VIOLATION_ID,'
        'VIOLATION_CATEGORY_CODE,IS_HEALTH_BASED_IND,CONTAMINANT_CODE\n'
    )
    violations_rows = (
        '2020Q1,AL001,V1,MCL,Y,1040\n'
        '2020Q1,AL002,V2,MCL,Y,1040\n'
    )
    systems_header = (
        'SUBMISSIONYEARQUARTER,PWSID,PWS_ACTIVITY_CODE,'
        'POPULATION_SERVED_COUNT,STATE_CODE\n'
    )
    systems_rows = (
        '2020Q1,AL001,A,1000,AL\n'
        '2020Q1,AL002,A,2000,AL\n'
        '2020Q1,AL003,A,3000,AL\n'
        '2020Q1,WY001,A,500,WY\n'
    )
    with tempfile.TemporaryDirectory() as tmp:
        v_path = write(tmp, 'fake_violations.csv', (
            violations_header + violations_rows
        ))
        s_path = write(tmp, 'fake_systems.csv', (
            systems_header + systems_rows
        ))
        epa = clean_epa_data(violations_path=v_path, systems_path=s_path)

        al = epa[epa['state_postal'] == 'AL'].iloc[0]
        # hand-computed: 2 unique violations / 3 systems = 0.6667
        assert abs(al['nitrate_rate_per_system'] - 2 / 3) < 1e-9, (
            f"expected AL nitrate_rate_per_system 0.6667, "
            f"got {al['nitrate_rate_per_system']}"
        )
        # hand-computed: 2 violations / 6000 population * 100_000
        assert abs(al['nitrate_rate_per_100k_capita'] - 33.3333) < 1e-3, (
            f"expected AL nitrate_rate_per_100k_capita ~33.33, "
            f"got {al['nitrate_rate_per_100k_capita']}"
        )

        wy = epa[epa['state_postal'] == 'WY'].iloc[0]
        # WY has a water system but zero violations -- confirms the
        # violation_count fillna(0) path, not a missing/NaN rate
        assert wy['nitrate_rate_per_system'] == 0, (
            'expected WY (no violations) to have rate 0, got '
            f"{wy['nitrate_rate_per_system']}"
        )


def main():
    tests = [
        test_load_cdc_csv_drops_suppressed_rows,
        test_load_rate_column_renames_and_selects,
        test_load_pooled_hormone_rate_pools_across_files,
        test_clean_usgs_data_averages_across_years,
        test_clean_usda_data_sums_land_components_and_filters,
        test_clean_epa_data_computes_both_rates_and_fills_missing,
    ]
    for test in tests:
        test()
        print(f'PASSED: {test.__name__}')
    print(f'\nAll {len(tests)} tests passed.')


if __name__ == '__main__':
    main()
