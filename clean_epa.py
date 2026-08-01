"""Builds a state-level nitrate/nitrite drinking-water violation rate
from the outputs of clean_epa_data.py (nitrate_violations_filtered.csv,
pub_water_systems_filtered.csv). Both normalizations from the proposal
are computed: violations per public water system and violations per
100,000 population served.
"""
import pandas as pd

from state_lookup import STATE_LOOKUP

VIOLATIONS_PATH = 'nitrate_violations_filtered.csv'
WATER_SYSTEMS_PATH = 'pub_water_systems_filtered.csv'


def clean_epa_data():
    violations = pd.read_csv(VIOLATIONS_PATH)
    systems = pd.read_csv(WATER_SYSTEMS_PATH)

    violations_with_state = violations.merge(
        systems[['PWSID', 'STATE_CODE']], on='PWSID', how='inner'
    )
    violation_counts = (
        violations_with_state.groupby('STATE_CODE')['VIOLATION_ID']
        .nunique()
        .reset_index(name='violation_count')
    )

    system_stats = systems.groupby('STATE_CODE', as_index=False).agg(
        system_count=('PWSID', 'nunique'),
        population_served=('POPULATION_SERVED_COUNT', 'sum'),
    )

    epa = system_stats.merge(violation_counts, on='STATE_CODE', how='left')
    epa['violation_count'] = epa['violation_count'].fillna(0)
    epa['nitrate_rate_per_system'] = epa['violation_count'] / epa['system_count']
    epa['nitrate_rate_per_100k_capita'] = (
        epa['violation_count'] / epa['population_served'] * 100_000
    )
    epa = epa.rename(columns={'STATE_CODE': 'state_postal'})
    return STATE_LOOKUP.merge(epa, on='state_postal', how='inner')


def main():
    epa = clean_epa_data()
    print(epa.describe())
    print(f'States with EPA nitrate data: {epa.shape[0]}')
    epa.to_csv('epa_state_table.csv', index=False)


if __name__ == '__main__':
    main()
