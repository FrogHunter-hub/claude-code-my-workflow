---
name: write-section
description: Draft a paper section based on structural notes in the manuscript and empirical results. Follows JF/QJE conventions and runs proofreader on output.
disable-model-invocation: false
argument-hint: "[section number (e.g., 'II') or title (e.g., 'Data and Measurement')]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Edit", "Task"]
---

# Write Paper Section

Draft or expand a section of the manuscript based on the structural notes and available results.

**Input:** `$ARGUMENTS` — a section number (II, III, IV, etc.) or title.

---

## Steps

1. **Read the manuscript** (`Overleaf/main.tex`) to find the target section and its `\note{...}` blocks describing what should go there.

2. **Read supporting materials:**
   - `.claude/rules/manuscript-writing-conventions.md` for JF/QJE style
   - `.claude/rules/knowledge-base-template.md` for notation, taxonomy, and paper progression
   - Relevant results in `results/` (tables, figures, manifests)
   - Methodology docs in `Overleaf/Methodology/` if relevant

3. **Draft the section** following these conventions:
   - JF/QJE prose style (clear, concise, formal)
   - Consistent notation from the knowledge base
   - Proper `\citet{}` / `\citep{}` citations
   - Reference tables and figures by number
   - Define variables on first use
   - Economic intuition before formal specification

4. **Write the draft** into `Overleaf/main.tex` — replacing the `\note{...}` blocks with actual prose while preserving the section structure.

5. **Run the proofreader agent** on the modified section:
   ```
   Launch proofreader agent to review the new section
   ```

6. **Address any High-severity issues** from the proofreader before presenting.

---

## Important

- **Preserve existing content.** If a section has both drafted text and notes, expand the notes without overwriting the drafted text.
- **Be conservative with claims.** Only state what the results support.
- **Use the paper's notation.** Check knowledge-base-template.md before introducing any symbol.
- **Cross-reference.** Verify that "as shown in Table X" actually refers to the correct table.
- **Flag uncertainties.** If you're unsure about a claim or result, add `% TODO: verify` as a LaTeX comment.
