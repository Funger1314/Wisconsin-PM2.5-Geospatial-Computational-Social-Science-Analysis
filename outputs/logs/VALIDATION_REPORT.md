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

## Spatial-Weights Sensitivity Validation
| specification | k | n_components | n_islands | min_neighbors | mean_neighbors | max_neighbors | global_moran_I | global_p_sim | n_significant_local_clusters | significant_local_counties |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_queen | nan | 8 | 5 | 0 | 1.125 | 3 | -0.139923 | 0.402 | 1 | Ozaukee (Low-High) |
| knn_3 | 3.0 | 1 | 0 | 3 | 3.000 | 3 | -0.097149 | 0.461 | 1 | Ozaukee (Low-High) |
| knn_4 | 4.0 | 1 | 0 | 4 | 4.000 | 4 | -0.080429 | 0.476 | 0 | None |
| knn_5 | 5.0 | 1 | 0 | 5 | 5.000 | 5 | -0.029374 | 0.307 | 1 | Ashland (Low-Low) |

- Fixed random seed: 42
- Permutations per specification: 999
- Queen contiguity among monitored counties only has 8 connected components and 5 island counties.
- KNN3, KNN4, and KNN5 each form one connected component and zero islands.
- KNN weights are directional nearest-neighbor graphs; they were not symmetrized in this rebuild.
- No global specification has a permutation p-value below 0.05.
- Local classifications are specification-sensitive and no county is robust across at least three non-island specifications.

### Significant local clusters by specification
- legacy_queen: Ozaukee (Low-High)
- knn_3: Ozaukee (Low-High)
- knn_4: None
- knn_5: Ashland (Low-Low)

### Local stability table
| County | queen_cluster | knn3_cluster | knn4_cluster | knn5_cluster | significant_specification_count | stable_cluster |
| --- | --- | --- | --- | --- | --- | --- |
| Ashland | No neighbors | Not significant | Not significant | Low-Low | 1 | Not robust |
| Brown | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Dane | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Dodge | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Eau Claire | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Forest | No neighbors | Not significant | Not significant | Not significant | 0 | Not robust |
| Grant | No neighbors | Not significant | Not significant | Not significant | 0 | Not robust |
| Jackson | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Kenosha | No neighbors | Not significant | Not significant | Not significant | 0 | Not robust |
| Marathon | No neighbors | Not significant | Not significant | Not significant | 0 | Not robust |
| Milwaukee | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Monroe | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Outagamie | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Ozaukee | Low-High | Low-High | Not significant | Not significant | 2 | Not robust |
| Sauk | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |
| Waukesha | Not significant | Not significant | Not significant | Not significant | 0 | Not robust |

## Tests run
- Boundary coverage check for 72 counties
- Five-character county GEOID check
- Benchmark comparison table
- Spatial-weights comparison table and local stability table
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