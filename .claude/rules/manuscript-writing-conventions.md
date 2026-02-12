---
paths:
  - "Overleaf/**/*.tex"
---

# Manuscript Writing Conventions (JF/QJE Style)

**Target journals:** Journal of Finance, Quarterly Journal of Economics, Review of Financial Studies

---

## 1. Section Structure

- Roman numerals for main sections: I. Introduction, II. Data, ..., VII. Conclusion
- Letter subsections: II.A. Earnings Conference Call Data
- No deeper than two levels (no II.A.1)

## 2. Notation Consistency

Follow the notation registry in `.claude/rules/knowledge-base-template.md`:

| Subscript | Meaning | Example |
|-----------|---------|---------|
| $i$ | Firm | $Y_{it}$ |
| $k$ | Technology | $\text{Share}_{ikt}$ |
| $t$ | Time (quarter) | $X_{it}$ |
| $s$ | Industry (sector) | $\mu_s$ |

- Define every symbol on first use
- Greek letters for fixed effects: $\alpha_i$, $\gamma_{kt}$, $\mu_{st}$
- Shares always 0–1 internally; multiply for display as percentages

## 3. Table Standards

- **Package:** `booktabs` (never `\hline`)
- **Layout:** Three horizontal rules only: `\toprule`, `\midrule`, `\bottomrule`
- **Columns:** Roman numerals (I), (II), (III), ...
- **Stars:** $^{***}$ p<0.01, $^{**}$ p<0.05, $^{*}$ p<0.10
- **Standard errors:** In parentheses below coefficients
- **Notes:** Below table, starting with "Notes:" — describe sample, FE, clustering, variable definitions
- **Number format:** Comma separators for thousands (450,095), 3 decimal places for coefficients
- **Self-contained:** A reader should understand the table without reading the text

## 4. Figure Standards

- **Dimensions:** Match journal column width (typically 6.5" single-column)
- **Font:** Match paper font (Computer Modern or Times)
- **Labels:** Axis labels in sentence case with units
- **Legend:** Bottom or right, outside plot area
- **Caption:** Below figure, descriptive (not just "Figure 1")
- **Notes:** Below caption when needed (data source, sample period)
- **Format:** `.pdf` for submission, `.png` for quick viewing

## 5. Citation Conventions

- `\citet{key}` for textual: "Hassan et al. (2019) show that..."
- `\citep{key}` for parenthetical: "...following prior work \citep{hassan2019}"
- Never mix styles within a paragraph
- For multiple citations: `\citep{paper1, paper2, paper3}` (alphabetical)
- Working papers: note "(working paper)" in text on first mention

## 6. Equation Formatting

- `equation` for single-line, numbered if referenced
- `align` for multi-line derivations
- Number only equations that are referenced later
- Align on `=` sign in multi-line equations
- Define notation immediately after introducing an equation:
  ```latex
  \begin{equation}
  Y_{it} = \alpha_i + \gamma_{kt} + \beta X_{ikt} + \varepsilon_{ikt}
  \end{equation}
  where $Y_{it}$ is firm $i$'s outcome in quarter $t$, ...
  ```

## 7. Common Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| `\hline` in tables | Use `\toprule`, `\midrule`, `\bottomrule` |
| Undefined abbreviation | Define on first use, e.g., "fixed effects (FE)" |
| "significant" without context | Specify economic or statistical significance |
| Table without notes | Always include sample, FE, clustering info |
| Overfull hbox in equations | Use `\resizebox` or break across lines |
| Inconsistent decimal places | Use same precision within a table column |
