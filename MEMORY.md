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

<!-- Append new entries below. Most recent at bottom. -->
