---
name: run-stata
description: Run a Stata do-file using StataSE 19.5. Verifies log file creation and output.
disable-model-invocation: true
argument-hint: "[step number (e.g., '01') or script path (e.g., 'src/stata/01_setup.do')]"
allowed-tools: ["Bash", "Read", "Glob"]
---

# Run Stata Do-File

Execute a Stata do-file using StataSE 19.5 with full verification.

## Steps

1. **Identify the do-file:**
   - If `$ARGUMENTS` is a number (e.g., `01`): find `src/stata/0$ARGUMENTS_*.do`
   - If `$ARGUMENTS` is a path: use it directly
   - If `$ARGUMENTS` is a name: glob for matching do-file

2. **Run the do-file:**

```powershell
& $env:STATA_EXE /e do "[dofile_path]"
```

If `$env:STATA_EXE` is not set, use `D:\StataSE-64.exe`.

3. **Verify outputs:**
   - Check if log file was created in `logs/`
   - Read the last 30 lines of the log for errors (grep for `r(` error codes)
   - Check if output .dta files were created in `data_processed/`
   - Check if output .tex/.csv tables were created in `results/`

4. **Report results:**
   - Do-file: [path]
   - Log: [path or "not created"]
   - Errors: [none or list of r() codes]
   - Outputs: [list of files with sizes]

## Important

- Stata `/e` flag runs in batch mode (no GUI window)
- If the do-file fails, the log file contains the error — always read it
- Check for `version 19.5` at top of do-file before running
- Do NOT modify the do-file — only run and report
