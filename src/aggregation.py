"""County-level aggregation logic and fallback snapshot construction."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .cleaning import normalize_county_name, normalize_fips

LEGACY_REQUIRED_COLUMNS = (
    "Date",
    "Source",
    "Site ID",
    "POC",
    "Daily Mean PM2.5 Concentration",
    "Units",
    "Daily AQI Value",
    "Local Site Name",
    "Daily Obs Count",
    "Percent Complete",
    "AQS Parameter Code",
    "AQS Parameter Description",
    "Method Code",
    "Method Description",
    "CBSA Code",
    "CBSA Name",
    "State FIPS Code",
    "State",
    "County FIPS Code",
    "County",
    "Site Latitude",
    "Site Longitude",
)

LEGACY_BENCHMARKS: list[dict[str, Any]] = [
    {"County": "Ashland", "County_FIPS_Code": "55003", "PM25_Annual_Mean_2024": 4.697527, "n_sites": 1},
    {"County": "Brown", "County_FIPS_Code": "55009", "PM25_Annual_Mean_2024": 6.135246, "n_sites": 1},
    {"County": "Dane", "County_FIPS_Code": "55025", "PM25_Annual_Mean_2024": 6.434959, "n_sites": 2},
    {"County": "Dodge", "County_FIPS_Code": "55027", "PM25_Annual_Mean_2024": 5.394867, "n_sites": 1},
    {"County": "Eau Claire", "County_FIPS_Code": "55035", "PM25_Annual_Mean_2024": 6.448328, "n_sites": 1},
    {"County": "Forest", "County_FIPS_Code": "55041", "PM25_Annual_Mean_2024": 4.722958, "n_sites": 1},
    {"County": "Grant", "County_FIPS_Code": "55043", "PM25_Annual_Mean_2024": 7.346175, "n_sites": 1},
    {"County": "Jackson", "County_FIPS_Code": "55053", "PM25_Annual_Mean_2024": 5.677617, "n_sites": 1},
    {"County": "Kenosha", "County_FIPS_Code": "55059", "PM25_Annual_Mean_2024": 5.972404, "n_sites": 1},
    {"County": "Marathon", "County_FIPS_Code": "55073", "PM25_Annual_Mean_2024": 5.492896, "n_sites": 1},
    {"County": "Milwaukee", "County_FIPS_Code": "55079", "PM25_Annual_Mean_2024": 7.037637, "n_sites": 2},
    {"County": "Monroe", "County_FIPS_Code": "55081", "PM25_Annual_Mean_2024": 4.546407, "n_sites": 1},
    {"County": "Outagamie", "County_FIPS_Code": "55087", "PM25_Annual_Mean_2024": 6.106887, "n_sites": 1},
    {"County": "Ozaukee", "County_FIPS_Code": "55089", "PM25_Annual_Mean_2024": 5.109836, "n_sites": 1},
    {"County": "Sauk", "County_FIPS_Code": "55111", "PM25_Annual_Mean_2024": 5.600820, "n_sites": 1},
    {"County": "Waukesha", "County_FIPS_Code": "55133", "PM25_Annual_Mean_2024": 6.970588, "n_sites": 1},
]


def normalize_raw_daily_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a legacy-style EPA daily file to the expected schema."""
    missing = [column for column in LEGACY_REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Raw daily file is missing expected columns: {missing}")
    normalized = df.copy()
    normalized["Date"] = pd.to_datetime(normalized["Date"], format="%m/%d/%Y", errors="coerce")
    normalized["Daily Mean PM2.5 Concentration"] = pd.to_numeric(
        normalized["Daily Mean PM2.5 Concentration"], errors="coerce"
    )
    normalized["State FIPS Code"] = normalized["State FIPS Code"].map(
        lambda value: normalize_fips(value, 2)
    )
    normalized["County FIPS Code"] = normalized["County FIPS Code"].map(
        lambda value: normalize_fips(value, 3)
    )
    normalized["County_FIPS_Code"] = (
        normalized["State FIPS Code"].fillna("") + normalized["County FIPS Code"].fillna("")
    )
    normalized["County"] = normalized["County"].map(normalize_county_name)
    return normalized


def filter_wisconsin_2024(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Filter the raw daily file to Wisconsin records in calendar year 2024."""
    filtered = raw_df[
        raw_df["State"].eq("Wisconsin")
        & raw_df["Date"].dt.year.eq(2024)
        & raw_df["County_FIPS_Code"].str.startswith("55")
    ].copy()
    return filtered.reset_index(drop=True)


def summarize_raw_daily(filtered_df: pd.DataFrame) -> dict[str, Any]:
    """Compute quality-assurance summaries for a raw daily EPA table."""
    duplicated_site_date = (
        filtered_df.groupby(["Site ID", "Date"], dropna=False).size().reset_index(name="rows_per_site_date")
    )
    multi_row_site_dates = int((duplicated_site_date["rows_per_site_date"] > 1).sum())
    return {
        "row_count": int(len(filtered_df)),
        "date_min": filtered_df["Date"].min().strftime("%Y-%m-%d") if not filtered_df.empty else None,
        "date_max": filtered_df["Date"].max().strftime("%Y-%m-%d") if not filtered_df.empty else None,
        "missing_pm25": int(filtered_df["Daily Mean PM2.5 Concentration"].isna().sum()),
        "unique_sites": int(filtered_df["Site ID"].nunique(dropna=True)),
        "unique_counties": int(filtered_df["County_FIPS_Code"].nunique(dropna=True)),
        "unique_pocs": sorted(filtered_df["POC"].dropna().astype(str).unique().tolist()),
        "units": sorted(filtered_df["Units"].dropna().astype(str).unique().tolist()),
        "parameter_codes": sorted(
            filtered_df["AQS Parameter Code"].dropna().astype(str).unique().tolist()
        ),
        "multi_row_site_dates": multi_row_site_dates,
    }


def aggregate_legacy_from_raw(filtered_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reproduce the original two-stage legacy aggregation."""
    site_df = (
        filtered_df.groupby(["County_FIPS_Code", "County", "Site ID"], dropna=False)[
            "Daily Mean PM2.5 Concentration"
        ]
        .mean()
        .reset_index(name="site_annual_pm25")
        .sort_values(["County_FIPS_Code", "Site ID"])
        .reset_index(drop=True)
    )
    county_df = (
        site_df.groupby(["County_FIPS_Code", "County"], dropna=False)
        .agg(
            PM25_Annual_Mean_2024=("site_annual_pm25", "mean"),
            n_sites=("Site ID", "nunique"),
        )
        .reset_index()
        .sort_values("County_FIPS_Code")
        .reset_index(drop=True)
    )
    return site_df, county_df


def build_fallback_snapshot(
    simplified_df: pd.DataFrame, factbook_df: pd.DataFrame
) -> pd.DataFrame:
    """Create a transparent county snapshot when raw daily replication is unavailable."""
    benchmarks = pd.DataFrame(LEGACY_BENCHMARKS)
    simplified = simplified_df.rename(
        columns={
            "Population_2020_Census": "Population_2020_Census_simplified",
            "PM25_Weighted_Annual_Mean_ug_m3": "PM25_simplified_wtd_am_ug_m3",
            "PM25_24hr_ug_m3": "PM25_simplified_24hr_ug_m3",
        }
    )
    factbook = factbook_df.rename(
        columns={
            "Population_2020_Census": "Population_2020_Census_factbook",
            "PM25_Wtd_AM_ug_m3": "PM25_factbook_wtd_am_ug_m3",
            "PM25_24hr_ug_m3": "PM25_factbook_24hr_ug_m3",
        }
    )
    merged = benchmarks.merge(
        simplified[
            [
                "County_FIPS_Code",
                "Population_2020_Census_simplified",
                "PM25_simplified_wtd_am_ug_m3",
                "PM25_simplified_24hr_ug_m3",
            ]
        ],
        on="County_FIPS_Code",
        how="left",
    ).merge(
        factbook[
            [
                "County_FIPS_Code",
                "Population_2020_Census_factbook",
                "PM25_factbook_wtd_am_ug_m3",
                "PM25_factbook_24hr_ug_m3",
            ]
        ],
        on="County_FIPS_Code",
        how="left",
    )
    merged["Population_2020_Census"] = merged["Population_2020_Census_simplified"].fillna(
        merged["Population_2020_Census_factbook"]
    )
    merged["Population_Source"] = merged["Population_2020_Census_simplified"].notna().map(
        {True: "Wisconsin_PM25_simplified.xlsx", False: "ctyfactbook2024_0.xlsx"}
    )
    merged["pm25_minus_simplified"] = (
        merged["PM25_Annual_Mean_2024"] - merged["PM25_simplified_wtd_am_ug_m3"]
    )
    merged["pm25_minus_factbook"] = (
        merged["PM25_Annual_Mean_2024"] - merged["PM25_factbook_wtd_am_ug_m3"]
    )
    merged["Data_Mode"] = "fallback_county_snapshot"
    return merged.sort_values("County_FIPS_Code").reset_index(drop=True)


def build_site_placeholder_table(county_df: pd.DataFrame) -> pd.DataFrame:
    """Create a non-fabricated site-level placeholder table for fallback mode."""
    placeholder = county_df[["County_FIPS_Code", "County", "n_sites"]].copy()
    placeholder["Site ID"] = pd.NA
    placeholder["site_annual_pm25"] = pd.NA
    placeholder["source_status"] = (
        "Site-level values unavailable because raw daily EPA data could not be retrieved in this rebuild."
    )
    return placeholder[
        ["County_FIPS_Code", "County", "n_sites", "Site ID", "site_annual_pm25", "source_status"]
    ]


def build_monitor_coverage(counties_gdf: pd.DataFrame, county_df: pd.DataFrame) -> pd.DataFrame:
    """Join monitor counts to all 72 counties."""
    coverage = counties_gdf[["County_FIPS_Code", "County", "land_area_sqkm"]].copy()
    coverage = coverage.merge(
        county_df[["County_FIPS_Code", "County", "PM25_Annual_Mean_2024", "n_sites", "Population_2020_Census"]],
        on=["County_FIPS_Code", "County"],
        how="left",
    )
    coverage["n_sites"] = coverage["n_sites"].fillna(0).astype(int)
    coverage["has_monitor"] = coverage["PM25_Annual_Mean_2024"].notna()
    coverage["population_density_per_sqkm"] = (
        coverage["Population_2020_Census"] / coverage["land_area_sqkm"]
    )
    return coverage.sort_values("County_FIPS_Code").reset_index(drop=True)


def join_counties(counties_gdf: pd.DataFrame, county_df: pd.DataFrame) -> pd.DataFrame:
    """Spatially join county estimates to all 72 county polygons."""
    joined = counties_gdf.merge(
        county_df.drop(columns=["County"], errors="ignore"),
        on="County_FIPS_Code",
        how="left",
        suffixes=("", "_analysis"),
    )
    return joined.sort_values("County_FIPS_Code").reset_index(drop=True)

