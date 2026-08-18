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
    plt.figure(figsize=(8, 6))
    sns.scatterplot(
        x="pesticide_intensity", y="overall_rate", hue="nitrate_rate",
        data=data, palette="viridis"
    )
    sns.regplot(
        x="pesticide_intensity", y="overall_rate", data=data,
        scatter=False, color="red"
    )
    plt.title("Overall rate vs Pesticide intensity (colored by nitrate rate)")
    plt.xlabel("Pesticide intensity")
    plt.ylabel("Overall rate")
    plt.legend(title="Nitrate rate", loc="best")
    p = outdir / "q2_scatter_pesticide_overall.png"
    plt.savefig(p, bbox_inches="tight", dpi=150)
    plt.close()
    logging.info(f"Saved {p}")


def plot_interaction(data, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    data = data.copy()
    data["nitrate_bin"] = pd.qcut(
        data["nitrate_rate"], q=3, labels=["low", "med", "high"]
    )

    plt.figure(figsize=(8, 6))
    colors = {"low": "tab:blue", "med": "tab:orange", "high": "tab:green"}

    for label, group in data.groupby("nitrate_bin"):
        sns.regplot(
            x="pesticide_intensity", y="overall_rate", data=group,
            scatter=False, ci=None, label=label, color=colors[label]
        )

    plt.title(
        "Interaction: overall vs pesticide intensity stratified by "
        "nitrate terciles"
    )
    plt.xlabel("Pesticide intensity")
    plt.ylabel("Overall rate")
    plt.legend(title="nitrate_bin")

    p = outdir / "q2_interaction_strata.png"
    plt.savefig(p, bbox_inches="tight", dpi=150)
    plt.close()
    logging.info(f"Saved {p}")


def plot_residuals(model, data, outdir, name="model3"):
    outdir.mkdir(parents=True, exist_ok=True)
    fitted = model.fittedvalues
    resid = model.resid

    plt.figure(figsize=(8, 4))
    plt.subplot(1, 2, 1)
    plt.scatter(fitted, resid)
    plt.axhline(0, color='red', linestyle='--')
    plt.xlabel('Fitted')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted')

    plt.subplot(1, 2, 2)
    sm.qqplot(resid, line='s', ax=plt.gca())
    plt.title('QQ plot')

    p = outdir / f"{name}_residuals.png"
    plt.savefig(p, bbox_inches="tight", dpi=150)
    plt.close()
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
    pd.DataFrame(rows).to_csv(outpath, index=False)
    logging.info(f"Saved model scores to {outpath}")


def write_captions(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    captions = {
        "q2_scatter_pesticide_overall.png": (
            "Scatter of overall rate vs pesticide intensity, colored by "
            "nitrate rate. Chosen to show raw relationship and how "
            "nitrate levels vary across points."
        ),
        "q2_interaction_strata.png": (
            "Stratified means of overall rate vs pesticide intensity "
            "for low/med/high nitrate terciles — visualizes "
            "interaction effect."
        ),
        "model3_residuals.png": (
            "Residual diagnostics for the combined model to inspect "
            "normality and heteroskedasticity."
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
    data = prepare_data(df)
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
    print(m1.summary())
    print(m2.summary())
    print(m3.summary())
    print(
        f"5-fold CV R^2 scores (model3 features): "
        f"mean={scores.mean():.4f}, std={scores.std():.4f}"
    )


if __name__ == "__main__":
    main()
