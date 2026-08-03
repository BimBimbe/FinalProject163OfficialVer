"""Q1 combo-EDA: CDC hormone-related cancer incidence vs. USGS/USDA
pesticide-use intensity, one row per contiguous state (DC excluded --
no pesticide data). Answers RQ1: does higher pesticide-use intensity
associate with higher hormone-related cancer incidence?
"""
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression

DATA_PATH = 'output/state_table.csv'
COLS = ['hormone_rate', 'pesticide_intensity']


def load_q1_data(path=DATA_PATH):
    df = pd.read_csv(path)
    return df[['state', 'state_postal'] + COLS]


def report_size_and_missingness(df):
    print(f'Q1 table: {df.shape[0]} rows, {df.shape[1]} columns')
    print('Rows = states (contiguous U.S.; DC excluded, no pesticide data).')
    print('Columns = state identifiers plus hormone_rate and '
          'pesticide_intensity.')
    print('Missing values per column:')
    print(df.isna().sum())


def summarize(df):
    print(df[COLS].describe())


def plot_scatter(df, out_path='output/q1_scatter.png'):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(df['pesticide_intensity'], df['hormone_rate'], color='#2C6E62')
    ax.set_xlabel('Pesticide-use intensity (avg kg / ag. acre, 2013-2017)')
    ax.set_ylabel('Hormone-related cancer rate (per 100,000, pooled)')
    ax.set_title(
        'Hormone-related cancer incidence vs. pesticide-use intensity, '
        'by state'
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'Wrote {out_path}')


def plot_tertile_bar(df, out_path='output/q1_tertile_bar.png'):
    tertiles = pd.qcut(
        df['pesticide_intensity'], 3, labels=['Low', 'Medium', 'High']
    )
    means = df.groupby(tertiles, observed=True)['hormone_rate'].mean()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(means.index.astype(str), means.values, color='#2C6E62')
    ax.set_xlabel('Pesticide-use intensity tertile')
    ax.set_ylabel('Mean hormone-related cancer rate (per 100,000)')
    ax.set_title('Mean hormone-related cancer rate by pesticide-use tertile')
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'Wrote {out_path}')
    print(means)


def run_correlations(df):
    r, p_pearson = stats.pearsonr(
        df['pesticide_intensity'], df['hormone_rate']
    )
    rho, p_spearman = stats.spearmanr(
        df['pesticide_intensity'], df['hormone_rate']
    )
    print(f'Pearson r = {r:.4f}, p = {p_pearson:.4f}')
    print(f'Spearman rho = {rho:.4f}, p = {p_spearman:.4f}')
    return r, p_pearson, rho, p_spearman


def run_regression(df, out_path='output/q1_residuals.png'):
    x = df[['pesticide_intensity']].values
    y = df['hormone_rate'].values
    model = LinearRegression().fit(x, y)
    pred = model.predict(x)
    residuals = y - pred
    r_squared = model.score(x, y)
    print(
        f'slope = {model.coef_[0]:.4f}, intercept = {model.intercept_:.4f}, '
        f'R^2 = {r_squared:.4f}'
    )

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(pred, residuals, color='#8C6425')
    ax.axhline(0, color='#5B6B65', linestyle='--')
    ax.set_xlabel('Predicted hormone-related cancer rate')
    ax.set_ylabel('Residual')
    ax.set_title('Residuals of hormone_rate ~ pesticide_intensity')
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'Wrote {out_path}')
    return model.coef_[0], model.intercept_, r_squared


def main():
    df = load_q1_data()
    report_size_and_missingness(df)
    summarize(df)
    plot_scatter(df)
    plot_tertile_bar(df)
    run_correlations(df)
    run_regression(df)


if __name__ == '__main__':
    main()
