---
paths:
  - "src/**/*.py"
  - "src/**/*.do"
  - "explorations/**"
---

# Research Project Orchestrator (Simplified)

**For Python scripts, Stata do-files, and data analysis** -- use this simplified loop instead of the full multi-agent orchestrator.

## The Simple Loop

```
Plan approved → orchestrator activates
  │
  Step 1: IMPLEMENT — Execute plan steps
  │
  Step 2: VERIFY — Run code, check outputs
  │         Python: conda run -n Technology python [script]
  │         Stata: & $env:STATA_EXE /e do "[dofile]"
  │         Manifests: JSON written to results/runs/
  │         Plots: PDF/PNG created in Figures/
  │         If verification fails → fix → re-verify
  │
  Step 3: SCORE — Apply quality-gates rubric
  │
  └── Score >= 80?
        YES → Done (commit when user signals)
        NO  → Fix blocking issues, re-verify, re-score
```

**No 5-round loops. No multi-agent reviews. Just: write, test, done.**

## Verification Checklist

- [ ] Script runs without errors
- [ ] All imports/packages at top
- [ ] No hardcoded absolute paths
- [ ] `SEED = 42` at top (Python) or `set seed 42` (Stata)
- [ ] Output files created at expected paths
- [ ] Manifest JSON written to `results/runs/` (Python)
- [ ] Log file created in `logs/` (Stata)
- [ ] Tolerance checks pass (if applicable)
- [ ] Quality score >= 80
