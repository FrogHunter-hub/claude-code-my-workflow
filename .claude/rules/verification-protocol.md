---
paths:
  - "src/**/*.py"
  - "src/**/*.do"
  - "Overleaf/**/*.tex"
---

# Task Completion Verification Protocol

**At the end of EVERY task, Claude MUST verify the output works correctly.** This is non-negotiable.

## For Python Scripts (.py):
1. Run the script: `conda run -n Technology python src/py/SCRIPT.py`
2. Check exit code (0 = success)
3. Verify manifest JSON was written to `results/runs/`
4. Verify output files exist with non-zero size in `data_processed/` or `results/`
5. Spot-check key numbers for reasonable magnitude
6. Report verification results

## For Stata Do-Files (.do):
1. Run the do-file: `& $env:STATA_EXE /e do "src/stata/SCRIPT.do"`
2. Check that the log file was created in `logs/`
3. Grep log for `r(` error codes — these indicate Stata errors
4. Verify output .dta and .tex files exist with non-zero size
5. Check that `_merge` tabulations show expected match rates
6. Report verification results

## For LaTeX Manuscript (.tex):
1. Compile with 3-pass sequence:
   ```
   cd Overleaf
   pdflatex -interaction=nonstopmode main.tex
   bibtex main
   pdflatex -interaction=nonstopmode main.tex
   pdflatex -interaction=nonstopmode main.tex
   ```
2. Check exit code
3. Grep for `Overfull \\hbox` warnings — count them
4. Grep for `undefined citations` — these are errors
5. Verify PDF was generated: check `Overleaf/main.pdf` size
6. Report: compilation status, overfull hbox count, undefined citations

## For Bibliography:
- Check that all `\cite` references in modified .tex files have entries in `Overleaf/references.bib`

## Common Pitfalls:
- **Python encoding:** Non-ASCII firm names fail without `encoding="utf-8"`
- **Stata paths:** PowerShell requires `& $env:STATA_EXE` syntax, not direct path
- **LaTeX references:** Run bibtex between pdflatex passes, not after
- **Assuming success:** Always verify output files exist AND contain correct content

## Verification Checklist:
```
[ ] Output file created successfully
[ ] No compilation/runtime errors
[ ] Manifest/log written (Python/Stata)
[ ] Key outputs have non-zero size
[ ] Spot-checked numbers for reasonable magnitude
[ ] Reported results to user
```
