"""Load project sources from the organized raw-data directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd

from .cleaning import normalize_county_name, normalize_fips, prepare_wisconsin_counties
from .paths import RAW_DIR


@dataclass(frozen=True)
class SourcePaths:
    """Resolved file locations for the project."""

    uploaded_dir: Path
    extracted_dir: Path
    factbook_xlsx: Path
    simplified_xlsx: Path
    simplified_csv: Path
    assignment_pdf: Path
    shapefile: Path
    raw_daily_csv: Path | None
    raw_daily_zip: Path | None


def _single_match(pattern: str) -> Path:
    matches = sorted(RAW_DIR.rglob(pattern))
    if not matches:
        raise FileNotFoundError(f"No match found for pattern: {pattern}")
    return matches[0]


def discover_source_paths() -> SourcePaths:
    """Discover raw, extracted, and supplementary inputs."""
    uploaded_dir = RAW_DIR / "source_uploads"
    extracted_dir = RAW_DIR / "extracted"
    raw_daily_csv_matches = sorted(RAW_DIR.rglob("ad_viz_plotval_data*.csv"))
    raw_daily_zip_matches = sorted(RAW_DIR.rglob("daily_88101_2024.zip"))
    return SourcePaths(
        uploaded_dir=uploaded_dir,
        extracted_dir=extracted_dir,
        factbook_xlsx=_single_match("ctyfactbook2024_0.xlsx"),
        simplified_xlsx=_single_match("Wisconsin_PM25_simplified.xlsx"),
        simplified_csv=_single_match("Wisconsin_PM25_simplified.csv"),
        assignment_pdf=_single_match("FinalProject.pdf"),
        shapefile=_single_match("WI_CensusTL_Counties_2019.shp"),
        raw_daily_csv=raw_daily_csv_matches[0] if raw_daily_csv_matches else None,
        raw_daily_zip=raw_daily_zip_matches[0] if raw_daily_zip_matches else None,
    )


def inventory_files(base_dir: Path | None = None) -> list[Path]:
    """Return a sorted inventory of source files."""
    root = base_dir or RAW_DIR
    return sorted(path for path in root.rglob("*") if path.is_file())


def load_factbook_wisconsin(path: Path) -> pd.DataFrame:
    """Load the EPA county factbook and keep Wisconsin rows."""
    df = pd.read_excel(path, sheet_name="County Factbook 2024", header=2)
    renamed = df.rename(
        columns={
            "County FIPS Code": "County_FIPS_Code",
            "Population (2020 Census)": "Population_2020_Census",
            "PM2.5     Wtd AM (µg/m3) ": "PM25_Wtd_AM_ug_m3",
            "PM2.5     24-hr (µg/m3) ": "PM25_24hr_ug_m3",
        }
    )
    wisconsin = renamed[renamed["State"] == "Wisconsin"].copy()
    wisconsin["County_FIPS_Code"] = wisconsin["County_FIPS_Code"].map(
        lambda value: normalize_fips(value, 5)
    )
    wisconsin["County"] = wisconsin["County"].map(normalize_county_name)
    numeric_cols = ["Population_2020_Census", "PM25_Wtd_AM_ug_m3", "PM25_24hr_ug_m3"]
    for column in numeric_cols:
        wisconsin[column] = pd.to_numeric(wisconsin[column], errors="coerce")
    return wisconsin.reset_index(drop=True)


def load_simplified_pm25(path: Path) -> pd.DataFrame:
    """Load the simplified Wisconsin PM2.5 file."""
    df = pd.read_excel(path)
    df["County_FIPS_Code"] = df["County_FIPS_Code"].map(lambda value: normalize_fips(value, 5))
    df["County"] = df["County"].map(normalize_county_name)
    numeric_cols = [
        "Population_2020_Census",
        "PM25_Weighted_Annual_Mean_ug_m3",
        "PM25_24hr_ug_m3",
    ]
    for column in numeric_cols:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.reset_index(drop=True)


def load_wisconsin_counties(path: Path) -> gpd.GeoDataFrame:
    """Read and clean the Wisconsin county shapefile."""
    return prepare_wisconsin_counties(gpd.read_file(path))
