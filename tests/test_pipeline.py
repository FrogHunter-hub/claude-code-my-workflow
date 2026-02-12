"""
test_pipeline.py — Pipeline Integration Tests

Tests for the data cleaning and analysis pipeline.
Run with: conda run -n Technology pytest -q tests/
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_directory_structure():
    """Verify project directory structure exists."""
    required_dirs = [
        "src/py",
        "src/stata",
        "data",
        "data_processed",
        "results/runs",
        "logs",
        "Figures",
        "Overleaf",
    ]
    for d in required_dirs:
        assert (ROOT / d).is_dir(), f"Missing directory: {d}"


def test_pipeline_scripts_exist():
    """Verify pipeline scripts are present."""
    scripts = [
        "src/py/01_clean.py",
        "src/py/02_analysis.py",
        "src/py/manifest.py",
        "src/stata/01_setup.do",
        "src/stata/02_analysis.do",
    ]
    for s in scripts:
        assert (ROOT / s).is_file(), f"Missing script: {s}"


def test_manifest_utility():
    """Test manifest creation and reading."""
    from src.py.manifest import create_manifest, write_manifest, read_latest_manifest
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"

        manifest = create_manifest(
            script_path=Path("test_script.py"),
            seed=42,
            input_files=["data/test.csv"],
            output_files=["results/test_output.csv"],
            row_counts={"input": 100, "output": 95},
        )

        assert manifest["seed"] == 42
        assert manifest["script"] == "test_script.py"

        written_path = write_manifest(manifest, runs_dir)
        assert written_path.exists()

        loaded = read_latest_manifest(runs_dir, "test_script")
        assert loaded is not None
        assert loaded["seed"] == 42
