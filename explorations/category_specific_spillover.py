"""
Exploration: Category-specific spillover regressions.

For each of the 5 macro cause categories and 5 macro effect categories,
run the baseline spillover regression separately:

    s_{ikt,c} = beta_c * peer_share_{i,c}^{-k} + alpha_k + gamma_t + eps

This tells us which categories drive the stacked result.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pyhdfe
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]

# --- Load and prepare (same as 06_table_IVB_spillover.py) ---
panel = pd.read_csv(ROOT / "data_processed" / "panel_ikt.csv", encoding="utf-8")

N_CAUSE = 5
N_EFFECT = 5
CAUSE_COLS = [f"share_cause_{c}" for c in range(1, N_CAUSE + 1)]
EFFECT_COLS = [f"share_effect_{c}" for c in range(1, N_EFFECT + 1)]

# Macro category names (from the taxonomy)
CAUSE_NAMES = {
    1: "Tech Innovation & Advancement",
    2: "Market Demand & Consumer Behavior",
    3: "Strategic Partnerships & Collab.",
    4: "Regulatory & Policy Drivers",
    5: "Cost & Economic Viability",
}
EFFECT_NAMES = {
    1: "Revenue & Financial Growth",
    2: "Market Expansion & Adoption",
    3: "Product & Service Innovation",
    4: "Operational Efficiency &Tic Improve.",
    5: "Cost Reduction & Efficiency",
}

# Multi-tech sample
techs_per_firm = panel.groupby("gvkey")["technology"].nunique()
multi_tech_firms = techs_per_firm[techs_per_firm >= 2].index
df = panel[panel["gvkey"].isin(multi_tech_firms)].copy()


def compute_peer_shares(data, share_cols, prefix):
    firm_sum = data.groupby("gvkey")[share_cols].sum()
    firm_n = data.groupby("gvkey")[share_cols].count()
    own_sum = data.groupby(["gvkey", "technology"])[share_cols].transform("sum")
    own_n = data.groupby(["gvkey", "technology"])[share_cols].transform("count")
    firm_sum_mapped = data["gvkey"].map(firm_sum.to_dict(orient="index"))
    firm_n_mapped = data["gvkey"].map(firm_n.to_dict(orient="index"))
    firm_sum_df = pd.DataFrame(firm_sum_mapped.tolist(), index=data.index)
    firm_n_df = pd.DataFrame(firm_n_mapped.tolist(), index=data.index)
    for col in share_cols:
        peer_col = f"{prefix}_{col}"
        numerator = firm_sum_df[col] - own_sum[col]
        denominator = firm_n_df[col] - own_n[col]
        data[peer_col] = numerator / denominator.replace(0, np.nan)
    return data


df = compute_peer_shares(df, CAUSE_COLS, "peer")
df = compute_peer_shares(df, EFFECT_COLS, "peer")

peer_cause_cols = [f"peer_{c}" for c in CAUSE_COLS]
peer_effect_cols = [f"peer_{c}" for c in EFFECT_COLS]
df = df.dropna(subset=peer_cause_cols + peer_effect_cols)


def run_single_category_reg(data, own_col, peer_col, cluster_col="gvkey"):
    """Run OLS: own_share_c = beta * peer_share_c + tech FE + qtr FE."""
    sub = data[["gvkey", "technology", "dateQ", own_col, peer_col]].dropna().copy()
    sub = sub.reset_index(drop=True)

    y = sub[own_col].values.astype(np.float64)
    X = sub[peer_col].values.astype(np.float64).reshape(-1, 1)
    clusters = sub[cluster_col].values

    fe_ids = np.column_stack([
        pd.Categorical(sub["technology"]).codes,
        pd.Categorical(sub["dateQ"]).codes,
    ])

    algo = pyhdfe.create(fe_ids, drop_singletons=False, residualize_method="map")
    yX = np.column_stack([y, X])
    yX_dm = algo.residualize(yX)
    y_dm = yX_dm[:, 0]
    X_dm = yX_dm[:, 1:]

    keep = np.abs(X_dm.ravel()) > 1e-15
    if keep.sum() < 10:
        return None

    ols = sm.OLS(y_dm[keep], X_dm[keep]).fit(
        cov_type="cluster", cov_kwds={"groups": clusters[keep]}
    )

    resid = y_dm[keep] - X_dm[keep].ravel() * ols.params[0]
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum(y_dm[keep] ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    return {
        "beta": ols.params[0],
        "se": ols.bse[0],
        "tstat": ols.tvalues[0],
        "pval": ols.pvalues[0],
        "n_obs": len(sub),
        "r2": r2,
    }


def star(pval):
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.10:
        return "*"
    return ""


# --- Run category-specific regressions ---
print("=" * 75)
print("CATEGORY-SPECIFIC SPILLOVER REGRESSIONS")
print("(Baseline FE: technology + quarter, clustered at firm)")
print("=" * 75)

results = []

print("\n--- CAUSE SIDE ---")
print(f"{'Category':<42s} {'beta':>8s} {'se':>8s} {'t':>8s} {'N':>8s} {'R2':>8s}")
print("-" * 75)
for c in range(1, N_CAUSE + 1):
    own_col = f"share_cause_{c}"
    peer_col = f"peer_share_cause_{c}"
    res = run_single_category_reg(df, own_col, peer_col)
    if res:
        s = star(res["pval"])
        print(f"{CAUSE_NAMES[c]:<42s} {res['beta']:>7.4f}{s:<3s} "
              f"({res['se']:.4f}) {res['tstat']:>7.2f} {res['n_obs']:>7,d} "
              f"{res['r2']:>7.4f}")
        results.append({
            "side": "cause", "category": c, "name": CAUSE_NAMES[c],
            **res
        })

print("\n--- EFFECT SIDE ---")
print(f"{'Category':<42s} {'beta':>8s} {'se':>8s} {'t':>8s} {'N':>8s} {'R2':>8s}")
print("-" * 75)
for c in range(1, N_EFFECT + 1):
    own_col = f"share_effect_{c}"
    peer_col = f"peer_share_effect_{c}"
    res = run_single_category_reg(df, own_col, peer_col)
    if res:
        s = star(res["pval"])
        print(f"{EFFECT_NAMES[c]:<42s} {res['beta']:>7.4f}{s:<3s} "
              f"({res['se']:.4f}) {res['tstat']:>7.2f} {res['n_obs']:>7,d} "
              f"{res['r2']:>7.4f}")
        results.append({
            "side": "effect", "category": c, "name": EFFECT_NAMES[c],
            **res
        })

# Summary
print("\n" + "=" * 75)
print("SUMMARY: Ranked by |beta|")
print("=" * 75)
results_df = pd.DataFrame(results)
results_df["abs_beta"] = results_df["beta"].abs()
results_df = results_df.sort_values("abs_beta", ascending=False)
for _, row in results_df.iterrows():
    s = star(row["pval"])
    sig = "SIG" if row["pval"] < 0.05 else "n.s."
    print(f"  {row['side']:>6s}  {row['name']:<42s}  beta={row['beta']:.4f}{s:<3s}  [{sig}]")

# Save
out_path = ROOT / "explorations" / "category_specific_spillover_results.csv"
results_df.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
