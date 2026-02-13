# Claude Code Starter Prompt — Managerial Theories of Technology

## How to Start

Open your terminal in the project directory, or open the Claude Code panel in VS Code:

```bash
cd "C:\Users\Xingx\Dropbox\claude-code-my-workflow"
claude
```

**Using VS Code?** Open the Claude Code panel instead (Ctrl+Shift+P → "Claude Code: Open"). Everything works the same.

---

## Paste This Prompt (New Session Recovery)

Copy and paste the block below into Claude Code at the start of a new session:

---

> I am continuing work on **Managerial Theories of Technology**. This is an empirical finance paper that extracts causal theories managers hold about 29 disruptive technologies from 450,000 quarterly earnings calls (2002–2024) using LLMs. We use Python (conda env `Technology`, Python 3.11) for data cleaning and analysis, Stata SE 19.5 for selected regressions, and LaTeX (Overleaf) for the manuscript.
>
> **Current state of the paper:**
> - **Drafted:** Section I (Introduction), II.D (Panel Construction), III.A–C (Top-Scoring Transcripts, Cross-Technology Variation, Time-Series Patterns), IV.A–C (Variance Decomposition, Spillover, Belief Dynamics)
> - **Tables completed:** Table I (macro taxonomy), Table II (summary stats), Table V (variance decomposition), Table VI (spillover), Table VII (persistence)
> - **Figures completed:** Figure I (cross-tech bars), Figure II (tech-push vs demand-pull scatter), Figure III (time-series patterns), Figure IV (persistence decay)
> - **Not yet started:** Sections II.A–C, II.E, III.D–E, IV.D, V, VI, VII
> - **Section V** requires firm-level outcome data (Compustat, CRSP, I/B/E/S) not yet in the panel
>
> Read CLAUDE.md, MEMORY.md, and the most recent plan in quality_reports/plans/ to understand the full context. Check `git log --oneline -10` for recent work. Then ask me what I'd like to work on.

---

## What This Does

Claude will:

1. Read `CLAUDE.md` (project configuration, paper structure, conventions)
2. Read `MEMORY.md` (persistent corrections and learned facts)
3. Check recent git history to understand what was last completed
4. Optionally read the most recent plan file for context on in-progress work
5. Ask what you'd like to work on next

---

## Example Tasks

```
Draft Section II.B (Extracting Causal Statements) following the notes in main.tex.
```

```
Build the external proxy correlation table for Section III.D.
```

```
Write Section V.A — I've added Compustat data to data/compustat_quarterly.csv.
```

```
Create a figure showing the distribution of cause-effect ratios across technologies.
```

```
Run /devils-advocate on Section IV to stress-test the identification strategy.
```

```
Run /proofread on Section III.B.
```

Claude will automatically use the plan-first workflow for non-trivial tasks, run the relevant reviewers, and handle the orchestration.

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project config, paper structure, commands, conventions |
| `MEMORY.md` | Persistent corrections (`[LEARN]` tags) |
| `.claude/rules/` | 15 rule files (orchestrator, plan-first, quality gates, code conventions, etc.) |
| `.claude/rules/knowledge-base-template.md` | Notation registry, taxonomy, paper progression |
| `work plans and summary/` | Methods summaries for each completed section |
| `quality_reports/plans/` | Saved plans that survive context compression |

---

## Python Pipeline Scripts

| Script | Output | Section |
|--------|--------|---------|
| `01_clean.py` | `data_processed/panel_ikt.csv` | II.D |
| `03_table_II_summary_stats.py` | Table II (summary_stats.tex) | II.D |
| `04_table_IIIA_top_scoring.py` | Online Appendix top-scoring table | III.A |
| `04b_figure_IIIB_techpush_demandpull.py` | Figure II (scatter plot) | III.B |
| `05_figure_II_time_series.py` | Figure III (time-series panels) | III.C |
| `06_table_IVB_spillover.py` | Table VI + robustness + by-category | IV.B |
| `07_table_IVC_dynamics.py` | Table VII + Figure IV (persistence) | IV.C |

All scripts: `set PYTHONIOENCODING=utf-8 && conda run -n Technology python src/py/<script>.py`
