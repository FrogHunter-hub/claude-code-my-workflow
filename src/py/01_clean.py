"""
01_clean.py — Data Cleaning Pipeline

Purpose: Load raw earnings call data, extract causal statements,
         and build the firm × technology × quarter panel.
Inputs:  data/ (raw transcripts, technology keywords, taxonomy)
Outputs: data_processed/ (cleaned panel, causal snippets)
"""

from pathlib import Path
import json
import datetime
import os

import pandas as pd
import numpy as np

SEED = 42
ROOT = Path(__file__).resolve().parents[2]

np.random.seed(SEED)

# 0. Setup ----
os.makedirs(ROOT / "data_processed", exist_ok=True)
os.makedirs(ROOT / "results" / "runs", exist_ok=True)
os.makedirs(ROOT / "logs", exist_ok=True)

# 1. Load Data ----
# TODO: Load raw transcripts from data/
# TODO: Load technology keyword list (29 technologies from Kalyani et al. 2025)
# TODO: Load taxonomy definitions

# 2. Extract Causal Statements ----
# TODO: Apply LLM extraction pipeline
# TODO: Parse cause spans and effect spans

# 3. Build Panel ----
# TODO: Aggregate to firm × technology × quarter level
# TODO: Compute cause shares and effect shares (0–1 range)
# TODO: Merge with firm characteristics

# 4. Export ----
# TODO: Save cleaned panel to data_processed/
# TODO: Save causal snippets to data_processed/

# 5. Manifest ----
manifest = {
    "script": Path(__file__).name,
    "timestamp": datetime.datetime.now().isoformat(),
    "seed": SEED,
    "input_files": [],
    "output_files": [],
    "row_counts": {},
    "parameters": {},
}
manifest_path = (
    ROOT / "results" / "runs"
    / f"{Path(__file__).stem}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
)
manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"Manifest written to {manifest_path}")
