"""
06_table_IVB_spillover.py — Cross-Technology Belief Spillover

Purpose: For Section IV.B, test whether a firm's causal/effect frame for
         technology A predicts its frame for technology B.  Uses a stacked
         regression of own shares on leave-one-out peer shares with
         multi-way fixed effects via pyhdfe + statsmodels.

Main table:  4 columns (Baseline, Ind x Qtr, Tech x Qtr, First appearance)
Robustness:  (A) >=3 techs, (B) snippet-weighted, (C) drop-one-category,
             (D) continuous similarity interaction

Inputs:  data_processed/panel_ikt.csv

Outputs: results/tables/table_IVB_spillover.csv
         results/tables/table_IVB_spillover_robustness.csv
         Overleaf/Tables/spillover.tex
         Overleaf/Tables/spillover_robustness.tex
         results/runs/06_table_IVB_spillover_<timestamp>.json
"""

from pathlib import Path
import json
import datetime
import os
import warnings

import pandas as pd
import numpy as np
import pyhdfe
import statsmodels.api as sm

warnings.filterwarnings("ignore", category=FutureWarning)

SEED = 42
ROOT = Path(__file__).resolve().parents[2]

np.random.seed(SEED)

# 0. Setup ----------------------------------------------------------------
os.makedirs(ROOT / "results" / "tables", exist_ok=True)
os.makedirs(ROOT / "results" / "runs", exist_ok=True)
os.makedirs(ROOT / "Overleaf" / "Tables", exist_ok=True)

N_CAUSE = 5
N_EFFECT = 5
CAUSE_COLS = [f"share_cause_{c}" for c in range(1, N_CAUSE + 1)]
EFFECT_COLS = [f"share_effect_{c}" for c in range(1, N_EFFECT + 1)]

# =========================================================================
# 1. Load data and build multi-tech sample
# =========================================================================
print("Loading panel_ikt.csv ...")
input_path = ROOT / "data_processed" / "panel_ikt.csv"
if not input_path.exists():
    raise FileNotFoundError(
        f"Required input not found: {input_path}\n"
        "Run 01_clean.py first to generate panel_ikt.csv."
    )
panel = pd.read_csv(input_path, encoding="utf-8")
raw_rows = len(panel)
print(f"  Raw panel rows: {raw_rows:,}")

# Restrict to multi-tech firms (>=2 technologies all-time)
techs_per_firm = panel.groupby("gvkey")["technology"].nunique()
multi_tech_firms = techs_per_firm[techs_per_firm >= 2].index
df = panel[panel["gvkey"].isin(multi_tech_firms)].copy()
n_multi_firms = df["gvkey"].nunique()
print(f"  Multi-tech firms (>=2 techs): {n_multi_firms:,}")
print(f"  Observations: {len(df):,}")

