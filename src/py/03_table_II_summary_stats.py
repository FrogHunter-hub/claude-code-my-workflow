"""
03_table_II_summary_stats.py — Summary Statistics for Panel Construction (Table II)

Purpose: Build the firm x technology x quarter panel from causal snippets,
         compute summary statistics, and generate LaTeX Table II.
Inputs:  data/raw/AllTech_2002-2024_with_LLM_results(with Causal and non-Causal snippets).csv
         data/raw/Causal_Snippets_with_Categories.csv
Outputs: results/tables/table_II_summary_stats.csv
         Overleaf/Tables/summary_stats.tex
         data_processed/panel_ikt.csv
         results/runs/03_table_II_<timestamp>.json
"""

from pathlib import Path
import json
import datetime
import os
import re

import pandas as pd
import numpy as np

SEED = 42
ROOT = Path(__file__).resolve().parents[2]
np.random.seed(SEED)

# ── Paths ─────────────────────────────────────────────────────────
ALLTECH_PATH = (
    ROOT / "data" / "raw"
    / "AllTech_2002-2024_with_LLM_results(with Causal and non-Causal snippets).csv"
)
CAUSAL_PATH = ROOT / "data" / "raw" / "Causal_Snippets_with_Categories.csv"

OUT_CSV = ROOT / "results" / "tables" / "table_II_summary_stats.csv"
OUT_TEX = ROOT / "Overleaf" / "Tables" / "summary_stats.tex"
OUT_PANEL = ROOT / "data_processed" / "panel_ikt.csv"
ts = datetime.datetime.now()
OUT_MANIFEST = (
    ROOT / "results" / "runs" / f"03_table_II_{ts:%Y%m%d_%H%M%S}.json"
)

