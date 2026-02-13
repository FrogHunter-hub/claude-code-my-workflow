"""
04_table_IIIA_top_scoring.py — Face Validity: Top-Scoring Transcripts

Purpose: For Section III.A, document all 29 technologies with one
         Technology Innovation ("tech-push") snippet and one Market Demand
         ("demand-pull") snippet each, using the complete sent_window
         from the raw transcript. Only selects snippets where the content
         clearly maps to the assigned macro category.

Inputs:  data/raw/Causal_Snippets_with_Categories.csv
         data/raw/AllTech_2002-2024_with_LLM_results(with Causal and non-Causal snippets).csv

Outputs: results/tables/table_IIIA_top_scoring.csv
         Overleaf/Appendix/top_scoring_transcripts.tex
         results/runs/04_table_IIIA_<timestamp>.json
"""

from pathlib import Path
import json
import datetime
import os
import random

import pandas as pd
import numpy as np

SEED = 42
ROOT = Path(__file__).resolve().parents[2]

random.seed(SEED)
np.random.seed(SEED)

# --- Scoring parameters (recorded in manifest for reproducibility) ---
SCORE_PHRASE_FOUND = 100       # base reward for verbatim phrase match
SCORE_KW_HIT = 15             # per category-confirming keyword
SCORE_ANTI_KW_PENALTY = 30    # per contradicting keyword (2x reward)
SCORE_WINDOW_SWEETSPOT = 20   # bonus for window length in [WINDOW_LEN_MIN, WINDOW_LEN_MAX]
SCORE_PHRASE_LEN_CAP = 80     # max contribution from phrase length
SCORE_MANUAL_BOOST = 1000     # manual override boost
WINDOW_LEN_MIN = 100
WINDOW_LEN_MAX = 600

# 0. Setup ----
os.makedirs(ROOT / "results" / "tables", exist_ok=True)
os.makedirs(ROOT / "results" / "runs", exist_ok=True)
os.makedirs(ROOT / "Overleaf" / "Appendix", exist_ok=True)

MACRO_LABELS = {
    1: "Technology Innovation and Advancement",
    2: "Market Demand and Consumer Behavior",
}


def escape_latex(text):
    """Escape LaTeX special characters in transcript text."""
    if not isinstance(text, str):
        return ""
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


# ================================================================
# 1. Load cause-side snippets for macro categories 1 and 2
# ================================================================
print("Loading Causal_Snippets_with_Categories.csv...")
snippets = pd.read_csv(
    ROOT / "data" / "raw" / "Causal_Snippets_with_Categories.csv",
    usecols=[
        "technology",
        "side",
        "macro_id",
        "macro_name",
        "phrase",
        "input_id",
        "company_name",
    ],
    encoding="utf-8",
)
cause_snip = snippets[
    (snippets["side"] == "cause") & (snippets["macro_id"].isin([1, 2]))
].copy()
cause_snip = cause_snip.dropna(subset=["phrase", "input_id"])
cause_snip["input_id"] = pd.to_numeric(cause_snip["input_id"], errors="coerce")
n_bad_ids = cause_snip["input_id"].isna().sum()
if n_bad_ids > 0:
    print(f"  WARNING: {n_bad_ids} rows with non-numeric input_id dropped")
    cause_snip = cause_snip.dropna(subset=["input_id"])
cause_snip["input_id"] = cause_snip["input_id"].astype(int)
cause_snip["phrase_len"] = cause_snip["phrase"].str.len()
print(f"  Cause snippets (macro 1+2): {len(cause_snip):,}")

all_techs = sorted(cause_snip["technology"].unique())
print(f"  Technologies present: {len(all_techs)}")

# ================================================================
# 2. Read AllTech in chunks, keeping only rows that match our snippets
# ================================================================
print("\nLoading sent_window from AllTech (chunked)...")
target_ids = set(cause_snip["input_id"].unique())
print(f"  Target input_ids: {len(target_ids):,}")

alltech_file = (
    ROOT
    / "data"
    / "raw"
    / "AllTech_2002-2024_with_LLM_results(with Causal and non-Causal snippets).csv"
)

context_parts = []
chunk_size = 500_000
for chunk_num, chunk in enumerate(
    pd.read_csv(
        alltech_file,
        usecols=["input_id", "sent_window"],
        chunksize=chunk_size,
        encoding="utf-8",
    )
):
    matched = chunk[chunk["input_id"].isin(target_ids)]
    if len(matched) > 0:
        context_parts.append(matched)
    if (chunk_num + 1) % 5 == 0:
        print(f"  Processed {(chunk_num + 1) * chunk_size:,} rows...")

