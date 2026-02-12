---
name: proofread
description: Run the proofreading protocol on manuscript files. Checks grammar, typos, LaTeX issues, notation consistency, and academic writing quality. Produces a report without editing files.
disable-model-invocation: true
argument-hint: "[filename or 'all' or section number]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Task"]
---

# Proofread Manuscript Files

Run the proofreading protocol on LaTeX manuscript files. This produces a report of all issues found WITHOUT editing any source files.

## Steps

1. **Identify files to review:**
   - If `$ARGUMENTS` is a specific filename: review that file only
   - If `$ARGUMENTS` is a section number (e.g., "II"): find that section in `Overleaf/main.tex`
   - If `$ARGUMENTS` is "all": review all `.tex` files in `Overleaf/`

2. **For each file, launch the proofreader agent** that checks for:

   **GRAMMAR:** Subject-verb agreement, articles (a/an/the), prepositions, tense consistency
   **TYPOS:** Misspellings, search-and-replace artifacts, duplicated words
   **LATEX ISSUES:** Overfull hbox, undefined citations, orphaned refs/labels
   **NOTATION:** Consistent subscripts (i, k, t, s), symbol definitions, share conventions
   **SECTION STRUCTURE:** Roman numeral numbering, table/figure numbering, cross-references
   **ACADEMIC QUALITY:** Informal language, unsupported claims, jargon without definition

3. **Produce a detailed report** for each file listing every finding with:
   - Location (section title or line number)
   - Current text (what's wrong)
   - Proposed fix (what it should be)
   - Category and severity

4. **Save each report** to `quality_reports/[FILENAME]_proofread_report.md`

5. **IMPORTANT: Do NOT edit any source files.**
   Only produce the report. Fixes are applied separately after user review.

6. **Present summary** to the user:
   - Total issues found per file
   - Breakdown by category
   - Most critical issues highlighted