for d in [OUT_CSV.parent, OUT_TEX.parent, OUT_PANEL.parent, OUT_MANIFEST.parent]:
    os.makedirs(d, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# PANEL A — Technology Snippet Extraction (from AllTech)
# ═══════════════════════════════════════════════════════════════════
print("=" * 60)
print("PANEL A: Loading AllTech file...")

alltech_cols = [
    "identified_technology", "Year", "File", "Technology",
    "detailed_causal_analysis",
]
for p in [ALLTECH_PATH, CAUSAL_PATH]:
    if not p.exists():
        raise FileNotFoundError(f"Required input not found: {p.relative_to(ROOT)}")

at = pd.read_csv(ALLTECH_PATH, usecols=alltech_cols, low_memory=False, encoding="utf-8")

total_snippets = len(at)
print(f"  Total snippets in corpus: {total_snippets:,}")

# Tech-relevant: identified_technology is not "none" and not missing
mask_tech = at["identified_technology"].notna() & (
    at["identified_technology"].str.strip().str.lower() != "none"
)
at_tech = at.loc[mask_tech]
tech_snippets = len(at_tech)
tech_share_pct = 100 * tech_snippets / total_snippets
print(f"  Technology-relevant snippets: {tech_snippets:,} ({tech_share_pct:.1f}%)")

# Causal ratio among tech-relevant
causal_mask = at_tech["detailed_causal_analysis"].str.strip().str.upper() == "YES"
causal_count = int(causal_mask.sum())
causal_ratio_pct = 100 * causal_count / tech_snippets
print(f"  Snippets with causal content: {causal_count:,} ({causal_ratio_pct:.1f}%)")

unique_transcripts = at_tech["File"].nunique()
unique_techs_a = at_tech["Technology"].nunique()
year_min = int(at_tech["Year"].min())
year_max = int(at_tech["Year"].max())
print(f"  Unique transcripts: {unique_transcripts:,}")
print(f"  Unique technologies: {unique_techs_a}")
print(f"  Sample period: {year_min}--{year_max}")

# Snippets per transcript (tech-relevant)
spt = at_tech.groupby("File").size()
spt_stats = {
    "mean": spt.mean(), "sd": spt.std(),
    "p25": spt.quantile(0.25), "median": spt.median(),
    "p75": spt.quantile(0.75),
}
print(f"  Snippets/transcript: mean={spt_stats['mean']:.1f}, "
      f"median={spt_stats['median']:.0f}")

del at, at_tech  # free memory


# ═══════════════════════════════════════════════════════════════════
# PANELS B–E — Causal Panel (from Causal Snippets)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PANELS B-E: Loading Causal Snippets...")

causal_cols = [
    "gvkey", "technology", "dateQ", "side", "input_id",
    "macro_id", "macro_name", "sic", "loc",
]
cs = pd.read_csv(CAUSAL_PATH, usecols=causal_cols, low_memory=False, encoding="utf-8")
raw_causal = len(cs)
print(f"  Raw causal snippets: {raw_causal:,}")

# 1. Drop rows missing key identifiers
cs = cs.dropna(subset=["gvkey", "technology", "dateQ", "side", "macro_id"])
after_drop = len(cs)
print(f"  After dropping missing key fields: {after_drop:,} "
      f"(dropped {raw_causal - after_drop:,})")

cs["gvkey"] = pd.to_numeric(cs["gvkey"], errors="coerce")
cs["macro_id"] = pd.to_numeric(cs["macro_id"], errors="coerce")
n_bad = cs[["gvkey", "macro_id"]].isna().any(axis=1).sum()
if n_bad > 0:
    print(f"  WARNING: {n_bad} rows with non-numeric gvkey/macro_id — dropping")
    cs = cs.dropna(subset=["gvkey", "macro_id"])
cs["gvkey"] = cs["gvkey"].astype(int)
cs["macro_id"] = cs["macro_id"].astype(int)

# Validate macro_id values are in expected range
assert cs["macro_id"].isin(range(1, 6)).all(), (
    f"Unexpected macro_id values: {sorted(cs['macro_id'].unique())}"
)

# Validate macro_name matches expected labels
EXPECTED_CAUSE = {
    1: "Technology Innovation and Advancement",
    2: "Market Demand and Consumer Behavior",
    3: "Regulatory and Policy Drivers",
    4: "Strategic Partnerships and Investment",
    5: "Cost and Economic Viability",
}
EXPECTED_EFFECT = {
    1: "Revenue and Financial Growth",
    2: "Cost Reduction and Efficiency",
    3: "Market Expansion and Adoption",
    4: "Product and Service Innovation",
    5: "Operational Efficiency and Automation",
}
for side_name, expected in [("cause", EXPECTED_CAUSE), ("effect", EXPECTED_EFFECT)]:
    subset = cs[cs["side"] == side_name]
    actual = subset.groupby("macro_id")["macro_name"].first().to_dict()
    for mid, ename in expected.items():
        assert actual.get(mid) == ename, (
            f"{side_name} macro_id={mid}: expected '{ename}', got '{actual.get(mid)}'"
        )

# 2. Deduplicate: one span per (firm, tech, quarter, side, statement, macro)
pre_dedup = len(cs)
cs = cs.drop_duplicates(
    subset=["gvkey", "technology", "dateQ", "side", "input_id", "macro_id"]
)
post_dedup = len(cs)
print(f"  After dedup: {post_dedup:,} (removed {pre_dedup - post_dedup:,})")

# 3. Collapse to firm-tech-quarter-side-macro counts
counts = (
    cs.groupby(["gvkey", "technology", "dateQ", "side", "macro_id"])
    .size()
    .reset_index(name="n")
)

# Keep firm metadata (most recent quarter per gvkey for stable SIC/location)
firm_info = (
    cs.sort_values("dateQ", ascending=False)
    .drop_duplicates("gvkey", keep="first")[["gvkey", "sic", "loc"]]
)

# 4. Pivot to wide: one row per (gvkey, tech, dateQ, side)
wide = counts.pivot_table(
    index=["gvkey", "technology", "dateQ", "side"],
    columns="macro_id",
    values="n",
    fill_value=0,
).reset_index()
wide.columns.name = None

# Rename macro_id columns 1..5 -> n1..n5
rename_map = {c: f"n{c}" for c in range(1, 6) if c in wide.columns}
wide = wide.rename(columns=rename_map)
for c in range(1, 6):
    if f"n{c}" not in wide.columns:
        wide[f"n{c}"] = 0

# N_side and shares
wide["N_side"] = sum(wide[f"n{c}"] for c in range(1, 6))
for c in range(1, 6):
    wide[f"share{c}"] = wide[f"n{c}"] / wide["N_side"]

# 5. Apply >=3 threshold per side
pre_thresh = len(wide)
wide = wide[wide["N_side"] >= 3].copy()
print(f"  After >=3 threshold: {len(wide):,} side-obs "
      f"(dropped {pre_thresh - len(wide):,})")

# 6. Split cause / effect
cause_df = wide[wide["side"] == "cause"].copy()
effect_df = wide[wide["side"] == "effect"].copy()
print(f"  Cause side-obs: {len(cause_df):,}   "
      f"Effect side-obs: {len(effect_df):,}")

# Rename for merge
c_rename = {f"n{c}": f"n_cause_{c}" for c in range(1, 6)}
c_rename.update({f"share{c}": f"share_cause_{c}" for c in range(1, 6)})
c_rename["N_side"] = "N_cause"
cause_df = cause_df.rename(columns=c_rename).drop(columns=["side"])

e_rename = {f"n{c}": f"n_effect_{c}" for c in range(1, 6)}
e_rename.update({f"share{c}": f"share_effect_{c}" for c in range(1, 6)})
e_rename["N_side"] = "N_effect"
effect_df = effect_df.rename(columns=e_rename).drop(columns=["side"])

# 7. Inner join -> joint panel (require both sides meet threshold)
panel = pd.merge(
    cause_df, effect_df,
    on=["gvkey", "technology", "dateQ"],
    how="inner",
    validate="1:1",
)
n_cause_only = len(cause_df) - len(panel)
n_effect_only = len(effect_df) - len(panel)
print(f"  Joint panel (inner join): {len(panel):,} observations")
print(f"    Cause-only dropped: {n_cause_only:,}, "
      f"Effect-only dropped: {n_effect_only:,}")

# Intensity measures
assert (panel["N_effect"] > 0).all(), "Zero N_effect found — division by zero risk"
panel["N_total"] = panel["N_cause"] + panel["N_effect"]
panel["cause_effect_ratio"] = panel["N_cause"] / panel["N_effect"]

# Merge firm metadata
pre_merge = len(panel)
panel = panel.merge(firm_info, on="gvkey", how="left", validate="m:1")
assert len(panel) == pre_merge, "Firm metadata merge changed row count"

# Save panel
panel.to_csv(OUT_PANEL, index=False, encoding="utf-8")
print(f"  Panel saved -> {OUT_PANEL.relative_to(ROOT)}")


# ── Compute statistics ────────────────────────────────────────────

def dist_stats(s):
    """Return dict of distributional statistics."""
    return {
        "mean": s.mean(), "sd": s.std(),
        "p25": s.quantile(0.25), "median": s.median(),
        "p75": s.quantile(0.75),
    }


# Panel B dimensions
n_obs = len(panel)
n_firms = panel["gvkey"].nunique()
n_techs = panel["technology"].nunique()
n_quarters = panel["dateQ"].nunique()
n_countries = panel["loc"].nunique()

opf = panel.groupby("gvkey").size()
opf_stats = dist_stats(opf)

# Panels C-D: macro category names (LaTeX-escaped)
CAUSE_NAMES = {
    1: "Technology Innovation \\& Advancement",
    2: "Market Demand \\& Consumer Behavior",
    3: "Regulatory \\& Policy Drivers",
    4: "Strategic Partnerships \\& Investment",
    5: "Cost \\& Economic Viability",
}
EFFECT_NAMES = {
    1: "Revenue \\& Financial Growth",
    2: "Cost Reduction \\& Efficiency",
    3: "Market Expansion \\& Adoption",
    4: "Product \\& Service Innovation",
    5: "Operational Efficiency \\& Automation",
}

cause_stats = {c: dist_stats(panel[f"share_cause_{c}"]) for c in range(1, 6)}
effect_stats = {c: dist_stats(panel[f"share_effect_{c}"]) for c in range(1, 6)}

# Panel E: intensity measures (label, stats, format function)
intensity_items = [
    ("Total span count, $N_{ikt}$", dist_stats(panel["N_total"])),
    ("Cause spans, $N^{\\text{cause}}_{ikt}$", dist_stats(panel["N_cause"])),
    ("Effect spans, $N^{\\text{effect}}_{ikt}$", dist_stats(panel["N_effect"])),
    ("Cause-to-effect ratio", dist_stats(panel["cause_effect_ratio"])),
]

# Sanity checks: shares must sum to 1.0 by construction
SHARE_TOL = 1e-6
cause_mean_sum = sum(cause_stats[c]["mean"] for c in range(1, 6))
effect_mean_sum = sum(effect_stats[c]["mean"] for c in range(1, 6))
assert abs(cause_mean_sum - 1.0) < SHARE_TOL, (
    f"Cause shares do not sum to 1: {cause_mean_sum:.6f}"
)
assert abs(effect_mean_sum - 1.0) < SHARE_TOL, (
    f"Effect shares do not sum to 1: {effect_mean_sum:.6f}"
)
print(f"\n  Shares sum check PASSED (cause={cause_mean_sum:.6f}, "
      f"effect={effect_mean_sum:.6f})")

print(f"\n  Panel B: {n_obs:,} obs, {n_firms:,} firms, "
      f"{n_techs} techs, {n_quarters} quarters, {n_countries} countries")


# ═══════════════════════════════════════════════════════════════════
# CSV OUTPUT
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Writing CSV...")

# Map internal keys to display column names
STAT_COLS = {"mean": "Mean", "sd": "SD", "p25": "P25", "median": "Median", "p75": "P75"}

rows = []

# Panel A scalars
for label, val in [
    ("Total snippets in corpus", total_snippets),
    ("Technology-relevant snippets", tech_snippets),
    ("Share of total (%)", round(tech_share_pct, 1)),
    ("Causal ratio (%)", round(causal_ratio_pct, 1)),
    ("Unique transcripts", unique_transcripts),
    ("Unique technologies", unique_techs_a),
    ("Year min", year_min),
    ("Year max", year_max),
]:
    rows.append({"Panel": "A", "Variable": label, "Value": val})

rows.append({
    "Panel": "A", "Variable": "Snippets per transcript",
    **{STAT_COLS[k]: v for k, v in spt_stats.items()},
})

# Panel B scalars
for label, val in [
    ("Observations", n_obs),
    ("Unique firms", n_firms),
    ("Unique technologies", n_techs),
    ("Unique quarters", n_quarters),
    ("Countries", n_countries),
]:
    rows.append({"Panel": "B", "Variable": label, "Value": val})

rows.append({
    "Panel": "B", "Variable": "Obs per firm",
    **{STAT_COLS[k]: v for k, v in opf_stats.items()},
})

# Panel C
for c in range(1, 6):
    name = CAUSE_NAMES[c].replace("\\&", "&")
    rows.append({
        "Panel": "C", "Variable": name,
        **{STAT_COLS[k]: v for k, v in cause_stats[c].items()},
    })

# Panel D
for c in range(1, 6):
    name = EFFECT_NAMES[c].replace("\\&", "&")
    rows.append({
        "Panel": "D", "Variable": name,
        **{STAT_COLS[k]: v for k, v in effect_stats[c].items()},
    })

# Panel E
for label, stats in intensity_items:
    clean = re.sub(r"[\$\\{}]", "", label).replace("text", "")
    rows.append({
        "Panel": "E", "Variable": clean,
        **{STAT_COLS[k]: v for k, v in stats.items()},
    })

csv_df = pd.DataFrame(rows)
csv_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
print(f"  CSV -> {OUT_CSV.relative_to(ROOT)}")


# ═══════════════════════════════════════════════════════════════════
# LATEX TABLE
# ═══════════════════════════════════════════════════════════════════
print("Writing LaTeX table...")


def fmt_int(x):
    """Format integer with comma separator."""
    return f"{int(x):,}"


def fmt_pct(x):
    """Format percentage (1 decimal)."""
    return f"{x:.1f}\\%"


def fmt_share(x):
    """Format share to 3 decimal places."""
    return f"{x:.3f}"


def fmt_f1(x):
    """Format float to 1 decimal place."""
    return f"{x:.1f}"


def fmt_f2(x):
    """Format float to 2 decimal places."""
    return f"{x:.2f}"


def scalar_row(label, value_str):
    """Row where value spans all stat columns."""
    return f"{label} & \\multicolumn{{5}}{{r}}{{{value_str}}} \\\\\n"


def dist_row(label, stats, fmt):
    """Row with Mean, SD, P25, Median, P75."""
    vals = [fmt(stats[k]) for k in ("mean", "sd", "p25", "median", "p75")]
    return f"{label} & {' & '.join(vals)} \\\\\n"


lines = []
lines.append("\\begin{table}[!htbp]\\centering\n")
lines.append("\\caption{Summary Statistics}\n")
lines.append("\\label{tab:summary-stats}\n")
lines.append("\\begin{flushleft}\\footnotesize\n")
lines.append(
    "\\textit{Notes.} This table reports summary statistics for the "
    "firm--technology--quarter panel constructed from earnings conference "
    "call transcripts. Panel~A describes the technology snippet extraction "
    f"from {fmt_int(total_snippets)} text windows across "
    f"{fmt_int(unique_transcripts)} transcripts ({year_min}--{year_max}). "
    "Technology-relevant snippets are those where the LLM identifies a specific "
    "technology from the 29 disruptive technologies in \\citet{kalyani2025}. "
    "The causal ratio is the share of technology-relevant snippets containing "
    "at least one causal statement. "
    "Panel~B reports dimensions of the causal panel after deduplication "
    "and applying a minimum threshold of three spans per side (cause or effect). "
    "Panels~C and~D report the distribution of cause and effect shares across "
    "the five macro categories; by construction, shares on each side sum to one "
    "for every observation. "
    "Panel~E reports intensity measures. "
    "See Section~II.D for variable definitions.\n"
)
lines.append("\\end{flushleft}\n")
lines.append("\\resizebox{\\textwidth}{!}{%\n")
lines.append("\\begin{tabular}{lrrrrr}\n")
lines.append("\\hline\\hline\n")
lines.append(" & Mean & SD & P25 & Median & P75 \\\\\n")

# ── Panel A ──────────────────────────────────────────────────────
lines.append("\\hline\n")
lines.append(
    "\\multicolumn{6}{l}{\\textsc{Panel A. "
    "Technology Snippet Extraction}} \\\\\n"
)
lines.append(scalar_row("Total snippets in corpus", fmt_int(total_snippets)))
lines.append(scalar_row("Technology-relevant snippets", fmt_int(tech_snippets)))
lines.append(scalar_row("\\quad Share of total", fmt_pct(tech_share_pct)))
lines.append(scalar_row("Causal ratio", fmt_pct(causal_ratio_pct)))
lines.append(scalar_row("Unique transcripts", fmt_int(unique_transcripts)))
lines.append(scalar_row("Unique technologies", str(unique_techs_a)))
lines.append(scalar_row("Sample period", f"{year_min}--{year_max}"))
lines.append(dist_row("Snippets per transcript", spt_stats, fmt_f1))

# ── Panel B ──────────────────────────────────────────────────────
lines.append("\\hline\n")
lines.append(
    "\\multicolumn{6}{l}{\\textsc{Panel B. "
    "Causal Panel Dimensions}} \\\\\n"
)
lines.append(
    scalar_row("Firm--technology--quarter observations", fmt_int(n_obs))
)
lines.append(scalar_row("Unique firms", fmt_int(n_firms)))
lines.append(scalar_row("Unique technologies", str(n_techs)))
lines.append(scalar_row("Unique quarters", str(n_quarters)))
lines.append(scalar_row("Countries", str(n_countries)))
lines.append(dist_row("Observations per firm", opf_stats, fmt_f1))

# ── Panel C ──────────────────────────────────────────────────────
lines.append("\\hline\n")
lines.append(
    "\\multicolumn{6}{l}{\\textsc{Panel C. Cause Shares}} \\\\\n"
)
for c in range(1, 6):
    lines.append(dist_row(CAUSE_NAMES[c], cause_stats[c], fmt_share))

# ── Panel D ──────────────────────────────────────────────────────
lines.append("\\hline\n")
lines.append(
    "\\multicolumn{6}{l}{\\textsc{Panel D. Effect Shares}} \\\\\n"
)
for c in range(1, 6):
    lines.append(dist_row(EFFECT_NAMES[c], effect_stats[c], fmt_share))

# ── Panel E ──────────────────────────────────────────────────────
lines.append("\\hline\n")
lines.append(
    "\\multicolumn{6}{l}{\\textsc{Panel E. Intensity Measures}} \\\\\n"
)
for label, stats in intensity_items:
    # Use 1 decimal for counts, 2 decimal for ratio
    fmt = fmt_f2 if "ratio" in label.lower() else fmt_f1
    lines.append(dist_row(label, stats, fmt))

lines.append("\\hline\\hline\n")
lines.append("\\end{tabular}%\n")
lines.append("}\n")
lines.append("\\vspace{0.25em}\n")
lines.append("\\end{table}\n")

tex_content = "".join(lines)
OUT_TEX.write_text(tex_content, encoding="utf-8")
print(f"  LaTeX -> {OUT_TEX.relative_to(ROOT)}")


# ═══════════════════════════════════════════════════════════════════
# RUN MANIFEST
# ═══════════════════════════════════════════════════════════════════
manifest = {
    "script": Path(__file__).name,
    "timestamp": ts.isoformat(),
    "seed": SEED,
    "input_files": [
        str(ALLTECH_PATH.relative_to(ROOT)),
        str(CAUSAL_PATH.relative_to(ROOT)),
    ],
    "output_files": [
        str(p.relative_to(ROOT)) for p in [OUT_CSV, OUT_TEX, OUT_PANEL]
    ],
    "row_counts": {
        "alltech_total": total_snippets,
        "alltech_tech_relevant": tech_snippets,
        "alltech_causal": causal_count,
        "causal_raw": raw_causal,
        "causal_after_drop": after_drop,
        "causal_after_dedup": post_dedup,
        "panel_obs": n_obs,
        "panel_firms": n_firms,
        "panel_techs": n_techs,
        "panel_quarters": n_quarters,
        "panel_countries": n_countries,
    },
    "parameters": {
        "min_spans_threshold": 3,
        "dedup_keys": [
            "gvkey", "technology", "dateQ", "side", "input_id", "macro_id"
        ],
    },
}
OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"  Manifest -> {OUT_MANIFEST.relative_to(ROOT)}")

print("\nDone.")
