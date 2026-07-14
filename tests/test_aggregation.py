import geopandas as gpd
import numpy as np
import pandas as pd

from src.paths import OUTPUTS_DIR, PM25_FIELD
from src.spatial_stats import run_spatial_analysis


def _county_table() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS_DIR / "tables" / "county_annual_pm25.csv")


def _coverage_table() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS_DIR / "tables" / "county_monitor_coverage.csv")


def _spatial_results() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS_DIR / "tables" / "spatial_sensitivity_results.csv")


def _weights_comparison() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS_DIR / "tables" / "spatial_weights_comparison.csv")


def _stability_table() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS_DIR / "tables" / "local_cluster_stability.csv")


def test_monitored_counties_equal_16():
    county_df = _county_table()
    assert len(county_df) == 16


def test_highest_and_lowest_counties_match_expected():
    county_df = _county_table()
    highest = county_df.loc[county_df[PM25_FIELD].idxmax(), "County"]
    lowest = county_df.loc[county_df[PM25_FIELD].idxmin(), "County"]
    assert highest == "Grant"
    assert lowest == "Monroe"


def test_statewide_join_retains_72_rows():
    coverage_df = _coverage_table()
    assert len(coverage_df) == 72


def test_no_duplicate_county_fips_in_county_table():
    county_df = _county_table()
    assert county_df["County_FIPS_Code"].is_unique


def test_queen_components_and_islands_match_expected():
    weights_df = _weights_comparison()
    queen = weights_df.loc[weights_df["specification"] == "legacy_queen"].iloc[0]
    assert int(queen["n_components"]) == 8
    assert int(queen["n_islands"]) == 5


def test_all_knn_specifications_have_one_component_and_zero_islands():
    weights_df = _weights_comparison()
    knn = weights_df[weights_df["specification"].str.startswith("knn_")]
    assert (knn["n_components"] == 1).all()
    assert (knn["n_islands"] == 0).all()


def test_all_spatial_specifications_cover_the_same_16_counties():
    spatial_df = _spatial_results()
    county_sets = {
        specification: set(group["County_FIPS_Code"])
        for specification, group in spatial_df.groupby("specification")
    }
    expected = next(iter(county_sets.values()))
    assert len(expected) == 16
    for county_set in county_sets.values():
        assert county_set == expected


def test_fixed_seed_results_are_reproducible():
    joined = gpd.read_file(OUTPUTS_DIR / "tables" / "wisconsin_counties_pm25_joined.geojson")
    first = run_spatial_analysis(joined)["comparison_table"].set_index("specification")
    second = run_spatial_analysis(joined)["comparison_table"].set_index("specification")
    for specification in first.index:
        assert np.isclose(
            first.loc[specification, "global_moran_I"],
            second.loc[specification, "global_moran_I"],
            atol=1e-12,
        )
        assert np.isclose(
            first.loc[specification, "global_p_sim"],
            second.loc[specification, "global_p_sim"],
            atol=1e-12,
        )


def test_spatial_weights_comparison_has_four_rows():
    weights_df = _weights_comparison()
    assert len(weights_df) == 4


def test_local_cluster_stability_has_16_rows():
    stability_df = _stability_table()
    assert len(stability_df) == 16


def test_no_global_p_value_is_below_alpha():
    weights_df = _weights_comparison()
    assert (weights_df["global_p_sim"] >= 0.05).all()


def test_queen_islands_are_not_labeled_as_meaningful_clusters():
    spatial_df = _spatial_results()
    queen = spatial_df[spatial_df["specification"] == "legacy_queen"]
    islands = queen[queen["is_island"]]
    assert set(islands["cluster"]) == {"No neighbors"}


def test_no_local_cluster_is_robust_across_three_non_island_specifications():
    stability_df = _stability_table()
    assert (stability_df["stable_cluster"] == "Not robust").all()
