# State-Level Associations Between Agricultural Pesticide Use, Nitrate Drinking-Water Violations, and Cancer Incidence in the United States

CSE 163 Final Project — Aarushi Koneru and Quynh Le

## Overview

This project examines state-level associations between agricultural
pesticide use, nitrate/nitrite drinking-water violations, and cancer
incidence in the United States, using CDC, USGS, USDA, and EPA data.
We ask:

1. Is agricultural pesticide-use intensity associated with
   age-adjusted incidence of hormone-related cancers at the state
   level?
2. Do agricultural pesticide use and nitrate/nitrite drinking-water
   violations together explain more variation in overall cancer
   incidence than either exposure alone?
3. Are higher rates of health-based nitrate/nitrite drinking-water
   violations associated with higher age-adjusted incidence of
   colorectal and stomach (gastric) cancers?

See the full report for our methods, results, and limitations.

## Setup

### 1. Install dependencies

This project uses Python 3.9+.

---requirements---

All third-party libraries are listed in `requirements.txt`. Install
them with:

```
pip install -r requirements.txt
```

This installs: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`,
`scikit-learn`, `statsmodels`.

---end requirements---

### 2. Download the one large data file

Everything needed to run the pipeline is already committed to this
repository **except** one file that is too large for git:

- Download `qs.census2017.txt.gz` (138MB, USDA 2017 Census of
  Agriculture) from
  <https://www.nass.usda.gov/datasets/qs.census2017.txt.gz>
  and place it in the project root (same folder as `main.py`).

All other inputs — CDC WONDER exports, USGS pesticide-use files, the
EPA nitrate/water-system filtered CSVs, and the USDA/state lookup
table — are already included in the repository.

> **Note:** `clean_epa_data.py` is a *separate, one-time* preprocessing
> script that filters the original ~3.8GB raw EPA SDWA
> (`SDWA_VIOLATIONS_ENFORCEMENT.csv`, `SDWA_PUB_WATER_SYSTEMS.csv`)
> downloads down to the small `nitrate_violations_filtered.csv` and
> `pub_water_systems_filtered.csv` files that are already committed.
> **You do not need to download the raw SDWA files or run
> `clean_epa_data.py` to reproduce any of our results** — it's included
> for transparency/reproducibility of that one preprocessing step only.

## Files

### Data-cleaning modules

| File | Description |
|---|---|
| `state_lookup.py` | Crosswalk table (state name, FIPS code, postal abbreviation) used to join every other dataset on a common state key. |
| `clean_cdc.py` | Loads the CDC WONDER cancer exports and builds one state-level table with `overall_rate`, `hormone_rate` (pooled across five hormone-related cancer sites), `colorectal_rate`, and `stomach_rate`. |
| `clean_usgs.py` | Loads the USGS county-level agricultural pesticide-use files (2013–2017) and aggregates them into each state's average annual pesticide-use total. |
| `clean_usda.py` | Loads the USDA 2017 Census of Agriculture bulk file and reconstructs each state's total agricultural land area (acres), used as the denominator for pesticide-use intensity. |
| `clean_epa.py` | Builds the state-level nitrate/nitrite drinking-water violation rate (per water system and per 100,000 population) from the filtered EPA files. |
| `clean_epa_data.py` | One-time preprocessing script that filters the raw multi-GB EPA SDWA downloads down to the nitrate/nitrite violation and water-system CSVs used by `clean_epa.py`. Not required to reproduce results (see note above). |
| `main.py` | Merges the CDC, USGS, USDA, and EPA tables into the two analysis tables used by the research questions, and writes them to `output/`. |

### Analysis modules (one per research question)

| File | Description |
|---|---|
| `q1.py` | Answers RQ1: is pesticide-use intensity associated with hormone-related cancer incidence? Produces summary statistics, a scatterplot, a tertile bar chart, correlation tests, and a linear regression with residual plot. |
| `q2codeplot.py` | Answers RQ2: do pesticide use and nitrate violations together explain more variation in overall cancer incidence than either alone? Fits three OLS models (pesticide-only, nitrate-only, combined with interaction), runs 5-fold cross-validation, and saves diagnostic plots and influential-point/model-score CSVs. |
| `q3.py` | Answers RQ3: are nitrate violation rates associated with colorectal and stomach cancer incidence? Produces scatterplots, correlation/regression results, and two sensitivity analyses (excluding small states; per-capita nitrate normalization). |

### Testing

| File | Description |
|---|---|
| `test_clean.py` | Assert-based tests for the four cleaning modules (`clean_cdc.py`, `clean_usgs.py`, `clean_usda.py`, `clean_epa.py`), run against small hand-built fixture CSVs rather than the full project datasets. |

## How to run

Run these from the project root, in order:

0. **Install dependencies** (see [Setup](#setup) above):

   ```
   pip install -r requirements.txt
   ```

1. **Build the analysis tables:**

   ```
   python main.py
   ```

   Writes `output/state_table.csv` (48 states — contiguous U.S., needs
   pesticide data) and `output/state_table_cdc_epa.csv` (51 states —
   all states + D.C., CDC + EPA only).

2. **Run each research question's analysis:**

   ```
   python q1.py
   python q2codeplot.py
   python q3.py
   ```

   `q1.py` and `q3.py` read from `output/` and write their figures back
   to `output/`. `q2codeplot.py` reads from `output/` and writes its
   figures to `figures/q2/`, plus `q2_model_scores.csv` and
   `q2_influential.csv` to the project root.

3. **Run the tests:**

   ```
   python test_clean.py
   ```

   Prints `PASSED` for each of the 6 tests.

## Notes

- Alaska, Hawaii, and California are excluded from the pesticide-based
  analyses (RQ1, RQ2) — USGS coverage is contiguous-U.S.-only, and
  California's 2017 file is distributed separately. They are included
  in the RQ3 table, which does not use pesticide data.
- D.C. is excluded from the pesticide-based analyses (no agricultural
  land) but included in the RQ3 table.
- See the full report for research questions, methodology, results,
  and limitations.
