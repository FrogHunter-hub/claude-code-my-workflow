"""
05_figure_II_time_series.py — Time-Series Patterns of Technology Discussion

Purpose: For Section III.C, generate Figure II showing the number of unique
         firms discussing each technology per quarter for 6 technologies
         in 3 archetypes: platform (ramp), feature (spike/decline),
         policy-driven (waves).

Inputs:  data_processed/panel_ikt.csv

Outputs: Overleaf/Figures/figure_II_time_series.pdf
         Overleaf/Figures/figure_II_time_series.png
         results/tables/figure_II_time_series_data.csv
         results/runs/05_figure_II_<timestamp>.json
"""

from pathlib import Path
import json
import datetime
import os

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

SEED = 42
ROOT = Path(__file__).resolve().parents[2]

np.random.seed(SEED)

# 0. Setup ----
os.makedirs(ROOT / "results" / "tables", exist_ok=True)
os.makedirs(ROOT / "results" / "runs", exist_ok=True)
os.makedirs(ROOT / "Overleaf" / "Figures", exist_ok=True)

# ================================================================
# 1. Define technology archetypes and event markers
# ================================================================

PANELS = {
    "A": {
        "title": "Panel A. Platform Technologies (Sustained Ramp)",
        "techs": ["Cloud computing", "Machine Learning AI"],
        "markers": [
            ("2022-11-01", "ChatGPT", "Machine Learning AI"),
        ],
    },
    "B": {
        "title": "Panel B. Feature Technologies (Spike and Decline)",
        "techs": ["Touch screen", "Rfid tags"],
        "markers": [
            ("2007-06-01", "iPhone", "Touch screen"),
        ],
    },
    "C": {
        "title": "Panel C. Policy-Driven Technologies (Stop-Go Waves)",
        "techs": ["Solar Power", "Hybrid vehicle electric car"],
        "markers": [
            ("2009-02-01", "ARRA"),
            ("2015-12-01", "Paris/ITC"),
            ("2018-01-01", "Solar tariffs"),
            ("2022-08-01", "IRA"),
        ],
    },
}

# Display labels for legend
TECH_LABELS = {
    "Cloud computing": "Cloud Computing",
    "Machine Learning AI": "Machine Learning / AI",
    "Touch screen": "Touch Screen",
    "Rfid tags": "RFID Tags",
    "Solar Power": "Solar Power",
    "Hybrid vehicle electric car": "Hybrid / Electric Vehicle",
}

# ================================================================
# 2. Load and process data
# ================================================================
print("Loading panel_ikt.csv...")
input_path = ROOT / "data_processed" / "panel_ikt.csv"
if not input_path.exists():
    raise FileNotFoundError(
        f"Required input not found: {input_path}\n"
        f"Run 01_clean.py first to generate panel_ikt.csv."
    )
panel = pd.read_csv(
    input_path,
    usecols=["gvkey", "technology", "dateQ"],
    encoding="utf-8",
)
raw_panel_rows = len(panel)
print(f"  Raw panel rows: {raw_panel_rows:,}")

# Keep only our 6 technologies
all_techs = []
for cfg in PANELS.values():
    all_techs.extend(cfg["techs"])
panel["technology"] = panel["technology"].str.strip()
panel = panel[panel["technology"].isin(all_techs)].copy()
missing_techs = set(all_techs) - set(panel["technology"].unique())
if missing_techs:
    raise ValueError(f"Technologies not found in data: {missing_techs}")
print(f"  Rows for selected technologies: {len(panel):,}")

# Deduplicate to unique (gvkey, technology, dateQ)
panel = panel.drop_duplicates(subset=["gvkey", "technology", "dateQ"])
print(f"  After dedup: {len(panel):,}")

# Count unique firms per (technology, dateQ)
firm_counts = (
    panel.groupby(["technology", "dateQ"])["gvkey"]
    .nunique()
    .reset_index()
    .rename(columns={"gvkey": "n_firms"})
)


def parse_dateQ(dq):
    """Convert '2021q3' to datetime (first day of quarter)."""
    year = int(dq[:4])
    q = int(dq[-1])
    month = (q - 1) * 3 + 1
    return pd.Timestamp(year=year, month=month, day=1)


firm_counts["date"] = firm_counts["dateQ"].apply(parse_dateQ)

# Create complete date range for all techs (fill missing with 0)
all_dates = pd.date_range(
    start=firm_counts["date"].min(),
    end=firm_counts["date"].max(),
    freq="QS",
)
complete_index = pd.MultiIndex.from_product(
    [all_techs, all_dates], names=["technology", "date"]
)
firm_counts = (
    firm_counts.set_index(["technology", "date"])
    .reindex(complete_index)
    .fillna({"n_firms": 0})
    .reset_index()
)
firm_counts["n_firms"] = firm_counts["n_firms"].astype(int)

