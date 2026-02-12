# Claude Code Starter Prompt — Managerial Theories of Technology

## How to Start

Open your terminal in the project directory, or open the Claude Code panel in VS Code:

```bash
cd "C:\Users\Xingx\Dropbox\claude-code-my-workflow"
claude
```

**Using VS Code?** Open the Claude Code panel instead (Ctrl+Shift+P → "Claude Code: Open"). Everything works the same.

---

## Paste This Prompt

Copy and paste the block below into Claude Code:

---

> I am starting to work on **Managerial Theories of Technology** in this repo. We are writing an empirical finance paper that extracts causal theories managers hold about 29 disruptive technologies from 450,000 quarterly earnings calls (2002–2024) using LLMs. The paper documents that these beliefs are heterogeneous at the firm level, persistent across technologies, predict firm actions (investment, hiring, M&A), and that biased beliefs predict misallocation. We use Python (conda env `Technology`, Python 3.11) for data cleaning and NLP pipelines, Stata SE 19.5 for regressions, and LaTeX for the manuscript (Main file: Overleaf/main.tex; Bib: Overleaf/references.bib).
>
> I want our collaboration to be structured, precise, and rigorous. When creating tables and figures, everything must be publication-ready (JF/QJE style). When writing code, everything must be reproducible with deterministic seeds, manifests, and logs.
>
> I've set up the Claude Code academic workflow (forked from `pedrohcgs/claude-code-my-workflow`). The configuration files are already in this repo. Please read them, understand the workflow, and then **update all configuration files to fit my project** — specifically:
>
> 1. Adapt agents: replace R-focused agents with Python and Stata reviewers; replace Beamer/Quarto agents with manuscript-focused agents (empirical reviewer, identification critic).
> 2. Adapt rules: replace R code conventions with Python and Stata conventions; replace Beamer/Quarto sync rules with manuscript writing conventions; update quality gates for `.py`, `.do`, and `.tex` files.
> 3. Adapt skills: replace lecture-creation skills with paper-writing skills (`/run-python`, `/run-stata`, `/write-section`, `/build-table`, `/build-figure`); keep research skills (`/lit-review`, `/review-paper`, `/devils-advocate`, `/research-ideation`, `/interview-me`).
> 4. Update the knowledge base with the paper's notation, variable definitions, key empirical facts, and the 5+5 macro taxonomy.
> 5. Update hooks and settings for Windows/PowerShell and the project's tool chain.
>
> The paper's current state: Introduction (Section I) is fully drafted in `Overleaf/main.tex`. Sections II–VII have structural notes (`\note{...}` blocks) describing what each subsection should contain. Table V (variance decomposition) is drafted. The Python and Stata scripts in `src/` are scaffolded with manifest support but contain placeholder logic — real analysis code needs to be written.
>
> After adapting the configuration, use the plan-first workflow for all non-trivial tasks. Once I approve a plan, switch to contractor mode — coordinate everything autonomously and only come back to me when there's ambiguity or a decision to make.
>
> Enter plan mode and start by adapting the workflow configuration for this project.

---

## What This Does

Claude will:

1. Read `CLAUDE.md` and all files in `.claude/` (rules, agents, skills, hooks)
2. Understand that this is an empirical research paper, not a lecture course
3. Systematically adapt every configuration file:
   - **Agents:** Create `python-reviewer`, `stata-reviewer`, `empirical-critic`, `empirical-fixer` to replace `r-reviewer`, `quarto-critic`, `quarto-fixer`, `beamer-translator`, `slide-auditor`, `pedagogy-reviewer`, `tikz-reviewer`
   - **Rules:** Create `python-code-conventions.md`, `stata-code-conventions.md`, `manuscript-conventions.md` to replace `r-code-conventions.md`, `beamer-quarto-sync.md`, `single-source-of-truth.md`, `no-pause-beamer.md`, `tikz-visual-quality.md`
   - **Skills:** Create `/run-python`, `/run-stata`, `/write-section`, `/build-table`, `/build-figure` to replace `/compile-latex`, `/deploy`, `/extract-tikz`, `/translate-to-quarto`, `/qa-quarto`, `/slide-excellence`, `/create-lecture`, `/visual-audit`
   - **Knowledge base:** Fill in notation registry, variable definitions, paper progression, and anti-patterns
   - **Hooks & settings:** Update `.claude/settings.json` for PowerShell, Python, Stata, conda permissions
4. Present a plan for your approval
5. After approval, implement all changes autonomously
6. Present a summary of what was adapted

## After the First Session

For subsequent sessions, just describe your task:

```
Write the Python pipeline for extracting causal triples from earnings call transcripts.
```

```
Draft Section II.B (Extracting Causal Statements) following the notes in main.tex.
```

```
Build Table II (summary statistics) from the processed panel data.
```

Claude will automatically use the plan-first workflow, run the relevant reviewers, and handle the orchestration.
