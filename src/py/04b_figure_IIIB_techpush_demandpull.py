"""
04b_figure_IIIB_techpush_demandpull.py — Technology-Push vs. Demand-Pull Scatter

Purpose: For Section III.B, generate a scatter plot showing the share of cause
         spans classified as Technology Innovation & Advancement (x-axis) vs.
         Market Demand & Consumer Behavior (y-axis) for each technology.
         Circle area proportional to total causal snippet count.

Inputs:  data_processed/panel_ikt.csv

Outputs: Overleaf/Figures/figure_techpush_demandpull.pdf
         Overleaf/Figures/figure_techpush_demandpull.png
         results/tables/figure_techpush_demandpull_data.csv
         results/runs/04b_figure_IIIB_<timestamp>.json
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
from adjustText import adjust_text

SEED = 42
ROOT = Path(__file__).resolve().parents[2]
np.random.seed(SEED)

# Minimum total cause spans to include a technology
MIN_CAUSE_SPANS = 100

# Category names
CAUSE_1_NAME = "Technology Innovation and Advancement"
CAUSE_2_NAME = "Market Demand and Consumer Behavior"

# Display labels for technologies
TECH_LABELS = {
    "3d printing": "3D Printing",
    "Autonomous Cars": "Autonomous Vehicles",
    "Bispecific monoclonal antibody": "Bispecific Antibody",
    "Cloud computing": "Cloud Computing",
    "Computer vision": "Computer Vision",
    "Drug conjugates": "Drug Conjugates",
    "Electronic gaming": "Electronic Gaming",
    "Fingerprint sensor": "Fingerprint Sensor",
    "Fracking": "Fracking",
    "Hybrid vehicle electric car": "Hybrid/Electric Vehicle",
    "Lithium battery": "Lithium Battery",
    "Machine Learning AI": "Machine Learning/AI",
    "Millimeter wave": "Millimeter Wave",
    "Mobile payment": "Mobile Payment",
    "Oled display": "OLED Display",
    "Online streaming": "Online Streaming",
    "Rfid tags": "RFID Tags",
    "Search Engine": "Search Engine",
    "Smart devices": "Smart Devices",
    "Social Networking": "Social Networking",
    "Solar Power": "Solar Power",
    "Stent graft": "Stent Graft",
    "Touch screen": "Touch Screen",
    "Virtual Reality": "Virtual Reality",
    "Wifi": "WiFi",
    "Wireless charging": "Wireless Charging",
}

# Colors
COLOR_TECH_PUSH = "#7B9BBE"    # muted steel blue
COLOR_DEMAND_PULL = "#C4756D"  # muted dusty rose
COLOR_DIAG = "#999999"

# ================================================================
# Setup
# ================================================================
os.makedirs(ROOT / "results" / "tables", exist_ok=True)
os.makedirs(ROOT / "results" / "runs", exist_ok=True)
os.makedirs(ROOT / "Overleaf" / "Figures", exist_ok=True)

# ================================================================
# 1. Load and aggregate data
# ================================================================
print("Loading panel_ikt.csv...")
panel = pd.read_csv(ROOT / "data_processed" / "panel_ikt.csv")
raw_rows = len(panel)
print(f"  Rows: {raw_rows:,}, Technologies: {panel['technology'].nunique()}")

# Span-weighted technology-level shares
tech_agg = panel.groupby("technology").agg(
    n_cause_1=("n_cause_1", "sum"),
    n_cause_2=("n_cause_2", "sum"),
    N_cause=("N_cause", "sum"),
).reset_index()

tech_agg["tech_push"] = tech_agg["n_cause_1"] / tech_agg["N_cause"] * 100
tech_agg["demand_pull"] = tech_agg["n_cause_2"] / tech_agg["N_cause"] * 100

# Filter by minimum cause spans
n_before = len(tech_agg)
tech_agg = tech_agg[tech_agg["N_cause"] >= MIN_CAUSE_SPANS].copy()
n_excluded = n_before - len(tech_agg)
print(f"  Technologies with >= {MIN_CAUSE_SPANS} cause spans: {len(tech_agg)} "
      f"(excluded {n_excluded})")

# Add display labels
tech_agg["label"] = (
    tech_agg["technology"]
    .map(TECH_LABELS)
    .fillna(tech_agg["technology"])
)

# Classify dominance
tech_agg["dominant"] = np.where(
    tech_agg["tech_push"] > tech_agg["demand_pull"],
    "tech_push", "demand_pull"
)

print("\nTechnology-level shares:")
for _, row in tech_agg.sort_values("tech_push").iterrows():
    marker = "T" if row["dominant"] == "tech_push" else "D"
    print(f"  [{marker}] {row['label']:<28s} "
          f"tech_push={row['tech_push']:5.1f}%  "
          f"demand_pull={row['demand_pull']:5.1f}%  "
          f"N={row['N_cause']:,.0f}")

# ================================================================
# 2. Figure styling
# ================================================================
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
    "grid.alpha": 0.4,
})

# ================================================================
# 3. Create scatter plot
# ================================================================
fig, ax = plt.subplots(1, 1, figsize=(7.0, 7.2))
fig.subplots_adjust(bottom=0.16)

# Bubble size: area proportional to N_cause
# Scale so largest bubble is ~1200 pts² and smallest is still visible
size_scale = 1200 / tech_agg["N_cause"].max()
sizes = tech_agg["N_cause"] * size_scale
# Ensure minimum visibility for small technologies
sizes = sizes.clip(lower=25)

# Edge color: slightly darker version of fill
import matplotlib.colors as mcolors

def darken(hex_color, factor=0.7):
    r, g, b = mcolors.to_rgb(hex_color)
    return (r * factor, g * factor, b * factor)

edge_tech = darken(COLOR_TECH_PUSH, 0.75)
edge_demand = darken(COLOR_DEMAND_PULL, 0.75)

# Colors based on dominance
fill_colors = [
    COLOR_TECH_PUSH if d == "tech_push" else COLOR_DEMAND_PULL
    for d in tech_agg["dominant"]
]
edge_colors = [
    edge_tech if d == "tech_push" else edge_demand
    for d in tech_agg["dominant"]
]

# Scatter
ax.scatter(
    tech_agg["tech_push"],
    tech_agg["demand_pull"],
    s=sizes,
    c=fill_colors,
    alpha=0.60,
    edgecolors=edge_colors,
    linewidths=0.6,
    zorder=3,
)

# Axis limits — set BEFORE annotations so we can position relative to data
ax.set_xlim(10, 80)
ax.set_ylim(-3, 50)

# Diagonal (equal share line)
ax.plot(
    [-5, 55], [-5, 55],
    color=COLOR_DIAG, linestyle="--", linewidth=0.8, alpha=0.5, zorder=1,
)

# "equal share" text along diagonal
ax.text(
    47, 49, "equal share",
    rotation=45, fontsize=7, color="#888888", fontstyle="italic",
    ha="center", va="bottom", zorder=1,
)

# Schmookler / Schumpeter annotations — position in clear areas
ax.text(
    11, 48.5, "Schmookler",
    fontsize=10, fontstyle="italic", fontweight="bold",
    color=COLOR_DEMAND_PULL, alpha=0.85, ha="left", va="bottom",
)
ax.text(
    11, 46.8, "(demand-pull)",
    fontsize=8, fontstyle="italic",
    color=COLOR_DEMAND_PULL, alpha=0.7, ha="left", va="top",
)

ax.text(
    78, 5, "Schumpeter",
    fontsize=10, fontstyle="italic", fontweight="bold",
    color=COLOR_TECH_PUSH, alpha=0.85, ha="right", va="bottom",
)
ax.text(
    78, 3.3, "(technology-push)",
    fontsize=8, fontstyle="italic",
    color=COLOR_TECH_PUSH, alpha=0.7, ha="right", va="top",
)

# Technology labels with adjustText
texts = []
for _, row in tech_agg.iterrows():
    texts.append(
        ax.text(
            row["tech_push"], row["demand_pull"], row["label"],
            fontsize=6.5, ha="center", va="center", zorder=5,
        )
    )

adjust_text(
    texts,
    x=tech_agg["tech_push"].values,
    y=tech_agg["demand_pull"].values,
    arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.4),
    expand=(1.5, 1.8),
    force_text=(1.0, 1.2),
    force_points=(0.4, 0.4),
    only_move="xy",
    ensure_inside_axes=True,
)

# Axes
ax.set_xlabel(f"{CAUSE_1_NAME} share (%)", fontsize=9.5)
ax.set_ylabel(f"{CAUSE_2_NAME} share (%)", fontsize=9.5)

# Grid
ax.grid(True, color="#dddddd", linewidth=0.3, alpha=0.6, zorder=0)

# Remove top/right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# ================================================================
# 4. Below-axis legend (two centered rows, matching reference style)
# ================================================================
from matplotlib.offsetbox import (
    AnchoredOffsetbox, HPacker, VPacker, TextArea, DrawingArea,
)
from matplotlib.patches import Circle as MplCircle

# --- Row 1: Snippet count with reference circles ---
row1_items = []
# "Snippet count:" label
row1_items.append(TextArea("Snippet count:", textprops=dict(fontsize=7.5,
                           color="#555555")))

ref_counts = [3000, 9000, 18000]
for count in ref_counts:
    r_pts = np.sqrt(count * size_scale / np.pi)  # radius in points
    r_draw = max(r_pts * 0.55, 3)  # scale for DrawingArea
    box_size = r_draw * 2 + 4
    da = DrawingArea(box_size, box_size, 0, 0)
    circle = MplCircle((box_size / 2, box_size / 2), r_draw,
                        fc="#cccccc", ec="#999999", lw=0.5, alpha=0.5)
    da.add_artist(circle)
    row1_items.append(da)
    row1_items.append(TextArea(f"{count:,}", textprops=dict(fontsize=7,
                               color="#555555")))

row1 = HPacker(children=row1_items, align="center", pad=0, sep=6)

# --- Row 2: Color legend (two items centered) ---
row2_items = []
for color, label in [(COLOR_TECH_PUSH, "Technology-push dominant"),
                     (COLOR_DEMAND_PULL, "Demand-pull dominant")]:
    da = DrawingArea(12, 12, 0, 0)
    circle = MplCircle((6, 6), 5, fc=color, ec="none", alpha=0.7)
    da.add_artist(circle)
    row2_items.append(da)
    row2_items.append(TextArea(label, textprops=dict(fontsize=7,
                               color="#555555")))
    # spacer between the two items
    if color == COLOR_TECH_PUSH:
        row2_items.append(TextArea("    ", textprops=dict(fontsize=7)))

row2 = HPacker(children=row2_items, align="center", pad=0, sep=4)

# Stack rows vertically and anchor below plot
legend_box = VPacker(children=[row1, row2], align="center", pad=0, sep=8)
anchored = AnchoredOffsetbox(
    loc="upper center",
    child=legend_box,
    bbox_to_anchor=(0.5, -0.06),
    bbox_transform=ax.transAxes,
    frameon=False,
    pad=0,
)
ax.add_artist(anchored)

# ================================================================
# 5. Save figure
# ================================================================
pdf_path = ROOT / "Overleaf" / "Figures" / "figure_techpush_demandpull.pdf"
png_path = ROOT / "Overleaf" / "Figures" / "figure_techpush_demandpull.png"

fig.savefig(pdf_path, dpi=300, bbox_inches="tight")
fig.savefig(png_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"\nFigure saved: {pdf_path}")
print(f"Figure saved: {png_path}")

# ================================================================
# 6. Export underlying data
# ================================================================
export_cols = ["technology", "label", "tech_push", "demand_pull",
               "N_cause", "dominant"]
csv_path = ROOT / "results" / "tables" / "figure_techpush_demandpull_data.csv"
tech_agg[export_cols].sort_values("tech_push").to_csv(
    csv_path, index=False, encoding="utf-8", float_format="%.2f"
)
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
        "panel_raw_total": raw_rows,
        "technologies_total": n_before,
        "technologies_included": len(tech_agg),
        "technologies_excluded": n_excluded,
        "min_cause_spans": MIN_CAUSE_SPANS,
    },
    "summary": {
        "tech_push_dominant": int((tech_agg["dominant"] == "tech_push").sum()),
        "demand_pull_dominant": int((tech_agg["dominant"] == "demand_pull").sum()),
        "tech_push_mean": float(tech_agg["tech_push"].mean()),
        "demand_pull_mean": float(tech_agg["demand_pull"].mean()),
        "correlation": float(tech_agg["tech_push"].corr(tech_agg["demand_pull"])),
    },
}

manifest_path = (
    ROOT / "results" / "runs"
    / f"{Path(__file__).stem}_{run_timestamp:%Y%m%d_%H%M%S}.json"
)
manifest_path.write_text(
    json.dumps(manifest, indent=2, default=str), encoding="utf-8"
)
print(f"Manifest written to {manifest_path}")
print("\nDone.")
