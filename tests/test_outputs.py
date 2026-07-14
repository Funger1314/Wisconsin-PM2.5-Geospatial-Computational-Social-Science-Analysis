from pathlib import Path

import nbformat

from src.paths import LOGS_DIR, NOTEBOOKS_DIR, OUTPUTS_DIR, PROJECT_ROOT, REPORTS_DIR, SLIDES_DIR
from src.validation import find_content_paths, notebook_has_error_outputs


def test_required_outputs_exist_and_are_nonempty():
    required_paths = [
        OUTPUTS_DIR / "figures" / "pm25_2024_choropleth.png",
        OUTPUTS_DIR / "figures" / "pm25_2024_ranked_bar.png",
        OUTPUTS_DIR / "figures" / "global_moran_sensitivity.png",
        OUTPUTS_DIR / "figures" / "lisa_cluster_map_legacy.png",
        OUTPUTS_DIR / "figures" / "lisa_cluster_map_knn4.png",
        OUTPUTS_DIR / "figures" / "lisa_weights_comparison.png",
        OUTPUTS_DIR / "figures" / "pm25_vs_population_density.png",
        OUTPUTS_DIR / "tables" / "county_annual_pm25.csv",
        OUTPUTS_DIR / "tables" / "site_annual_pm25.csv",
        OUTPUTS_DIR / "tables" / "county_monitor_coverage.csv",
        OUTPUTS_DIR / "tables" / "spatial_weights_comparison.csv",
        OUTPUTS_DIR / "tables" / "local_cluster_stability.csv",
        OUTPUTS_DIR / "tables" / "wisconsin_counties_pm25_joined.geojson",
        OUTPUTS_DIR / "tables" / "spatial_sensitivity_results.csv",
        REPORTS_DIR / "Wisconsin_PM25_Writing_Sample_2to3_pages.docx",
        REPORTS_DIR / "Wisconsin_PM25_Writing_Sample_2to3_pages.pdf",
        SLIDES_DIR / "Wisconsin_PM25_Spatial_Analysis.pptx",
        SLIDES_DIR / "Wisconsin_PM25_Spatial_Analysis.pdf",
        LOGS_DIR / "VALIDATION_REPORT.md",
    ]
    for path in required_paths:
        assert path.exists(), f"Missing required output: {path}"
        assert path.stat().st_size > 0, f"Output is empty: {path}"


def test_no_content_paths_remain():
    assert find_content_paths() == []


def test_notebooks_exist_and_have_no_error_outputs():
    notebooks = [
        NOTEBOOKS_DIR / "00_legacy_replication.ipynb",
        NOTEBOOKS_DIR / "01_portfolio_analysis.ipynb",
    ]
    for notebook_path in notebooks:
        assert notebook_path.exists()
        assert not notebook_has_error_outputs(notebook_path)
        notebook = nbformat.read(notebook_path, as_version=4)
        executed_code_cells = [cell for cell in notebook.cells if cell.cell_type == "code" and cell.execution_count]
        assert executed_code_cells, f"No executed code cells found in {notebook_path}"


def test_readme_includes_reproduction_commands():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "make all" in readme
    assert "make analysis" in readme
