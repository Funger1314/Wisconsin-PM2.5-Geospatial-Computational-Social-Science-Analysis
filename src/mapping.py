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
    plot_gdf = joined_gdf.merge(
        local_results[["County_FIPS_Code", "cluster"]],
        on="County_FIPS_Code",
        how="left",
    )
    plot_gdf["cluster"] = plot_gdf["cluster"].fillna("No monitoring data")

    fig, ax = plt.subplots(figsize=(11, 8.5))
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
    legend_handles = [
        Patch(facecolor=palette[category], edgecolor="black", hatch="///" if category == "No neighbors" else None, label=category)
        for category in category_order
    ]
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
