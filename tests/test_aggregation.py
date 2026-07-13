import pandas as pd

from src.paths import OUTPUTS_DIR, PM25_FIELD


def _county_table() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS_DIR / "tables" / "county_annual_pm25.csv")


def _coverage_table() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS_DIR / "tables" / "county_monitor_coverage.csv")


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


def test_knn4_has_no_islands():
    spatial_df = pd.read_csv(OUTPUTS_DIR / "tables" / "spatial_sensitivity_results.csv")
    knn4 = spatial_df[spatial_df["specification"] == "knn_4"]
    assert not knn4["is_island"].any()

