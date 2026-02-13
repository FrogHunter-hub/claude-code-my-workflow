"""
07_table_IVC_dynamics.py — Belief Persistence and Dynamics

Purpose: For Section IV.C, document the temporal persistence of belief
         structures within firm-technology pairs.  Tests whether a firm's
         initial causal/effect frame predicts its frame years later,
         conditional on technology x quarter trends.

Main table:  4 columns (All later obs, Tenure 1-4q, 5-12q, 13+q)
Figure:      Persistence decay curve (avg correlation by tenure quarter)

Inputs:  data_processed/panel_ikt.csv

Outputs: results/tables/table_IVC_persistence.csv
         Overleaf/Tables/persistence.tex
         Overleaf/Figures/figure_III_persistence.pdf
         Overleaf/Figures/figure_III_persistence.png
         results/runs/07_table_IVC_dynamics_<timestamp>.json
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=FutureWarning)

SEED = 42
ROOT = Path(__file__).resolve().parents[2]

np.random.seed(SEED)

# 0. Setup ----------------------------------------------------------------
os.makedirs(ROOT / "results" / "tables", exist_ok=True)
os.makedirs(ROOT / "results" / "runs", exist_ok=True)
os.makedirs(ROOT / "Overleaf" / "Tables", exist_ok=True)
os.makedirs(ROOT / "Overleaf" / "Figures", exist_ok=True)

N_CAUSE = 5
N_EFFECT = 5
CAUSE_COLS = [f"share_cause_{c}" for c in range(1, N_CAUSE + 1)]
EFFECT_COLS = [f"share_effect_{c}" for c in range(1, N_EFFECT + 1)]

# =========================================================================
# 1. Load data and build multi-obs sample
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


def q_to_num(q):
    """Convert '2021q3' to integer (year*4 + quarter)."""
    y, qn = q.split("q")
    return int(y) * 4 + int(qn)


# Identify firm-tech pairs with >=2 observations
pair_counts = panel.groupby(["gvkey", "technology"]).size().reset_index(name="n_obs")
multi_obs_pairs = pair_counts[pair_counts["n_obs"] >= 2][["gvkey", "technology"]]
df = panel.merge(multi_obs_pairs, on=["gvkey", "technology"])
n_pairs = len(multi_obs_pairs)
n_firms = df["gvkey"].nunique()
print(f"  Firm-tech pairs with >=2 obs: {n_pairs:,}")
print(f"  Firms: {n_firms:,}")
print(f"  Observations: {len(df):,}")

# Compute tenure (quarters since first mention per firm-tech pair)
first_q = df.groupby(["gvkey", "technology"])["dateQ"].min().reset_index()
first_q.rename(columns={"dateQ": "first_dateQ"}, inplace=True)
df = df.merge(first_q, on=["gvkey", "technology"], how="left")
df["q_num"] = df["dateQ"].apply(q_to_num)
df["first_q_num"] = df["first_dateQ"].apply(q_to_num)
df["tenure_q"] = df["q_num"] - df["first_q_num"]

# =========================================================================
# 2. Extract initial shares and merge onto all later observations
# =========================================================================
print("\nExtracting initial shares ...")
initial_obs = df[df["tenure_q"] == 0][
    ["gvkey", "technology"] + CAUSE_COLS + EFFECT_COLS
].copy()
init_rename = {c: f"init_{c}" for c in CAUSE_COLS + EFFECT_COLS}
initial_obs = initial_obs.rename(columns=init_rename)

# Later observations (tenure >= 1)
df_later = df[df["tenure_q"] >= 1].merge(initial_obs, on=["gvkey", "technology"])
n_later = len(df_later)
n_later_pairs = df_later.groupby(["gvkey", "technology"]).ngroups
print(f"  Later observations (tenure >= 1): {n_later:,}")
print(f"  Pairs with later obs: {n_later_pairs:,}")

# Tenure bins
df_later["tenure_bin"] = pd.cut(
    df_later["tenure_q"],
    bins=[0, 4, 12, 200],
    labels=["1-4q", "5-12q", "13+q"],
    right=True,
)

for b in ["1-4q", "5-12q", "13+q"]:
    n = (df_later["tenure_bin"] == b).sum()
    print(f"  Tenure bin {b}: {n:,} obs")

# Industry (2-digit SIC)
df_later["sic2"] = (df_later["sic"].fillna(0).astype(int) // 100).astype(str)

# =========================================================================
# 3. Compute drift statistics (for prose)
# =========================================================================
print("\nComputing drift statistics ...")

# Distance from initial frame
for side, cols in [("cause", CAUSE_COLS), ("effect", EFFECT_COLS)]:
    init_cols = [f"init_{c}" for c in cols]
    df_later[f"dist_init_{side}"] = np.sqrt(
        sum((df_later[c] - df_later[ic]) ** 2 for c, ic in zip(cols, init_cols))
    )

# Pairs with >=3 later obs for drift comparison
pair_drift = (
    df_later.groupby(["gvkey", "technology"])
    .agg(
        mean_drift_cause=("dist_init_cause", "mean"),
        mean_drift_effect=("dist_init_effect", "mean"),
        n_later_obs=("tenure_q", "count"),
    )
    .reset_index()
)
pair_drift_3 = pair_drift[pair_drift["n_later_obs"] >= 3]
drift_cause = pair_drift_3["mean_drift_cause"].mean()
drift_effect = pair_drift_3["mean_drift_effect"].mean()
frac_cause_gt_effect = (
    pair_drift_3["mean_drift_cause"] > pair_drift_3["mean_drift_effect"]
).mean()
print(f"  Pairs with >=3 later obs: {len(pair_drift_3):,}")
print(f"  Mean cause drift:  {drift_cause:.3f}")
print(f"  Mean effect drift: {drift_effect:.3f}")
print(f"  Cause > effect in {frac_cause_gt_effect:.1%} of pairs")

# =========================================================================
# 4. Figure III: Persistence decay curve
# =========================================================================
print("\nGenerating Figure III: Persistence decay curve ...")

# For each tenure quarter, compute avg cross-category correlation
# between initial shares and current shares
max_tenure_fig = 24
tenure_vals = list(range(1, max_tenure_fig + 1))

corr_cause = []
corr_effect = []
n_obs_per_tenure = []

for t in tenure_vals:
    mask = df_later["tenure_q"] == t
    subset = df_later[mask]
    n_obs_per_tenure.append(mask.sum())

    if mask.sum() < 30:
        corr_cause.append(np.nan)
        corr_effect.append(np.nan)
        continue

    # Average correlation across 5 categories
    rs_c = []
    for c in CAUSE_COLS:
        r = subset[c].corr(subset[f"init_{c}"])
        rs_c.append(r)
    corr_cause.append(np.mean(rs_c))

    rs_e = []
    for c in EFFECT_COLS:
        r = subset[c].corr(subset[f"init_{c}"])
        rs_e.append(r)
    corr_effect.append(np.mean(rs_e))

# Also compute for tenure buckets (for table reference)
bucket_corrs = {}
for b_lo, b_hi, label in [(1, 4, "1-4q"), (5, 12, "5-12q"), (13, 24, "13+q")]:
    mask = (df_later["tenure_q"] >= b_lo) & (df_later["tenure_q"] <= b_hi)
    subset = df_later[mask]
    for side, cols in [("cause", CAUSE_COLS), ("effect", EFFECT_COLS)]:
        rs = [subset[c].corr(subset[f"init_{c}"]) for c in cols]
        bucket_corrs[(side, label)] = np.mean(rs)

print("  Persistence decay by bucket:")
for side in ["cause", "effect"]:
    for label in ["1-4q", "5-12q", "13+q"]:
        print(f"    {side} {label}: r = {bucket_corrs[(side, label)]:.3f}")

# Plot
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["CMU Serif", "Computer Modern Roman", "Times New Roman",
                    "Times", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.facecolor": "white",
})

fig, ax = plt.subplots(figsize=(6.5, 4))

# Filter out NaN for plotting
valid_c = [(t, r) for t, r in zip(tenure_vals, corr_cause) if not np.isnan(r)]
valid_e = [(t, r) for t, r in zip(tenure_vals, corr_effect) if not np.isnan(r)]

ax.plot([t for t, _ in valid_c], [r for _, r in valid_c],
        color="#2166ac", marker="o", markersize=4, linewidth=1.5,
        label="Cause shares", zorder=3)
ax.plot([t for t, _ in valid_e], [r for _, r in valid_e],
        color="#b2182b", marker="s", markersize=4, linewidth=1.5,
        linestyle="--", label="Effect shares", zorder=3)

ax.set_xlabel("Tenure (quarters since first mention)")
ax.set_ylabel("Avg. correlation with initial shares")
ax.set_xlim(0.5, max_tenure_fig + 0.5)
ax.set_ylim(0, 0.6)
ax.set_xticks([1, 4, 8, 12, 16, 20, 24])
ax.axhline(y=0, color="gray", linewidth=0.5, linestyle=":")
ax.legend(loc="upper right", frameon=True, fancybox=False, edgecolor="gray")
ax.grid(axis="y", linewidth=0.3, alpha=0.5)

# Add N annotations on secondary axis
ax2 = ax.twinx()
ax2.bar(tenure_vals, n_obs_per_tenure, color="gray", alpha=0.15, width=0.8,
        zorder=1)
ax2.set_ylabel("Number of observations", color="gray")
ax2.tick_params(axis="y", labelcolor="gray")
ax2.set_ylim(0, max(n_obs_per_tenure) * 3)  # Scale bars to bottom third

fig.tight_layout()

fig_pdf = ROOT / "Overleaf" / "Figures" / "figure_III_persistence.pdf"
fig_png = ROOT / "Overleaf" / "Figures" / "figure_III_persistence.png"
fig.savefig(fig_pdf, dpi=300, bbox_inches="tight")
fig.savefig(fig_png, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"  Saved: {fig_pdf}")
print(f"  Saved: {fig_png}")


# =========================================================================
# 5. Stack to long format for persistence regressions
# =========================================================================
print("\nStacking to long format ...")


def stack_persistence(data, own_cols, init_cols, side_label):
    """Reshape: 5 rows per obs (one per macro category c)."""
    records = []
    for c_idx in range(len(own_cols)):
        chunk = data[["gvkey", "technology", "dateQ", "sic2",
                       "tenure_q", "tenure_bin"]].copy()
        chunk["category"] = c_idx + 1
        chunk["own_share"] = data[own_cols[c_idx]].values
        chunk["init_share"] = data[init_cols[c_idx]].values
        records.append(chunk)
    long = pd.concat(records, ignore_index=True)
    long["side"] = side_label
    return long


init_cause_cols = [f"init_{c}" for c in CAUSE_COLS]
init_effect_cols = [f"init_{c}" for c in EFFECT_COLS]

cause_long = stack_persistence(df_later, CAUSE_COLS, init_cause_cols, "cause")
effect_long = stack_persistence(df_later, EFFECT_COLS, init_effect_cols, "effect")

print(f"  Cause stacked rows: {len(cause_long):,}")
print(f"  Effect stacked rows: {len(effect_long):,}")

# Create category-interacted FE columns
for long_df in [cause_long, effect_long]:
    cat = long_df["category"].astype(str)
    long_df["tech_cat"] = long_df["technology"].astype(str) + "_" + cat
    long_df["qtr_cat"] = long_df["dateQ"].astype(str) + "_" + cat


# =========================================================================
# 6. Regression infrastructure (reuse from 06_table_IVB)
# =========================================================================

def run_hdfe_ols(data, fe_cols, cluster_col="gvkey", x_cols=None):
    """
    Demean y and x via pyhdfe (Frisch-Waugh-Lovell), then run OLS
    with firm-clustered standard errors.
    """
    if x_cols is None:
        x_cols = ["init_share"]

    valid = pd.Series(True, index=data.index)
    for col in ["own_share"] + x_cols + fe_cols:
        valid &= data[col].notna()
    sub = data.loc[valid].copy().reset_index(drop=True)

    y = sub["own_share"].values.astype(np.float64)
    X = np.column_stack([sub[c].values.astype(np.float64) for c in x_cols])
    clusters = sub[cluster_col].values

    fe_ids = np.column_stack([
        pd.Categorical(sub[col]).codes for col in fe_cols
    ])

    algo = pyhdfe.create(fe_ids, drop_singletons=False,
                         residualize_method="map")
    yX = np.column_stack([y, X])
    yX_dm = algo.residualize(yX)
    y_dm = yX_dm[:, 0]
    X_dm = yX_dm[:, 1:]

    x_var = np.abs(X_dm).max(axis=1) if X_dm.ndim > 1 else np.abs(X_dm)
    keep = x_var > 1e-15
    if keep.sum() < 10:
        raise ValueError(f"Only {keep.sum()} rows with non-zero demeaned X")

    y_dm = y_dm[keep]
    X_dm = X_dm[keep] if X_dm.ndim > 1 else X_dm[keep].reshape(-1, 1)
    clusters_keep = clusters[keep]

    ols_cl = sm.OLS(y_dm, X_dm).fit(
        cov_type="cluster", cov_kwds={"groups": clusters_keep}
    )

    resid = y_dm - X_dm @ ols_cl.params
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum(y_dm ** 2)
    r2_within = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    result = {"n_obs": len(sub), "r2": r2_within}
    if len(x_cols) == 1:
        result["beta"] = ols_cl.params[0]
        result["se"] = ols_cl.bse[0]
        result["tstat"] = ols_cl.tvalues[0]
        result["pval"] = ols_cl.pvalues[0]
    else:
        for i, col_name in enumerate(x_cols):
            result[f"beta_{col_name}"] = ols_cl.params[i]
            result[f"se_{col_name}"] = ols_cl.bse[i]
            result[f"tstat_{col_name}"] = ols_cl.tvalues[i]
            result[f"pval_{col_name}"] = ols_cl.pvalues[i]

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
# 7. Main table specifications (columns I-IV)
# =========================================================================
print("\n" + "=" * 60)
print("PERSISTENCE TABLE: Columns I-IV")
print("=" * 60)

MAIN_SPECS = [
    {"label": "(I)",   "desc": "All horizons",  "fe": ["tech_cat", "qtr_cat"],
     "sample": "all"},
    {"label": "(II)",  "desc": "Tenure 1--4q",  "fe": ["tech_cat", "qtr_cat"],
     "sample": "1-4q"},
    {"label": "(III)", "desc": "Tenure 5--12q", "fe": ["tech_cat", "qtr_cat"],
     "sample": "5-12q"},
    {"label": "(IV)",  "desc": "Tenure 13+q",   "fe": ["tech_cat", "qtr_cat"],
     "sample": "13+q"},
]

main_results = {}
for side, long_df in [("cause", cause_long), ("effect", effect_long)]:
    print(f"\n  --- {side.upper()} side ---")
    for spec in MAIN_SPECS:
        label = spec["label"]
        if spec["sample"] == "all":
            sample = long_df
        else:
            sample = long_df[long_df["tenure_bin"] == spec["sample"]]

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
# 8. Export CSV
# =========================================================================
print("\nExporting CSV ...")

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
csv_path = ROOT / "results" / "tables" / "table_IVC_persistence.csv"
csv_df.to_csv(csv_path, index=False, encoding="utf-8")
print(f"  Saved: {csv_path}")


# =========================================================================
# 9. Generate LaTeX table
# =========================================================================
print("\nGenerating LaTeX table ...")


def fmt_coef(res, beta_key="beta"):
    if res is None:
        return ("", "")
    b = res[beta_key]
    se = res[beta_key.replace("beta", "se")]
    pval = res[beta_key.replace("beta", "pval")]
    s = star(pval)
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
tex.append(r"\caption{Belief Persistence}")
tex.append(r"\label{tab:persistence}")
tex.append(r"\begin{flushleft}\footnotesize")
tex.append(
    r"\textit{Notes.} This table reports estimates from stacked regressions "
    r"of a firm's current cause (Panel~A) or effect (Panel~B) share on its "
    r"initial share from the first quarter in which the firm discusses the technology. "
    r"Each observation is a firm--technology--quarter--category for quarters after first "
    r"mention ($\text{tenure} \geq 1$), "
    r"where categories are the five macro cause or effect groups defined in Section~II.D. "
    r"All specifications include technology$\times$category and quarter$\times$category "
    r"fixed effects. "
    r"Column~(I) pools all post-initial observations. "
    r"Columns~(II)--(IV) split by tenure horizon: "
    r"1--4~quarters, 5--12~quarters, and 13+~quarters since first mention. "
    r"Standard errors clustered at the firm level are in parentheses. "
    r"$^{***}$~$p<0.01$, $^{**}$~$p<0.05$, $^{*}$~$p<0.10$."
)
tex.append(r"\end{flushleft}")
tex.append(r"\resizebox{\textwidth}{!}{%")
tex.append(r"\begin{tabular}{l" + "c" * ncols + "}")
tex.append(r"\hline\hline")

# Panel A: Cause shares
tex.append(r"\multicolumn{" + str(ncols + 1) +
           r"}{l}{\textsc{Panel A. Cause shares}}\\")
tex.append(" & " + " & ".join(
    [r"\parbox[b]{2.2cm}{\centering " + d + "}" for d in col_descs]
) + r" \\")
tex.append(" & " + " & ".join(col_labels) + r" \\")
tex.append(r"\hline")

coef_line = "Initial share"
se_line = ""
for spec in MAIN_SPECS:
    c, s = fmt_coef(main_results.get(("cause", spec["label"])))
    coef_line += f" & {c}"
    se_line += f" & {s}"
tex.append(coef_line + r" \\")
tex.append(se_line + r" \\[6pt]")

# FE indicators
tex.append(r"Technology $\times$ category FE & Yes & Yes & Yes & Yes \\")
tex.append(r"Quarter $\times$ category FE & Yes & Yes & Yes & Yes \\")

n_line = "Observations"
r2_line = "$R^2$"
for spec in MAIN_SPECS:
    res = main_results.get(("cause", spec["label"]))
    n_line += f" & {fmt_n(res)}"
    r2_line += f" & {fmt_r2(res)}"
tex.append(n_line + r" \\")
tex.append(r2_line + r" \\")

# Panel B: Effect shares
tex.append(r"\hline")
tex.append(r"\multicolumn{" + str(ncols + 1) +
           r"}{l}{\textsc{Panel B. Effect shares}}\\")
tex.append(" & " + " & ".join(col_labels) + r" \\")
tex.append(r"\hline")

coef_line = "Initial share"
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
tex_path = ROOT / "Overleaf" / "Tables" / "persistence.tex"
tex_path.write_text(tex_content, encoding="utf-8")
print(f"  Saved: {tex_path}")


# =========================================================================
# 10. Manifest
# =========================================================================
run_timestamp = datetime.datetime.now()


def make_serializable(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


manifest = {
    "script": Path(__file__).name,
    "timestamp": run_timestamp.isoformat(),
    "seed": SEED,
    "input_files": ["data_processed/panel_ikt.csv"],
    "output_files": [
        str(csv_path.relative_to(ROOT)),
        str(tex_path.relative_to(ROOT)),
        str(fig_pdf.relative_to(ROOT)),
        str(fig_png.relative_to(ROOT)),
    ],
    "row_counts": {
        "panel_raw": raw_rows,
        "multi_obs_pairs": n_pairs,
        "multi_obs_firms": n_firms,
        "later_observations": n_later,
        "cause_stacked": len(cause_long),
        "effect_stacked": len(effect_long),
    },
    "drift_statistics": {
        "pairs_with_3plus_later_obs": len(pair_drift_3),
        "mean_cause_drift": float(drift_cause),
        "mean_effect_drift": float(drift_effect),
        "frac_cause_gt_effect": float(frac_cause_gt_effect),
    },
    "persistence_by_bucket": {
        f"{side}_{label}": float(bucket_corrs[(side, label)])
        for side in ["cause", "effect"]
        for label in ["1-4q", "5-12q", "13+q"]
    },
    "main_results": {
        f"{side}_{spec['label']}": {
            k: make_serializable(v)
            for k, v in main_results[(side, spec["label"])].items()
        } if main_results.get((side, spec["label"])) else None
        for side in ["cause", "effect"]
        for spec in MAIN_SPECS
    },
    "parameters": {
        "n_cause_categories": N_CAUSE,
        "n_effect_categories": N_EFFECT,
        "clustering": "firm (gvkey)",
        "fe": ["tech_cat", "qtr_cat"],
        "max_tenure_figure": max_tenure_fig,
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
