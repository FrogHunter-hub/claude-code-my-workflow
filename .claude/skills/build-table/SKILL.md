---
name: build-table
description: Generate a publication-ready regression table in booktabs LaTeX format from analysis results. Follows JF/QJE table conventions.
disable-model-invocation: true
argument-hint: "[table description, number, or results path]"
allowed-tools: ["Read", "Bash", "Write", "Glob"]
---

# Build Publication-Ready Table

Generate a LaTeX regression table meeting JF/QJE standards.

**Input:** `$ARGUMENTS` — a table description (e.g., "variance decomposition Table V"), table number, or path to results file.

---

## Steps

1. **Locate the source data:**
   - Check `results/` for CSV or JSON files matching the table description
   - Check `data_processed/` for intermediate results
   - If no results exist, report what analysis needs to run first

2. **Format the table** following `.claude/rules/manuscript-writing-conventions.md`:
   - `booktabs` package: `\toprule`, `\midrule`, `\bottomrule` only
   - Column headers in Roman numerals: (I), (II), (III), ...
   - Coefficients with 3 decimal places
   - Standard errors in parentheses below coefficients
   - Significance stars: $^{***}$ p<0.01, $^{**}$ p<0.05, $^{*}$ p<0.10
   - Bottom panel: N, R-squared, FE indicators (Yes/No), Clustering level

3. **Add table notes:**
   - Start with "Notes:"
   - Describe the dependent variable
   - List fixed effects included
   - Specify clustering level
   - Define any non-obvious variables
   - State sample period and coverage

4. **Export:**
   - Save `.tex` to `results/table_[N].tex`
   - Save `.csv` to `results/table_[N].csv`
   - Report: table dimensions, number of specifications, key findings

## Important

- Tables must be **self-contained** — a reader understands them without the text
- Use `\input{../results/table_V.tex}` pattern for inclusion in the manuscript
- Comma separators for thousands (450,095 not 450095)
- Consistent decimal alignment within columns
