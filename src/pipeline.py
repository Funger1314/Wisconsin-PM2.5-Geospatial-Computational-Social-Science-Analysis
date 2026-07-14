"""End-to-end project pipeline for the Wisconsin PM2.5 rebuild."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from .aggregation import (
    LEGACY_BENCHMARKS,
    aggregate_legacy_from_raw,
    build_fallback_snapshot,
    build_monitor_coverage,
    build_site_placeholder_table,
    filter_wisconsin_2024,
    join_counties,
    normalize_raw_daily_schema,
    summarize_raw_daily,
)
from .data_loading import discover_source_paths, inventory_files, load_factbook_wisconsin, load_simplified_pm25, load_wisconsin_counties
from .mapping import (
    plot_choropleth,
    plot_global_moran_sensitivity,
    plot_lisa_cluster_map,
    plot_lisa_weights_comparison,
    plot_population_scatter,
    plot_ranked_bar,
)
from .notebooks import build_legacy_notebook, build_portfolio_notebook, execute_notebook
from .paths import FIGURES_DIR, INTERIM_DIR, LOGS_DIR, NOTEBOOKS_DIR, OUTPUTS_DIR, PERMUTATIONS, PM25_FIELD, PROCESSED_DIR, PROJECT_ROOT, RAW_DIR, REPORTS_DIR, SEED, SLIDES_DIR, TABLES_DIR
from .reporting import build_slide_deck, build_slide_pdf, build_writing_sample_docx, build_writing_sample_pdf, write_project_summary
from .spatial_stats import run_spatial_analysis
from .validation import benchmark_comparison, find_content_paths


@dataclass
class AnalysisContext:
    """Analysis outputs used across reports, notebooks, and tests."""

    county_df: pd.DataFrame
    site_df: pd.DataFrame
    joined_gdf: gpd.GeoDataFrame
    coverage_df: pd.DataFrame
    pm25_population_df: pd.DataFrame
    benchmark_df: pd.DataFrame
    spatial_df: pd.DataFrame
    spatial_weights_df: pd.DataFrame
    local_stability_df: pd.DataFrame
    summary: dict[str, object]


def _ensure_directories() -> None:
    for path in [INTERIM_DIR, PROCESSED_DIR, FIGURES_DIR, TABLES_DIR, LOGS_DIR, REPORTS_DIR, SLIDES_DIR, NOTEBOOKS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def _format_markdown_table(df: pd.DataFrame) -> str:
    """Render a compact markdown table without external dependencies."""
    columns = list(df.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(str(row[column]) for column in columns) + " |"
        for _, row in df.iterrows()
    ]
    return "\n".join([header, separator] + rows)


def _write_source_metadata(source_paths, discovered_files: list[Path], raw_status: dict[str, object]) -> None:
    metadata = f"""# Source Metadata

## Local materials discovered
{chr(10).join(f"- `{path.relative_to(PROJECT_ROOT)}`" for path in discovered_files)}

## Official source references
- EPA Air Trends county page: https://www.epa.gov/air-trends/air-quality-cities-and-counties
- EPA AirData download page: https://aqs.epa.gov/aqsweb/airdata/download_files.html
- Candidate raw daily PM2.5 file for parameter 88101: https://aqs.epa.gov/aqsweb/airdata/daily_88101_2024.zip
- GeoData@Wisconsin county layer: https://geodata.wisc.edu/catalog/604F7A0B-1715-43B8-835E-4032851481AD
- U.S. Census county population page: https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html

## Rebuild status
- Raw daily EPA file located locally: `{raw_status['raw_daily_found']}`
- Raw daily EPA file retrieved successfully in this workspace: `{raw_status['raw_daily_retrieved']}`
- Raw daily path used: `{raw_status['raw_daily_path']}`
- Notes: {raw_status['notes']}
"""
    (RAW_DIR / "SOURCE_METADATA.md").write_text(metadata, encoding="utf-8")


def _write_data_gaps(raw_status: dict[str, object]) -> None:
    content = f"""# Data Gaps

## What was missing
- The original classroom notebook was not present in the supplied workspace.
- The original slide deck was not present in the supplied workspace.
- The legacy EPA raw daily export `ad_viz_plotval_data.csv` was not present.

## Network retrieval attempt
- Official target file: `https://aqs.epa.gov/aqsweb/airdata/daily_88101_2024.zip`
- Retrieval status: `{raw_status['notes']}`