context_df = (
    pd.concat(context_parts, ignore_index=True) if context_parts else pd.DataFrame()
)
context_df = context_df.drop_duplicates(subset=["input_id"])
print(f"  Unique sent_windows collected: {len(context_df):,}")

# ================================================================
# 3. Join snippets with sent_window
# ================================================================
merged = cause_snip.merge(context_df, on="input_id", how="inner")
merged = merged.dropna(subset=["sent_window"])
merged["sw_len"] = merged["sent_window"].str.len()
print(f"\nMerged rows (snippet + sent_window): {len(merged):,}")

# ================================================================
# 4. Score each snippet for clarity
# ================================================================
# A snippet is "clear" if:
#   (a) the extracted phrase appears verbatim in the sent_window, AND
#   (b) the phrase/window contain category-identifying keywords so a
#       reader can immediately tell whether it is tech-push or demand-pull.

# Keywords that signal each category to a human reader
TECH_PUSH_KW = [
    "technolog", "innovat", "develop", "engineer", "design", "platform",
    "algorithm", "protocol", "improv", "advanc", "r&d", "prototype",
    "patent", "architectur", "perform", "invent", "breakthrough",
    "next-generation", "next generation", "novel", "upgrade",
    "software", "hardware", "chip", "processor", "sensor", "module",
    "system", "solution", "capability", "efficien", "faster", "speed",
    "accuracy", "resolution", "precision", "automat",
]
DEMAND_PULL_KW = [
    "demand", "market", "customer", "consumer", "adopt", "growth",
    "need", "user", "buyer", "subscriber", "penetrat", "usage",
    "popularity", "appetite", "willingness", "prefer", "trend",
    "shift", "migration", "uptake", "interest", "opportunity",
    "e-commerce", "commercial", "sales growth", "revenue growth",
    "expanding market", "market size", "market share",
]
# Anti-keywords: words that suggest the snippet was mis-scored
TECH_PUSH_ANTI = ["demand", "market size", "market share", "customer need"]
DEMAND_PULL_ANTI = ["algorithm", "prototype", "r&d", "patent"]


def phrase_in_window(row):
    """Check if the extracted phrase appears in the sent_window."""
    phrase = str(row["phrase"]).lower().strip()
    window = str(row["sent_window"]).lower()
    return phrase in window


