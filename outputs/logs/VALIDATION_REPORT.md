# Validation Report

## Discovered files
- `data/raw/SOURCE_METADATA.md`
- `data/raw/extracted/GEOG Final Project Data/.DS_Store`
- `data/raw/extracted/GEOG Final Project Data/FinalProject.pdf`
- `data/raw/extracted/GEOG Final Project Data/PM2.5数据/Wisconsin_PM25_simplified.csv`
- `data/raw/extracted/GEOG Final Project Data/PM2.5数据/Wisconsin_PM25_simplified.xlsx`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.cpg`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.dbf`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.prj`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.sbn`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.sbx`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.shp`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.shp.xml`
- `data/raw/extracted/GEOG Final Project Data/WI_CensusTL_Counties_2019/WI_CensusTL_Counties_2019.shx`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/._.DS_Store`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/._FinalProject.pdf`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/PM2.5数据/._Wisconsin_PM25_simplified.csv`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/PM2.5数据/._Wisconsin_PM25_simplified.xlsx`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.cpg`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.dbf`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.prj`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.sbn`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.sbx`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.shp`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.shp.xml`
- `data/raw/extracted/__MACOSX/GEOG Final Project Data/WI_CensusTL_Counties_2019/._WI_CensusTL_Counties_2019.shx`
- `data/raw/source_uploads/GEOG Final Project Data.zip`
- `data/raw/source_uploads/Wisconsin_PM25_simplified.csv`
- `data/raw/source_uploads/Wisconsin_PM25_simplified.xlsx`
- `data/raw/source_uploads/ctyfactbook2024_0.xlsx`

## Raw data path
- Raw daily file used: `not available`
- True raw-level replication succeeded: `False`
- Notes: Fallback county snapshot used because raw daily retrieval failed.

## County benchmark comparison
```csv
County,County_FIPS_Code,PM25_Annual_Mean_2024_benchmark,n_sites_benchmark,PM25_Annual_Mean_2024_computed,n_sites_computed,abs_diff_pm25,abs_diff_n_sites
Ashland,55003,4.697527,1,4.697527,1,0.0,0
Brown,55009,6.135246,1,6.135246,1,0.0,0
Dane,55025,6.434959,2,6.434959,2,0.0,0
Dodge,55027,5.394867,1,5.394867,1,0.0,0
Eau Claire,55035,6.448328,1,6.448328,1,0.0,0
Forest,55041,4.722958,1,4.722958,1,0.0,0
Grant,55043,7.346175,1,7.346175,1,0.0,0
Jackson,55053,5.677617,1,5.677617,1,0.0,0
Kenosha,55059,5.972404,1,5.972404,1,0.0,0
Marathon,55073,5.492896,1,5.492896,1,0.0,0
Milwaukee,55079,7.037637,2,7.037637,2,0.0,0
Monroe,55081,4.546407,1,4.546407,1,0.0,0
Outagamie,55087,6.106887,1,6.106887,1,0.0,0
Ozaukee,55089,5.109836,1,5.109836,1,0.0,0
Sauk,55111,5.60082,1,5.60082,1,0.0,0
Waukesha,55133,6.970588,1,6.970588,1,0.0,0
```

## Moran diagnostics
- Legacy Moran's I: -0.1399234378
- Expected I: -0.0666666667
- Permutation p-value: 0.4020000000
- Legacy islands: Ashland, Forest, Grant, Kenosha, Marathon

## Tests run
- Boundary coverage check for 72 counties
- Five-character county GEOID check
- Benchmark comparison table
- Notebook execution pass
- Rendered writing sample and slide outputs created

## Notebook execution status
- 00_legacy_replication.ipynb: executed
- 01_portfolio_analysis.ipynb: executed

## Slide and report rendering status
- Writing sample DOCX: created
- Writing sample PDF: created
- Slides PPTX: created
- Slides PDF: created

## Remaining discrepancy
- Raw daily EPA records could not be retrieved into the workspace, so site-level replication remains incomplete.