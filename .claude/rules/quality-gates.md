---
paths:
  - "src/**/*.py"
  - "src/**/*.do"
  - "Overleaf/**/*.tex"
---

# Quality Gates & Scoring Rubrics

## Thresholds

- **80/100 = Commit** -- good enough to save
- **90/100 = PR** -- ready for co-author review
- **95/100 = Excellence** -- publication-ready

## Python Scripts (.py)

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Syntax/runtime errors | -100 |
| Critical | Hard-coded absolute paths | -20 |
| Critical | Overwrites raw data in `data/` | -20 |
| Critical | Domain-specific bug (wrong estimand, wrong merge) | -30 |
| Major | Missing `SEED` at top | -10 |
| Major | No manifest written | -10 |
| Major | No log output | -5 |
| Major | Missing error handling on file I/O | -5 |
| Minor | Style violations (black/flake8) | -1 per issue |
| Minor | Missing docstring on public function | -2 |
| Minor | Long lines in non-math code (>99 chars) | -1 |

## Stata Do-Files (.do)

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Does not run cleanly | -100 |
| Critical | Missing `version 19.5` | -15 |
| Critical | Overwrites raw data | -20 |
| Critical | Wrong clustering/SE specification | -30 |
| Major | Missing `set more off` | -10 |
| Major | No log file created | -10 |
| Major | Unchecked `_merge` after merge | -10 |
| Major | Hard-coded absolute paths | -10 |
| Minor | Missing header (purpose, author, date) | -3 |
| Minor | No comments on non-obvious steps | -1 |

## LaTeX Manuscript (.tex)

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Compilation failure | -100 |
| Critical | Undefined citation | -15 |
| Critical | Equation typo (wrong sign, missing term) | -10 |
| Major | Overfull hbox > 10pt | -5 |
| Major | Notation inconsistency | -5 |
| Major | Missing table notes | -3 |
| Minor | Grammar/typo | -1 |
| Minor | Inconsistent citation style (\citet vs \citep) | -1 |

## Enforcement

- **Score < 80:** Block commit. List blocking issues.
- **Score < 90:** Allow commit, warn. List recommendations.
- **One critical finding:** Automatic fail regardless of score.
- User can override with justification.

## Quality Reports

Generated **at merge time and after adversarial review rounds**.
Use `quality_reports/TEMPLATE.md` for format.
Save to `quality_reports/merges/YYYY-MM-DD_[branch-name].md`.

## Tolerance Thresholds (Empirical)

| Quantity | Tolerance | Rationale |
|----------|-----------|-----------|
| Point estimates | 1e-6 | Numerical precision |
| Standard errors | 1e-4 | Clustering variability |
| R-squared | 1e-4 | FE precision |
| Variance shares (Table V) | 0.01pp | Display rounding |
| Sample sizes | Exact match | No reason for difference |