# Industry (2-digit SIC for industry x quarter FE)
df["sic2"] = (df["sic"].fillna(0).astype(int) // 100).astype(str)

# =========================================================================
# 2. Leave-one-out peer shares
# =========================================================================
print("\nComputing leave-one-out peer shares ...")


def compute_peer_shares(data, share_cols, prefix):
    """
    For each (firm, tech) observation, compute the firm's average share
    across ALL other technologies (leave-technology-out).

    Strategy: firm-level sum/count minus own-tech sum/count.
    """
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

# Drop rows with missing peers (shouldn't happen for multi-tech, but safety)
before = len(df)
df = df.dropna(subset=peer_cause_cols + peer_effect_cols)
print(f"  Dropped {before - len(df)} rows with missing peers")
print(f"  Final multi-tech sample: {len(df):,} obs, {df['gvkey'].nunique():,} firms")

# =========================================================================
# 3. First-appearance subsample
# =========================================================================
print("\nBuilding first-appearance subsample ...")
first_q = df.groupby(["gvkey", "technology"])["dateQ"].min().reset_index()
first_q.rename(columns={"dateQ": "first_dateQ"}, inplace=True)
df = df.merge(first_q, on=["gvkey", "technology"], how="left")
df["is_first"] = df["dateQ"] == df["first_dateQ"]
n_first = df["is_first"].sum()
print(f"  First-appearance observations: {n_first:,}")

# =========================================================================
# 4. Technology similarity (for continuous interaction)
# =========================================================================
print("\nComputing technology-pair similarity ...")

# Aggregate cause-share profile per technology (across all firms)
tech_profiles = panel.groupby("technology")[CAUSE_COLS].mean()
profiles_arr = tech_profiles.values
norms = np.linalg.norm(profiles_arr, axis=1, keepdims=True)
norms[norms == 0] = 1e-12
normed = profiles_arr / norms
cos_sim_arr = normed @ normed.T
cos_sim_matrix = pd.DataFrame(
    cos_sim_arr, index=tech_profiles.index, columns=tech_profiles.index,
)


def compute_avg_tech_similarity(data, cos_sim_matrix):
    """Average cosine similarity between own tech and firm's other techs."""
    firm_techs = data.groupby("gvkey")["technology"].apply(set).to_dict()
    sims = []
    for _, row in data.iterrows():
        gvkey = row["gvkey"]
        own_tech = row["technology"]
        other_techs = firm_techs[gvkey] - {own_tech}
        if not other_techs:
            sims.append(np.nan)
            continue
        pair_sims = [cos_sim_matrix.loc[own_tech, t] for t in other_techs
                     if t in cos_sim_matrix.index]
        sims.append(np.mean(pair_sims) if pair_sims else np.nan)
    return sims


print("  Computing per-observation similarity (may take a moment) ...")
df["tech_similarity"] = compute_avg_tech_similarity(df, cos_sim_matrix)
sim_median = df["tech_similarity"].median()
sim_p25 = df["tech_similarity"].quantile(0.25)
sim_p75 = df["tech_similarity"].quantile(0.75)
print(f"  Similarity: median={sim_median:.4f}, p25={sim_p25:.4f}, p75={sim_p75:.4f}")

# =========================================================================
# 5. Stack to long format (one row per category)
# =========================================================================
print("\nStacking to long format ...")


def stack_to_long(data, own_cols, peer_cols, side_label, weight_col=None):
    """Reshape: 5 rows per obs (one per macro category c)."""
    records = []
    for c_idx in range(len(own_cols)):
        chunk = data[["gvkey", "technology", "dateQ", "sic2",
                       "is_first", "tech_similarity"]].copy()
        chunk["category"] = c_idx + 1
        chunk["own_share"] = data[own_cols[c_idx]].values
        chunk["peer_share"] = data[peer_cols[c_idx]].values
        if weight_col is not None:
            chunk["weight"] = data[weight_col].values
        records.append(chunk)
    long = pd.concat(records, ignore_index=True)
    long["side"] = side_label
    return long


cause_long = stack_to_long(df, CAUSE_COLS, peer_cause_cols, "cause", "N_cause")
effect_long = stack_to_long(df, EFFECT_COLS, peer_effect_cols, "effect", "N_effect")

print(f"  Cause stacked rows: {len(cause_long):,}")
print(f"  Effect stacked rows: {len(effect_long):,}")


# =========================================================================
# 6. Regression infrastructure
# =========================================================================

def prepare_data(long_df):
    """Create category-interacted FE columns for proper stacked estimation."""
    long_df = long_df.copy()
    cat = long_df["category"].astype(str)
    long_df["tech_cat"] = long_df["technology"].astype(str) + "_" + cat
    long_df["qtr_cat"] = long_df["dateQ"].astype(str) + "_" + cat
    sic2_dateQ = long_df["sic2"].astype(str) + "_" + long_df["dateQ"].astype(str)
    long_df["indqtr_cat"] = sic2_dateQ + "_" + cat
    techqtr = long_df["technology"].astype(str) + "_" + long_df["dateQ"].astype(str)
    long_df["techqtr_cat"] = techqtr + "_" + cat
    # Interaction term for check D
    long_df["peer_x_sim"] = long_df["peer_share"] * long_df["tech_similarity"]
    return long_df


cause_long = prepare_data(cause_long)
effect_long = prepare_data(effect_long)


def run_hdfe_ols(data, fe_cols, cluster_col="gvkey", x_cols=None,
                 weights=None):
    """
    Demean y and x via pyhdfe (Frisch-Waugh-Lovell), then run OLS
    with firm-clustered standard errors.  Equivalent to Stata reghdfe.

    x_cols: list of RHS column names (default: ["peer_share"])
    weights: column name for WLS weights, or None for OLS.

    Returns dict with beta, se, tstat, pval per regressor, plus n_obs, r2.
    """
    if x_cols is None:
        x_cols = ["peer_share"]

    all_cols = ["own_share"] + x_cols + fe_cols
    if weights is not None:
        all_cols.append(weights)

    valid = pd.Series(True, index=data.index)
    for col in ["own_share"] + x_cols + fe_cols:
        valid &= data[col].notna()
    if weights is not None:
        valid &= data[weights].notna() & (data[weights] > 0)
    sub = data.loc[valid].copy().reset_index(drop=True)

    y = sub["own_share"].values.astype(np.float64)
    X = np.column_stack([sub[c].values.astype(np.float64) for c in x_cols])
    clusters = sub[cluster_col].values

    w = None
    if weights is not None:
        w = sub[weights].values.astype(np.float64)

    # Build FE id matrix
    fe_ids = np.column_stack([
        pd.Categorical(sub[col]).codes for col in fe_cols
    ])

    # Demean using pyhdfe
    algo = pyhdfe.create(fe_ids, drop_singletons=False,
                         residualize_method="map")
    yX = np.column_stack([y, X])
    yX_dm = algo.residualize(yX)
    y_dm = yX_dm[:, 0]
    X_dm = yX_dm[:, 1:]

    # Drop rows where demeaned X has no variation
    x_var = np.abs(X_dm).max(axis=1) if X_dm.ndim > 1 else np.abs(X_dm)
    keep = x_var > 1e-15
    if keep.sum() < 10:
        raise ValueError(f"Only {keep.sum()} rows with non-zero demeaned X")

    y_dm = y_dm[keep]
    X_dm = X_dm[keep] if X_dm.ndim > 1 else X_dm[keep].reshape(-1, 1)
    clusters_keep = clusters[keep]
    w_keep = w[keep] if w is not None else None

    # OLS (or WLS) on demeaned data
    if w_keep is not None:
        sqrt_w = np.sqrt(w_keep)
        y_w = y_dm * sqrt_w
        X_w = X_dm * sqrt_w[:, None] if X_dm.ndim > 1 else X_dm * sqrt_w
        ols_cl = sm.OLS(y_w, X_w).fit(
            cov_type="cluster", cov_kwds={"groups": clusters_keep}
        )
    else:
        ols_cl = sm.OLS(y_dm, X_dm).fit(
            cov_type="cluster", cov_kwds={"groups": clusters_keep}
        )

    # Within R2
    resid = y_dm - X_dm @ ols_cl.params
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum(y_dm ** 2)
    r2_within = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    # Package results per regressor
    result = {"n_obs": len(sub), "r2": r2_within}
    for i, col_name in enumerate(x_cols):
        suffix = "" if len(x_cols) == 1 else f"_{col_name}"
        result[f"beta{suffix}"] = ols_cl.params[i]
        result[f"se{suffix}"] = ols_cl.bse[i]
        result[f"tstat{suffix}"] = ols_cl.tvalues[i]
        result[f"pval{suffix}"] = ols_cl.pvalues[i]

    # For single-regressor case, keep flat keys for backward compatibility
    if len(x_cols) == 1:
        result["beta"] = result.pop("beta")
        result["se"] = result.pop("se")
        result["tstat"] = result.pop("tstat")
        result["pval"] = result.pop("pval")

    return result


def star(pval):
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.10:
        return "*"
    return ""


# =========================================================================
# 7. Main table specifications (columns I–IV)
# =========================================================================
print("\n" + "=" * 60)
print("MAIN TABLE: Columns I–IV")
print("=" * 60)

MAIN_SPECS = [
    {"label": "(I)",   "desc": "Baseline",      "fe": ["tech_cat", "qtr_cat"],        "sample": "all"},
    {"label": "(II)",  "desc": "Ind x Qtr",     "fe": ["tech_cat", "indqtr_cat"],     "sample": "all"},
    {"label": "(III)", "desc": "Tech x Qtr",     "fe": ["techqtr_cat", "indqtr_cat"],  "sample": "all"},
    {"label": "(IV)",  "desc": "First appear.",  "fe": ["tech_cat", "qtr_cat"],        "sample": "first"},
]

main_results = {}
for side, long_df in [("cause", cause_long), ("effect", effect_long)]:
    print(f"\n  --- {side.upper()} side ---")
    for spec in MAIN_SPECS:
        label = spec["label"]
        if spec["sample"] == "all":
            sample = long_df
        elif spec["sample"] == "first":
            sample = long_df[long_df["is_first"]]
        else:
            raise ValueError(f"Unknown sample: {spec['sample']}")

        print(f"    {label} ({spec['desc']}): {len(sample):,} stacked rows ... ",
              end="", flush=True)
        try:
            res = run_hdfe_ols(sample, spec["fe"])
            s = star(res["pval"])
            print(f"beta={res['beta']:.4f}{s}, se={res['se']:.4f}, "
                  f"N={res['n_obs']:,}, R2={res['r2']:.4f}")
            main_results[(side, label)] = res
        except Exception as e:
            print(f"FAILED: {e}")
            main_results[(side, label)] = None


# =========================================================================
# 8. Robustness checks
# =========================================================================
print("\n" + "=" * 60)
print("ROBUSTNESS CHECKS")
print("=" * 60)

robust_results = {}

# --- Check A: >=3 technologies per firm ---
print("\n  [A] >=3 technologies per firm ...")
three_tech_firms = techs_per_firm[techs_per_firm >= 3].index
for side, long_df in [("cause", cause_long), ("effect", effect_long)]:
    sample = long_df[long_df["gvkey"].isin(three_tech_firms)]
    n_firms = sample["gvkey"].nunique()
    print(f"      {side}: {len(sample):,} rows, {n_firms} firms ... ", end="", flush=True)
    try:
        res = run_hdfe_ols(sample, ["tech_cat", "qtr_cat"])
        s = star(res["pval"])
        print(f"beta={res['beta']:.4f}{s}, se={res['se']:.4f}")
        robust_results[("A", side)] = res
    except Exception as e:
        print(f"FAILED: {e}")
        robust_results[("A", side)] = None

# --- Check B: Snippet-weighted (WLS) ---
print("\n  [B] Snippet-weighted (WLS) ...")
for side, long_df, wcol in [("cause", cause_long, "weight"),
                              ("effect", effect_long, "weight")]:
    print(f"      {side}: {len(long_df):,} rows ... ", end="", flush=True)
    try:
        res = run_hdfe_ols(long_df, ["tech_cat", "qtr_cat"], weights=wcol)
        s = star(res["pval"])
        print(f"beta={res['beta']:.4f}{s}, se={res['se']:.4f}")
        robust_results[("B", side)] = res
    except Exception as e:
        print(f"FAILED: {e}")
        robust_results[("B", side)] = None

# --- Check C: Drop-one-category stability ---
print("\n  [C] Drop-one-category stability ...")
for side, long_df in [("cause", cause_long), ("effect", effect_long)]:
    betas = []
    for drop_c in range(1, 6):
        sample = long_df[long_df["category"] != drop_c]
        try:
            res = run_hdfe_ols(sample, ["tech_cat", "qtr_cat"])
            betas.append(res["beta"])
        except Exception:
            betas.append(np.nan)
    b_min, b_max = np.nanmin(betas), np.nanmax(betas)
    b_mean = np.nanmean(betas)
    print(f"      {side}: betas={[f'{b:.4f}' for b in betas]}")
    print(f"             range=[{b_min:.4f}, {b_max:.4f}], mean={b_mean:.4f}")
    robust_results[("C", side)] = {
        "betas": betas,
        "beta_min": b_min,
        "beta_max": b_max,
        "beta_mean": b_mean,
    }

# --- Check D: Continuous similarity interaction ---
print("\n  [D] Continuous similarity interaction ...")
for side, long_df in [("cause", cause_long), ("effect", effect_long)]:
    sample = long_df.dropna(subset=["tech_similarity"])
    print(f"      {side}: {len(sample):,} rows ... ", end="", flush=True)
    try:
        res = run_hdfe_ols(
            sample, ["tech_cat", "qtr_cat"],
            x_cols=["peer_share", "peer_x_sim", "tech_similarity"],
        )
        s1 = star(res["pval_peer_share"])
        s2 = star(res["pval_peer_x_sim"])
        print(f"beta_peer={res['beta_peer_share']:.4f}{s1}, "
              f"beta_interact={res['beta_peer_x_sim']:.4f}{s2}")
        # Implied effects at p25 and p75
        b1 = res["beta_peer_share"]
        b2 = res["beta_peer_x_sim"]
        res["implied_p25"] = b1 + b2 * sim_p25
        res["implied_p75"] = b1 + b2 * sim_p75
        print(f"             implied at p25 sim ({sim_p25:.3f}): "
              f"{res['implied_p25']:.4f}")
        print(f"             implied at p75 sim ({sim_p75:.3f}): "
              f"{res['implied_p75']:.4f}")
        robust_results[("D", side)] = res
    except Exception as e:
        print(f"FAILED: {e}")
        robust_results[("D", side)] = None


# =========================================================================
# 9. Export CSV (main + robustness)
# =========================================================================
print("\nExporting CSV ...")

# Main table CSV
csv_rows = []
for side in ["cause", "effect"]:
    for spec in MAIN_SPECS:
        label = spec["label"]
        res = main_results.get((side, label))
        if res is None:
            continue
        csv_rows.append({
            "side": side, "column": label, "description": spec["desc"],
            "sample": spec["sample"], "fe": " + ".join(spec["fe"]),
            "beta": res["beta"], "se": res["se"], "tstat": res["tstat"],
            "pval": res["pval"], "n_obs": res["n_obs"], "r2": res["r2"],
            "stars": star(res["pval"]),
        })
csv_df = pd.DataFrame(csv_rows)
csv_path = ROOT / "results" / "tables" / "table_IVB_spillover.csv"
csv_df.to_csv(csv_path, index=False, encoding="utf-8")
print(f"  Saved: {csv_path}")

# Robustness CSV
rob_rows = []
for check_key in ["A", "B", "D"]:
    for side in ["cause", "effect"]:
        res = robust_results.get((check_key, side))
        if res is None:
            continue
        if check_key == "D":
            rob_rows.append({
                "check": check_key, "side": side,
                "beta_peer": res["beta_peer_share"],
                "se_peer": res["se_peer_share"],
                "beta_interact": res["beta_peer_x_sim"],
                "se_interact": res["se_peer_x_sim"],
                "n_obs": res["n_obs"], "r2": res["r2"],
            })
        else:
            rob_rows.append({
                "check": check_key, "side": side,
                "beta": res["beta"], "se": res["se"],
                "n_obs": res["n_obs"], "r2": res["r2"],
            })
for side in ["cause", "effect"]:
    cres = robust_results.get(("C", side))
    if cres:
        rob_rows.append({
            "check": "C", "side": side,
            "beta_min": cres["beta_min"], "beta_max": cres["beta_max"],
            "beta_mean": cres["beta_mean"],
        })
rob_df = pd.DataFrame(rob_rows)
rob_csv_path = ROOT / "results" / "tables" / "table_IVB_spillover_robustness.csv"
rob_df.to_csv(rob_csv_path, index=False, encoding="utf-8")
print(f"  Saved: {rob_csv_path}")


# =========================================================================
# 10. Generate main LaTeX table (4 columns)
# =========================================================================
print("\nGenerating main LaTeX table ...")


def fmt_coef(res, beta_key="beta"):
    if res is None:
        return ("", "")
    b = res[beta_key]
    se = res[beta_key.replace("beta", "se")]
    s = star(res[beta_key.replace("beta", "pval")])
    return (f"{b:.3f}{s}", f"({se:.3f})")


def fmt_n(res):
    if res is None:
        return ""
    return f"{res['n_obs']:,}"


def fmt_r2(res):
    if res is None:
        return ""
    return f"{res['r2']:.3f}"


ncols = len(MAIN_SPECS)
col_labels = [s["label"] for s in MAIN_SPECS]
col_descs = [s["desc"] for s in MAIN_SPECS]

tex = []
tex.append(r"\begin{table}[!htbp]\centering")
tex.append(r"\caption{Cross-Technology Belief Spillover}")
tex.append(r"\label{tab:spillover}")
tex.append(r"\begin{flushleft}\footnotesize")
tex.append(
    r"\textit{Notes.} This table reports estimates from stacked regressions "
    r"of a firm's own cause (Panel~A) or effect (Panel~B) share for technology~$k$ "
    r"on the firm's leave-one-out peer share from its other technologies. "
    r"Each observation is a firm--technology--quarter--category, where categories "
    r"are the five macro cause or effect groups defined in Section~II.D. "
    r"The peer share for firm~$i$ in category~$c$ excludes all observations "
    r"for the same technology~$k$. "
    r"All fixed effects are interacted with category. "
    r"Column~(I) includes technology$\times$category and quarter$\times$category fixed effects. "
    r"Column~(II) replaces quarter with industry$\times$quarter FE. "
    r"Column~(III) further adds technology$\times$quarter FE, absorbing technology-specific trends. "
    r"Column~(IV) restricts to the first quarter in which a firm discusses "
    r"each technology. "
    r"Standard errors clustered at the firm level are in parentheses. "
    r"$^{***}$~$p<0.01$, $^{**}$~$p<0.05$, $^{*}$~$p<0.10$."
)
tex.append(r"\end{flushleft}")
tex.append(r"\resizebox{\textwidth}{!}{%")
tex.append(r"\begin{tabular}{l" + "c" * ncols + "}")
tex.append(r"\hline\hline")

# Panel A
tex.append(r"\multicolumn{" + str(ncols + 1) + r"}{l}{\textsc{Panel A. Cause shares}}\\")
tex.append(" & " + " & ".join(
    [r"\parbox[b]{2.2cm}{\centering " + d + "}" for d in col_descs]
) + r" \\")
tex.append(" & " + " & ".join(col_labels) + r" \\")
tex.append(r"\hline")

coef_line = "Peer share"
se_line = ""
for spec in MAIN_SPECS:
    c, s = fmt_coef(main_results.get(("cause", spec["label"])))
    coef_line += f" & {c}"
    se_line += f" & {s}"
tex.append(coef_line + r" \\")
tex.append(se_line + r" \\[6pt]")

# FE indicators
fe_indicators = {
    r"Technology $\times$ category FE":
        [True, True, False, True],
    r"Quarter $\times$ category FE":
        [True, False, False, True],
    r"Ind. $\times$ quarter $\times$ category FE":
        [False, True, True, False],
    r"Technology $\times$ quarter $\times$ category FE":
        [False, False, True, False],
}
for fe_name, flags in fe_indicators.items():
    line = fe_name
    for flag in flags:
        line += " & Yes" if flag else " & No"
    tex.append(line + r" \\")

n_line = "Observations"
r2_line = "$R^2$"
for spec in MAIN_SPECS:
    res = main_results.get(("cause", spec["label"]))
    n_line += f" & {fmt_n(res)}"
    r2_line += f" & {fmt_r2(res)}"
tex.append(n_line + r" \\")
tex.append(r2_line + r" \\")

# Panel B
tex.append(r"\hline")
tex.append(r"\multicolumn{" + str(ncols + 1) + r"}{l}{\textsc{Panel B. Effect shares}}\\")
tex.append(" & " + " & ".join(col_labels) + r" \\")
tex.append(r"\hline")

coef_line = "Peer share"
se_line = ""
for spec in MAIN_SPECS:
    c, s = fmt_coef(main_results.get(("effect", spec["label"])))
    coef_line += f" & {c}"
    se_line += f" & {s}"
tex.append(coef_line + r" \\")
tex.append(se_line + r" \\[6pt]")

n_line = "Observations"
r2_line = "$R^2$"
for spec in MAIN_SPECS:
    res = main_results.get(("effect", spec["label"]))
    n_line += f" & {fmt_n(res)}"
    r2_line += f" & {fmt_r2(res)}"
tex.append(n_line + r" \\")
tex.append(r2_line + r" \\")
tex.append(r"\hline\hline")
tex.append(r"\end{tabular}%")
tex.append(r"}")
tex.append(r"\vspace{0.25em}")
tex.append(r"\end{table}")

tex_content = "\n".join(tex)
tex_path = ROOT / "Overleaf" / "Tables" / "spillover.tex"
tex_path.write_text(tex_content, encoding="utf-8")
print(f"  Saved: {tex_path}")


# =========================================================================
# 11. Generate robustness LaTeX table (Panel A = Cause, Panel B = Effect)
# =========================================================================
print("\nGenerating robustness LaTeX table ...")


def fmt_neg(val, decimals=3):
    """Format a number, using $-$ for negative values in LaTeX."""
    if val < 0:
        return f"$-${abs(val):.{decimals}f}"
    return f"{val:.{decimals}f}"


def build_robustness_panel(side_label, side_key):
    """Build LaTeX rows for one panel (cause or effect) of the robustness table."""
    ra = robust_results.get(("A", side_key))
    rb = robust_results.get(("B", side_key))
    rc = robust_results.get(("C", side_key))
    rd = robust_results.get(("D", side_key))

    lines = []

    # Peer share coefficients: cols I (A), II (B), III (C: empty), IV (D)
    coef_a = f"{ra['beta']:.3f}{star(ra['pval'])}" if ra else ""
    coef_b = f"{rb['beta']:.3f}{star(rb['pval'])}" if rb else ""
    coef_d = fmt_neg(rd["beta_peer_share"]) + star(rd["pval_peer_share"]) if rd else ""
    lines.append(f"Peer share & {coef_a} & {coef_b} & & {coef_d} \\\\")

    se_a = f"({ra['se']:.3f})" if ra else ""
    se_b = f"({rb['se']:.3f})" if rb else ""
    se_d = f"({rd['se_peer_share']:.3f})" if rd else ""
    lines.append(f" & {se_a} & {se_b} & & {se_d} \\\\[6pt]")

    # Peer share x similarity: only col IV (D)
    coef_int = fmt_neg(rd["beta_peer_x_sim"]) + star(rd["pval_peer_x_sim"]) if rd else ""
    se_int = f"({rd['se_peer_x_sim']:.3f})" if rd else ""
    lines.append(f"Peer share $\\times$ similarity & & & & {coef_int} \\\\")
    lines.append(f" & & & & {se_int} \\\\[6pt]")

    # Beta range: only col III (C)
    if rc:
        lines.append(f"$\\hat{{\\beta}}$ range & & & "
                      f"[{rc['beta_min']:.3f}, {rc['beta_max']:.3f}] & \\\\")
        lines.append(f"Mean across drops & & & "
                      f"{rc['beta_mean']:.3f} & \\\\[6pt]")

    # Implied effects: only col IV (D)
    if rd:
        lines.append(f"Implied effect at p25 sim. & & & & "
                      f"{rd['implied_p25']:.3f} \\\\")
        lines.append(f"Implied effect at p75 sim. & & & & "
                      f"{rd['implied_p75']:.3f} \\\\[6pt]")

    # Observations and R2
    n_a = f"{ra['n_obs']:,}" if ra else ""
    n_b = f"{rb['n_obs']:,}" if rb else ""
    n_d = f"{rd['n_obs']:,}" if rd else ""
    r2_a = f"{ra['r2']:.3f}" if ra else ""
    r2_b = f"{rb['r2']:.3f}" if rb else ""
    r2_d = f"{rd['r2']:.3f}" if rd else ""
    lines.append(f"Observations & {n_a} & {n_b} & & {n_d} \\\\")
    lines.append(f"$R^2$ & {r2_a} & {r2_b} & & {r2_d} \\\\")

    return lines


# Count >=3 tech firms for notes
n_three_tech = int((techs_per_firm >= 3).sum())

rtex = []
rtex.append(r"\begin{table}[!htbp]\centering")
rtex.append(r"\caption{Cross-Technology Belief Spillover: Robustness}")
rtex.append(r"\label{tab:spillover_robust}")
rtex.append(r"\begin{flushleft}\footnotesize")
rtex.append(
    r"\textit{Notes.} This table reports robustness checks for the spillover "
    r"regressions in Table~\ref{tab:spillover}. All specifications include "
    r"technology$\times$category and quarter$\times$category fixed effects "
    r"with standard errors clustered at the firm level. "
    f"Column~(I) restricts the sample to the {n_three_tech} firms discussing "
    r"at least three technologies. "
    r"Column~(II) weights observations by the number of causal (effect) snippets "
    r"underlying the share estimate. "
    r"Column~(III) reports the range of the baseline coefficient when each "
    r"of the five categories is dropped in turn from the stacked regression. "
    r"Column~(IV) interacts the peer share with the continuous cosine similarity "
    r"between the focal technology's and the peer technologies' aggregate "
    r"cause-share vectors; implied effects are evaluated at the 25th and 75th "
    r"percentiles of similarity. "
    r"$^{***}$~$p<0.01$, $^{**}$~$p<0.05$, $^{*}$~$p<0.10$."
)
rtex.append(r"\end{flushleft}")
rtex.append(r"\resizebox{\textwidth}{!}{%")
rtex.append(r"\begin{tabular}{lcccc}")
rtex.append(r"\hline\hline")

# Panel A: Cause shares
rtex.append(r"\multicolumn{5}{l}{\textsc{Panel A. Cause shares}}\\")
rtex.append(
    r" & \parbox[b]{2.2cm}{\centering $\geq 3$ technologies}"
    r" & \parbox[b]{2.2cm}{\centering Snippet-weighted}"
    r" & \parbox[b]{2.2cm}{\centering Drop-one-category}"
    r" & \parbox[b]{2.2cm}{\centering Similarity interaction} \\"
)
rtex.append(r" & (I) & (II) & (III) & (IV) \\")
rtex.append(r"\hline")
rtex.extend(build_robustness_panel("Cause shares", "cause"))

# Panel B: Effect shares
rtex.append(r"\hline")
rtex.append(r"\multicolumn{5}{l}{\textsc{Panel B. Effect shares}}\\")
rtex.append(r" & (I) & (II) & (III) & (IV) \\")
rtex.append(r"\hline")
rtex.extend(build_robustness_panel("Effect shares", "effect"))

rtex.append(r"\hline\hline")
rtex.append(r"\end{tabular}%")
rtex.append(r"}")
rtex.append(r"\vspace{0.25em}")
rtex.append(r"\end{table}")

rtex_content = "\n".join(rtex)
rtex_path = ROOT / "Overleaf" / "Tables" / "spillover_robustness.tex"
rtex_path.write_text(rtex_content, encoding="utf-8")
print(f"  Saved: {rtex_path}")


# =========================================================================
# 12. Manifest
# =========================================================================
run_timestamp = datetime.datetime.now()

# Serialize robust_results for JSON
def make_serializable(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

robust_json = {}
for k, v in robust_results.items():
    key_str = f"{k[0]}_{k[1]}"
    if v is None:
        robust_json[key_str] = None
    else:
        robust_json[key_str] = {
            kk: make_serializable(vv) for kk, vv in v.items()
        }

manifest = {
    "script": Path(__file__).name,
    "timestamp": run_timestamp.isoformat(),
    "seed": SEED,
    "input_files": ["data_processed/panel_ikt.csv"],
    "output_files": [
        str(csv_path.relative_to(ROOT)),
        str(rob_csv_path.relative_to(ROOT)),
        str(tex_path.relative_to(ROOT)),
        str(rtex_path.relative_to(ROOT)),
    ],
    "row_counts": {
        "panel_raw": raw_rows,
        "multi_tech_obs": len(df),
        "multi_tech_firms": int(df["gvkey"].nunique()),
        "cause_stacked": len(cause_long),
        "effect_stacked": len(effect_long),
        "first_appearance_obs": int(n_first),
        "similarity_median": float(sim_median),
        "similarity_p25": float(sim_p25),
        "similarity_p75": float(sim_p75),
        "three_tech_firms": int((techs_per_firm >= 3).sum()),
    },
    "main_results": {
        f"{side}_{spec['label']}": main_results.get((side, spec["label"]))
        for side in ["cause", "effect"]
        for spec in MAIN_SPECS
    },
    "robustness_results": robust_json,
    "parameters": {
        "n_cause_categories": N_CAUSE,
        "n_effect_categories": N_EFFECT,
        "clustering": "firm (gvkey)",
        "main_specifications": [
            {"col": s["label"], "desc": s["desc"], "fe": s["fe"],
             "sample": s["sample"]}
            for s in MAIN_SPECS
        ],
    },
}

manifest_path = (
    ROOT / "results" / "runs"
    / f"{Path(__file__).stem}_{run_timestamp:%Y%m%d_%H%M%S}.json"
)
manifest_path.write_text(
    json.dumps(manifest, indent=2, default=str), encoding="utf-8"
)
print(f"\nManifest: {manifest_path}")
print("\nDone.")