def keyword_score(text, keywords):
    """Count how many category keywords appear in text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


print("Scoring snippet clarity...")
merged["phrase_found"] = merged.apply(phrase_in_window, axis=1)
print(
    f"  Phrase found in sent_window: "
    f"{merged['phrase_found'].sum():,} / {len(merged):,} "
    f"({merged['phrase_found'].mean():.1%})"
)

# Keyword hits in combined phrase+window text
merged["combo_text"] = merged["phrase"].fillna("") + " " + merged["sent_window"].fillna("")
merged["tp_kw_hits"] = merged["combo_text"].apply(lambda t: keyword_score(t, TECH_PUSH_KW))
merged["dp_kw_hits"] = merged["combo_text"].apply(lambda t: keyword_score(t, DEMAND_PULL_KW))
merged["tp_anti_hits"] = merged["combo_text"].apply(lambda t: keyword_score(t, TECH_PUSH_ANTI))
merged["dp_anti_hits"] = merged["combo_text"].apply(lambda t: keyword_score(t, DEMAND_PULL_ANTI))

# For macro_id=1 (tech-push): reward tech keywords, penalize demand keywords
# For macro_id=2 (demand-pull): reward demand keywords, penalize tech keywords
merged["kw_bonus"] = np.where(
    merged["macro_id"] == 1,
    merged["tp_kw_hits"] * SCORE_KW_HIT - merged["tp_anti_hits"] * SCORE_ANTI_KW_PENALTY,
    merged["dp_kw_hits"] * SCORE_KW_HIT - merged["dp_anti_hits"] * SCORE_ANTI_KW_PENALTY,
)

# Score: phrase_found (required) + phrase length + window sweetspot + keyword bonus
merged["clarity_score"] = (
    merged["phrase_found"].astype(float) * SCORE_PHRASE_FOUND
    + merged["phrase_len"].clip(upper=SCORE_PHRASE_LEN_CAP)
    + np.where(
        (merged["sw_len"] >= WINDOW_LEN_MIN) & (merged["sw_len"] <= WINDOW_LEN_MAX),
        SCORE_WINDOW_SWEETSPOT, 0,
    )
    + merged["kw_bonus"]
)

# Manual overrides: for (technology, macro_id) pairs where the automated
# keyword-scoring algorithm selects a snippet whose category assignment
# is ambiguous to a human reader, we boost a manually-identified alternative.
#
# Selection criteria: the override phrase must (a) appear in a snippet already
# in the candidate set (phrase_found=True), and (b) more transparently
# illustrate the macro category than the top-scoring automated pick.
#
# These overrides affect only face-validity display (Online Appendix Table);
# they do not alter any statistical analysis.
# Reviewed: 2026-02-12. 13 of 58 (technology x macro) cells required override.
MANUAL_OVERRIDES = {
    ("GPS", 1): "introduction of C-Series",
    ("GPS", 2): "dramatic growth in interest in commercial GPS systems",
    ("Lane departure warning", 1): "transition to our next generation LDW unit",
    ("Lithium battery", 1): "exceptional technology in terms of cycle life",
    ("Lithium battery", 2): "increased lithium battery adoption",
    ("Machine Learning AI", 2): "growing demand for artificial intelligence and machine learning",
    ("Millimeter wave", 2): "market acceptance of millimeter wave",
    ("Social Networking", 1): "integrated search engine optimization, social networking",
    ("Solar Power", 2): "robust demand for power supply equipment",
    ("Virtual Reality", 2): "increased consumer demand for virtual reality",
    ("Wifi", 1): "XBAR's ability to deliver performance",
    ("Wireless charging", 2): "industry adoption of wireless charging",
    ("Fracking", 1): "technology advances in horizontal drilling",
}

for (tech, mid), phrase_sub in MANUAL_OVERRIDES.items():
    mask = (
        (merged["technology"] == tech)
        & (merged["macro_id"] == mid)
        & merged["phrase"].str.contains(phrase_sub, case=False, na=False)
    )
    merged.loc[mask, "clarity_score"] += SCORE_MANUAL_BOOST
    n_boosted = mask.sum()
    if n_boosted == 0:
        print(f"  WARNING: override for ({tech}, {mid}) matched 0 snippets")
    else:
        print(f"  Override: ({tech}, {mid}) boosted {n_boosted} snippet(s)")

# ================================================================
# 5. Select best snippet per (technology, macro_id)
# ================================================================
# Only keep snippets where the phrase is found in sent_window
clear = merged[merged["phrase_found"]].copy()
print(f"\nClear snippets (phrase found in window): {len(clear):,}")

# For each (technology, macro_id), pick the top-scoring snippet
best = (
    clear
    .sort_values("clarity_score", ascending=False)
    .groupby(["technology", "macro_id"], sort=False)
    .head(1)
    .reset_index(drop=True)
)
print(f"  Best snippet per (technology, macro_id): {len(best)}")

# Pivot: one row per technology, columns for macro 1 and macro 2
results = []
for tech in all_techs:
    row = {"technology": tech}
    for mid in [1, 2]:
        match = best[(best["technology"] == tech) & (best["macro_id"] == mid)]
        label = "tech_push" if mid == 1 else "demand_pull"
        if len(match) > 0:
            m = match.iloc[0]
            row[f"{label}_sent_window"] = m["sent_window"]
            row[f"{label}_phrase"] = m["phrase"]
            row[f"{label}_company"] = m["company_name"]
            row[f"{label}_input_id"] = int(m["input_id"])
        else:
            row[f"{label}_sent_window"] = None
            row[f"{label}_phrase"] = None
            row[f"{label}_company"] = None
            row[f"{label}_input_id"] = None
    results.append(row)

results_df = pd.DataFrame(results)

# Report coverage
n_tp = results_df["tech_push_sent_window"].notna().sum()
n_dp = results_df["demand_pull_sent_window"].notna().sum()
print(f"\nCoverage: {n_tp}/29 tech-push, {n_dp}/29 demand-pull")
missing_tp = results_df[results_df["tech_push_sent_window"].isna()]["technology"].tolist()
missing_dp = results_df[results_df["demand_pull_sent_window"].isna()]["technology"].tolist()
if missing_tp:
    print(f"  Missing tech-push: {missing_tp}")
if missing_dp:
    print(f"  Missing demand-pull: {missing_dp}")

# ================================================================
# 6. Export CSV
# ================================================================
csv_path = ROOT / "results" / "tables" / "table_IIIA_top_scoring.csv"
results_df.to_csv(csv_path, index=False, encoding="utf-8")
print(f"\nCSV saved: {csv_path}")

# ================================================================
# 7. Generate LaTeX table
# ================================================================


def bold_phrase_in_window(window, phrase):
    """Escape the window for LaTeX, then bold the phrase within it."""
    if not isinstance(phrase, str) or not phrase.strip():
        return escape_latex(window)
    phrase_clean = phrase.strip()
    # Find the phrase in the raw window (case-insensitive) to preserve original casing
    lower_window = window.lower()
    lower_phrase = phrase_clean.lower()
    idx = lower_window.find(lower_phrase)
    if idx == -1:
        return escape_latex(window)
    # Split window into before / match / after, escape each, bold the match
    before = window[:idx]
    match = window[idx : idx + len(phrase_clean)]
    after = window[idx + len(phrase_clean) :]
    return (
        escape_latex(before)
        + "\\textbf{" + escape_latex(match) + "}"
        + escape_latex(after)
    )


def build_latex_table(df):
    """Build the Online Appendix longtable: 29 technologies x 2 snippet columns.

    Matches the manuscript convention used in other tables:
    - Caption at normal document font size (not shrunk by \\tabfont)
    - Notes in \\footnotesize above the table body (first page only)
    - \\hline\\hline top/bottom, \\hline for internal separators
    - Data rows in \\footnotesize via column spec >{}
    """
    notes = (
        "\\textit{Notes.} "
        "For each of the 29 technologies, this table presents one earnings-call "
        "excerpt classified as \\textit{Technology Innovation and Advancement} "
        "(``tech-push'') and one classified as \\textit{Market Demand and Consumer "
        "Behavior} (``demand-pull'') by the LLM pipeline. "
        "Excerpts are selected from cause-side spans whose extracted phrase "
        "appears verbatim in the surrounding sentence window, ensuring that the "
        "category assignment is transparent to the reader. "
        "Bolded text marks the extracted causal phrase. "
        "A dash indicates that no cause-side span of that category exists for "
        "the technology. "
        "See Section~II.D for the taxonomy and Section~III.A for discussion."
    )

    header_row = (
        "Technology & "
        "Technology Innovation and Advancement & "
        "Market Demand and Consumer Behavior \\\\"
    )

    # Column spec: >{\footnotesize} applies footnotesize to data cells only.
    # Caption and notes use their own explicit font sizes.
    col_spec = (
        ">{\\footnotesize}p{2.8cm} "
        ">{\\footnotesize}p{10.2cm} "
        ">{\\footnotesize}p{10.2cm}"
    )

    lines = []
    lines.append("\\begin{landscape}")

    # --- Caption and notes OUTSIDE the longtable ---
    # This prevents the endfirsthead from overflowing the first page.
    # \enlargethispage gives longtable enough room to start on the caption page
    # (the 1.5in top/bottom margins leave only ~6.3in landscape text height).
    # \addtocounter prevents double-incrementing (captionof + longtable both step).
    lines.append("\\enlargethispage{4cm}")
    lines.append(
        "\\captionof{table}{Top-Scoring Transcripts: Technology Innovation "
        "versus Market Demand Snippets}"
    )
    lines.append("\\label{tab:top-scoring}")
    lines.append("\\vspace{-0.3em}")
    lines.append(
        "{\\footnotesize\\noindent" + notes + "\\par}"
    )
    lines.append("\\vspace{0.3em}")
    lines.append("\\addtocounter{table}{-1}%")
    lines.append("\\setlength{\\LTpre}{0pt}")

    # --- Longtable: compact headers only ---
    lines.append(
        "\\begin{longtable}{" + col_spec + "}"
    )

    # --- First-page header: just column headers ---
    lines.append("\\hline\\hline")
    lines.append(header_row)
    lines.append("\\hline")
    lines.append("\\endfirsthead")

    # --- Continuation-page header ---
    lines.append(
        "\\multicolumn{3}{l}{\\tablename\\ \\thetable\\ (continued)} "
        "\\\\[0.3em]"
    )
    lines.append("\\hline\\hline")
    lines.append(header_row)
    lines.append("\\hline")
    lines.append("\\endhead")

    # --- Continuation-page footer ---
    lines.append("\\hline")
    lines.append(
        "\\multicolumn{3}{r}{\\textit{Continued on next page}} \\\\"
    )
    lines.append("\\endfoot")

    # --- Last-page footer ---
    lines.append("\\hline\\hline")
    lines.append("\\endlastfoot")

    # --- Data rows ---
    for _, row in df.iterrows():
        tech_esc = escape_latex(row["technology"])

        # Tech-push cell: bold the phrase inside the window
        tp_sw = row.get("tech_push_sent_window")
        tp_phrase = row.get("tech_push_phrase")
        if pd.notna(tp_sw) and isinstance(tp_sw, str):
            tp_text = bold_phrase_in_window(tp_sw.strip(), tp_phrase)
        else:
            tp_text = "---"

        # Demand-pull cell: bold the phrase inside the window
        dp_sw = row.get("demand_pull_sent_window")
        dp_phrase = row.get("demand_pull_phrase")
        if pd.notna(dp_sw) and isinstance(dp_sw, str):
            dp_text = bold_phrase_in_window(dp_sw.strip(), dp_phrase)
        else:
            dp_text = "---"

        lines.append(f"{tech_esc} & {tp_text} & {dp_text} \\\\")

    lines.append("\\end{longtable}")
    lines.append("\\end{landscape}")

    return "\n".join(lines)


latex_content = build_latex_table(results_df)

tex_path = ROOT / "Overleaf" / "Appendix" / "top_scoring_transcripts.tex"
tex_path.write_text(latex_content, encoding="utf-8")
print(f"LaTeX table saved: {tex_path}")

# ================================================================
# 8. Print snippets for manual verification
# ================================================================
print("\n" + "=" * 80)
print("SNIPPETS FOR MANUAL VERIFICATION")
print("=" * 80)

for _, row in results_df.iterrows():
    print(f"\n{'─' * 70}")
    print(f"Technology: {row['technology']}")
    for label, prefix in [
        ("TECH-PUSH", "tech_push"),
        ("DEMAND-PULL", "demand_pull"),
    ]:
        sw = row.get(f"{prefix}_sent_window")
        phrase = row.get(f"{prefix}_phrase")
        company = row.get(f"{prefix}_company")
        if pd.notna(sw):
            print(f"\n  [{label}] Company: {company}")
            print(f"  Phrase: \"{phrase}\"")
            print(f"  Window: {str(sw)[:300]}")
        else:
            print(f"\n  [{label}] --- (no clear snippet available)")

# ================================================================
# 9. Manifest
# ================================================================
run_timestamp = datetime.datetime.now()

manifest = {
    "script": Path(__file__).name,
    "timestamp": run_timestamp.isoformat(),
    "seed": SEED,
    "input_files": [
        "data/raw/Causal_Snippets_with_Categories.csv",
        "data/raw/AllTech_2002-2024_with_LLM_results(with Causal and non-Causal snippets).csv",
    ],
    "output_files": [
        str(csv_path.relative_to(ROOT)),
        str(tex_path.relative_to(ROOT)),
    ],
    "row_counts": {
        "cause_snippets_macro12": len(cause_snip),
        "merged_with_window": len(merged),
        "clear_snippets": len(clear),
        "technologies": len(all_techs),
        "tech_push_covered": int(n_tp),
        "demand_pull_covered": int(n_dp),
    },
    "parameters": {
        "macro_ids": [1, 2],
        "selection": "phrase_found_in_sent_window, sorted by clarity_score",
        "score_phrase_found": SCORE_PHRASE_FOUND,
        "score_kw_hit": SCORE_KW_HIT,
        "score_anti_kw_penalty": SCORE_ANTI_KW_PENALTY,
        "score_window_sweetspot": SCORE_WINDOW_SWEETSPOT,
        "score_phrase_len_cap": SCORE_PHRASE_LEN_CAP,
        "score_manual_boost": SCORE_MANUAL_BOOST,
        "window_len_range": [WINDOW_LEN_MIN, WINDOW_LEN_MAX],
        "n_manual_overrides": len(MANUAL_OVERRIDES),
        "manual_override_keys": [
            f"{tech}|macro_{mid}" for (tech, mid) in MANUAL_OVERRIDES
        ],
        "chunk_size": chunk_size,
    },
    "missing_tech_push": missing_tp,
    "missing_demand_pull": missing_dp,
}

manifest_path = (
    ROOT
    / "results"
    / "runs"
    / f"{Path(__file__).stem}_{run_timestamp:%Y%m%d_%H%M%S}.json"
)
manifest_path.write_text(
    json.dumps(manifest, indent=2, default=str), encoding="utf-8"
)
print(f"\nManifest written to {manifest_path}")
print("\nDone.")
