"""Plotting functions for maps, charts, and context graphics."""

from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd

os.environ.setdefault("MPLCONFIGDIR", str((Path(__file__).resolve().parents[1] / ".mplconfig")))
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from .paths import PM25_FIELD


def _cluster_palette() -> tuple[dict[str, str], list[str]]:
    palette = {
        "High-High": "#d73027",
        "Low-Low": "#4575b4",
        "Low-High": "#74add1",
        "High-Low": "#f46d43",
        "Not significant": "#d9d9d9",
        "No neighbors": "#f7f7f7",
        "No monitoring data": "#efefef",
    }
    category_order = [
        "High-High",
        "Low-Low",
        "Low-High",
        "High-Low",
        "Not significant",
        "No neighbors",
        "No monitoring data",
    ]
    return palette, category_order


def _save_dual(fig: plt.Figure, png_path: Path) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path = png_path.with_suffix(".svg")
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_choropleth(joined_gdf: gpd.GeoDataFrame, png_path: Path) -> None:
    """Render the statewide county choropleth."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    joined_gdf.plot(
        column=PM25_FIELD,
        cmap="OrRd",
        linewidth=0.6,
        edgecolor="black",
        legend=True,
        missing_kwds={"color": "#d9d9d9", "edgecolor": "black", "label": "No monitoring data"},
        ax=ax,
    )
    ax.set_title("Wisconsin County-Level Annual Mean PM2.5 (2024)", fontsize=16, pad=12)
    ax.set_axis_off()
    _save_dual(fig, png_path)


def plot_ranked_bar(county_df: pd.DataFrame, png_path: Path) -> None:
    """Render the monitored-county ranking chart."""
    ordered = county_df.sort_values(PM25_FIELD, ascending=False).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    ax.barh(ordered["County"], ordered[PM25_FIELD], color="#c23b22")
    ax.invert_yaxis()
    ax.set_xlabel("Annual mean PM2.5 ($\\mu g/m^3$)", fontsize=12)
    ax.set_ylabel("County", fontsize=12)
    ax.set_title("Monitored Wisconsin Counties Ranked by Annual Mean PM2.5", fontsize=15, pad=12)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    _save_dual(fig, png_path)


def plot_lisa_cluster_map(
    joined_gdf: gpd.GeoDataFrame,
    local_results: pd.DataFrame,
    png_path: Path,
    title: str,
) -> None:
    """Render a manual-legend LISA cluster map."""
    palette, category_order = _cluster_palette()
    plot_gdf = joined_gdf.merge(
        local_results[["County_FIPS_Code", "cluster"]],
        on="County_FIPS_Code",
        how="left",
    )
    plot_gdf["cluster"] = plot_gdf["cluster"].fillna("No monitoring data")

    fig, ax = plt.subplots(figsize=(11, 8.5))
    _plot_lisa_panel(ax=ax, plot_gdf=plot_gdf, palette=palette, category_order=category_order)
    legend_handles = _legend_handles(palette, category_order)
    ax.legend(
        handles=legend_handles,
        title="Local Moran category",
        loc="lower left",
        frameon=True,
        fontsize=9,
        title_fontsize=10,
    )
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_axis_off()
    _save_dual(fig, png_path)


def _plot_lisa_panel(
    ax: plt.Axes,
    plot_gdf: gpd.GeoDataFrame,
    palette: dict[str, str],
    category_order: list[str],
) -> None:
    """Plot a single LISA classification panel with consistent styling."""
    for category in category_order:
        subset = plot_gdf[plot_gdf["cluster"] == category]
        if subset.empty:
            continue
        hatch = "///" if category == "No neighbors" else None
        subset.plot(
            color=palette[category],
            edgecolor="black",
            linewidth=0.6,
            hatch=hatch,
            ax=ax,
        )


def _legend_handles(palette: dict[str, str], category_order: list[str]) -> list[Patch]:
    """Create shared legend handles for LISA figures."""
    return [
        Patch(facecolor=palette[category], edgecolor="black", hatch="///" if category == "No neighbors" else None, label=category)
        for category in category_order
    ]


def plot_global_moran_sensitivity(comparison_df: pd.DataFrame, png_path: Path) -> None:
    """Render a clean comparison of Global Moran's I across weight specifications."""
    label_map = {
        "legacy_queen": "Queen",
        "knn_3": "KNN3",
        "knn_4": "KNN4",
        "knn_5": "KNN5",
    }
    ordered = comparison_df.copy()
    ordered["label"] = ordered["specification"].map(label_map)
    ordered["sort_order"] = ordered["specification"].map({"legacy_queen": 0, "knn_3": 1, "knn_4": 2, "knn_5": 3})
    ordered = ordered.sort_values("sort_order").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    colors = ["#981c24", "#4c78a8", "#72b7b2", "#54a24b"]
    x = np.arange(len(ordered))
    ax.axhline(
        float(ordered["expected_I"].iloc[0]),
        color="#444444",
        linestyle="--",
        linewidth=1.4,
        label="Expected I under spatial randomness",
    )
    ax.plot(x, ordered["global_moran_I"], color="#444444", linewidth=1.4, zorder=2)
    ax.scatter(x, ordered["global_moran_I"], s=110, color=colors, edgecolor="white", linewidth=0.8, zorder=3)
    for idx, row in ordered.iterrows():
        offset = 0.012 if row["global_moran_I"] <= float(ordered["expected_I"].iloc[0]) else -0.016
        va = "bottom" if offset > 0 else "top"
        ax.text(
            idx,
            row["global_moran_I"] + offset,
            f"p={row['global_p_sim']:.3f}",
            ha="center",
            va=va,
            fontsize=10,
            color="#333333",
        )
    ax.set_xticks(x, ordered["label"])
    ax.set_ylabel("Global Moran's I", fontsize=12)
    ax.set_title("Global Moran's I Across Spatial-Weight Specifications", fontsize=15, pad=14)
    fig.text(
        0.5,
        0.93,
        "None of the global permutation tests is statistically significant at alpha = 0.05.",
        ha="center",
        fontsize=11,
        color="#444444",
    )
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(loc="lower right", frameon=True, fontsize=10)
    _save_dual(fig, png_path)