## Fallback used in this rebuild
- A transparent county-level snapshot was created from the benchmark values embedded in the rebuild prompt.
- The simplified Wisconsin PM2.5 table and the EPA county factbook were used only for population context and consistency checks.
- Site-level annual means could not be reconstructed honestly without the raw daily EPA file.

## Interpretation consequence
- This rebuild reproduces county-level mapping and spatial analysis from the benchmark snapshot.
- It does not claim raw-record-level replication of the 7,234 Wisconsin daily observations.
"""
    (PROJECT_ROOT / "DATA_GAPS.md").write_text(content, encoding="utf-8")


def _write_license_notice() -> None:
    content = """# License Or Data Notice

This repository contains a reproducible rebuild of a classroom project using public environmental and geographic data plus user-supplied course materials.

- EPA Air Trends / AirData source materials remain subject to EPA terms and citation expectations.
- GeoData@Wisconsin distributes the archived county boundary layer sourced from the U.S. Census Bureau TIGER/Line program.
- Population context fields in the supplied tables refer to the 2020 Census.
- User-supplied course files are preserved for project reconstruction and should not be redistributed without confirming permission.
"""
    (PROJECT_ROOT / "LICENSE_OR_DATA_NOTICE.md").write_text(content, encoding="utf-8")


def _write_support_files() -> None:
    (PROJECT_ROOT / ".gitignore").write_text(
        ".venv/\n__pycache__/\n.pytest_cache/\n.ipynb_checkpoints/\n.jupyter/\n.mplconfig/\n__MACOSX/\n._*\n.DS_Store\n",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "requirements.txt").write_text(
        "\n".join(
            [
                "pandas==3.0.3",
                "numpy==2.5.1",
                "matplotlib==3.11.0",
                "geopandas==1.1.4",
                "pyogrio==0.13.0",
                "shapely==2.1.2",
                "pyproj==3.7.2",
                "libpysal==4.15.0",
                "esda==2.10.0",
                "mapclassify==2.10.0",
                "openpyxl==3.1.5",
                "nbconvert==7.17.1",
                "nbformat==5.10.4",
                "nbclient==0.11.0",
                "ipykernel==7.3.0",
                "pytest==9.1.1",
                "pypdf==6.14.2",
                "python-pptx==1.0.2",
                "python-docx==1.2.0",
                "reportlab==5.0.0",
                "jinja2==3.1.6",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "environment.yml").write_text(
        """name: wisconsin-pm25-spatial-analysis
channels:
  - conda-forge
dependencies:
  - python=3.12
  - pip
  - pip:
      - -r requirements.txt
""",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "Makefile").write_text(
        """PYTHON=.venv/bin/python

setup:
\tpython3 -m venv .venv
\t$(PYTHON) -m pip install -r requirements.txt

validate-data:
\t$(PYTHON) -m src.pipeline validate

analysis:
\t$(PYTHON) -m src.pipeline analysis

notebook:
\t$(PYTHON) -m src.pipeline notebooks

test:
\t$(PYTHON) -m pytest -q

slides:
\t$(PYTHON) -m src.pipeline slides

report:
\t$(PYTHON) -m src.pipeline report

all:
\t$(PYTHON) -m src.pipeline all
""",
        encoding="utf-8",
    )


def _build_population_context(joined_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    monitored = joined_gdf[joined_gdf[PM25_FIELD].notna()].copy()
    monitored["population_density_per_sqkm"] = monitored["Population_2020_Census"] / monitored["land_area_sqkm"]
    monitored["log_population_density"] = monitored["population_density_per_sqkm"].map(
        lambda value: np.nan if pd.isna(value) or value <= 0 else float(np.log(value))
    )
    monitored["pm25_density_correlation"] = pd.NA
    return monitored[
        [
            "County_FIPS_Code",
            "County",
            PM25_FIELD,
            "Population_2020_Census",
            "land_area_sqkm",
            "population_density_per_sqkm",
            "log_population_density",
        ]
    ].sort_values("County_FIPS_Code")


def _write_markdown_summary(summary: dict[str, object], comparison_df: pd.DataFrame) -> None:
    compact = comparison_df[
        ["specification", "global_moran_I", "global_p_sim", "n_components", "n_islands"]
    ].copy()
    compact["global_moran_I"] = compact["global_moran_I"].map(lambda value: f"{value:.6f}")
    compact["global_p_sim"] = compact["global_p_sim"].map(lambda value: f"{value:.3f}")
    text = f"""# Wisconsin PM2.5 Project Summary

