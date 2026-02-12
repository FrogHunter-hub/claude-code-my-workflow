version 19.5
set more off
capture log close _all

* ============================================================
* Title:   01_setup.do — Data Setup and Variable Construction
* Author:  [Author]
* Date:    2026-02-12
* Purpose: Load cleaned panel from Python pipeline, construct
*          Stata-specific variables, and prepare for regression.
* Inputs:  data_processed/ (panel from 01_clean.py)
* Outputs: data_processed/ (.dta files for Stata analysis)
* ============================================================

log using "logs/01_setup.log", replace

* --- Globals ---
global ROOT "."
global DATA "$ROOT/data"
global PROCESSED "$ROOT/data_processed"
global RESULTS "$ROOT/results"
global LOGS "$ROOT/logs"

* 1. Load Data ----
* TODO: Import cleaned panel from Python pipeline
* use "$PROCESSED/panel.dta", clear

* 2. Variable Construction ----
* TODO: Construct growth orientation (Revenue Growth + Market Expansion + Product Innovation)
* TODO: Construct efficiency orientation (Cost Reduction + Operational Efficiency)
* TODO: Construct disagreement measure (manager vs analyst vectors)

* 3. Sample Restrictions ----
* TODO: Apply sample restrictions
* TODO: Document dropped observations
* count

* 4. Label Variables ----
* TODO: Label all key variables for table output

* 5. Save ----
* TODO: Save constructed dataset
* save "$PROCESSED/panel_stata.dta", replace

log close
