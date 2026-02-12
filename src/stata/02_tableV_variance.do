/********************************************************************
Table V — Hassan-style Variance Decomposition (Hassan et al. 2019 Table VIII style)
+ ADDITION: Technology FE (main effect), on top of Technology × Time FE.

This script is workflow-adapted for:
- Windows + PowerShell
- Repo-relative paths
- Outputs to results/ and syncs final LaTeX to Overleaf/inputs/

Inputs (priority order):
1) data_processed/vd_panel.dta  (preferred: already aggregated with share1-share5)
2) data/raw/Snippets_merged_with_meta.csv  (fallback)
3) Environment variable VD_INPUT_CSV (absolute path to CSV)

Outputs:
- logs/02_tableV_variance.log
- results/variance_decomp/vd_hassanlike_results.dta
- results/variance_decomp/vd_hassanlike_results_withmean.dta
- results/variance_decomp/vd_{side}_{share}.tex (debug/appendix)
- results/tables/table_V.csv
- results/tables/table_V.tex   (FINAL; copied to Overleaf/inputs/table_V.tex)
- results/runs/stata_02_tableV_variance_<timestamp>.json

Decomposition logic:
Nested FE projections with incremental R^2 shares that sum to 100%.
All models estimated on the SAME sample as the most saturated model (via e(sample)).
********************************************************************/

clear all
set more off
version 19.5
set maxvar 32767
capture log close _all

*=========================
* 0) Repo paths (assumes you run from repo root)
*=========================
local ROOT "`c(pwd)'"

* Basic sanity check: we expect to see src/stata in repo root
if !fileexists("`ROOT'\src\stata\02_tableV_variance.do") {
    di as error "ERROR: Please run Stata from the repo root directory."
    di as error "Current c(pwd) = `ROOT'"
    exit 198
}

local LOGDIR     "`ROOT'\logs"
local RESULTSDIR "`ROOT'\results"
local VDOUT      "`RESULTSDIR'\variance_decomp"
local TABLEDIR   "`RESULTSDIR'\tables"
local RUNSDIR    "`RESULTSDIR'\runs"
local OVERLEAFIN "`ROOT'\Overleaf\inputs"

capture mkdir "`LOGDIR'"
capture mkdir "`RESULTSDIR'"
capture mkdir "`VDOUT'"
capture mkdir "`TABLEDIR'"
capture mkdir "`RUNSDIR'"
capture mkdir "`OVERLEAFIN'"

log using "`LOGDIR'\02_tableV_variance.log", replace text
*=========================
* Column labels — must match macro_id -> macro_name in raw CSV
* Source of truth: Causal_Snippets_with_Categories.csv (macro_id, macro_name)
* Validated by: src/py/03_table_II_summary_stats.py
*=========================
local CAUSE1  "Technology Innovation and Advancement"
local CAUSE2  "Market Demand and Consumer Behavior"
local CAUSE3  "Regulatory and Policy Drivers"
local CAUSE4  "Strategic Partnerships and Investment"
local CAUSE5  "Cost and Economic Viability"

local EFFECT1 "Revenue and Financial Growth"
local EFFECT2 "Cost Reduction and Efficiency"
local EFFECT3 "Market Expansion and Adoption"
local EFFECT4 "Product and Service Innovation"
local EFFECT5 "Operational Efficiency and Automation"

* Escape LaTeX special chars in labels (basic)
foreach L in CAUSE1 CAUSE2 CAUSE3 CAUSE4 CAUSE5 EFFECT1 EFFECT2 EFFECT3 EFFECT4 EFFECT5 {
    local `L' = subinstr("``L''", "&", "\&", .)
    local `L' = subinstr("``L''", "%", "\%", .)
    local `L' = subinstr("``L''", "_", "\_", .)
}

*=========================
* 1) Input configuration
*=========================
local PANEL_DTA "`ROOT'\data_processed\vd_panel.dta"
local RAW_CSV   "`ROOT'\data\raw\Snippets_merged_with_meta.csv"

* Environment override (absolute path)
local ENV_CSV : environment VD_INPUT_CSV
if "`ENV_CSV'" != "" {
    local RAW_CSV "`ENV_CSV'"
}

*=========================
* 2) Load data
*=========================
local INPUT_USED ""

