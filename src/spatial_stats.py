"""Spatial-weights construction and Moran statistics."""

from __future__ import annotations

from dataclasses import dataclass

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


def _run_single_spec(
    monitored_gdf: gpd.GeoDataFrame,
    specification: str,
    kind: str,
    k: int | None = None,
) -> SpatialRun:
    values = monitored_gdf[PM25_FIELD].to_numpy()
    weights = _build_weights(monitored_gdf, kind=kind, k=k)
    components, island_ids = _connected_components(weights)
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
    local_results["global_moran_I"] = global_moran.I
    local_results["expected_I"] = global_moran.EI
    local_results["global_p_sim"] = global_moran.p_sim
    local_results["global_z_sim"] = global_moran.z_sim
    local_results["n_components"] = components
    local_results["n_islands"] = len(island_ids)
    local_results["seed"] = SEED
    local_results["permutations"] = PERMUTATIONS
    summary = {
        "specification": specification,
        "k": k,
        "global_moran_I": float(global_moran.I),
        "expected_I": float(global_moran.EI),
        "global_p_sim": float(global_moran.p_sim),
        "global_z_sim": float(global_moran.z_sim),
        "n_components": int(components),
        "n_islands": int(len(island_ids)),
        "island_fips": list(island_ids),
    }
    return SpatialRun(local_results=local_results, summary=summary)


def run_spatial_analysis(joined_gdf: gpd.GeoDataFrame) -> dict[str, object]:
    """Run legacy Queen and KNN sensitivity analyses."""
    monitored = joined_gdf[joined_gdf[PM25_FIELD].notna()].copy().reset_index(drop=True)
    queen = _run_single_spec(monitored, specification="legacy_queen", kind="queen")
    knn_runs = [_run_single_spec(monitored, specification=f"knn_{k}", kind="knn", k=k) for k in (3, 4, 5)]
    all_local = pd.concat([queen.local_results] + [run.local_results for run in knn_runs], ignore_index=True)
    island_name_map = (
        monitored.loc[monitored["County_FIPS_Code"].isin(queen.summary["island_fips"]), ["County_FIPS_Code", "County"]]
        .sort_values("County")
        .values.tolist()
    )
    return {
        "monitored_counties": monitored,
        "queen": queen,
        "knn_runs": knn_runs,
        "all_local_results": all_local,
        "legacy_island_names": [name for _, name in island_name_map],
        "knn4": next(run for run in knn_runs if run.summary["k"] == 4),
    }
