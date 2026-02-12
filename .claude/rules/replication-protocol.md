---
paths:
  - "src/**/*.py"
  - "src/**/*.do"
---

# Replication-First Protocol

**Core principle:** Replicate original results to the dot BEFORE extending.

---

## Phase 1: Inventory & Baseline

Before writing any analysis code:

- [ ] Read the paper's methodology section and any replication notes
- [ ] Inventory data files, variable definitions, and sample restrictions
- [ ] Record gold standard numbers from the paper:

```markdown
## Replication Targets: [Paper Author (Year)]

| Target | Table/Figure | Value | SE/CI | Notes |
|--------|-------------|-------|-------|-------|
| Main effect | Table V, Col 3 | 0.632 | (0.084) | Primary specification |
```

- [ ] Store targets in `quality_reports/replication_targets_[table].md`

---

## Phase 2: Implement & Execute

- [ ] Follow `python-code-conventions.md` for Python scripts
- [ ] Follow `stata-code-conventions.md` for Stata do-files
- [ ] Match original specification exactly (covariates, sample, clustering, SE computation)
- [ ] Document every specification choice with inline comments
- [ ] Save all intermediate results (Python: to `data_processed/`, Stata: as .dta)
- [ ] Write manifest JSON on every run

### Cross-Language Pitfalls

| Python (statsmodels/linearmodels) | Stata | Trap |
|-----------------------------------|-------|------|
| `PanelOLS(..., entity_effects=True)` | `reghdfe y x, absorb(firm_id)` | Different singleton handling |
| `cluster_entity=True` | `cluster(firm_id)` | Small-sample df adjustment may differ |
| `pd.merge(how='left')` | `merge m:1 ... using` | Default NA handling differs |
| `np.log()` on zeros | `gen ln_y = ln(y)` | Both produce NaN/missing, but silently |

---

## Phase 3: Verify Match

### Tolerance Thresholds

| Type | Tolerance | Rationale |
|------|-----------|-----------|
| Integers (N, counts) | Exact match | No reason for any difference |
| Point estimates | 1e-6 | Numerical precision |
| Standard errors | 1e-4 | Clustering variability |
| R-squared | 1e-4 | FE precision |
| Variance shares (Table V) | 0.01pp | Display rounding |

### If Mismatch

**Do NOT proceed to extensions.** Isolate which step introduces the difference, check common causes (sample size, SE computation, default options, variable definitions), and document the investigation even if unresolved.

### Replication Report

Save to `quality_reports/replication_report_[table].md`:

```markdown
# Replication Report: [Table/Figure]
**Date:** [YYYY-MM-DD]
**Scripts:** [Python/Stata paths]

## Summary
- **Targets checked / Passed / Failed:** N / M / K
- **Overall:** [REPLICATED / PARTIAL / FAILED]

## Results Comparison

| Target | Paper | Ours | Diff | Status |
|--------|-------|------|------|--------|

## Discrepancies (if any)
- **Target:** X | **Investigation:** ... | **Resolution:** ...

## Environment
- Python version, key packages (with versions)
- Stata version, ado packages
- Data source and date
```

---

## Phase 4: Only Then Extend

After replication is verified (all targets PASS):

- [ ] Commit replication script: "Replicate Table X — all targets match"
- [ ] Now extend with robustness checks, alternative specifications, etc.
- [ ] Each extension builds on the verified baseline
