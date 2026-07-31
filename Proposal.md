Title: State-Level Associations Between Agricultural Pesticide Use, Nitrate Drinking-Water Violations, and Cancer Incidence in the United States
Authors: Aarushi Koneru and Quynh Le
Summary of Research Questions
Pesticides and hormone-related cancers: Is there a statistically significant positive association between a state's agricultural pesticide-use intensity and its age-adjusted incidence of hormone-related cancers?


Combined exposure and overall cancer: Do agricultural pesticide use and nitrate/nitrite drinking-water violations together explain more variation in overall cancer incidence than either exposure alone? Specifically, does a model using both exposures (including their interaction) predict overall cancer incidence better than either single-exposure model?


Nitrate violations and digestive cancers: Are states with higher rates of health-based nitrate/nitrite drinking-water violations associated with higher age-adjusted incidence of colorectal and stomach (gastric) cancers?


Motivation
Cancer prevention depends in part on understanding environmental conditions that may be associated with disease. Agricultural pesticide use and contaminants in public drinking water can affect large populations, yet these exposures vary substantially across U.S. states. By combining pesticide-use estimates, drinking-water compliance data, and cancer-incidence rates, we will examine whether states with higher environmental exposure measures also tend to report higher rates of selected cancers.
This project connects environmental science with public-health data and helps identify patterns that could guide future research and monitoring. However, our analysis will measure state-level associations rather than causation: it cannot determine whether a particular person's exposure caused their cancer. Cancer incidence is also influenced by factors such as age, smoking prevalence, access to screening and healthcare, occupation, and socioeconomic conditions. Because most solid cancers develop over 10-30 years while our exposure data cover only recent years, we treat the exposure measures as proxies for chronic state-level conditions rather than the actual causal window.
Datasets
CDC WONDER Cancer Statistics:
URL: https://catalog.data.gov/dataset/cdc-wonder-cancer-statistics
We will run queries and export tab-delimited (.txt) tables of age-adjusted incidence per 100,000 by state, for each cancer group we need (overall, hormone-related, colorectal, stomach), for a single consistent multi-year window. Two practical constraints: (a) rates based on fewer than 16 cases are suppressed, some small states may be missing for rare cancers such as stomach cancer; (b) "hormone-related cancers" is not a built-in category, so we define it explicitly (see Method).

         2. U.S. Geological Survey Estimated Annual Agricultural Pesticide Use
URL: https://data.usgs.gov/datacatalog/data/USGS:5e95c12282ce172707f2524e
This dataset contains estimated annual agricultural pesticide-use data at the county level for the contiguous United States from 2013-2017. We will clean and aggregate estimated pesticide use across counties and years to create a state-level pesticide-use measure, used in Research Questions 1 and 2. This release covers only the conterminous U.S., so Alaska and Hawaii are excluded, and California's values come from a separate state source appended after the fact. Seed-treatment applications were dropped starting in 2015, creating a small methodological break between 2013-14 and 2015-17.
3. Drinking water compliance and nitrate measures- EPA ECHO/SDWIS
URL: https://echo.epa.gov/tools/data-downloads/sdwa-download-summary

We will download drinking-water compliance records and identify nitrate/nitrite-related health-based violations. EPA provides national downloads for key drinking-water metrics derived from SDWIS data. We will calculate each state's number or rate of nitrate/nitrite violations relative to its number of public water systems or population served, depending on which is available in the download.
Challenge Goals
Multiple Datasets
Our project joins three independently produced datasets: cancer-incidence rates (CDC WONDER), county-level pesticide-use estimates (USGS), and drinking-water compliance records (EPA SDWIS). We will standardize state identifiers across FIPS codes and 2-letter postal codes, aggregate county-level pesticide data up to the state level, reduce per-water-system violation records to per-state rates, and merge everything into one analysis table with one row per state. Our research questions cannot be answered from any single dataset; they exist only in the merged table.
Result Validity
 Because we have at most ~49 states, we treat statistical rigor as central. For each correlation we report a p-value and interpret non-significant results as genuine nulls. For the regression models we guard against overfitting with cross-validation, compare models by R-squared, inspect residual plots and outlier states with matplotlib to check whether a few states drive a result, and run sensitivity analyses that exclude very small states and try alternative normalizations.
Method
Overview
We build one table with one row per state. Because the USGS pesticide data covers only the conterminous U.S., the analysis table has up to 49 rows (48 contiguous states + D.C.); Alaska and Hawaii are excluded from any pesticide-based question. Joins use state FIPS codes and 2-letter postal codes as keys. All analysis is done in Python with pandas and scikit-learn; figures use matplotlib and seaborn. Because the USGS and EPA files are large, we develop locally.
Build variables:
CDC
1. Export four separate tab-delimited (.txt) tables from CDC WONDER using the same multi-year time period:
- Overall cancer incidence
- Hormone-related cancers
 - Colorectal cancer
- Stomach cancer
 2. For each export, import the file into pandas.
3. Keep the State column and the Age-Adjusted Rate column, which reports cancer incidence per 100,000 population. If exported, retain the 95% confidence interval columns for documentation.
 4. Rename the Age-Adjusted Rate column according to the cancer type (for example, overall_rate, hormone_rate, colorectal_rate, and stomach_rate)
 5. Remove rows where CDC suppresses the rate because fewer than 16 cases occurred.
 6. Merge the four cancer tables into one table containing one row per state.

