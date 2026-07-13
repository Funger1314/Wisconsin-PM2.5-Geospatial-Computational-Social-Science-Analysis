"""Project paths and shared constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
LOGS_DIR = OUTPUTS_DIR / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"
SLIDES_DIR = PROJECT_ROOT / "slides"

SEED = 42
PERMUTATIONS = 999
PROJECTED_CRS = "EPSG:3071"
PM25_FIELD = "PM25_Annual_Mean_2024"