def plot_lisa_weights_comparison(
    joined_gdf: gpd.GeoDataFrame,
    local_results_df: pd.DataFrame,
    png_path: Path,
) -> None:
    """Render a four-panel LISA comparison across Queen and KNN specifications."""
    panel_specs = [
        ("legacy_queen", "Queen contiguity"),
        ("knn_3", "KNN (k = 3)"),
        ("knn_4", "KNN (k = 4)"),
        ("knn_5", "KNN (k = 5)"),
    ]
    palette, category_order = _cluster_palette()
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    axes_flat = axes.flatten()
    for ax, (specification, title) in zip(axes_flat, panel_specs):
        spec_df = local_results_df[local_results_df["specification"] == specification]
        plot_gdf = joined_gdf.merge(
            spec_df[["County_FIPS_Code", "cluster"]],
            on="County_FIPS_Code",
            how="left",
        )
        plot_gdf["cluster"] = plot_gdf["cluster"].fillna("No monitoring data")
        _plot_lisa_panel(ax=ax, plot_gdf=plot_gdf, palette=palette, category_order=category_order)
        ax.set_title(title, fontsize=13, pad=8)
        ax.set_axis_off()
    handles = _legend_handles(palette, category_order)
    fig.legend(
        handles=handles,
        title="Local Moran category",
        loc="lower center",
        ncols=4,
        frameon=True,
        fontsize=10,
        title_fontsize=11,
        bbox_to_anchor=(0.5, 0.03),
    )
    fig.suptitle("Local Moran Cluster Sensitivity Across Spatial-Weight Specifications", fontsize=16, y=0.97)
    fig.text(
        0.5,
        0.94,
        "County outlines, extent, cluster colors, and alpha = 0.05 threshold are held constant across panels.",
        ha="center",
        fontsize=11,
        color="#444444",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.92))
    _save_dual(fig, png_path)


def plot_population_scatter(pm25_population_df: pd.DataFrame, png_path: Path) -> None:
    """Render PM2.5 versus population density for monitored counties."""
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    ax.scatter(
        pm25_population_df["log_population_density"],
        pm25_population_df[PM25_FIELD],
        color="#7f0000",
        edgecolor="white",
        s=85,
    )
    for _, row in pm25_population_df.nlargest(4, "Population_2020_Census").iterrows():
        ax.annotate(row["County"], (row["log_population_density"], row[PM25_FIELD]), xytext=(5, 5), textcoords="offset points", fontsize=9)
    ax.set_xlabel("Log population density (persons per sq. km)", fontsize=12)
    ax.set_ylabel("Annual mean PM2.5 ($\\mu g/m^3$)", fontsize=12)
    ax.set_title("PM2.5 and Population Density Across Monitored Wisconsin Counties", fontsize=14, pad=12)
    ax.grid(alpha=0.3, linestyle="--")
    _save_dual(fig, png_path)