if fileexists("`PANEL_DTA'") {
    use "`PANEL_DTA'", clear
    local INPUT_USED "data_processed/vd_panel.dta"
}
else if fileexists("`RAW_CSV'") {
    import delimited "`RAW_CSV'", clear varnames(1)
    local INPUT_USED "`RAW_CSV'"
}
else {
    di as error "ERROR: No input found."
    di as error "Expected either:"
    di as error "  - `PANEL_DTA'"
    di as error "  - `RAW_CSV' (or set VD_INPUT_CSV env var)"
    exit 198
}

*=========================
* 3) Harmonize names & types
*=========================
capture confirm variable side
if _rc {
    di as error "ERROR: Required variable 'side' not found."
    exit 459
}
replace side = lower(trim(side)) if !missing(side)

* Technology name — force short name so it won't clash with tech_id / tech_time
capture rename technology tech

* Time variable: prefer dateQ
capture confirm variable dateq
if !_rc {
    capture confirm variable dateQ
    if _rc rename dateq dateQ
}

* Required vars checks (minimum needed for either branch)
capture confirm variable gvkey
if _rc {
    di as error "ERROR: Required variable 'gvkey' not found."
    exit 459
}
capture confirm variable sic
if _rc {
    di as error "ERROR: Required variable 'sic' not found."
    exit 459
}
capture confirm variable macro_id
if _rc {
    di as error "ERROR: Required variable 'macro_id' not found."
    exit 459
}
capture confirm variable tech
if _rc {
    di as error "ERROR: Required variable 'tech' not found."
    exit 459
}
capture confirm variable dateQ
if _rc {
    di as error "ERROR: Required variable 'dateQ' not found."
    exit 459
}

* Convert types (safe)
capture destring macro_id, replace
capture destring sic, replace force
capture confirm numeric variable gvkey
if _rc {
    capture destring gvkey, replace force
}

*=========================
* 4) Keep usable rows
*=========================
keep if inlist(side,"cause","effect")
drop if missing(macro_id) | missing(gvkey) | missing(tech) | missing(dateQ) | missing(sic)

*=========================
* 5) Build shares if needed
*    If share1-share5 already exist, we keep them.
*=========================
capture confirm variable share1
if _rc {
    * We need input_id to deduplicate at snippet level
    capture confirm variable input_id
    if _rc {
        di as error "ERROR: share1 not found AND input_id not found. Cannot build shares."
        di as error "Provide data_processed/vd_panel.dta with share1-share5, or a raw CSV with input_id."
        exit 459
    }

    * Deduplicate within firm×tech×time×side×input_id×macro_id
    duplicates drop gvkey tech dateQ side input_id macro_id, force

    gen one = 1

    * Collapse to firm×tech×time×side×macro_id×sic
    collapse (sum) n=one, by(gvkey tech dateQ side macro_id sic)

    * Wide counts n1..n5
    reshape wide n, i(gvkey tech dateQ side sic) j(macro_id)

    * Ensure n1..n5 exist and replace missing with 0
    foreach m of numlist 1/5 {
        capture confirm variable n`m'
        if _rc gen n`m' = 0
        replace n`m' = 0 if missing(n`m')
    }

    egen N = rowtotal(n1 n2 n3 n4 n5)
    drop if N==0

    foreach m of numlist 1/5 {
        gen share`m' = n`m' / N
    }

    * Minimum evidence threshold (can edit)
    local MIN_N = 3
    drop if N < `MIN_N'
}
else {
    * If shares exist, ensure we have share1-share5
    foreach m of numlist 1/5 {
        capture confirm variable share`m'
        if _rc {
            di as error "ERROR: share`m' missing. Need share1-share5."
            exit 459
        }
    }
}

*=========================
* 6) Industry definitions (SIC 2/3/4-digit)
*=========================
gen sic2 = floor(sic/100)
gen sic3 = floor(sic/10)
gen sic4 = sic

*=========================
* 7) IDs for absorbing fixed effects
*=========================
egen firm_id   = group(gvkey)        // firm FE id
egen time_id   = group(dateQ)        // time FE id (quarter)
egen tech_id   = group(tech)         // technology FE id
egen tech_time = group(tech dateQ)   // technology × time FE id

