"""
manifest.py — Run Manifest Utility

Purpose: Helper functions for creating and reading JSON run manifests.
         Every pipeline step writes a manifest to results/runs/ for
         reproducibility and audit trail.
"""

from pathlib import Path
import json
import datetime
from typing import Any, Dict, List, Optional


def create_manifest(
    script_path: Path,
    seed: int,
    input_files: List[str],
    output_files: List[str],
    row_counts: Dict[str, int],
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict:
    """Create a run manifest dictionary.

    Args:
        script_path: Path to the script that ran.
        seed: Random seed used.
        input_files: List of input file paths.
        output_files: List of output file paths.
        row_counts: Dict mapping dataset names to row counts.
        parameters: Optional dict of run parameters.

    Returns:
        Manifest dictionary ready to write as JSON.
    """
    return {
        "script": script_path.name,
        "timestamp": datetime.datetime.now().isoformat(),
        "seed": seed,
        "input_files": input_files,
        "output_files": output_files,
        "row_counts": row_counts,
        "parameters": parameters or {},
    }


def write_manifest(manifest: Dict, runs_dir: Path) -> Path:
    """Write manifest to results/runs/ with timestamped filename.

    Args:
        manifest: Manifest dictionary from create_manifest().
        runs_dir: Path to results/runs/ directory.

    Returns:
        Path to the written manifest file.
    """
    runs_dir.mkdir(parents=True, exist_ok=True)
    script_stem = Path(manifest["script"]).stem
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = runs_dir / f"{script_stem}_{timestamp}.json"
    filepath.write_text(json.dumps(manifest, indent=2))
    return filepath


def read_latest_manifest(runs_dir: Path, script_name: str = None) -> Optional[Dict]:
    """Read the most recent manifest from results/runs/.

    Args:
        runs_dir: Path to results/runs/ directory.
        script_name: Optional filter by script name stem.

    Returns:
        Most recent manifest dict, or None if no manifests found.
    """
    if not runs_dir.exists():
        return None

    pattern = f"{script_name}_*.json" if script_name else "*.json"
    manifests = sorted(runs_dir.glob(pattern), key=lambda p: p.stat().st_mtime)

    if not manifests:
        return None

    return json.loads(manifests[-1].read_text())
