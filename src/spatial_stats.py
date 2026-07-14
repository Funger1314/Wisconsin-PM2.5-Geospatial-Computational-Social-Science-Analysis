"""Spatial-weights construction and Moran statistics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from esda import Moran, Moran_Local
from libpysal.weights import KNN, Queen

from .paths import PERMUTATIONS, PM25_FIELD, PROJECTED_CRS, SEED


@dataclass
class SpatialRun:
    """Container for a spatial specification and its outputs."""

    specification: str
    weights_definition: str
    weights: Any
    local_results: pd.DataFrame
    summary: dict[str, object]


def _build_weights(monitored_gdf: gpd.GeoDataFrame, kind: str, k: int | None = None):
    ids = monitored_gdf["County_FIPS_Code"].tolist()
    if kind == "queen":
        weights = Queen.from_dataframe(monitored_gdf, ids=ids, use_index=False)
    elif kind == "knn":
        projected = monitored_gdf.to_crs(PROJECTED_CRS)
        points = projected.representative_point()
        coords = np.column_stack([points.x.to_numpy(), points.y.to_numpy()])
        weights = KNN.from_array(coords, k=k or 4, ids=ids)
    else:
        raise ValueError(f"Unsupported weights kind: {kind}")
    weights.transform = "R"
    return weights


def _connected_components(weights) -> tuple[int, list[str]]:
    graph = weights.to_networkx().to_undirected()
    components = nx.number_connected_components(graph)
    return components, list(weights.islands)


def _weights_definition(kind: str, k: int | None, is_asymmetric: bool) -> str:
    """Create a recruiter-readable weight-specification description."""
    if kind == "queen":
        return (
            "Queen contiguity among monitored counties only; row-standardized shared-boundary weights. "
            "This preserves the legacy specification but fragments when monitored counties do not touch."
        )
    asymmetry_note = "asymmetric neighbor lists" if is_asymmetric else "symmetric neighbor lists"
    return (
        f"Directed K-nearest-neighbor weights using county representative points in {PROJECTED_CRS}; "
        f"k={k}; row-standardized; {asymmetry_note}; not symmetrized."
    )


def _classify_local(local: Moran_Local, island_ids: set[str], fips: pd.Series) -> tuple[list[str], list[bool]]:
    quadrant_map = {1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"}
    clusters: list[str] = []
    island_mask: list[bool] = []
    for idx, county_fips in enumerate(fips.tolist()):
        is_island = county_fips in island_ids
        island_mask.append(is_island)
        if is_island:
            clusters.append("No neighbors")
        elif local.p_sim[idx] < 0.05:
            clusters.append(quadrant_map.get(int(local.q[idx]), "Not significant"))
        else:
            clusters.append("Not significant")
    return clusters, island_mask


def _significant_local_rows(local_results: pd.DataFrame) -> pd.DataFrame:
    """Return statistically significant non-island LISA rows."""
    return local_results[
        (~local_results["is_island"]) & local_results["cluster"].ne("Not significant")
    ].copy()


def _format_significant_local_counties(local_results: pd.DataFrame) -> str:
    """Format a compact specification-level list of significant local counties."""
    significant = _significant_local_rows(local_results)
    if significant.empty:
        return "None"
    return "; ".join(
        f"{row.County} ({row.cluster})" for row in significant.itertuples(index=False)
    )


def _run_single_spec(
    monitored_gdf: gpd.GeoDataFrame,
    specification: str,
    kind: str,
    k: int | None = None,
) -> SpatialRun:
    values = monitored_gdf[PM25_FIELD].to_numpy()
    weights = _build_weights(monitored_gdf, kind=kind, k=k)
    components, island_ids = _connected_components(weights)
    is_asymmetric = bool(getattr(weights, "asymmetries", []))
    neighbor_counts = pd.Series(weights.cardinalities, name="n_neighbors")
    np.random.seed(SEED)
    global_moran = Moran(values, weights, permutations=PERMUTATIONS)
    local = Moran_Local(values, weights, permutations=PERMUTATIONS, seed=SEED, island_weight=0)
    clusters, island_mask = _classify_local(local, set(island_ids), monitored_gdf["County_FIPS_Code"])
    local_results = monitored_gdf[
        ["County_FIPS_Code", "County", PM25_FIELD]
    ].copy()
    local_results["specification"] = specification
    local_results["k"] = k
    local_results["local_moran_I"] = local.Is
    local_results["local_p_sim"] = local.p_sim
    local_results["quadrant"] = local.q
    local_results["cluster"] = clusters
    local_results["is_island"] = island_mask
    local_results["alpha_0_05_significant"] = (~local_results["is_island"]) & local_results["cluster"].ne("Not significant")
    local_results["n_neighbors"] = local_results["County_FIPS_Code"].map(neighbor_counts)
    local_results["global_moran_I"] = global_moran.I
    local_results["expected_I"] = global_moran.EI
    local_results["global_p_sim"] = global_moran.p_sim
    local_results["global_z_sim"] = global_moran.z_sim
    local_results["n_components"] = components
    local_results["n_islands"] = len(island_ids)
    local_results["seed"] = SEED
    local_results["permutations"] = PERMUTATIONS
    significant_locals = _significant_local_rows(local_results)
    weights_definition = _weights_definition(kind=kind, k=k, is_asymmetric=is_asymmetric)
    summary = {
        "specification": specification,
        "weights_definition": weights_definition,
        "k": k,
        "n_counties": int(len(monitored_gdf)),
        "global_moran_I": float(global_moran.I),
        "expected_I": float(global_moran.EI),
        "global_p_sim": float(global_moran.p_sim),
        "global_z_sim": float(global_moran.z_sim),
        "n_components": int(components),
        "n_islands": int(len(island_ids)),
        "min_neighbors": int(neighbor_counts.min()),
        "mean_neighbors": float(neighbor_counts.mean()),
        "max_neighbors": int(neighbor_counts.max()),
        "n_significant_local_clusters": int(len(significant_locals)),
        "significant_local_counties": _format_significant_local_counties(local_results),
        "is_asymmetric": is_asymmetric,
        "asymmetry_count": int(len(getattr(weights, "asymmetries", []))),
        "island_fips": list(island_ids),
    }
    return SpatialRun(
        specification=specification,
        weights_definition=weights_definition,
        weights=weights,
        local_results=local_results,
        summary=summary,
    )


def build_spatial_weights_comparison(runs: list[SpatialRun]) -> pd.DataFrame:
    """Build the one-row-per-specification comparison table."""
    rows = [run.summary for run in runs]
    comparison = pd.DataFrame(rows)
    column_order = [
        "specification",
        "weights_definition",
        "k",
        "n_counties",
        "n_components",
        "n_islands",
        "min_neighbors",
        "mean_neighbors",
        "max_neighbors",
        "global_moran_I",
        "expected_I",
        "global_p_sim",
        "global_z_sim",
        "n_significant_local_clusters",
        "significant_local_counties",
    ]
    return comparison[column_order].copy()


def build_local_cluster_stability(
    local_results: pd.DataFrame,
    monitored_gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Summarize county-level cluster stability across specifications."""
    specifications = {
        "legacy_queen": ("queen_cluster", "queen_p"),
        "knn_3": ("knn3_cluster", "knn3_p"),
        "knn_4": ("knn4_cluster", "knn4_p"),
        "knn_5": ("knn5_cluster", "knn5_p"),
    }
    stability = monitored_gdf[["County", "County_FIPS_Code", PM25_FIELD]].copy()
    significance_specs: dict[str, list[str]] = {county_fips: [] for county_fips in stability["County_FIPS_Code"]}
    significance_labels: dict[str, list[str]] = {county_fips: [] for county_fips in stability["County_FIPS_Code"]}

    for specification, (cluster_col, p_col) in specifications.items():
        spec_df = local_results[local_results["specification"] == specification][
            ["County_FIPS_Code", "cluster", "local_p_sim", "alpha_0_05_significant"]
        ].rename(columns={"cluster": cluster_col, "local_p_sim": p_col})
        stability = stability.merge(spec_df.drop(columns=["alpha_0_05_significant"]), on="County_FIPS_Code", how="left")
        significant_rows = local_results[
            (local_results["specification"] == specification) & local_results["alpha_0_05_significant"]
        ][["County_FIPS_Code", "cluster"]]
        for row in significant_rows.itertuples(index=False):
            significance_specs[row.County_FIPS_Code].append(specification)
            significance_labels[row.County_FIPS_Code].append(row.cluster)

    stable_clusters: list[str] = []
    stability_interpretations: list[str] = []
    significant_counts: list[int] = []
    for row in stability.itertuples(index=False):
        spec_hits = significance_specs[row.County_FIPS_Code]
        label_hits = significance_labels[row.County_FIPS_Code]
        significant_counts.append(len(spec_hits))
        label_counts = pd.Series(label_hits).value_counts() if label_hits else pd.Series(dtype="int64")
        stable_label = "Not robust"
        if not label_counts.empty and int(label_counts.iloc[0]) >= 3:
            stable_label = str(label_counts.index[0])
        stable_clusters.append(stable_label)
        if stable_label != "Not robust":
            interpretation = (
                f"Stable {stable_label} classification under {int(label_counts.iloc[0])} non-island specifications."
            )
        elif not spec_hits:
            interpretation = "No statistically significant local cluster under any tested specification."
        else:
            readable_specs = ", ".join(spec.replace("legacy_queen", "Queen").replace("knn_", "KNN") for spec in spec_hits)
            interpretation = (
                f"Significant local labels appear under {readable_specs} but do not persist across at least three non-island specifications."
            )
        stability_interpretations.append(interpretation)

    stability["significant_specification_count"] = significant_counts
    stability["stable_cluster"] = stable_clusters
    stability["stability_interpretation"] = stability_interpretations
    return stability.sort_values("County_FIPS_Code").reset_index(drop=True)