*=========================
* 8) Check reghdfe availability
*=========================
cap which reghdfe
if _rc {
    di as error "ERROR: reghdfe not found. Install it in your Stata environment:"
    di as error "  ssc install reghdfe, replace"
    di as error "Also ensure ftools is installed if prompted."
    exit 199
}

* Save prepared panel to tempfile for clean reload inside loops
tempfile panel
save `panel', replace

*=========================
* 9) Hassan-style variance decomposition (now with Technology FE)
*=========================
tempfile vdres
tempname ph

postfile `ph' ///
    str6  side ///
    str8  indvar ///
    str10 yname ///
    double timeFE indFE indTimeFE techFE techTimeFE firmLevel firmFE residFE ///
    double r2_M1 r2_M2 r2_M3 r2_M4 r2_M5 r2_M6 ///
    long   Nobs ///
    int    Nsectors ///
    using `vdres', replace

foreach SIDE in cause effect {

    use `panel', clear
    keep if side=="`SIDE'"

    foreach INDVAR in sic2 sic3 sic4 {

        * Build industry ids for this granularity
        capture drop ind_id ind_time
        egen ind_id   = group(`INDVAR')
        egen ind_time = group(`INDVAR' dateQ)

        foreach y of varlist share1-share5 {

            *------------------------------------------------------------
            * Step 0: Run the most saturated model FIRST to define sample
            * M6: Industry×Time + Tech×Time + Firm
            *------------------------------------------------------------
            capture drop __smp
            reghdfe `y', absorb(ind_time tech_time firm_id)
            local r2_6 = e(r2)
            gen byte __smp = e(sample)

            quietly count if __smp==1
            local N = r(N)

            * Count number of industries in the M6 estimation sample
            preserve
                keep if __smp==1
                bysort `INDVAR': gen byte __tag = (_n==1)
                quietly count if __tag==1
                local NS = r(N)
                drop __tag
            restore

            *------------------------------------------------------------
            * M5: Industry×Time + Tech×Time (no firm FE)
            *------------------------------------------------------------
            reghdfe `y' if __smp==1, absorb(ind_time tech_time)
            local r2_5 = e(r2)

            *------------------------------------------------------------
            * M4: Industry×Time + Tech FE
            *------------------------------------------------------------
            reghdfe `y' if __smp==1, absorb(ind_time tech_id)
            local r2_4 = e(r2)

            *------------------------------------------------------------
            * M3: Industry×Time only
            *------------------------------------------------------------
            reghdfe `y' if __smp==1, absorb(ind_time)
            local r2_3 = e(r2)

            *------------------------------------------------------------
            * M2: Time + Industry
            *------------------------------------------------------------
            reghdfe `y' if __smp==1, absorb(time_id ind_id)
            local r2_2 = e(r2)

            *------------------------------------------------------------
            * M1: Time only
            *------------------------------------------------------------
            reghdfe `y' if __smp==1, absorb(time_id)
            local r2_1 = e(r2)

            *------------------------------------------------------------
            * Convert to Hassan-style variance shares (% of total variance)
            *------------------------------------------------------------
            local sh_time     = 100*(`r2_1')
            local sh_ind      = 100*(`r2_2' - `r2_1')
            local sh_indtime  = 100*(`r2_3' - `r2_2')
            local sh_tech     = 100*(`r2_4' - `r2_3')
            local sh_techtime = 100*(`r2_5' - `r2_4')
            local sh_firmlev  = 100*(1 - `r2_5')
            local sh_firm     = 100*(`r2_6' - `r2_5')
            local sh_resid    = 100*(1 - `r2_6')

            * Guard against tiny negative numbers from numerical precision
            foreach z in sh_time sh_ind sh_indtime sh_tech sh_techtime sh_firmlev sh_firm sh_resid {
                if ``z'' < 0 & ``z'' > -1e-8 local `z' = 0
            }

            post `ph' ///
                ("`SIDE'") ("`INDVAR'") ("`y'") ///
                (`sh_time') (`sh_ind') (`sh_indtime') (`sh_tech') (`sh_techtime') ///
                (`sh_firmlev') (`sh_firm') (`sh_resid') ///
                (`r2_1') (`r2_2') (`r2_3') (`r2_4') (`r2_5') (`r2_6') ///
                (`N') (`NS')

            drop __smp
        }
    }
}

postclose `ph'

use `vdres', clear
save "`VDOUT'\vd_hassanlike_results.dta", replace

*=========================
* 10) Add mean-across-shares rows (component-wise mean across share1..share5)
*=========================
preserve
    use "`VDOUT'\vd_hassanlike_results.dta", clear
    collapse (mean) timeFE indFE indTimeFE techFE techTimeFE firmLevel firmFE residFE ///
             (mean) r2_M1 r2_M2 r2_M3 r2_M4 r2_M5 r2_M6 ///
             (first) Nobs Nsectors, by(side indvar)
    gen str10 yname = "mean"
    tempfile vdmean
    save `vdmean', replace
restore

use "`VDOUT'\vd_hassanlike_results.dta", clear
append using `vdmean'
save "`VDOUT'\vd_hassanlike_results_withmean.dta", replace

*=========================
* 11) Export per-side tables (debug / appendix)
*=========================
use "`VDOUT'\vd_hassanlike_results_withmean.dta", clear
local fmt "%6.2f"

foreach SIDE in cause effect {
    foreach Y in share1 share2 share3 share4 share5 mean {

        preserve
            keep if side=="`SIDE'" & yname=="`Y'"

            keep side yname indvar ///
                timeFE indFE indTimeFE techFE techTimeFE firmLevel firmFE residFE ///
                Nsectors Nobs

            duplicates drop side yname indvar, force

            reshape wide ///
                timeFE indFE indTimeFE techFE techTimeFE firmLevel firmFE residFE Nsectors Nobs, ///
                i(side yname) j(indvar) string

            local outfile "`VDOUT'\vd_`SIDE'_`Y'.tex"

            local SideTitle = cond("`SIDE'"=="cause","Cause","Effect")
            local YTitle    = cond("`Y'"=="mean","(Mean across shares)","(`Y')")
            local title     "Variance Decomposition of Causal Framework Shares: `SideTitle' `YTitle'"
            local label     "tab:vd_`SIDE'_`Y'"

            * Format numbers (percent rows)
            local t2  = trim(string(timeFEsic2[1], "`fmt'"))
            local t3  = trim(string(timeFEsic3[1], "`fmt'"))
            local t4  = trim(string(timeFEsic4[1], "`fmt'"))

            local s2  = trim(string(indFEsic2[1], "`fmt'"))
            local s3  = trim(string(indFEsic3[1], "`fmt'"))
            local s4  = trim(string(indFEsic4[1], "`fmt'"))

            local st2 = trim(string(indTimeFEsic2[1], "`fmt'"))
            local st3 = trim(string(indTimeFEsic3[1], "`fmt'"))
            local st4 = trim(string(indTimeFEsic4[1], "`fmt'"))

            local te2 = trim(string(techFEsic2[1], "`fmt'"))
            local te3 = trim(string(techFEsic3[1], "`fmt'"))
            local te4 = trim(string(techFEsic4[1], "`fmt'"))

            local tt2 = trim(string(techTimeFEsic2[1], "`fmt'"))
            local tt3 = trim(string(techTimeFEsic3[1], "`fmt'"))
            local tt4 = trim(string(techTimeFEsic4[1], "`fmt'"))

            local fl2 = trim(string(firmLevelsic2[1], "`fmt'"))
            local fl3 = trim(string(firmLevelsic3[1], "`fmt'"))
            local fl4 = trim(string(firmLevelsic4[1], "`fmt'"))

            local f2  = trim(string(firmFEsic2[1], "`fmt'"))
            local f3  = trim(string(firmFEsic3[1], "`fmt'"))
            local f4  = trim(string(firmFEsic4[1], "`fmt'"))

            local r2  = trim(string(residFEsic2[1], "`fmt'"))
            local r3  = trim(string(residFEsic3[1], "`fmt'"))
            local r4  = trim(string(residFEsic4[1], "`fmt'"))

            local nsec2 = trim(string(Nsectorssic2[1], "%9.0f"))
            local nsec3 = trim(string(Nsectorssic3[1], "%9.0f"))
            local nsec4 = trim(string(Nsectorssic4[1], "%9.0f"))

            local nobs2 = trim(string(Nobssic2[1], "%12.0f"))
            local nobs3 = trim(string(Nobssic3[1], "%12.0f"))
            local nobs4 = trim(string(Nobssic4[1], "%12.0f"))

            tempname fh
            file open `fh' using "`outfile'", write replace text

            file write `fh' "\begin{table}[!htbp]\centering" _n
            file write `fh' "\caption{`title'}" _n
            file write `fh' "\label{`label'}" _n
            file write `fh' "\begin{tabular}{lccc}" _n
            file write `fh' "\toprule" _n
            file write `fh' "Industry granularity & 2-digit SIC & 3-digit SIC & 4-digit SIC \\\\" _n
            file write `fh' " & (1) & (2) & (3) \\\\" _n
            file write `fh' "\midrule" _n

            file write `fh' "Time FE & `t2'\% & `t3'\% & `t4'\% \\\\" _n
            file write `fh' "Industry FE & `s2'\% & `s3'\% & `s4'\% \\\\" _n
            file write `fh' "Industry $\times$ time FE & `st2'\% & `st3'\% & `st4'\% \\\\" _n
            file write `fh' "Technology FE & `te2'\% & `te3'\% & `te4'\% \\\\" _n
            file write `fh' "Technology $\times$ time FE & `tt2'\% & `tt3'\% & `tt4'\% \\\\" _n
            file write `fh' "Firm-level & `fl2'\% & `fl3'\% & `fl4'\% \\\\" _n
            file write `fh' "Permanent differences across firms (Firm FE) & `f2'\% & `f3'\% & `f4'\% \\\\" _n
            file write `fh' "Time-varying firm component (residual) & `r2'\% & `r3'\% & `r4'\% \\\\" _n
            file write `fh' "Number of industries & `nsec2' & `nsec3' & `nsec4' \\\\" _n
            file write `fh' "Observations & `nobs2' & `nobs3' & `nobs4' \\\\" _n

            file write `fh' "\bottomrule" _n
            file write `fh' "\end{tabular}" _n
            file write `fh' "\begin{minipage}{0.95\linewidth}\footnotesize" _n
            file write `fh' "Notes: Incremental \(R^2\) decomposition using nested fixed-effect projections (Hassan et al., 2019). "
            file write `fh' "All components are computed on the same estimation sample as the most saturated model using \texttt{e(sample)}. "
            file write `fh' "We include a Technology FE block in addition to Technology $\times$ Time fixed effects." _n
            file write `fh' "\end{minipage}" _n
            file write `fh' "\end{table}" _n

            file close `fh'
            di as txt "Saved LaTeX table: `outfile'"
        restore
    }
}

*=========================
* 12) Export Table V in requested format:
* Panel A: 5 cause columns (share1..share5 with cause names)
* Panel B: 5 effect columns (share1..share5 with effect names)
*=========================

