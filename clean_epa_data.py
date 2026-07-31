"""
Filters the raw EPA SDWA downloads (SDWA_VIOLATIONS_ENFORCEMENT.csv,
SDWA_PUB_WATER_SYSTEMS.csv, SDWA_REF_CODE_VALUES.csv) down to the
nitrate/nitrite health-based MCL violations and per-state water-system
counts needed for the project. The violations file is ~3.8GB, so it is
read in chunks rather than all at once.
"""
import pandas as pd

VIOLATIONS_PATH = 'SDWA_VIOLATIONS_ENFORCEMENT.csv'
WATER_SYSTEMS_PATH = 'SDWA_PUB_WATER_SYSTEMS.csv'
REF_CODES_PATH = 'SDWA_REF_CODE_VALUES.csv'

VIOLATIONS_COLS = [
    'SUBMISSIONYEARQUARTER', 'PWSID', 'VIOLATION_ID',
    'VIOLATION_CATEGORY_CODE', 'IS_HEALTH_BASED_IND', 'CONTAMINANT_CODE'
]
WATER_SYSTEMS_COLS = [
    'SUBMISSIONYEARQUARTER', 'PWSID', 'STATE_CODE',
    'PWS_ACTIVITY_CODE', 'POPULATION_SERVED_COUNT'
]


def get_nitrate_contaminant_codes(ref_codes_path):
    """Return the CONTAMINANT_CODE values for nitrate/nitrite."""
    ref = pd.read_csv(ref_codes_path)
    contaminants = ref[ref['VALUE_TYPE'] == 'CONTAMINANT_CODE']
    mask = contaminants['VALUE_DESCRIPTION'].str.contains(
        'nitrate|nitrite', case=False, na=False
    )
    matches = contaminants[mask]
    print(matches[['VALUE_CODE', 'VALUE_DESCRIPTION']])
    return set(matches['VALUE_CODE'])


def filter_nitrate_violations(violations_path, nitrate_codes, chunksize=500_000):
    """Stream the violations file and keep only health-based MCL
    violations for nitrate/nitrite contaminants."""
    kept_chunks = []
    for chunk in pd.read_csv(
        violations_path, usecols=VIOLATIONS_COLS, chunksize=chunksize,
        low_memory=False
    ):
        mask = (
            (chunk['VIOLATION_CATEGORY_CODE'] == 'MCL')
            & (chunk['IS_HEALTH_BASED_IND'] == 'Y')
            & (chunk['CONTAMINANT_CODE'].isin(nitrate_codes))
        )
        if mask.any():
            kept_chunks.append(chunk[mask])
    result = pd.concat(kept_chunks, ignore_index=True)
    # The file is a quarterly snapshot, so the same violation can appear
    # in multiple quarters. VIOLATION_ID uniquely identifies a violation.
    result = result.drop_duplicates(subset='VIOLATION_ID')
    return result


def load_latest_water_systems(water_systems_path):
    """Load the public water systems table, keeping only the most
    recent quarterly snapshot (rows repeat per PWSID across quarters)."""
    systems = pd.read_csv(
        water_systems_path, usecols=WATER_SYSTEMS_COLS, low_memory=False
    )
    latest_quarter = systems['SUBMISSIONYEARQUARTER'].max()
    latest = systems[systems['SUBMISSIONYEARQUARTER'] == latest_quarter]
    return latest[latest['PWS_ACTIVITY_CODE'] == 'A']


def main():
    nitrate_codes = get_nitrate_contaminant_codes(REF_CODES_PATH)
    print(f'Nitrate/nitrite contaminant codes: {nitrate_codes}')

    violations = filter_nitrate_violations(VIOLATIONS_PATH, nitrate_codes)
    print(f'Nitrate/nitrite health-based MCL violations: {len(violations)}')
    violations.to_csv('nitrate_violations_filtered.csv', index=False)

    systems = load_latest_water_systems(WATER_SYSTEMS_PATH)
    print(f'Active public water systems (latest quarter): {len(systems)}')
    systems.to_csv('pub_water_systems_filtered.csv', index=False)


if __name__ == '__main__':
    main()