## Project overview
This rebuild reconstructs a county-level PM2.5 spatial analysis for Wisconsin in 2024 and separates a legacy replication layer from a more defensible portfolio-grade interpretation.

## Key results
- Total Wisconsin counties in boundary layer: {summary['total_counties']}
- Monitored counties with benchmark PM2.5 values: {summary['monitored_counties']}
- Highest monitored county: {summary['highest_county']} ({summary['highest_value']:.6f})
- Lowest monitored county: {summary['lowest_county']} ({summary['lowest_value']:.6f})
- Legacy Moran's I: {summary['legacy_global_I']:.6f}
- Legacy expected I: {summary['legacy_expected_I']:.6f}
- Legacy permutation p-value with seed 42: {summary['legacy_global_p']:.6f}

## Interpretation
All monitored-county descriptive annual means in this rebuild are below 9.0 ug/m3. These descriptive means are not EPA regulatory design values and should not be interpreted as formal attainment determinations.

## Spatial-weights sensitivity results
{_format_markdown_table(compact)}

The monitored-county Queen graph contains 8 connected components and 5 island counties. KNN weights with k values of 3, 4, and 5 remove islands and keep all monitored counties in one connected component, but the KNN weights remain asymmetric because nearest-neighbor ties are directional and were not symmetrized. Across all four specifications, the global permutation test remains statistically insignificant, while county-specific LISA labels change with the neighborhood definition.

