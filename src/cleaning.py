"""Cleaning helpers for tabular and spatial data."""

from __future__ import annotations

from typing import Any

import geopandas as gpd
import pandas as pd


def normalize_fips(value: Any, width: int) -> str | None:
    """Return a zero-padded FIPS string or None for missing values."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    return digits.zfill(width)


def normalize_county_name(value: Any) -> str | None:
    """Normalize county labels to match Wisconsin boundary names."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith(" County"):
        text = text[: -len(" County")]
    return text.replace("Saint ", "St. ")


def prepare_wisconsin_counties(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clean the Wisconsin county boundary layer and add area fields."""
    counties = gdf.copy()
    counties["GEOID"] = counties["GEOID"].astype(str).str.zfill(5)
    counties["County_FIPS_Code"] = counties["GEOID"]
    counties["County"] = counties["NAME"].map(normalize_county_name)
    counties = counties.sort_values("County_FIPS_Code").reset_index(drop=True)
    if not counties.is_valid.all():
        counties["geometry"] = counties.buffer(0)
    counties["land_area_sqkm"] = counties["ALAND"] / 1_000_000
    return counties

