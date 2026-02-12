# Workflow Quick Reference

**Model:** Contractor (you direct, Claude orchestrates)

---

## The Loop

```
Your instruction
    ↓
[PLAN] (if multi-file or unclear) → Show plan → Your approval
    ↓
[EXECUTE] Implement, verify, done
    ↓
[REPORT] Summary + what's ready
    ↓
Repeat
```

---

## I Ask You When

- **Design forks:** "Cluster SEs at firm vs. firm-quarter level. Which?"
- **Specification ambiguity:** "Table note says 'technology × time FE' — interact or separate?"
- **Data question:** "Raw file has 3 date formats. Assume ISO 8601?"
- **Scope question:** "Also build Table III while here, or focus on Table II?"
- **Identification concern:** "Critic flagged reverse causality in V.A. Investigate or note as limitation?"

---

## I Just Execute When

- Code fix is obvious (bug, lint, path issue)
- Verification (pipeline runs, tests pass, compilation)
- Documentation (logs, manifests, commits)
- Table/figure formatting (per JF/QJE standards)
- Proofreading and citation checks

---

## Quality Gates (No Exceptions)

| Score | Action |
|-------|--------|
| >= 80 | Ready to commit |
| >= 90 | Ready for co-author review |
| >= 95 | Publication-ready |
| < 80  | Fix blocking issues |

One **critical** finding → automatic fail.

---

## Non-Negotiables

- Raw data (`data/`) is **read-only** — never modify
- Python paths: `Path(__file__).resolve().parents[2]` (repo-relative)
- Stata: `version 19.5`, `set more off`, log to `logs/`
- Seeds: `SEED = 42` once at top; `set seed 42` in Stata
- Every pipeline run → JSON manifest in `results/runs/`
- Tables → `.csv` + `.tex` in `results/`
- Figures → `.pdf` + `.png` in `Figures/`, white bg, explicit dimensions
- JF/QJE table style: booktabs, three-part notes, Roman numeral numbering

---

## Preferences

**Visual:** Publication-quality. Matplotlib/seaborn with custom palette. No default colors.
**Reporting:** Concise bullets. Details on request.
**Session logs:** Always (post-plan, incremental, end-of-session).
**Replication:** Strict. All results reproducible from raw data + code.

---

## Adversarial Review Loop

```
empirical-critic  →  score + findings (quality_reports/critic_round_N.yaml)
       ↓
empirical-fixer   →  apply fixes     (quality_reports/fixer_round_N.yaml)
       ↓
re-run pipeline   →  verify outputs
       ↓
loop back to critic (max 5 rounds or until pass)
```

---

## Exploration Mode

For experimental work, use the **Fast-Track** workflow:
- Work in `explorations/` folder
- 60/100 quality threshold (vs. 80/100 for production)
- No plan needed — just a research value check (2 min)
- See `.claude/rules/exploration-fast-track.md`

---

## Paper Progress

| Section | Status | Next Action |
|---------|--------|-------------|
| I. Introduction | Drafted | Proofread, finalize |
| II. Data & Measurement | Notes only | Write pipeline, then draft |
| III. Validation | Notes only | Build external-proxy correlations |
| IV. Structure of Beliefs | Table V drafted | Write remaining subsections |
| V. Beliefs & Actions | Notes only | Build Tables VI–VIII |
| VI. Beliefs & Misallocation | Notes only | Build Tables IX–X |
| VII. Conclusion | Notes only | Draft after IV–VI complete |

---

## Next Step

You provide task → I plan (if needed) → Your approval → Execute → Done.