USGS
Download the county-level agricultural pesticide-use estimates for 2013–2017.
Import the tab-delimited files into pandas.
Use the High Estimate pesticide values, as recommended in the project description.
For each year, group counties by State FIPS and sum the estimated pesticide kilograms across all pesticide compounds and counties within each state. The USGS data provide pesticide estimates organized by compound, year, state FIPS, county FIPS, and kilograms (kg).
Average each state’s total pesticide use across the five years (2013–2017).
Divide the average pesticide total by the state’s agricultural land area (obtained from USDA Census of Agriculture) to calculate pesticide-use intensity (kg per unit agricultural land).
Exclude Alaska and Hawaii because the USGS dataset contains only the contiguous United States.
EPA
Download the SDWIS drinking-water violations table and the reference table containing contaminant codes.
Import both files into pandas.
Use the reference table to identify contaminant codes corresponding to nitrate and nitrite.
Filter the violations table to retain only:
Health-based Maximum Contaminant Level (MCL) violations
Nitrate or nitrite contaminants
Group the remaining records by state.
Count the number of qualifying violations for each state.
Standardize the counts by dividing either by:
the number of public water systems in the state, or
the population served.
Create one variable representing each state’s nitrate violation rate. The alternative normalization is retained for sensitivity analysis.
Merging datasets
Convert all datasets to a common state identifier (State FIPS or postal abbreviation).
Merge the cancer, pesticide, and nitrate datasets into one table using an inner join.
Verify that each state appears only once.
Remove states with missing values caused by suppressed cancer rates or unavailable pesticide estimates.
      5.	Inspect summary statistics and missing values before beginning statistical analysis.

Question 1
We rename the CDC Age-Adjusted Rate column to hormone_rate after importing the hormone-related cancer table. Select the variables hormone_rate and pesticide_intensity from the merged dataset.
Produce a scatterplot to visually inspect the relationship.
Compute the Pearson correlation coefficient and corresponding p-value to test for a linear association.
Compute the Spearman rank correlation coefficient to evaluate whether a monotonic relationship exists if the relationship is not perfectly linear.
Fit a simple linear regression model predicting hormone-related cancer incidence from pesticide intensity.
Record the regression coefficient, intercept, and R² value.
Examine residual plots to identify influential outlier states.
Divide pesticide intensity into tertiles (low, medium, high) and compare the average hormone-related cancer incidence among the three groups.
Interpretation: A statistically significant positive correlation and positive regression slope support the state-level association between agricultural pesticide-use intensity and hormone-related cancer incidence. Non-significant or inconsistent results will be interpreted as the available state-level data do not support the proposed association. This analysis satisfies the Multiple Datasets challenge goal by combining CDC cancer dataset with USGS pesticide dataset.

Question 2
 Select overall_rate, pesticide_intensity, and nitrate_rate.
Create an interaction variable by multiplying pesticide intensity and nitrate violation rate.
Fit three linear regression models:
Model 1: Overall cancer ~ pesticide intensity
Model 2: Overall cancer ~ nitrate violation rate
Model 3: Overall cancer ~ pesticide intensity + nitrate violation rate + interaction
Evaluate each model using R² and 5-fold cross-validation.
Compare model performance to determine whether combining both environmental exposures improves prediction.
Examine residual plots for influential observations.
Interpretation: If the combined model consistently produces higher cross-validated R² than either single-exposure model, this suggests that the two environmental exposure measures together explain more variation in overall cancer incidence. This analysis satisfies both the Multiple Datasets and Result Validity challenge goals.


Question 3
Select colorectal_rate and nitrate_rate.
Compute Pearson and Spearman correlations with associated p-values.
Fit a linear regression model predicting colorectal cancer incidence from nitrate violation rate.
Repeat Steps 1–3 using stomach_rate.
Repeat the analyses after:
excluding Washington, D.C. and very small states, and
replacing the per-system nitrate rate with the per-capita nitrate rate.
Interpretation: Positive associations that remain statistically significant after both sensitivity analyses will be interpreted as evidence of a stable state-level association. Associations that disappear or reverse will be reported as inconclusive. This analysis supports the Result Validity challenge goal through statistical significance testing and sensitivity analyses.
Work Plan
Download, document, and inspect databases: query and export CDC WONDER tables, download USGS pesticide files and the EPA SDWIS ZIP, and record exact query settings and file versions. (Est: 5 hours)
Write data-cleaning functions and standardize states: parse each source, map FIPS to postal codes, handle suppressed cancer rows and the Alaska/Hawaii exclusion. (Est: 6 hours)
Create the cancer-incidence dataset and exploratory visuals. (Est: 4 hours)
Merge datasets and construct exposure variables (pesticide intensity, nitrate violation rate). (Est: 5 hours)
Perform statistical analysis and validity checks: correlations, regressions, model comparison, sensitivity analyses. (Est: 5 hours)
Build final visualizations and write findings. (Est: 4 hours)
Edit report, test scripts, and write reproducibility instructions. (Est: 6 hours)
Workflow, testing, and coordination:
We use Git and GitHub with feature branches and review each other's changes before merging.
Shared cleaning logic lives in one module so both members import the same functions.
We write assert-based test functions on the cleaning and aggregation functions using small, hand-checked inputs, and run flake8 for style.
 Work is split so each member owns specific research questions but reviews the other's code.
 If one task turns out to be unexpectedly hard (the EPA violation filtering is likely the one ), we will pair it and reallocate hours from lighter tasks.
Development environment:
Both of us set up local Python early with pandas, scikit-learn, matplotlib, and seaborn, using VS Code. We work locally rather than online because the USGS and EPA files are large and working with VS Code is just way better to navigate around than the notebook,  installing early avoids discovering a blocker close to the deadline.