print(f"  Final time-series rows (with zero-fill): {len(firm_counts):,}")
for tech in all_techs:
    subset = firm_counts[firm_counts["technology"] == tech]
    print(f"    {tech}: {subset['n_firms'].sum():,} firm-quarters, "
          f"peak={subset['n_firms'].max()}")

# ================================================================
# 3. Figure styling
# ================================================================

# Colorblind-safe muted palette (2 colors per panel)
COLORS = {
    "A": ["#2166ac", "#b2182b"],  # blue, red
    "B": ["#2166ac", "#b2182b"],
    "C": ["#2166ac", "#b2182b"],
}
LINE_STYLES = ["-", "--"]

# Try serif font (Computer Modern → Times New Roman → serif fallback)
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
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "grid.linewidth": 0.3,
    "grid.alpha": 0.5,
    "lines.linewidth": 1.3,
})

# ================================================================
# 4. Create 3-panel figure
# ================================================================
fig, axes = plt.subplots(3, 1, figsize=(6.5, 8.0), sharex=True)
fig.subplots_adjust(hspace=0.28, top=0.97, bottom=0.06, left=0.10, right=0.96)

for ax, (panel_key, cfg) in zip(axes, PANELS.items()):
    colors = COLORS[panel_key]
    techs = cfg["techs"]

    for i, tech in enumerate(techs):
        ts = firm_counts[firm_counts["technology"] == tech].sort_values("date")
        label = TECH_LABELS.get(tech, tech)
        ax.plot(
            ts["date"], ts["n_firms"],
            color=colors[i],
            linestyle=LINE_STYLES[i],
            label=label,
            zorder=3,
        )

    # Event markers
    for marker_info in cfg["markers"]:
        marker_date = pd.Timestamp(marker_info[0])
        marker_label = marker_info[1]
        ax.axvline(
            marker_date, color="#666666", linestyle=":", linewidth=0.7,
            alpha=0.8, zorder=1,
        )
        ax.text(
            marker_date, 0.95, f"  {marker_label}",
            transform=ax.get_xaxis_transform(),
            fontsize=7, color="#444444", ha="left", va="top",
            rotation=0,
        )

    # Panel title
    ax.set_title(cfg["title"], loc="left", fontweight="bold", fontsize=9.5)

    # Y-axis
    ax.set_ylabel("Number of firms")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=5))

    # Grid
    ax.grid(axis="y", color="#cccccc", linewidth=0.3, alpha=0.6)
    ax.grid(axis="x", visible=False)

    # Remove top/right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend
    ax.legend(loc="upper left", frameon=False, borderpad=0)

# X-axis formatting (shared)
axes[-1].xaxis.set_major_locator(mdates.YearLocator(3))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
axes[-1].set_xlim(pd.Timestamp("2002-01-01"), pd.Timestamp("2025-01-01"))

# ================================================================
# 5. Save figure
# ================================================================
pdf_path = ROOT / "Overleaf" / "Figures" / "figure_II_time_series.pdf"
png_path = ROOT / "Overleaf" / "Figures" / "figure_II_time_series.png"

fig.savefig(pdf_path, dpi=300, bbox_inches="tight")
fig.savefig(png_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"\nFigure saved: {pdf_path}")
print(f"Figure saved: {png_path}")

# ================================================================
# 6. Export underlying data
# ================================================================
export_df = firm_counts.copy()
export_df["dateQ"] = export_df["date"].dt.to_period("Q").astype(str)
export_cols = ["technology", "dateQ", "date", "n_firms"]
csv_path = ROOT / "results" / "tables" / "figure_II_time_series_data.csv"
export_df[export_cols].to_csv(csv_path, index=False, encoding="utf-8")
print(f"Data saved: {csv_path}")

# ================================================================
# 7. Manifest
# ================================================================
run_timestamp = datetime.datetime.now()

manifest = {
    "script": Path(__file__).name,
    "timestamp": run_timestamp.isoformat(),
    "seed": SEED,
    "input_files": ["data_processed/panel_ikt.csv"],
    "output_files": [
        str(pdf_path.relative_to(ROOT)),
        str(png_path.relative_to(ROOT)),
        str(csv_path.relative_to(ROOT)),
    ],
    "row_counts": {
        "panel_raw_total": raw_panel_rows,
        "panel_filtered": len(panel),
        "time_series_rows": len(firm_counts),
        "technologies": len(all_techs),
    },
    "parameters": {
        "technologies": {k: v["techs"] for k, v in PANELS.items()},
        "archetypes": {
            "A": "platform_ramp",
            "B": "feature_spike_decline",
            "C": "policy_driven_waves",
        },
        "date_range": "2002Q1-2024Q4",
        "metric": "n_unique_firms_per_quarter",
    },
}

manifest_path = (
    ROOT / "results" / "runs"
    / f"{Path(__file__).stem}_{run_timestamp:%Y%m%d_%H%M%S}.json"
)
manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
print(f"Manifest written to {manifest_path}")
print("\nDone.")
