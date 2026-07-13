# Data Gaps

## What was missing
- The original classroom notebook was not present in the supplied workspace.
- The original slide deck was not present in the supplied workspace.
- The legacy EPA raw daily export `ad_viz_plotval_data.csv` was not present.

## Network retrieval attempt
- Official target file: `https://aqs.epa.gov/aqsweb/airdata/daily_88101_2024.zip`
- Retrieval status: `Official EPA raw daily file could not be retrieved into the workspace because the legacy export was absent and direct download attempts failed at the SSL/network layer.`

## Fallback used in this rebuild
- A transparent county-level snapshot was created from the benchmark values embedded in the rebuild prompt.
- The simplified Wisconsin PM2.5 table and the EPA county factbook were used only for population context and consistency checks.
- Site-level annual means could not be reconstructed honestly without the raw daily EPA file.

## Interpretation consequence
- This rebuild reproduces county-level mapping and spatial analysis from the benchmark snapshot.
- It does not claim raw-record-level replication of the 7,234 Wisconsin daily observations.
