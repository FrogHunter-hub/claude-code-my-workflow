---
name: build-figure
description: Generate a publication-ready figure using matplotlib/seaborn. Follows JF/QJE figure conventions. Saves as PDF and PNG.
disable-model-invocation: true
argument-hint: "[figure description or data path]"
allowed-tools: ["Read", "Bash", "Write", "Glob"]
---

# Build Publication-Ready Figure

Generate a matplotlib/seaborn figure meeting JF/QJE standards.

**Input:** `$ARGUMENTS` — a figure description (e.g., "time series of technology mentions") or a data file path.

---

## Steps

1. **Locate the source data:**
   - Check `data_processed/` and `results/` for relevant data files
   - If no data exists, report what analysis needs to run first

2. **Create a Python plotting script** in `scripts/` following `.claude/rules/python-code-conventions.md`:
   - Import matplotlib, seaborn
   - Set publication style: serif fonts, white background
   - Use project color palette (no default matplotlib colors)
   - Set explicit `figsize` appropriate for journal column width

3. **Generate the figure** with these standards:
   - White background
   - Serif font family (Times / Computer Modern)
   - Axis labels in sentence case with units
   - Legend: bottom or outside, readable at journal size
   - Grid: light gray if needed, or none
   - No chart junk (unnecessary borders, backgrounds, 3D effects)

4. **Save the figure:**
   - PDF (vector): `Figures/figure_[N].pdf`
   - PNG (raster, 300 dpi): `Figures/figure_[N].png`
   - Report: dimensions, file sizes, what the figure shows

5. **Run the script:**
   ```powershell
   conda run -n Technology python scripts/plot_[name].py
   ```

## Important

- **PDF for submission**, PNG for quick viewing and presentations
- All figures must have explicit dimensions (no auto-sizing)
- Match font size to paper body text when printed
- Include data source in caption or notes
- For multi-panel figures: use `plt.subplot()` with consistent formatting
