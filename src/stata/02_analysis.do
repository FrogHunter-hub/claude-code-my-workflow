version 19.5
set more off
capture log close _all

* ============================================================
* Title:   02_analysis.do — Main Regression Analysis
* Author:  [Author]
* Date:    2026-02-12
* Purpose: Run panel regressions for Sections IV–VI of the paper.
*          Variance decomposition, beliefs→actions, misallocation.
* Inputs:  data_processed/panel_stata.dta (from 01_setup.do)
* Outputs: results/ (.tex and .csv tables), Figures/ (.pdf figures)
* ============================================================

log using "logs/02_analysis.log", replace

* --- Globals ---
global ROOT "."
global PROCESSED "$ROOT/data_processed"
global RESULTS "$ROOT/results"
global FIGURES "$ROOT/Figures"

* 1. Load Data ----
* TODO: use "$PROCESSED/panel_stata.dta", clear

* 2. Table V: Variance Decomposition ----
* TODO: Decompose cause/effect share variation
* TODO: Firm FE, technology FE, time FE, industry FE
* TODO: Report within-group R-squared

* 3. Tables VI–VIII: Beliefs and Firm Actions ----
* TODO: reghdfe [outcome] [cause_shares], absorb(tech#industry#quarter) cluster(firm_id)
* TODO: Growth orientation vs efficiency orientation
* TODO: Cause-side theories and strategic choices

* 4. Tables IX–X: Beliefs and Misallocation ----
* TODO: Ex post benchmarking
* TODO: Cross-technology belief transfer

* 5. Export Tables ----
* TODO: esttab using "$RESULTS/table_V.tex", replace booktabs
* TODO: esttab using "$RESULTS/table_V.csv", replace

log close
