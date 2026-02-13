# Project Memory

Corrections and learned facts that persist across sessions.
When a mistake is corrected, append a `[LEARN:category] wrong → right` to MEMORY.md.

---

## Project Context

- Paper: "Managerial Theories of Technology" — extracting causal theories from earnings calls
- Authors: Xingxu Chai (Frankfurt School), Ruishen Zhang (HKU), Laurence van Lent (Frankfurt School), Menghan Zhu (VU Amsterdam)
- Funding: DFG TRR 266
- Data: 450,095 calls, 19,469 firms, 94 countries, 2002–2024, 29 technologies (Kalyani et al. 2025 QJE)
- Extraction: 187,647 causal snippets → 197,818 cause spans + 385,418 effect spans
- Taxonomy: 5 macro causes × 5 macro effects (TNT-LLM two-layer)
- Key result: firm-level variation = 60–74% of total (Table V, variance decomposition)
- Benchmark papers for style: Hassan et al. (2019 QJE), Sautner et al. (2023 JF), Kalyani et al. (2025 QJE)

## Environment

- [LEARN:env] Python env name is `Technology` (not `base`), located at `D:\anaconda\envs\Technology`
- [LEARN:env] Stata executable is at `D:\StataSE-64.exe` (env var `STATA_EXE`)
- [LEARN:env] Platform is Windows — use PowerShell `.ps1` scripts, not bash
- [LEARN:env] Manuscript lives in `Overleaf/`, not `paper/`

---

## Data & Taxonomy

- [LEARN:taxonomy] Macro category labels must match macro_id→macro_name in Causal_Snippets_with_Categories.csv. Cause macro_id=3 is "Regulatory and Policy Drivers" (NOT "Competitive Landscape Dynamics" — that is a fine-grained category_name). Effect macro_ids 1-5 are: Revenue & Financial Growth, Cost Reduction & Efficiency, Market Expansion & Adoption, Product & Service Innovation, Operational Efficiency & Automation. The Stata do-file (02_tableV_variance.do) originally had wrong labels: cause_3 used a fine-grained name, and all 5 effect-side labels were permuted. Fixed 2026-02-12.
- [LEARN:data] AllTech CSV has 443,478 rows (text windows), not 12.6M. The 450,095 figure in the abstract is total earnings-call transcripts in Refinitiv, not text windows.
- [LEARN:data] Panel after dedup + >=3 threshold + inner join: 13,723 obs, 2,812 firms, 29 techs, 92 quarters, 42 countries.

## Code Patterns

- [LEARN:env] Windows GBK encoding breaks conda Python Unicode output. Always prefix: `set PYTHONIOENCODING=utf-8 &&` before `conda run`.
- [LEARN:env] conda run does not support multiline Python `-c` commands (newline assertion error). Write to a temp .py file instead.
- [LEARN:code] All stacked regressions use pyhdfe + statsmodels OLS with firm-clustered SEs. Pattern: residualize via `pyhdfe.create()`, then `sm.OLS().fit(cov_type="cluster")`.
- [LEARN:code] Figure floats go in `Overleaf/Figures/allfigures.tex`, NOT inline in `main.tex`. Table inputs go in `Overleaf/Tables/alltables.tex`.

## Analysis Decisions

- [LEARN:analysis] CER lifecycle hypothesis (cause-heavy → effect-heavy over tenure) is NOT supported by data. CER is flat across firm-tech tenure. Section IV.C reframed around belief persistence instead.
- [LEARN:analysis] Initial HHI → stickiness hypothesis is NOT supported. Positive correlation is mechanical (more concentrated → more room to drift).
- [LEARN:analysis] Cross-side persistence (cause→effect, effect→cause) shows NEGATIVE β (≈ −0.02 to −0.04). Cause and effect are genuinely separate belief dimensions. Decision: not added to paper (tangent, ambiguous interpretation).
- [LEARN:analysis] Effect beliefs are consistently more portable (IV.B: β=0.39 vs 0.27) AND more persistent (IV.C: β=0.17 vs 0.15) than cause beliefs. This asymmetry is a recurring theme.

## Writing Conventions

- [LEARN:writing] Use "and" not "&" in axis labels and category names in figures.
- [LEARN:writing] "Snippet count" vs "span count" — be precise. A snippet is a text window; a span is a classified cause/effect unit within a snippet. Use "cause span count" when referring to N_cause.
- [LEARN:writing] When referencing Schmookler/Schumpeter, use adjective forms ("Schumpeterian", "Schmooklerian") or describe as "technology-push versus demand-pull debate" to avoid needing formal citations.

<!-- Append new entries below. Most recent at bottom. -->