local INDVAR_FOR_TABLE "sic4"          // CHANGE TO "sic2" or "sic3" if desired
local fmt "%6.2f"

* Paths
local OUT_TEX_RESULTS "`TABLEDIR'\vardecomp.tex"
local OUT_TEX_OVERLEAF "`ROOT'\Overleaf\Tables\vardecomp.tex"
capture mkdir "`ROOT'\Overleaf\Tables"

use "`VDOUT'\vd_hassanlike_results_withmean.dta", clear

* We want per-share columns, not the mean row
keep if indvar=="`INDVAR_FOR_TABLE'"
keep if inlist(yname,"share1","share2","share3","share4","share5")
drop r2_M1 r2_M2 r2_M3 r2_M4 r2_M5 r2_M6   // not needed; vary across yname

* Reshape to wide: columns become share1..share5
reshape wide ///
    timeFE indFE indTimeFE techFE techTimeFE firmLevel firmFE residFE Nsectors Nobs, ///
    i(side indvar) j(yname) string

* Helper locals: formatted values for each side and each share
* NOTE: values are already in percent units (0..100).
foreach SIDE in cause effect {

    preserve
        keep if side=="`SIDE'"
        if _N!=1 {
            di as error "ERROR: Unexpected number of rows after reshape for side=`SIDE' (expected 1)."
            exit 459
        }

        foreach s in share1 share2 share3 share4 share5 {

            local `SIDE'_time_`s'     = trim(string(timeFE`s'[1], "`fmt'"))
            local `SIDE'_ind_`s'      = trim(string(indFE`s'[1], "`fmt'"))
            local `SIDE'_indtime_`s'  = trim(string(indTimeFE`s'[1], "`fmt'"))
            local `SIDE'_tech_`s'     = trim(string(techFE`s'[1], "`fmt'"))
            local `SIDE'_techtime_`s' = trim(string(techTimeFE`s'[1], "`fmt'"))
            local `SIDE'_firmlev_`s'  = trim(string(firmLevel`s'[1], "`fmt'"))
            local `SIDE'_firm_`s'     = trim(string(firmFE`s'[1], "`fmt'"))
            local `SIDE'_resid_`s'    = trim(string(residFE`s'[1], "`fmt'"))

            * Counts can differ across shares because e(sample) differs by y
            local `SIDE'_nsec_`s'     = trim(string(Nsectors`s'[1], "%9.0f"))
            local `SIDE'_nobs_`s'     = trim(string(Nobs`s'[1], "%12.0f"))
        }
    restore
}

