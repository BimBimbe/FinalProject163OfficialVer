"""Q2 analysis script

Creates interaction term between pesticide intensity and nitrate rate,
fits three regression models, computes R^2 and 5-fold CV, and saves
plots.

Usage: python q2codeplot.py
"""
from pathlib import Path
import logging

try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.model_selection import KFold, cross_val_score
    from sklearn.linear_model import LinearRegression
    import statsmodels.api as sm
except Exception:
    print(
        "Missing required packages. Install with: pip install pandas "
        "numpy matplotlib seaborn scikit-learn statsmodels"
    )
    raise

logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_state_table():
    candidates = [
        Path("output/state_table_cdc_epa.csv"),
        Path("output/state_table.csv"),
        Path("state_table_cdc_epa.csv"),
        Path("state_table.csv"),
    ]
    for p in candidates:
        if p.exists():
            logging.info(f"Loading {p}")
            return pd.read_csv(p)
    raise FileNotFoundError(
        "Could not find a state table CSV. Expected one of: "
        + ",".join(str(x) for x in candidates)
    )


def prepare_data(df, nitrate_col="nitrate_rate_per_system"):
    # ensure nitrate column exists
    if nitrate_col not in df.columns:
        raise KeyError(f"Missing nitrate column: {nitrate_col}")

    # ensure pesticide_intensity exists; compute if we have components
    if "pesticide_intensity" not in df.columns:
        if "avg_pesticide_kg" in df.columns and "ag_land_acres" in df.columns:
            logging.info(
                "Computing pesticide_intensity from "
                "avg_pesticide_kg / ag_land_acres"
            )
            df = df.copy()
            df["pesticide_intensity"] = (
                df["avg_pesticide_kg"] / df["ag_land_acres"]
            )
        else:
            # if pesticides missing in this table, try loading the
            # alternate table
            alt = Path("output/state_table.csv")
            if alt.exists():
                logging.info(
                    f"Reloading {alt} which contains pesticide fields"
                )
                df = pd.read_csv(alt)
            else:
                raise KeyError(
                    "Missing pesticide_intensity and unable to compute "
                    "it from available columns"
                )

    cols = ["overall_rate", "pesticide_intensity", nitrate_col]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns after fallback: {missing}")

    data = df[cols].copy()
    data = data.rename(columns={nitrate_col: "nitrate_rate"})
    data["interaction"] = data["pesticide_intensity"] * data["nitrate_rate"]
    data = data.replace([np.inf, -np.inf], np.nan).dropna()
    logging.info(f"Prepared data with {len(data)} rows after dropping NA/inf")
    return data


def fit_models(data):
    y = data["overall_rate"].values
    X1 = sm.add_constant(data[["pesticide_intensity"]])
    X2 = sm.add_constant(data[["nitrate_rate"]])
    X3 = sm.add_constant(
        data[["pesticide_intensity", "nitrate_rate", "interaction"]]
    )

    m1 = sm.OLS(y, X1).fit()
    m2 = sm.OLS(y, X2).fit()
    m3 = sm.OLS(y, X3).fit()
    return m1, m2, m3


def cv_scores(data, n_splits=5):
    X = data[["pesticide_intensity", "nitrate_rate", "interaction"]].values
    y = data["overall_rate"].values
    model = LinearRegression()
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=1)
    scores = cross_val_score(model, X, y, scoring="r2", cv=kf)
    return scores


def plot_scatter(data, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 6))
    sns.scatterplot(
        x="pesticide_intensity", y="overall_rate", hue="nitrate_rate",
        data=data, palette="viridis", s=100, alpha=0.7, edgecolors='black', linewidth=0.5
    )
    sns.regplot(
        x="pesticide_intensity", y="overall_rate", data=data,
        scatter=False, color="red", linewidth=2.5
    )
    plt.title("Overall cancer rate vs Pesticide intensity\n(colored by nitrate violation rate)", fontsize=13, fontweight='bold')
    plt.xlabel("Pesticide-use intensity (kg/acre, 2013–2017)", fontsize=12)
    plt.ylabel("Overall cancer rate (per 100,000)", fontsize=12)
    plt.legend(title="Nitrate rate (per system)", loc="best", fontsize=10)
    p = outdir / "q2_scatter_pesticide_overall.png"
    plt.savefig(p, bbox_inches="tight", dpi=300)
    plt.close()
    logging.info(f"Saved {p}")


