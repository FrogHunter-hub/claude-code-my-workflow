---
paths:
  - "src/**/*.do"
---

# Stata Code Standards

**Standard:** Senior applied econometrician quality. Every do-file must run cleanly from a fresh Stata session.

---

## 1. Header Block (Required)

Every do-file starts with:

```stata
version 19.5
set more off
capture log close _all

* ============================================================
* Title:   [Descriptive Title]
* Author:  [Name]
* Date:    [YYYY-MM-DD]
* Purpose: [What this script does]
* Inputs:  [Data files read]
* Outputs: [Data files and tables written]
* ============================================================

log using "logs/[script_name]_`c(current_date)'.log", replace
```

## 2. Path Management

- All paths relative to repo root
- Use globals for directory structure:
  ```stata
  global ROOT "."
  global DATA "$ROOT/data"
  global PROCESSED "$ROOT/data_processed"
  global RESULTS "$ROOT/results"
  global LOGS "$ROOT/logs"
  ```
- Never hardcode absolute paths (`C:\`, `D:\`)

## 3. Merge Protocol

After every `merge`:
```stata
merge m:1 firm_id quarter using "$PROCESSED/panel.dta"
tab _merge
assert _merge != 2  // or document why _merge==2 is acceptable
drop _merge          // or keep with explicit justification
```

**Never** proceed without checking `_merge`.

## 4. Estimation Standards

- **Clustering:** Always `cluster(firm_id)` at minimum for panel data
- **Fixed effects:** Prefer `reghdfe` over `areg` for multi-way FE (correct singleton handling)
- **Standard errors:** Document SE method choice with inline comment
- **Sample:** Document sample restrictions with comments and `count` before estimation

```stata
* Within tech × industry × quarter, cluster at firm level
reghdfe y x1 x2, absorb(tech#industry#quarter) cluster(firm_id)
```

## 5. Output Management

- Tables: Export as both `.csv` and `.tex` to `results/`
  ```stata
  esttab using "$RESULTS/table_V.tex", replace booktabs
  esttab using "$RESULTS/table_V.csv", replace
  ```
- Figures: Save as `.pdf` and `.png` to `Figures/`
- Log: Always open at start, close at end: `log close`

## 6. Known Pitfalls

| Bug | Impact | Fix |
|-----|--------|-----|
| `areg` vs `reghdfe` | Different singleton handling | Prefer `reghdfe` for multi-way FE |
| `reg` without `cluster()` | Wrong SEs for panel data | Always cluster at firm level |
| Missing `capture` before `log close` | Crashes if no log open | `capture log close _all` |
| `merge` without `_merge` check | Silent data loss | Always `tab _merge` |
| `encode` on large string vars | Memory explosion | Use `egen group()` instead |

## 7. Code Quality Checklist

```
[ ] version 19.5 on line 1
[ ] set more off
[ ] capture log close _all before log using
[ ] All paths relative (globals from repo root)
[ ] Every merge followed by tab _merge + assertion
[ ] Clustering specified for all panel regressions
[ ] reghdfe for multi-way FE (not areg)
[ ] Tables exported as .tex + .csv
[ ] Log closed at end of script
[ ] Comments explain specification choices (WHY not WHAT)
```