* Write LaTeX (match your style: flushleft notes, tabfont, hlinehline)
tempname fh
file open `fh' using "`OUT_TEX_RESULTS'", write replace text

file write `fh' "\begin{table}[!htbp]\centering" _n
file write `fh' "\caption{Variance Decomposition of Macro Shares}" _n
file write `fh' "\label{tab:vd_macroshares}" _n
file write `fh' "\begin{flushleft}\footnotesize" _n
file write `fh' "\textit{Notes.} This table reports the incremental \(R^{2}\) shares from projecting the firm--technology--quarter macro-share outcomes on nested sets of fixed effects (Hassan et al. style). "
file write `fh' "Columns in Panel A correspond to the five \emph{cause} macro categories; columns in Panel B correspond to the five \emph{effect} macro categories. "
file write `fh' "Industry granularity is fixed at `INDVAR_FOR_TABLE'. "
file write `fh' "All components are computed on the same estimation sample as the most saturated model using \texttt{e(sample)}." _n
file write `fh' "\end{flushleft}" _n
file write `fh' "\tabfont" _n
file write `fh' "\begin{tabular}{lccccc}" _n
file write `fh' "\hline\hline" _n

* Panel A header (cause names)
file write `fh' "\multicolumn{6}{l}{\textsc{Panel A. Cause}}\\ " _n
file write `fh' " & `CAUSE1' & `CAUSE2' & `CAUSE3' & `CAUSE4' & `CAUSE5' \\\\" _n
file write `fh' " & (1) & (2) & (3) & (4) & (5) \\\\" _n
file write `fh' "\hline" _n

