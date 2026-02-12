---
name: devils-advocate
description: Challenge the paper's identification strategy with 5-7 specific questions a top-journal referee would ask. Tests for reverse causality, omitted variables, selection bias, and alternative mechanisms.
disable-model-invocation: true
argument-hint: "[Section number, table, or topic to challenge]"
allowed-tools: ["Read", "Grep", "Glob"]
---

# Devil's Advocate Review

Critically examine the paper's identification strategy and challenge its causal claims with 5-7 specific questions.

**Philosophy:** "We arrive at the best causal inference through active dialogue. Every claim must survive adversarial scrutiny."

---

## Setup

1. **Read the target section/table** in `Overleaf/main.tex`
2. **Read the knowledge base** in `.claude/rules/knowledge-base-template.md` for the paper's identification approach
3. **Read adjacent sections** for context on how the claim fits the overall argument

---

## Challenge Categories

Generate 5-7 challenges from these categories:

### 1. Reverse Causality Challenges
> "Could firm actions cause the beliefs you observe, rather than the reverse?"

### 2. Omitted Variable Challenges
> "What unobserved factor could drive both the causal theory a manager holds and the firm's outcomes?"

### 3. Selection Bias Challenges
> "Are the firms discussing this technology systematically different from those that don't?"

### 4. Measurement Error Challenges
> "Could errors in your LLM extraction correlate with firm characteristics, biasing your estimates?"

### 5. Alternative Mechanism Challenges
> "Could strategic disclosure, analyst influence, or herding explain this pattern equally well?"

### 6. Specification Robustness Challenges
> "How sensitive are these results to alternative FE structures, clustering levels, or sample restrictions?"

### 7. External Validity Challenges
> "Do these findings generalize beyond public firms with English-language earnings calls?"

---

## Output Format

```markdown
# Devil's Advocate: [Section/Table Title]

## Challenges

### Challenge 1: [Category] — [Short title]
**Question:** [The specific question a referee would ask]
**Why it matters:** [Why this could undermine the paper's contribution]
**Evidence needed:** [What analysis or argument would address this]
**Sections affected:** [Which sections/tables are vulnerable]
**Severity:** [CRITICAL / MAJOR / MINOR]

[Repeat for 5-7 challenges]

## Paper's Existing Defenses
[2-3 things the paper already does well to address identification concerns]

## Summary Verdict
**Strengths:** [2-3 things done well]
**Must address before submission:** [0-2 critical changes]
**Should address (referee will ask):** [2-3 major improvements]
```

---

## Principles

- **Be specific:** Reference exact regressions, variable names, table columns
- **Be constructive:** Every challenge has a "evidence needed" to address it
- **Be calibrated:** Not every paper needs an IV — acknowledge when OLS + rich FE is appropriate
- **Think like a referee:** What would make you recommend Reject vs R&R?
- **Prioritize:** Identification threats > specification concerns > external validity
