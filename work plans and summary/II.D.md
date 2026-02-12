│ Plan to implement                                                                                                         │
│                                                                                                                           │
│ Plan: Create Table II — Summary Statistics for Panel Construction                                                         │
│                                                                                                                           │
│ Status: DRAFT                                                                                                             │
│ Date: 2026-02-12                                                                                                          │
│ Section: II.D. Panel Construction                                                                                         │
│                                                                                                                           │
│ ---                                                                                                                       │
│ Context                                                                                                                   │
│                                                                                                                           │
│ Section II.D describes the firm–technology–quarter panel and ends with:                                                   │
│ "Table~II reports summary statistics for the resulting panel."                                                            │
│                                                                                                                           │
│ A % TODO comment on line 218 of main.tex confirms this table hasn't been built yet. The task is to (1) write a Python     │
│ script that constructs the panel from raw data and computes summary statistics, and (2) generate a LaTeX table matching   │
│ the existing style in Overleaf/Tables/.                                                                                   │
│                                                                                                                           │
│ Data note: The user referenced Snippets_merged_with_meta.csv, but the actual file on disk is                              │
│ Causal_Snippets_with_Categories.csv (581,449 rows). This file contains cause/effect spans with macro categories. ~47K     │
│ rows have missing macro_id and will be dropped.                                                                           │
│                                                                                                                           │
│ ---                                                                                                                       │
│ Approach                                                                                                                  │
│                                                                                                                           │
│ Step 1: Create Python script src/py/03_table_II_summary_stats.py                                                          │
│                                                                                                                           │
│ Two data sources:                                                                                                         │
│                                                                                                                           │
│ 1. AllTech file (12.6M rows) — data/raw/AllTech_2002-2024_with_LLM_results(with Causal and non-Causal snippets).csv       │
│   - Used for Panel A (technology snippet statistics before causal filtering)                                              │
│   - Key column: identified_technology — valid when not "none" and not null                                                │
│   - Also uses: Year, File (transcript ID, contains ticker), Technology                                                    │
│   - Load only needed columns via usecols to manage 12.6M rows                                                             │
│ 2. Causal snippets file (581K rows) — data/raw/Causal_Snippets_with_Categories.csv                                        │
│   - Used for Panels B–E (causal panel after dedup + threshold)                                                            │
│   - Key cols: gvkey, technology, dateQ, side, input_id, macro_id, macro_name, sic                                         │
│                                                                                                                           │
│ Pipeline for Panel A (technology snippets):                                                                               │
│ 1. Load AllTech with usecols=['identified_technology', 'Year', 'File', 'Technology', 'detailed_causal_analysis']          │
│ 2. Filter to valid technology: identified_technology not in {"none", NaN}                                                 │
│ 3. Count: total snippets in corpus, tech-relevant snippets, unique transcripts (File), unique technologies, year range    │
│ 4. Compute causal ratio: share of tech-relevant snippets with detailed_causal_analysis == "YES"                           │
│ 5. Compute per-transcript snippet distribution                                                                            │
│                                                                                                                           │
│ Pipeline for Panels B–E (causal panel):                                                                                   │
│ 1. Load causal snippets (key cols only)                                                                                   │
│ 2. Drop rows with missing gvkey, dateQ, or macro_id                                                                       │
│ 3. Deduplicate on (gvkey, technology, dateQ, side, input_id, macro_id) — a single statement (input_id) CAN map to         │
│ multiple macro categories, but cannot be counted twice within the same macro category                                     │
│ 4. Collapse to firm–tech–quarter–side–macro counts                                                                        │
│ 5. Pivot to wide: n1..n5, compute N_side, shares share_c = n_c / N_side                                                   │
│ 6. Apply ≥3 threshold per side                                                                                            │
│ 7. Split cause/effect, inner-join on (gvkey, technology, dateQ) → joint panel                                             │
│ 8. Compute N_total, cause_effect_ratio                                                                                    │
│                                                                                                                           │
│ Table structure (5 panels):                                                                                               │
│ ┌─────────────────┬──────────────────────────────────────────────────────────────────────────┬─────────────────────────── │
│ ─┐                                                                                                                        │
│ │      Panel      │                                 Content                                  │         Statistics         │
│  │                                                                                                                        │
│ ├─────────────────┼──────────────────────────────────────────────────────────────────────────┼─────────────────────────── │
│ ─┤                                                                                                                        │
│ │ A. Technology   │ Total snippets in corpus, tech-relevant snippets, causal ratio (share    │ Single numbers +           │
│  │                                                                                                                        │
│ │ snippets        │ with ≥1 causal statement), unique transcripts, unique technologies,      │ Mean/Median for            │
│  │                                                                                                                        │
│ │                 │ sample period, snippets per transcript                                   │ per-transcript             │
│  │                                                                                                                        │
│ ├─────────────────┼──────────────────────────────────────────────────────────────────────────┼─────────────────────────── │
│ ─┤                                                                                                                        │
│ │ B. Causal panel │ Obs count, unique firms, technologies, quarters, obs per firm            │ Single numbers +           │
│  │                                                                                                                        │
│ │  dimensions     │                                                                          │ Mean/Median                │
│  │                                                                                                                        │
│ ├─────────────────┼──────────────────────────────────────────────────────────────────────────┼─────────────────────────── │
│ ─┤                                                                                                                        │
│ │ C. Cause shares │ 5 macro categories                                                       │ Mean, SD, P25, Median, P75 │
│  │                                                                                                                        │
│ ├─────────────────┼──────────────────────────────────────────────────────────────────────────┼─────────────────────────── │
│ ─┤                                                                                                                        │
│ │ D. Effect       │ 5 macro categories                                                       │ Mean, SD, P25, Median, P75 │
│  │                                                                                                                        │
│ │ shares          │                                                                          │                            │
│  │                                                                                                                        │
│ ├─────────────────┼──────────────────────────────────────────────────────────────────────────┼─────────────────────────── │
│ ─┤                                                                                                                        │
│ │ E. Intensity    │ N_total, N_cause, N_effect, cause/effect ratio                           │ Mean, SD, P25, Median, P75 │
│  │                                                                                                                        │
│ │ measures        │                                                                          │                            │
│  │                                                                                                                        │
│ └─────────────────┴──────────────────────────────────────────────────────────────────────────┴─────────────────────────── │
│ ─┘                                                                                                                        │
│ Outputs:                                                                                                                  │
│ - results/tables/table_II_summary_stats.csv — machine-readable stats                                                      │
│ - Overleaf/Tables/summary_stats.tex — LaTeX table for manuscript                                                          │
│ - data_processed/panel_ikt.csv — full panel (reusable downstream)                                                         │
│ - results/runs/03_table_II_<timestamp>.json — run manifest                                                                │
│                                                                                                                           │
│ Step 2: Create LaTeX table Overleaf/Tables/summary_stats.tex                                                              │
│                                                                                                                           │
│ Generated by the Python script. Style matches existing tables:                                                            │
│ - \begin{table}[!htbp]\centering with \hline\hline (matching vardecomp.tex and macroshare.tex)                            │
│ - Panel headers: \multicolumn{N}{l}{\textsc{Panel X. Description}}                                                        │
│ - Notes block: \begin{flushleft}\footnotesize \textit{Notes.} ...                                                         │
│ - \vspace{0.25em} before \end{table}                                                                                      │
│ - Shares: 3 decimal places; counts: comma-separated integers; ratios: 2 decimal places                                    │
│                                                                                                                           │
│ Step 3: Update Overleaf/Tables/alltables.tex                                                                              │
│                                                                                                                           │
│ Insert \input{Tables/summary_stats} before \input{Tables/macroshare}.                                                     │
│                                                                                                                           │
│ Step 4: Remove TODO from Overleaf/main.tex line 218                                                                       │
│                                                                                                                           │
│ Delete the comment % TODO: insert exact panel dimensions once summary-statistics pipeline is finalized.                   │
│                                                                                                                           │
│ ---                                                                                                                       │
│ Files to Create/Modify                                                                                                    │
│ ┌───────────────────────────────────────────┬───────────────────────────────────────────┐                                 │
│ │                   File                    │                  Action                   │                                 │
│ ├───────────────────────────────────────────┼───────────────────────────────────────────┤                                 │
│ │ src/py/03_table_II_summary_stats.py       │ Create — main script (~300 lines)         │                                 │
│ ├───────────────────────────────────────────┼───────────────────────────────────────────┤                                 │
│ │ Overleaf/Tables/summary_stats.tex         │ Create (generated by script)              │                                 │
│ ├───────────────────────────────────────────┼───────────────────────────────────────────┤                                 │
│ │ Overleaf/Tables/alltables.tex             │ Modify — add \input{Tables/summary_stats} │                                 │
│ ├───────────────────────────────────────────┼───────────────────────────────────────────┤                                 │
│ │ Overleaf/main.tex                         │ Modify — remove TODO on line 218          │                                 │
│ ├───────────────────────────────────────────┼───────────────────────────────────────────┤                                 │
│ │ data_processed/panel_ikt.csv              │ Create (generated by script)              │                                 │
│ ├───────────────────────────────────────────┼───────────────────────────────────────────┤                                 │
│ │ results/tables/table_II_summary_stats.csv │ Create (generated by script)              │                                 │
│ └───────────────────────────────────────────┴───────────────────────────────────────────┘                                 │
│ ---                                                                                                                       │
│ Verification                                                                                                              │
│                                                                                                                           │
│ 1. Run conda run -n Technology python src/py/03_table_II_summary_stats.py                                                 │
│ 2. Check that Overleaf/Tables/summary_stats.tex exists and is valid LaTeX                                                 │
│ 3. Panel A: tech-relevant snippets should be a large subset of 12.6M total                                                │
│ 4. Panel B: dimensions should be reasonable (~tens of thousands obs, thousands of firms, 29 techs, ~90 quarters)          │
│ 5. Panels C/D: cause/effect shares should each average to ~1.0 (compositional)                                            │
│ 6. Cross-check against known facts: 197,818 cause + 385,418 effect spans pre-dedup        