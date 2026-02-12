---
name: run-python
description: Run a Python pipeline step in the Technology conda environment. Verifies exit code, manifest, and output files.
disable-model-invocation: true
argument-hint: "[step number (e.g., '01') or script path (e.g., 'src/py/01_clean.py')]"
allowed-tools: ["Bash", "Read", "Glob"]
---

# Run Python Pipeline Step

Execute a Python script in the `Technology` conda environment with full verification.

## Steps

1. **Identify the script:**
   - If `$ARGUMENTS` is a number (e.g., `01`): find `src/py/0$ARGUMENTS_*.py`
   - If `$ARGUMENTS` is a path: use it directly
   - If `$ARGUMENTS` is a name (e.g., `clean`): glob for matching script

2. **Run the script:**

```powershell
conda run -n Technology python [script_path]
```

3. **Verify outputs:**
   - Check exit code (0 = success)
   - Check if manifest JSON was written to `results/runs/`
   - Check if output files were created in `data_processed/` or `results/`
   - Report file sizes for key outputs

4. **Report results:**
   - Script: [path]
   - Exit code: [0 or error]
   - Manifest: [path or "not written"]
   - Outputs: [list of files with sizes]
   - Duration: [approximate]

## Important

- Always use `conda run -n Technology` — never activate the env manually
- If the script fails, capture and display the error traceback
- Check `results/runs/` for the manifest — its absence is a warning
- Do NOT modify the script — only run and report
