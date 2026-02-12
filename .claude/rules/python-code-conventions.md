---
paths:
  - "src/**/*.py"
  - "scripts/**/*.py"
---

# Python Code Standards

**Standard:** Senior Principal Data Engineer + PhD researcher quality

---

## 1. Reproducibility

- `SEED = 42` defined ONCE at module top — never inside functions or loops
- Set all random states from this constant: `random.seed(SEED)`, `np.random.seed(SEED)`
- All imports at top of file, grouped: stdlib → third-party → local
- All paths via `Path(__file__).resolve().parents[2]` (repo root) — never hardcoded
- `os.makedirs(..., exist_ok=True)` for output directories
- Conda environment: `Technology` (Python 3.11)

## 2. Function Design

- `snake_case` naming, verb-noun pattern (`clean_transcripts`, `compute_shares`)
- Google-style docstrings on public functions
- Type hints on function signatures
- Default parameters for tuning values, no magic numbers in function bodies
- Return typed objects (DataFrames, dicts, namedtuples) — not bare tuples

## 3. Data Pipeline Pattern

Every pipeline script follows this structure:

```python
"""
Title: [Descriptive Title]
Purpose: [What this script does]
Inputs: [Data files read]
Outputs: [Files written]
"""

from pathlib import Path
import json, datetime

SEED = 42
ROOT = Path(__file__).resolve().parents[2]

# 0. Setup
# 1. Load data
# 2. Process
# 3. Analyze
# 4. Export results
# 5. Write manifest
```

## 4. Manifest Pattern

Every pipeline run writes a JSON manifest to `results/runs/`:

```python
manifest = {
    "script": Path(__file__).name,
    "timestamp": datetime.datetime.now().isoformat(),
    "seed": SEED,
    "input_files": [...],
    "output_files": [...],
    "row_counts": {"input": N, "output": M},
    "parameters": {...},
}
Path(ROOT / "results" / "runs" / f"{script_name}_{timestamp}.json").write_text(
    json.dumps(manifest, indent=2)
)
```

## 5. Pandas Pitfalls

| Bug | Impact | Fix |
|-----|--------|-----|
| `pd.read_csv()` without `encoding` | Fails on non-ASCII firm names | Always `encoding="utf-8"` |
| Missing `errors="coerce"` | Silent NaN propagation | `pd.to_numeric(..., errors="coerce")` and check |
| `groupby().apply()` with mutation | SettingWithCopyWarning | Use `.transform()` or explicit `.copy()` |
| String matching without `.str.lower()` | Case mismatches in tech keywords | Normalize case before matching |
| Chained indexing `df[col][mask]` | Unpredictable behavior | Use `df.loc[mask, col]` |

## 6. Figure Quality

- **Style:** Publication-ready (JF/QJE). White background. No default matplotlib colors.
- **Palette:** Define project colors at top of plotting scripts
- **Dimensions:** Explicit `figsize=(width, height)` — typically `(10, 6)` for full-width
- **Save:** Both `.pdf` (vector) and `.png` (300 dpi) to `Figures/`
- **Labels:** Sentence case, units included, readable at journal size
- **Font:** Serif (Times/Computer Modern) for paper figures

## 7. Line Length & Math Exceptions

**Standard:** 99 characters (Black default).

**Exception:** Lines may exceed 99 chars if:
1. Breaking would harm readability of a mathematical formula
2. An inline comment explains the operation
3. The line is in a numerically intensive section

## 8. Code Quality Checklist

```
[ ] SEED = 42 at top, used for all random operations
[ ] All paths via Path(__file__).resolve().parents[2]
[ ] Imports grouped: stdlib → third-party → local
[ ] Public functions have Google-style docstrings
[ ] Manifest JSON written to results/runs/
[ ] Figures saved as .pdf + .png with explicit dimensions
[ ] black --check passes
[ ] flake8 passes (or violations documented)
[ ] No hardcoded absolute paths
[ ] Raw data in data/ never overwritten
```
