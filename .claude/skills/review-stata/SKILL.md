---
name: review-stata
description: Run the Stata code review protocol on do-files. Checks specification correctness, merge protocols, clustering, and reproducibility. Produces a report without editing files.
disable-model-invocation: true
argument-hint: "[filename, path pattern, or 'all']"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Task"]
---

# Review Stata Do-Files

Run the comprehensive Stata code review protocol.

## Steps

1. **Identify do-files to review:**
   - If `$ARGUMENTS` is a specific `.do` filename: review that file only
   - If `$ARGUMENTS` is a directory (e.g., `src/stata/`): review all `.do` files in it
   - If `$ARGUMENTS` is `all`: review all Stata do-files in `src/stata/`

2. **For each do-file, launch the `stata-reviewer` agent** with instructions to:
   - Follow the full protocol in the agent instructions
   - Read `.claude/rules/stata-code-conventions.md` for current standards
   - Read `.claude/rules/knowledge-base-template.md` for domain pitfalls
   - Save report to `quality_reports/[script_name]_stata_review.md`

3. **After all reviews complete**, present a summary:
   - Total issues found per script
   - Breakdown by severity (Critical / High / Medium / Low)
   - Top 3 most critical issues

4. **IMPORTANT: Do NOT edit any Stata source files.**
   Only produce reports. Fixes are applied after user review.