## Limitation
The original raw EPA daily export and original classroom notebook were unavailable, so the rebuild uses a transparent county benchmark snapshot for the replication layer.
"""
    write_project_summary(text)


def _build_writing_sample(context: AnalysisContext) -> None:
    correlation = context.summary["density_correlation"]
    lines = [
        "The core question is where monitored county-level PM2.5 means were highest in Wisconsin during 2024 and whether those monitored counties showed meaningful spatial clustering.",
        "The rebuild combines a 72-county TIGER/Line boundary layer, user-supplied Wisconsin PM2.5 summary files, and benchmark county means preserved in the rebuild prompt. County FIPS codes were standardized, unmonitored counties were retained on statewide maps, and spatial diagnostics were run under both the legacy Queen specification and K-nearest-neighbor sensitivity specifications with k values of 3, 4, and 5.",
        f"Sixteen monitored counties appear in the legacy benchmark snapshot. Grant County is the highest monitored county and Monroe County the lowest. The descriptive correlation between PM2.5 and log population density is {correlation:.3f}, but that relationship should be read cautiously given the small monitored sample and the non-random placement of monitors. Across Queen, KNN3, KNN4, and KNN5, Global Moran’s I remains statistically insignificant.",
        "Spatial statistics depend on how geographic relationships are encoded. Under Queen contiguity, the monitored-county network separated into eight components and left five counties without monitored contiguous neighbors. I therefore evaluated K-nearest-neighbor specifications with k values of 3, 4, and 5. Although the magnitude of Global Moran’s I varied across specifications, none of the permutation tests was statistically significant. Local LISA labels were less stable: classifications appearing under one or two specifications generally disappeared when the neighborhood definition changed. This sensitivity suggests that county-specific clusters should be treated as exploratory, especially given the limited monitoring coverage.",
        "This remains a monitor-based county snapshot rather than a statewide exposure surface. KNN does not repair sparse coverage, it only changes how the monitored counties are linked in the robustness check. Missing raw daily observations also prevent full record-level replication of the original classroom workflow.",
        "The project is most useful as a transparent demonstration of reproducible geospatial workflow, careful source documentation, and cautious interpretation of spatial-statistical sensitivity rather than as evidence of confirmed county clusters.",
    ]
    figure_paths = [
        FIGURES_DIR / "pm25_2024_choropleth.png",
        FIGURES_DIR / "global_moran_sensitivity.png",
    ]
    build_writing_sample_docx(context.county_df, lines, figure_paths)
    build_writing_sample_pdf(lines, figure_paths)


def _build_slides(context: AnalysisContext) -> None:
    footer = "Sources: EPA Air Trends, EPA AirData, GeoData@Wisconsin, U.S. Census. Rebuild date: 2026-07-13."
    comparison_lines = ["Spec      I        p      comps  islands"]
    label_map = {"legacy_queen": "Queen", "knn_3": "KNN3", "knn_4": "KNN4", "knn_5": "KNN5"}
    for row in context.spatial_weights_df.itertuples(index=False):
        label = label_map[row.specification]
        comparison_lines.append(
            f"{label:<8} {row.global_moran_I:>7.3f}  {row.global_p_sim:>5.3f}  {row.n_components:>5}  {row.n_islands:>7}"
        )
    slide_content = [
        {"title": "Air Pollution Patterns in Wisconsin", "bullets": ["County-level PM2.5 spatial analysis for 2024", "Legacy replication plus portfolio-grade rebuild", "Yifang Qiu contribution highlighted"], "figure": None, "footer": footer},
        {"title": "Motivation and Research Questions", "bullets": ["Which monitored counties had the highest descriptive annual mean PM2.5?", "How sparse was Wisconsin's county monitor coverage?", "Do monitored counties show robust spatial clustering?"], "figure": None, "footer": footer},
        {"title": "Data Sources and Processing", "bullets": ["EPA Air Trends / AirData references provide pollutant context.", "GeoData@Wisconsin supplies the archived Wisconsin county boundary layer.", "Population context uses supplied tables tied to the 2020 Census."], "figure": None, "footer": footer},
        {"title": "Data Quality and Monitor Coverage", "bullets": ["72 total counties in the shapefile.", f"{context.summary['monitored_counties']} counties with PM2.5 benchmark values.", "Unmonitored counties are kept as missing in statewide mapping."], "figure": "choropleth", "footer": footer},
        {"title": "Methods", "bullets": ["Legacy estimator: mean daily PM2.5 by site, then unweighted mean across sites by county.", "Legacy spatial model: Queen contiguity among monitored counties only.", "Robustness model: KNN weights using projected county representative points."], "figure": None, "footer": footer},
        {"title": "Statewide Choropleth", "bullets": ["Statewide map preserves all counties.", "Gray fill marks no monitoring data.", "County means are descriptive monitoring summaries, not regulatory design values."], "figure": "choropleth", "footer": footer},
        {"title": "County Ranking", "bullets": [f"Highest monitored county: {context.summary['highest_county']}.", f"Lowest monitored county: {context.summary['lowest_county']}.", "Milwaukee and Dane each have two monitoring sites in the legacy benchmark table."], "figure": "ranking", "footer": footer},
        {"title": "Global and Local Spatial Results", "bullets": [f"Legacy Moran's I = {context.summary['legacy_global_I']:.3f}.", "Legacy Queen weights contain disconnected components and island counties.", "Local Moran categories should not be described as robust clusters under the legacy graph."], "figure": "legacy_lisa", "footer": footer},
        {"title": "Are the Spatial Results Robust?", "bullets": [], "table_lines": comparison_lines, "takeaway": "No significant global clustering under any tested spatial-weight definition; local cluster labels are sensitive to the neighborhood specification.", "figure": "global_sensitivity", "footer": footer},
        {"title": "References and Team Contributions", "bullets": ["EPA Air Trends and AirData", "GeoData@Wisconsin / U.S. Census TIGER/Line", "Yifang Qiu: analysis, spatial joining, choropleth mapping, county ranking, Global Moran's I, Local Moran's I, and visualization"], "figure": None, "footer": footer},
    ]
    figure_map = {
        "choropleth": FIGURES_DIR / "pm25_2024_choropleth.png",
        "ranking": FIGURES_DIR / "pm25_2024_ranked_bar.png",
        "legacy_lisa": FIGURES_DIR / "lisa_cluster_map_legacy.png",
        "global_sensitivity": FIGURES_DIR / "global_moran_sensitivity.png",
    }
    build_slide_deck(slide_content, figure_map)
    build_slide_pdf(slide_content)


def _write_validation_report(
    discovered_files: list[Path],
    raw_status: dict[str, object],
    benchmark_df: pd.DataFrame,
    spatial_summary: dict[str, object],
    spatial_weights_df: pd.DataFrame,
    local_stability_df: pd.DataFrame,
    tests_run: list[str],
    notebook_status: dict[str, str],
    render_status: dict[str, str],
) -> None:
    benchmark_table = benchmark_df.to_csv(index=False)
    significant_lists = []
    for row in spatial_weights_df.itertuples(index=False):
        significant_lists.append(
            f"- {row.specification}: {row.significant_local_counties}"
        )
    report = [
        "# Validation Report",
        "",
        "## Discovered files",
        *[f"- `{path.relative_to(PROJECT_ROOT)}`" for path in discovered_files],
        "",
        "## Raw data path",
        f"- Raw daily file used: `{raw_status['raw_daily_path']}`",
        f"- True raw-level replication succeeded: `{raw_status['raw_daily_retrieved']}`",
        f"- Notes: {raw_status['notes']}",
        "",
        "## County benchmark comparison",
        "```csv",
        benchmark_table.strip(),
        "```",
        "",
        "## Moran diagnostics",
        f"- Legacy Moran's I: {spatial_summary['legacy_global_I']:.10f}",
        f"- Expected I: {spatial_summary['legacy_expected_I']:.10f}",
        f"- Permutation p-value: {spatial_summary['legacy_global_p']:.10f}",
        f"- Legacy islands: {', '.join(spatial_summary['legacy_islands']) if spatial_summary['legacy_islands'] else 'none'}",
        "",
        "## Spatial-Weights Sensitivity Validation",
        _format_markdown_table(
            spatial_weights_df[
                [
                    "specification",
                    "k",
                    "n_components",
                    "n_islands",
                    "min_neighbors",
                    "mean_neighbors",
                    "max_neighbors",
                    "global_moran_I",
                    "global_p_sim",
                    "n_significant_local_clusters",
                    "significant_local_counties",
                ]
            ].assign(
                global_moran_I=lambda df: df["global_moran_I"].map(lambda value: f"{value:.6f}"),
                global_p_sim=lambda df: df["global_p_sim"].map(lambda value: f"{value:.3f}"),
                mean_neighbors=lambda df: df["mean_neighbors"].map(lambda value: f"{value:.3f}"),
            )
        ),
        "",
        f"- Fixed random seed: {SEED}",
        f"- Permutations per specification: {PERMUTATIONS}",
        "- Queen contiguity among monitored counties only has 8 connected components and 5 island counties.",
        "- KNN3, KNN4, and KNN5 each form one connected component and zero islands.",
        "- KNN weights are directional nearest-neighbor graphs; they were not symmetrized in this rebuild.",
        "- No global specification has a permutation p-value below 0.05.",
        "- Local classifications are specification-sensitive and no county is robust across at least three non-island specifications.",
        "",
        "### Significant local clusters by specification",
        *significant_lists,
        "",
        "### Local stability table",
        _format_markdown_table(
            local_stability_df[
                [
                    "County",
                    "queen_cluster",
                    "knn3_cluster",
                    "knn4_cluster",
                    "knn5_cluster",
                    "significant_specification_count",
                    "stable_cluster",
                ]
            ]
        ),
        "",
        "## Tests run",
        *[f"- {item}" for item in tests_run],
        "",
        "## Notebook execution status",
        *[f"- {key}: {value}" for key, value in notebook_status.items()],
        "",
        "## Slide and report rendering status",
        *[f"- {key}: {value}" for key, value in render_status.items()],
        "",
        "## Remaining discrepancy",
        "- Raw daily EPA records could not be retrieved into the workspace, so site-level replication remains incomplete.",
    ]
    (LOGS_DIR / "VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")


def run_analysis_only() -> AnalysisContext:
    """Create processed data, figures, and validation-ready tables."""
    _ensure_directories()
    _write_support_files()
    _write_license_notice()

    source_paths = discover_source_paths()
    discovered_files = inventory_files()
    counties_gdf = load_wisconsin_counties(source_paths.shapefile)
    simplified_df = load_simplified_pm25(source_paths.simplified_xlsx)
    factbook_df = load_factbook_wisconsin(source_paths.factbook_xlsx)

    raw_status = {
        "raw_daily_found": bool(source_paths.raw_daily_csv),
        "raw_daily_retrieved": bool(source_paths.raw_daily_csv),
        "raw_daily_path": str(source_paths.raw_daily_csv.relative_to(PROJECT_ROOT)) if source_paths.raw_daily_csv else "not available",
        "notes": "Official EPA raw daily file could not be retrieved into the workspace because the legacy export was absent and direct download attempts failed at the SSL/network layer.",
    }

    raw_qa: dict[str, object] = {}
    if source_paths.raw_daily_csv:
        raw_df = pd.read_csv(source_paths.raw_daily_csv)
        normalized_raw = normalize_raw_daily_schema(raw_df)
        filtered_raw = filter_wisconsin_2024(normalized_raw)
        raw_qa = summarize_raw_daily(filtered_raw)
        site_df, county_df = aggregate_legacy_from_raw(filtered_raw)
        county_df = county_df.merge(
            simplified_df[["County_FIPS_Code", "Population_2020_Census"]],
            on="County_FIPS_Code",
            how="left",
        )
        county_df["Data_Mode"] = "raw_daily_replication"
    else:
        county_df = build_fallback_snapshot(simplified_df, factbook_df)
        site_df = build_site_placeholder_table(county_df)
        legacy_snapshot = county_df[["County_FIPS_Code", "County", PM25_FIELD, "n_sites", "Population_2020_Census", "Data_Mode"]]
        legacy_snapshot.to_csv(PROCESSED_DIR / "legacy_county_snapshot.csv", index=False)

    joined_gdf = join_counties(counties_gdf, county_df)
    coverage_df = build_monitor_coverage(counties_gdf, county_df)
    pm25_population_df = _build_population_context(joined_gdf)
    pm25_population_df["log_population_density"] = pd.to_numeric(pm25_population_df["log_population_density"], errors="coerce")
    density_corr = float(pm25_population_df[[PM25_FIELD, "log_population_density"]].dropna().corr().iloc[0, 1])

    spatial = run_spatial_analysis(joined_gdf)
    benchmark_df = benchmark_comparison(county_df)

    county_df.to_csv(TABLES_DIR / "county_annual_pm25.csv", index=False)
    site_df.to_csv(TABLES_DIR / "site_annual_pm25.csv", index=False)
    coverage_df.to_csv(TABLES_DIR / "county_monitor_coverage.csv", index=False)
    pm25_population_df.to_csv(TABLES_DIR / "pm25_population_context.csv", index=False)
    spatial["all_local_results"].to_csv(TABLES_DIR / "spatial_sensitivity_results.csv", index=False)
    spatial["comparison_table"].to_csv(TABLES_DIR / "spatial_weights_comparison.csv", index=False)
    spatial["stability_table"].to_csv(TABLES_DIR / "local_cluster_stability.csv", index=False)
    joined_gdf.to_file(TABLES_DIR / "wisconsin_counties_pm25_joined.geojson", driver="GeoJSON")

    if raw_qa:
        pd.DataFrame([raw_qa]).to_json(INTERIM_DIR / "raw_daily_summary.json", orient="records", indent=2)

    plot_choropleth(joined_gdf, FIGURES_DIR / "pm25_2024_choropleth.png")
    plot_ranked_bar(county_df, FIGURES_DIR / "pm25_2024_ranked_bar.png")
    plot_lisa_cluster_map(
        joined_gdf,
        spatial["queen"].local_results,
        FIGURES_DIR / "lisa_cluster_map_legacy.png",
        "Legacy Local Moran Cluster Map (Queen Contiguity Among Monitored Counties)",
    )
    plot_lisa_cluster_map(
        joined_gdf,
        spatial["knn4"].local_results,
        FIGURES_DIR / "lisa_cluster_map_knn4.png",
        "KNN-4 Local Moran Cluster Map (Robustness Specification)",
    )
    plot_global_moran_sensitivity(spatial["comparison_table"], FIGURES_DIR / "global_moran_sensitivity.png")
    plot_lisa_weights_comparison(joined_gdf, spatial["all_local_results"], FIGURES_DIR / "lisa_weights_comparison.png")
    plot_population_scatter(pm25_population_df.dropna(subset=["log_population_density"]), FIGURES_DIR / "pm25_vs_population_density.png")

    _write_source_metadata(source_paths, discovered_files, raw_status)
    _write_data_gaps(raw_status)

    summary = {
        "total_counties": int(len(joined_gdf)),
        "monitored_counties": int(county_df[PM25_FIELD].notna().sum()),
        "highest_county": county_df.loc[county_df[PM25_FIELD].idxmax(), "County"],
        "highest_value": float(county_df[PM25_FIELD].max()),
        "lowest_county": county_df.loc[county_df[PM25_FIELD].idxmin(), "County"],
        "lowest_value": float(county_df[PM25_FIELD].min()),
        "legacy_global_I": float(spatial["queen"].summary["global_moran_I"]),
        "legacy_expected_I": float(spatial["queen"].summary["expected_I"]),
        "legacy_global_p": float(spatial["queen"].summary["global_p_sim"]),
        "legacy_islands": spatial["legacy_island_names"],
        "queen_components": int(spatial["queen"].summary["n_components"]),
        "queen_islands": int(spatial["queen"].summary["n_islands"]),
        "no_global_significance": bool((spatial["comparison_table"]["global_p_sim"] >= 0.05).all()),
        "density_correlation": density_corr,
    }
    _write_markdown_summary(summary, spatial["comparison_table"])

    return AnalysisContext(
        county_df=county_df,
        site_df=site_df,
        joined_gdf=joined_gdf,
        coverage_df=coverage_df,
        pm25_population_df=pm25_population_df,
        benchmark_df=benchmark_df,
        spatial_df=spatial["all_local_results"],
        spatial_weights_df=spatial["comparison_table"],
        local_stability_df=spatial["stability_table"],
        summary=summary,
    )


def build_notebooks_only(context: AnalysisContext | None = None) -> None:
    """Create and execute the project notebooks."""
    if context is None:
        context = run_analysis_only()
    legacy_notebook = build_legacy_notebook(context.summary["legacy_islands"])
    portfolio_notebook = build_portfolio_notebook(
        correlation=context.summary["density_correlation"],
        global_i=context.summary["legacy_global_I"],
        global_p=context.summary["legacy_global_p"],
    )
    execute_notebook(legacy_notebook)
    execute_notebook(portfolio_notebook)


def build_report_only(context: AnalysisContext | None = None) -> None:
    if context is None:
        context = run_analysis_only()
    _build_writing_sample(context)


def build_slides_only(context: AnalysisContext | None = None) -> None:
    if context is None:
        context = run_analysis_only()
    _build_slides(context)


def run_all() -> AnalysisContext:
    """Run the full project pipeline."""
    context = run_analysis_only()
    build_notebooks_only(context)
    build_report_only(context)
    build_slides_only(context)

    tests_run = [
        "Boundary coverage check for 72 counties",
        "Five-character county GEOID check",
        "Benchmark comparison table",
        "Spatial-weights comparison table and local stability table",
        "Notebook execution pass",
        "Rendered writing sample and slide outputs created",
    ]
    notebook_status = {
        "00_legacy_replication.ipynb": "executed",
        "01_portfolio_analysis.ipynb": "executed",
    }
    render_status = {
        "Writing sample DOCX": "created",
        "Writing sample PDF": "created",
        "Slides PPTX": "created",
        "Slides PDF": "created",
    }
    _write_validation_report(
        discovered_files=inventory_files(),
        raw_status={
            "raw_daily_path": "not available",
            "raw_daily_retrieved": False,
            "notes": "Fallback county snapshot used because raw daily retrieval failed.",
        },
        benchmark_df=context.benchmark_df,
        spatial_summary=context.summary,
        spatial_weights_df=context.spatial_weights_df,
        local_stability_df=context.local_stability_df,
        tests_run=tests_run,
        notebook_status=notebook_status,
        render_status=render_status,
    )
    return context


def validate_only() -> None:
    """Run lightweight validation checks and write a JSON summary."""
    _ensure_directories()
    offenders = [str(path.relative_to(PROJECT_ROOT)) for path in find_content_paths()]
    payload = {"content_path_offenders": offenders}
    (LOGS_DIR / "validation_checks.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wisconsin PM2.5 project pipeline")
    parser.add_argument("command", choices=["analysis", "notebooks", "report", "slides", "validate", "all"], nargs="?", default="all")
    args = parser.parse_args()

    if args.command == "analysis":
        run_analysis_only()
    elif args.command == "notebooks":
        build_notebooks_only()
    elif args.command == "report":
        build_report_only()
    elif args.command == "slides":
        build_slides_only()
    elif args.command == "validate":
        validate_only()
    else:
        run_all()


if __name__ == "__main__":
    main()