def run_spatial_analysis(joined_gdf: gpd.GeoDataFrame) -> dict[str, object]:
    """Run legacy Queen and KNN sensitivity analyses."""
    monitored = joined_gdf[joined_gdf[PM25_FIELD].notna()].copy().reset_index(drop=True)
    queen = _run_single_spec(monitored, specification="legacy_queen", kind="queen")
    knn_runs = [_run_single_spec(monitored, specification=f"knn_{k}", kind="knn", k=k) for k in (3, 4, 5)]
    all_runs = [queen] + knn_runs
    all_local = pd.concat([run.local_results for run in all_runs], ignore_index=True)
    comparison_table = build_spatial_weights_comparison(all_runs)
    stability_table = build_local_cluster_stability(all_local, monitored)
    island_name_map = (
        monitored.loc[monitored["County_FIPS_Code"].isin(queen.summary["island_fips"]), ["County_FIPS_Code", "County"]]
        .sort_values("County")
        .values.tolist()
    )
    return {
        "monitored_counties": monitored,
        "queen": queen,
        "knn_runs": knn_runs,
        "runs_by_specification": {run.specification: run for run in all_runs},
        "all_local_results": all_local,
        "comparison_table": comparison_table,
        "stability_table": stability_table,
        "legacy_island_names": [name for _, name in island_name_map],
        "knn4": next(run for run in knn_runs if run.summary["k"] == 4),
    }