file write `fh' "Time FE & `cause_time_share1'\% & `cause_time_share2'\% & `cause_time_share3'\% & `cause_time_share4'\% & `cause_time_share5'\% \\\\" _n
file write `fh' "Industry FE & `cause_ind_share1'\% & `cause_ind_share2'\% & `cause_ind_share3'\% & `cause_ind_share4'\% & `cause_ind_share5'\% \\\\" _n
file write `fh' "Industry $\times$ time FE & `cause_indtime_share1'\% & `cause_indtime_share2'\% & `cause_indtime_share3'\% & `cause_indtime_share4'\% & `cause_indtime_share5'\% \\\\" _n
file write `fh' "Technology FE & `cause_tech_share1'\% & `cause_tech_share2'\% & `cause_tech_share3'\% & `cause_tech_share4'\% & `cause_tech_share5'\% \\\\" _n
file write `fh' "Technology $\times$ time FE & `cause_techtime_share1'\% & `cause_techtime_share2'\% & `cause_techtime_share3'\% & `cause_techtime_share4'\% & `cause_techtime_share5'\% \\\\" _n
file write `fh' _char(96) _char(96) "Firm-level" _char(39) _char(39) " & `cause_firmlev_share1'\% & `cause_firmlev_share2'\% & `cause_firmlev_share3'\% & `cause_firmlev_share4'\% & `cause_firmlev_share5'\% \\\\" _n
file write `fh' "\quad \parbox[t]{0.62\linewidth}{Permanent differences across firms\\within industries (Firm FE)} & `cause_firm_share1'\% & `cause_firm_share2'\% & `cause_firm_share3'\% & `cause_firm_share4'\% & `cause_firm_share5'\% \\\\" _n
file write `fh' "\quad \parbox[t]{0.62\linewidth}{Time-varying firm component\\(residual)} & `cause_resid_share1'\% & `cause_resid_share2'\% & `cause_resid_share3'\% & `cause_resid_share4'\% & `cause_resid_share5'\% \\\\" _n
file write `fh' "Number of industries & `cause_nsec_share1' & `cause_nsec_share2' & `cause_nsec_share3' & `cause_nsec_share4' & `cause_nsec_share5' \\\\" _n

