---
name: compile-latex
description: Compile the LaTeX manuscript with pdflatex (3 passes + bibtex). Use when compiling the paper.
disable-model-invocation: true
argument-hint: "[filename without .tex extension, default: 'main']"
allowed-tools: ["Read", "Bash", "Glob"]
---

# Compile LaTeX Manuscript

Compile the manuscript using pdflatex with full citation resolution.

## Steps

1. **Navigate to Overleaf/ directory** and compile with 3-pass sequence:

```powershell
cd Overleaf
pdflatex -interaction=nonstopmode $ARGUMENTS.tex
bibtex $ARGUMENTS
pdflatex -interaction=nonstopmode $ARGUMENTS.tex
pdflatex -interaction=nonstopmode $ARGUMENTS.tex
```

If `$ARGUMENTS` is empty, default to `main`.

2. **Check for warnings:**
   - Grep output for `Overfull \\hbox` warnings — count them
   - Grep for `undefined citations` or `Label(s) may have changed`
   - Report any issues found

3. **Report results:**
   - Compilation success/failure
   - Number of overfull hbox warnings
   - Any undefined citations
   - PDF page count

## Why 3 passes?
1. First pdflatex: Creates `.aux` file with citation keys
2. bibtex: Reads `.aux`, generates `.bbl` with formatted references
3. Second pdflatex: Incorporates bibliography
4. Third pdflatex: Resolves all cross-references with final page numbers

## Important
- Use **pdflatex** (not xelatex) — matches Overleaf's default compiler
- Bibliography file is `references.bib` in the same directory
- No special `TEXINPUTS` needed — all files are in `Overleaf/`