def plot_interaction(data, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    # create tercile bins of nitrate_rate
    data = data.copy()
    data["nitrate_bin"] = pd.qcut(
        data["nitrate_rate"], q=3, labels=["low", "med", "high"], duplicates='drop'
    )
    
    fig, ax = plt.subplots(figsize=(9, 6))
    
    colors = {'low': '#1f77b4', 'med': '#ff7f0e', 'high': '#2ca02c'}
    for bin_label in ['low', 'med', 'high']:
        subset = data[data["nitrate_bin"] == bin_label]
        if len(subset) == 0:
            continue
        
        # Plot points
        ax.scatter(subset['pesticide_intensity'], subset['overall_rate'],
                   label=bin_label.capitalize(), color=colors[bin_label], s=100, alpha=0.6, edgecolors='black', linewidth=0.5)
        
        # Fit regression line for this subset
        if len(subset) > 1:
            x_subset = subset[['pesticide_intensity']].values
            y_subset = subset['overall_rate'].values
            from sklearn.linear_model import LinearRegression as LR
            model_subset = LR().fit(x_subset, y_subset)
            x_range_subset = np.linspace(subset['pesticide_intensity'].min(), subset['pesticide_intensity'].max(), 50)
            y_range_subset = model_subset.predict(x_range_subset.reshape(-1, 1))
            ax.plot(x_range_subset, y_range_subset, color=colors[bin_label], linewidth=2.5, linestyle='-')
    
    ax.set_xlabel("Pesticide-use intensity (kg/acre, 2013–2017)", fontsize=12)
    ax.set_ylabel("Overall cancer rate (per 100,000)", fontsize=12)
    ax.set_title("Interaction: overall cancer rate vs. pesticide intensity\nstratified by nitrate violation rate tertiles", fontsize=13, fontweight='bold')
    ax.legend(title="Nitrate rate tertile", fontsize=10, title_fontsize=11, loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    p = outdir / "q2_interaction_strata.png"
    fig.savefig(p, bbox_inches="tight", dpi=300)
    plt.close(fig)
    logging.info(f"Saved {p}")


def plot_residuals(model, data, outdir, name="model3"):
    outdir.mkdir(parents=True, exist_ok=True)
    fitted = model.fittedvalues
    resid = model.resid

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: residuals vs fitted
    ax1.scatter(fitted, resid, s=80, alpha=0.6, edgecolors='black', linewidth=0.5, color='steelblue')
    ax1.axhline(0, color='red', linestyle='--', linewidth=2)
    ax1.set_xlabel('Fitted values', fontsize=11)
    ax1.set_ylabel('Residuals', fontsize=11)
    ax1.set_title('Residuals vs. Fitted Values', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Right: QQ plot
    sm.qqplot(resid, line='s', ax=ax2, markersize=8)
    ax2.set_title('Normal Q-Q Plot', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    p = outdir / f"{name}_residuals.png"
    fig.savefig(p, bbox_inches="tight", dpi=300)
    plt.close(fig)
    logging.info(f"Saved {p}")


def influential_points(model, data, outpath):
    infl = model.get_influence()
    cooks = infl.cooks_distance[0]
    df = data.copy()
    df["cooks_d"] = cooks
    df.sort_values("cooks_d", ascending=False).head(20).to_csv(
        outpath, index=False
    )
    logging.info(f"Saved top influential points to {outpath}")


def save_model_scores(models, cv_scores_arr, outpath):
    rows = []
    for name, m in models.items():
        rows.append({
            "model": name,
            "r_squared": float(m.rsquared),
            "n_obs": int(m.nobs)
        })
    # add CV results summary for combined model
    rows.append({
        "model": "model3_cv_mean",
        "r_squared": float(np.mean(cv_scores_arr)),
        "n_obs": len(cv_scores_arr)
    })
    rows.append({
        "model": "model3_cv_std",
        "r_squared": float(np.std(cv_scores_arr)),
        "n_obs": len(cv_scores_arr)
    })
    pd.DataFrame(rows).to_csv(outpath, index=False)
    logging.info(f"Saved model scores to {outpath}")


def write_captions(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    captions = {
        "q2_scatter_pesticide_overall.png": (
            "Scatter of overall cancer rate vs pesticide intensity, colored by "
            "nitrate violation rate (per water system). Fitted regression line shown in red. "
            "Points colored by the continuous nitrate rate to visualize the relationship."
        ),
        "q2_interaction_strata.png": (
            "Stratified regression lines of overall cancer rate vs pesticide intensity "
            "for low/med/high nitrate violation rate tertiles — visualizes "
            "the interaction effect between pesticide use and nitrate exposure."
        ),
        "model3_residuals.png": (
            "Residual diagnostics for the combined model (pesticide + nitrate + interaction). "
            "Left panel: residuals vs. fitted values (checking heteroskedasticity). "
            "Right panel: Q-Q plot (checking normality of residuals)."
        ),
    }
    with open(outdir / "plot_captions.txt", "w", encoding="utf-8") as f:
        for k, v in captions.items():
            f.write(f"{k}: {v}\n\n")
    logging.info(f"Wrote captions to {outdir / 'plot_captions.txt'}")


def main():
    outdir = Path("figures/q2")
    csv_out = Path("q2_model_scores.csv")
    infl_out = Path("q2_influential.csv")

    df = load_state_table()
    data = prepare_data(df, nitrate_col="nitrate_rate_per_system")
    m1, m2, m3 = fit_models(data)
    scores = cv_scores(data, n_splits=5)

    models = {
        "model1_pesticide": m1, "model2_nitrate": m2, "model3_combined": m3
    }
    save_model_scores(models, scores, csv_out)
    influential_points(m3, data, infl_out)

    plot_scatter(data, outdir)
    plot_interaction(data, outdir)
    plot_residuals(m3, data, outdir, name="model3")
    write_captions(outdir)

    # print short summary
    print("\n" + "="*80)
    print("Q2 MODEL SUMMARY (using nitrate_rate_per_system)")
    print("="*80)
    print(m1.summary())
    print("\n" + "="*80)
    print(m2.summary())
    print("\n" + "="*80)
    print(m3.summary())
    print("\n" + "="*80)
    print(
        f"5-fold CV R^2 scores (model3 features): "
        f"mean={scores.mean():.4f}, std={scores.std():.4f}"
    )
    print(f"Individual CV fold scores: {scores}")
    print("="*80)


if __name__ == "__main__":
    main()
