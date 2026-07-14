"""Notebook creation and execution helpers."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import traceback

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output

from .paths import NOTEBOOKS_DIR


def _common_setup_code() -> str:
    return """from pathlib import Path
import sys
import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path.cwd().resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.paths import PM25_FIELD

county_df = pd.read_csv(PROJECT_ROOT / "outputs" / "tables" / "county_annual_pm25.csv")
coverage_df = pd.read_csv(PROJECT_ROOT / "outputs" / "tables" / "county_monitor_coverage.csv")
joined_gdf = gpd.read_file(PROJECT_ROOT / "outputs" / "tables" / "wisconsin_counties_pm25_joined.geojson")
spatial_df = pd.read_csv(PROJECT_ROOT / "outputs" / "tables" / "spatial_sensitivity_results.csv")
weights_df = pd.read_csv(PROJECT_ROOT / "outputs" / "tables" / "spatial_weights_comparison.csv")
stability_df = pd.read_csv(PROJECT_ROOT / "outputs" / "tables" / "local_cluster_stability.csv")
pm25_population_df = pd.read_csv(PROJECT_ROOT / "outputs" / "tables" / "pm25_population_context.csv")
"""


def build_legacy_notebook(legacy_island_names: list[str]) -> Path:
    """Create the legacy replication notebook."""
    notebook = new_notebook(
        cells=[
            new_markdown_cell("# Legacy Replication: Wisconsin County-Level PM2.5 Spatial Analysis (2024)"),
            new_markdown_cell(
                "This notebook documents the legacy replication layer of the rebuild. "
                "Because the original raw EPA daily export and the original course notebook were not available in the workspace, "
                "the county-level benchmark snapshot is used as a transparent fallback."
            ),
            new_code_cell(_common_setup_code()),
            new_markdown_cell("## Legacy county snapshot"),
            new_code_cell("print(county_df[['County_FIPS_Code', 'County', PM25_FIELD, 'n_sites', 'Data_Mode']].head(16).to_string(index=False))"),
            new_markdown_cell("## Monitor coverage"),
            new_code_cell("print(coverage_df[['has_monitor']].value_counts().rename('count').to_string())"),
            new_markdown_cell("## Legacy benchmark range"),
            new_code_cell(
                "print(county_df.sort_values(PM25_FIELD, ascending=False)[['County', PM25_FIELD, 'n_sites']].to_string(index=False))"
            ),
            new_markdown_cell("## Legacy figures"),
            new_markdown_cell(
                "![Choropleth](../outputs/figures/pm25_2024_choropleth.png)\n\n"
                "![Ranking](../outputs/figures/pm25_2024_ranked_bar.png)\n\n"
                "![Legacy LISA](../outputs/figures/lisa_cluster_map_legacy.png)"
            ),
            new_markdown_cell("## Spatial diagnostics"),
            new_code_cell(
                "legacy = spatial_df[spatial_df['specification'] == 'legacy_queen']\n"
                "print(legacy[['County', 'cluster', 'local_moran_I', 'local_p_sim', 'is_island']].sort_values('County').to_string(index=False))"
            ),
            new_markdown_cell(
                f"Legacy Queen weights contain disconnected monitored counties. "
                f"Island counties in this rebuild are: {', '.join(legacy_island_names) if legacy_island_names else 'none'}."
            ),
        ]
    )
    path = NOTEBOOKS_DIR / "00_legacy_replication.ipynb"
    nbformat.write(notebook, path)
    return path


def build_portfolio_notebook(correlation: float, global_i: float, global_p: float) -> Path:
    """Create the portfolio-grade notebook with required section headers."""
    markdown_sections = [
        "# Air Pollution Patterns in Wisconsin: A County-Level PM2.5 Spatial Analysis (2024)",
        "## 1. Title and executive summary\nThis notebook presents a reproducible county-level PM2.5 monitoring analysis for Wisconsin in 2024. It separates legacy replication from a more careful portfolio-grade interpretation.",
        "## 2. Motivation and research questions\nThe project asks where monitored county means were highest in Wisconsin, how sparse the monitor network was, and whether monitored counties showed evidence of spatial clustering.",
        "## 3. Data sources and provenance\nCore sources include EPA Air Trends / AirData references, the Wisconsin county boundary layer archived by GeoData@Wisconsin from U.S. Census TIGER/Line, and county population context from the supplied factbook-style tables tied to the 2020 Census.",
        "## 4. Data limitations\nThe original raw daily EPA export and the original classroom notebook were not available. As a result, this rebuild uses a benchmark-backed county snapshot for the replication layer and documents that limitation explicitly.",
        "## 5. Data cleaning and quality assurance\nCounty FIPS fields were normalized as five-character strings, Wisconsin county names were standardized, and the shapefile was checked for valid geometry and complete 72-county coverage.",
        "## 6. Monitoring coverage\nOnly 16 of Wisconsin's 72 counties have county-level PM2.5 values in the legacy benchmark snapshot, so statewide inference is limited by sparse monitor placement.",
        "## 7. Site-to-county aggregation\nThe original method averages annual site means within county without site weighting. In fallback mode, the county benchmark snapshot preserves that legacy estimator's target outputs.",
        "## 8. Descriptive spatial distribution\nThe statewide choropleth retains all counties and shades unmonitored counties separately to avoid overstating spatial completeness.",
        "## 9. County ranking\nGrant County is the highest benchmark county and Monroe County the lowest among monitored counties.",
        f"## 10. Global spatial autocorrelation\nThe legacy Queen specification produced Moran's I = {global_i:.3f} with simulation p-value = {global_p:.3f} under a fixed seed of 42. This is a weak and statistically uncertain signal.",
        "## 11. Local spatial autocorrelation\nLocal Moran categories are highly sensitive to monitor geography, especially under the disconnected legacy Queen graph.",
        "## 12. Spatial-Weights Sensitivity Analysis\nThe monitored-only Queen graph fragments because only counties with PM2.5 observations are included. If a monitored county has no monitored contiguous neighbor, it becomes an island. K-nearest-neighbor weights are used here as a sensitivity specification: they avoid islands by connecting each monitored county to a fixed number of geographically nearest monitored counties, while changing k changes the geographic scale of the spatial lag and the local permutation test.",
        "## 13. Interpretation and policy relevance\nAll monitored-county descriptive annual means are below 9.0 µg/m³, but these averages are not EPA regulatory design values and should not be interpreted as formal attainment determinations.",
        "## 14. Limitations\nCounty-level monitored means are not equivalent to population exposure. Sparse placement, monitor siting, and missing counties all constrain interpretation.",
        "## 15. Conclusion\nThe strongest conclusion is descriptive: monitored PM2.5 values vary across Wisconsin, but the monitor network is too sparse for broad statewide cluster claims.",
        "## 16. Team contributions\nYifang Qiu: analysis, spatial joining, choropleth mapping, county ranking, Global Moran's I, Local Moran's I, and visualization.",
        "## 17. References\nEPA Air Trends; EPA AirData pre-generated files page; GeoData@Wisconsin TIGER/Line county layer; U.S. Census county population resources.",
    ]
    notebook = new_notebook(cells=[new_markdown_cell(text) for text in markdown_sections[:2]])
    notebook.cells.extend(
        [
            new_code_cell(_common_setup_code()),
            new_code_cell(
                "summary = {\n"
                "    'monitored_counties': int(county_df[PM25_FIELD].notna().sum()),\n"
                "    'all_counties': int(len(coverage_df)),\n"
                "    'highest_county': county_df.loc[county_df[PM25_FIELD].idxmax(), 'County'],\n"
                "    'lowest_county': county_df.loc[county_df[PM25_FIELD].idxmin(), 'County'],\n"
                "}\nprint(summary)"
            ),
        ]
    )
    for section in markdown_sections[2:]:
        notebook.cells.append(new_markdown_cell(section))
        if section.startswith("## 6."):
            notebook.cells.append(
                new_code_cell(
                    "print(coverage_df[['County', 'has_monitor', 'n_sites']].sort_values(['has_monitor', 'County'], ascending=[False, True]).head(20).to_string(index=False))"
                )
            )
        elif section.startswith("## 8."):
            notebook.cells.append(
                new_markdown_cell(
                    "![Choropleth](../outputs/figures/pm25_2024_choropleth.png)"
                )
            )
        elif section.startswith("## 9."):
            notebook.cells.append(
                new_markdown_cell(
                    "![County Ranking](../outputs/figures/pm25_2024_ranked_bar.png)"
                )
            )
        elif section.startswith("## 10."):
            notebook.cells.append(
                new_code_cell(
                    "print(spatial_df[spatial_df['specification'] == 'legacy_queen'][['County', 'cluster', 'global_moran_I', 'global_p_sim']].head(16).to_string(index=False))"
                )
            )
        elif section.startswith("## 12."):
            notebook.cells.append(
                new_code_cell(
                    "print(weights_df[['specification', 'k', 'n_components', 'n_islands', 'global_moran_I', 'global_p_sim', 'n_significant_local_clusters', 'significant_local_counties']].to_string(index=False))"
                )
            )
            notebook.cells.append(
                new_markdown_cell(
                    "![Global Moran Sensitivity](../outputs/figures/global_moran_sensitivity.png)\n\n"
                    "![LISA Weights Comparison](../outputs/figures/lisa_weights_comparison.png)"
                )
            )
            notebook.cells.append(
                new_code_cell(
                    "print(stability_df[['County', 'queen_cluster', 'knn3_cluster', 'knn4_cluster', 'knn5_cluster', 'significant_specification_count', 'stable_cluster']].to_string(index=False))"
                )
            )
            notebook.cells.append(
                new_markdown_cell(
                    "The substantive global conclusion is stable across spatial-weight definitions. Global Moran’s I is statistically insignificant under Queen contiguity and under KNN specifications with k ranging from 3 to 5. However, local LISA classifications are not stable. The Queen graph is fragmented because only monitored counties are included, leaving five counties without contiguous monitored neighbors. KNN eliminates islands, but changing k alters each county’s spatial lag and the resulting local permutation test. Accordingly, county-specific cluster labels are treated as exploratory rather than robust policy findings."
                )
            )
        elif section.startswith("## 13."):
            notebook.cells.append(
                new_markdown_cell(
                    "![Population Context](../outputs/figures/pm25_vs_population_density.png)"
                )
            )
            notebook.cells.append(
                new_code_cell(
                    f"print('Correlation between PM2.5 and log population density: {correlation:.3f}')"
                )
            )
    path = NOTEBOOKS_DIR / "01_portfolio_analysis.ipynb"
    nbformat.write(notebook, path)
    return path


def execute_notebook(path: Path) -> None:
    """Execute a notebook in-process and write captured stream outputs."""
    notebook = nbformat.read(path, as_version=4)
    globals_dict: dict[str, object] = {}
    old_cwd = Path.cwd()
    try:
        os_cwd = path.parent
        import os

        os.chdir(os_cwd)
        execution_count = 1
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            stdout = io.StringIO()
            stderr = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exec(cell.source, globals_dict)
            except Exception as exc:  # pragma: no cover - surfaced in executed notebook
                tb_lines = traceback.format_exc().splitlines()
                cell.outputs = [
                    new_output(
                        output_type="error",
                        ename=type(exc).__name__,
                        evalue=str(exc),
                        traceback=tb_lines,
                    )
                ]
                cell.execution_count = execution_count
                raise
            combined = stdout.getvalue() + stderr.getvalue()
            outputs = []
            if combined:
                outputs.append(new_output(output_type="stream", name="stdout", text=combined))
            cell.outputs = outputs
            cell.execution_count = execution_count
            execution_count += 1
    finally:
        import os

        os.chdir(old_cwd)
    nbformat.write(notebook, path)
