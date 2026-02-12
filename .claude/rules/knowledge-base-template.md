---
paths:
  - "Overleaf/**/*.tex"
  - "src/**/*.py"
  - "src/**/*.do"
---

# Research Knowledge Base: Managerial Theories of Technology

## Notation Registry

| Rule | Convention | Example | Anti-Pattern |
|------|-----------|---------|-------------|
| Firm subscript | $i$ | $Y_{it}$ | Using $f$ or $j$ for firms |
| Technology subscript | $k$ | $\text{Share}_{ikt}$ | Using $t$ for technology (conflicts with time) |
| Time subscript | $t$ (quarter) | $X_{it}$ | Using $q$ for quarter |
| Industry subscript | $s$ (sector) | $\mu_s$ | Using $j$ or $ind$ |
| Fixed effects | Greek letters | $\alpha_i$, $\gamma_{kt}$, $\mu_{st}$ | Subscript-only notation |
| Cause share | Proportion 0–1 | $\text{CauseShare}_{ikt}^{(c)}$ | Percentage without converting |
| Effect share | Proportion 0–1 | $\text{EffectShare}_{ikt}^{(e)}$ | Same |

## Macro Taxonomy (5 + 5)

### 5 Macro Cause Categories

| # | Category | Definition | Typical technologies |
|---|----------|------------|---------------------|
| 1 | Technology Innovation | R&D breakthroughs, capability building | ML/AI, cloud computing |
| 2 | Market Demand | Customer pull, consumer preferences | Mobile payments, streaming |
| 3 | Regulatory & Policy | Mandates, subsidies, compliance | Solar, hybrid EV |
| 4 | Strategic & Competitive | Partnerships, competitive pressure, M&A | Varies |
| 5 | Cost & Efficiency | Cost reduction as adoption driver | Automation, RFID |

### 5 Macro Effect Categories

| # | Category | Definition |
|---|----------|------------|
| 1 | Revenue Growth | New markets, revenue expansion |
| 2 | Cost Reduction | OpEx savings, efficiency gains |
| 3 | Market Expansion | Market share, geographic reach |
| 4 | Product Innovation | New products, capabilities |
| 5 | Operational Efficiency | Process improvement, workflow |

## Paper Progression

| § | Title | Core Question | Key Tables/Figures | Key Method |
|---|-------|--------------|-------------------|------------|
| I | Introduction | What are managerial theories of technology? | — | — |
| II | Data & Measurement | How to extract causal theories at scale? | Table I (taxonomy), Table II (summary stats) | LLM chain-of-thought, TNT-LLM |
| III | Validation | Do measures capture what we claim? | Table III (external proxies), Table IV (measurement error) | AR(1) IV, correlation |
| IV | Structure of Beliefs | Are beliefs heterogeneous and persistent? | Table V (variance decomposition) | FE decomposition, cross-tech regression |
| V | Beliefs & Actions | Do theories predict resource allocation? | Tables VI–VIII | Within tech-industry-time regressions |
| VI | Beliefs & Misallocation | Do biased beliefs cause worse outcomes? | Tables IX–X | Ex post benchmarking, cross-tech spillover |
| VII | Conclusion | — | — | — |

## Benchmark Papers (Style & Method)

| Paper | Journal | What We Follow |
|-------|---------|---------------|
| Hassan et al. (2019) | QJE | Variance decomposition (Table VIII), validation approach |
| Sautner et al. (2023) | JF | Climate exposure measurement, external proxy correlation |
| Hassan et al. (2023) | RFS | Epidemic exposure, demand-vs-supply shock analysis |
| Kalyani et al. (2025) | QJE | 29 technologies list, diffusion measurement |
| Bordalo, Gennaioli, Shleifer (2018) | JF | Diagnostic expectations theory |

## Design Principles

| Principle | Rationale | Applied In |
|-----------|-----------|------------|
| Firm-level variation is the contribution | Parallels Hassan et al. (2019) finding | Sec IV.A (Table V) |
| Composition > intensity | Distinguish from attention/sentiment measures | Throughout |
| Within tech-industry-time identification | Remove aggregate and sectoral confounds | Sec V, VI |
| Separate management remarks from Q&A | Test for strategic disclosure vs. genuine beliefs | Sec II.E, V.C |
| Ex post benchmark as ground truth | Avoid researcher-imposed "correct" theory | Sec VI.A |

## Anti-Patterns (Don't Do This)

| Anti-Pattern | What Happened | Correction |
|-------------|---------------|-----------|
| Hard-coded Windows paths | `C:\Users\...` in Python scripts | Use `Path(__file__).resolve().parents[2]` |
| Overwriting raw data | Script modified CSV in `data/` | Raw data is read-only; write to `data_processed/` |
| Multiple seeds | `random.seed()` called inside functions | One `SEED = 42` at module top |
| Stata without `version` | Do-file silently uses wrong version | Always start with `version 19.5` |
| Percentage vs proportion | Shares stored as 0–100 in some places, 0–1 in others | Always 0–1 internally; multiply for display |

## Python Code Pitfalls

| Bug | Impact | Fix |
|-----|--------|-----|
| `pd.read_csv()` without `encoding` | Fails on non-ASCII firm names | Always specify `encoding="utf-8"` |
| Missing `errors="coerce"` on numeric conversion | Silent NaN propagation | Use `pd.to_numeric(..., errors="coerce")` and check |
| `groupby().apply()` with mutation | SettingWithCopyWarning, wrong results | Use `.transform()` or explicit copy |
| String matching without `.str.lower()` | Case mismatches in technology keywords | Normalize case before matching |

## Stata Code Pitfalls

| Bug | Impact | Fix |
|-----|--------|-----|
| `reg` without `cluster()` | Wrong SEs for panel data | Always cluster at firm level minimum |
| `areg` vs `reghdfe` | `areg` drops singletons differently | Prefer `reghdfe` for multi-way FE |
| Missing `capture` before `log close` | Crashes if no log open | Use `capture log close _all` |
| `merge` without checking `_merge` | Silent data loss | Always `tab _merge` and handle mismatches |
