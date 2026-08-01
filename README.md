Plans and update:
- 

## Setup

Everything needed to run `python main.py` is committed except one file,
which is too large for git:

- Download `qs.census2017.txt.gz` (138MB, USDA 2017 Census of
  Agriculture) from https://www.nass.usda.gov/datasets/qs.census2017.txt.gz
  and place it in the project root (same folder as `main.py`).

Then `python main.py` writes `output/state_table.csv` (48 states,
needs pesticide data) and `output/state_table_cdc_epa.csv` (51 states,
CDC + EPA only).
