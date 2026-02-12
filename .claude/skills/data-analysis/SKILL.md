---
name: data-analysis
description: End-to-end Python data analysis workflow from exploration through regression to publication-ready tables and figures
disable-model-invocation: true
argument-hint: "[dataset path or description of analysis goal]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Edit", "Bash", "Task"]
---

# Data Analysis Workflow

Run an end-to-end data analysis in Python: load, explore, analyze, and produce publication-ready output.

**Input:** `$ARGUMENTS` — a dataset path (e.g., `data_processed/panel.csv`) or a description of the analysis goal (e.g., "variance decomposition of cause shares with firm, tech, and time FE").

---

## Constraints

- **Follow Python code conventions** in `.claude/rules/python-code-conventions.md`
- **Save all scripts** to `src/py/` with descriptive names
- **Save all outputs** (figures, tables, manifests) to `results/` and `Figures/`
- **Write manifest JSON** to `results/runs/` on every execution
- **Use project conventions** for figures (check `.claude/rules/manuscript-writing-conventions.md`)
- **Run python-reviewer** on the generated script before presenting results

---

## Workflow Phases

### Phase 1: Setup and Data Loading

1. Read `.claude/rules/python-code-conventions.md` for project standards
2. Create Python script with proper module docstring (title, purpose, inputs, outputs)
3. Import packages at top: `pandas`, `numpy`, `statsmodels`, `matplotlib`, `seaborn`
4. Set `SEED = 42` once at top
5. Set `ROOT = Path(__file__).resolve().parents[2]`
6. Load and inspect the dataset

### Phase 2: Exploratory Data Analysis

Generate diagnostic outputs:
- **Summary statistics:** `.describe()`, missingness rates, variable types
- **Distributions:** Histograms for key continuous variables
- **Relationships:** Scatter plots, correlation matrices
- **Time patterns:** If panel data, plot trends over time
- **Group comparisons:** Compare across technology categories or cause/effect types

Save all diagnostic figures to `Figures/diagnostics/`.

### Phase 3: Main Analysis

Based on the research question:
- **Regression analysis:** Use `statsmodels` or `linearmodels` for panel data
- **Standard errors:** Cluster at the firm level (document why)
- **Multiple specifications:** Start simple, progressively add FE
- **Effect sizes:** Report standardized effects alongside raw coefficients
- **Variance decomposition:** If applicable, compute within/between variation

### Phase 4: Publication-Ready Output

**Tables:**
- Format as booktabs LaTeX (see `.claude/rules/manuscript-writing-conventions.md`)
- Include: coefficients, SEs in parentheses, stars, N, R-squared, FE indicators
- Export as `.tex` and `.csv` to `results/`

**Figures:**
- Use matplotlib/seaborn with publication style
- White background, serif fonts, explicit dimensions
- Export as `.pdf` and `.png` (300 dpi) to `Figures/`

### Phase 5: Save and Review

1. Write manifest JSON to `results/runs/`
2. Create output directories with `os.makedirs(..., exist_ok=True)`
3. Run the python-reviewer agent on the generated script:

```
Launch python-reviewer agent to review src/py/[script_name].py
```

4. Address any Critical or High issues from the review.

---

## Script Structure

Follow this template:

```python
"""
[Descriptive Title]

Purpose: [What this script does]
Inputs:  [Data files]
Outputs: [Figures, tables, manifests]
"""

from pathlib import Path
import json
import datetime
import pandas as pd
import numpy as np

SEED = 42
ROOT = Path(__file__).resolve().parents[2]

np.random.seed(SEED)

# 0. Setup ----
os.makedirs(ROOT / "results" / "runs", exist_ok=True)

# 1. Data Loading ----

# 2. Exploratory Analysis ----

# 3. Main Analysis ----

# 4. Tables and Figures ----

# 5. Manifest ----
manifest = {
    "script": Path(__file__).name,
    "timestamp": datetime.datetime.now().isoformat(),
    "seed": SEED,
    "input_files": [...],
    "output_files": [...],
    "row_counts": {...},
}
(ROOT / "results" / "runs" / f"{Path(__file__).stem}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json").write_text(
    json.dumps(manifest, indent=2)
)
```

---

## Important

- **Reproduce, don't guess.** If the user specifies a regression, run exactly that.
- **Show your work.** Print summary statistics before jumping to regression.
- **Check for issues.** Look for multicollinearity, outliers, perfect prediction.
- **Use relative paths.** All paths via `ROOT = Path(__file__).resolve().parents[2]`.
- **No hardcoded values.** Use variables for sample restrictions, date ranges, etc.
