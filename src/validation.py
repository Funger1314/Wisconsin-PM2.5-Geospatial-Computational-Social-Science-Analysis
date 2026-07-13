"""Validation helpers for benchmark checks and project scans."""

from __future__ import annotations

from pathlib import Path

import nbformat
import pandas as pd

from .aggregation import LEGACY_BENCHMARKS
from .paths import PM25_FIELD, PROJECT_ROOT


def benchmark_comparison(county_df: pd.DataFrame) -> pd.DataFrame:
    """Compare computed county means against the legacy benchmark table."""
    benchmarks = pd.DataFrame(LEGACY_BENCHMARKS)
    merged = benchmarks.merge(
        county_df[["County_FIPS_Code", PM25_FIELD, "n_sites"]],
        on="County_FIPS_Code",
        how="left",
        suffixes=("_benchmark", "_computed"),
    )
    merged["abs_diff_pm25"] = (merged["PM25_Annual_Mean_2024_benchmark"] - merged["PM25_Annual_Mean_2024_computed"]).abs()
    merged["abs_diff_n_sites"] = (merged["n_sites_benchmark"] - merged["n_sites_computed"]).abs()
    return merged


def find_content_paths(project_root: Path | None = None) -> list[Path]:
    """Find text-based source files that still contain legacy Colab-style root paths."""
    root = project_root or PROJECT_ROOT
    offenders: list[Path] = []
    text_suffixes = {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".ipynb", ".csv"}
    marker = "/" + "content/"
    skip_roots = {
        root / ".venv",
        root / ".git",
        root / ".pytest_cache",
        root / ".ipynb_checkpoints",
    }
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in text_suffixes:
            continue
        if any(skipped in path.parents for skipped in skip_roots):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if marker in text:
            offenders.append(path)
    return offenders


def notebook_has_error_outputs(path: Path) -> bool:
    """Return True when an executed notebook still contains an error output."""
    notebook = nbformat.read(path, as_version=4)
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                return True
    return False