file write `fh' "\hline" _n

* Panel B header (effect names)
file write `fh' "\multicolumn{6}{l}{\textsc{Panel B. Effect}}\\ " _n
file write `fh' " & `EFFECT1' & `EFFECT2' & `EFFECT3' & `EFFECT4' & `EFFECT5' \\\\" _n
file write `fh' " & (1) & (2) & (3) & (4) & (5) \\\\" _n
file write `fh' "\hline" _n

file write `fh' "Time FE & `effect_time_share1'\% & `effect_time_share2'\% & `effect_time_share3'\% & `effect_time_share4'\% & `effect_time_share5'\% \\\\" _n
file write `fh' "Industry FE & `effect_ind_share1'\% & `effect_ind_share2'\% & `effect_ind_share3'\% & `effect_ind_share4'\% & `effect_ind_share5'\% \\\\" _n
file write `fh' "Industry $\times$ time FE & `effect_indtime_share1'\% & `effect_indtime_share2'\% & `effect_indtime_share3'\% & `effect_indtime_share4'\% & `effect_indtime_share5'\% \\\\" _n
file write `fh' "Technology FE & `effect_tech_share1'\% & `effect_tech_share2'\% & `effect_tech_share3'\% & `effect_tech_share4'\% & `effect_tech_share5'\% \\\\" _n
file write `fh' "Technology $\times$ time FE & `effect_techtime_share1'\% & `effect_techtime_share2'\% & `effect_techtime_share3'\% & `effect_techtime_share4'\% & `effect_techtime_share5'\% \\\\" _n
file write `fh' _char(96) _char(96) "Firm-level" _char(39) _char(39) " & `effect_firmlev_share1'\% & `effect_firmlev_share2'\% & `effect_firmlev_share3'\% & `effect_firmlev_share4'\% & `effect_firmlev_share5'\% \\\\" _n
file write `fh' "\quad \parbox[t]{0.62\linewidth}{Permanent differences across firms\\within industries (Firm FE)} & `effect_firm_share1'\% & `effect_firm_share2'\% & `effect_firm_share3'\% & `effect_firm_share4'\% & `effect_firm_share5'\% \\\\" _n
file write `fh' "\quad \parbox[t]{0.62\linewidth}{Time-varying firm component\\(residual)} & `effect_resid_share1'\% & `effect_resid_share2'\% & `effect_resid_share3'\% & `effect_resid_share4'\% & `effect_resid_share5'\% \\\\" _n
file write `fh' "Number of industries & `effect_nsec_share1' & `effect_nsec_share2' & `effect_nsec_share3' & `effect_nsec_share4' & `effect_nsec_share5' \\\\" _n

file write `fh' "\hline\hline" _n
file write `fh' "\end{tabular}" _n
file write `fh' "" _n
file write `fh' "\vspace{0.25em}" _n
file write `fh' "\end{table}" _n

file close `fh'
di as txt "Saved LaTeX table (results): `OUT_TEX_RESULTS'"

* Copy to Overleaf target path
copy "`OUT_TEX_RESULTS'" "`OUT_TEX_OVERLEAF'", replace
di as txt "Synced LaTeX table (Overleaf): `OUT_TEX_OVERLEAF'"

log close
exit 0
