# Wisconsin PM2.5 Project Summary

## Project overview
This rebuild reconstructs a county-level PM2.5 spatial analysis for Wisconsin in 2024 and separates a legacy replication layer from a more defensible portfolio-grade interpretation.

## Key results
- Total Wisconsin counties in boundary layer: 72
- Monitored counties with benchmark PM2.5 values: 16
- Highest monitored county: Grant (7.346175)
- Lowest monitored county: Monroe (4.546407)
- Legacy Moran's I: -0.139923
- Legacy expected I: -0.066667
- Legacy permutation p-value with seed 42: 0.402000

## Interpretation
All monitored-county descriptive annual means in this rebuild are below 9.0 ug/m3. These descriptive means are not EPA regulatory design values and should not be interpreted as formal attainment determinations.

## Spatial-weights sensitivity results
| specification | global_moran_I | global_p_sim | n_components | n_islands |
| --- | --- | --- | --- | --- |
| legacy_queen | -0.139923 | 0.402 | 8 | 5 |
| knn_3 | -0.097149 | 0.461 | 1 | 0 |
| knn_4 | -0.080429 | 0.476 | 1 | 0 |
| knn_5 | -0.029374 | 0.307 | 1 | 0 |

The monitored-county Queen graph contains 8 connected components and 5 island counties. KNN weights with k values of 3, 4, and 5 remove islands and keep all monitored counties in one connected component, but the KNN weights remain asymmetric because nearest-neighbor ties are directional and were not symmetrized. Across all four specifications, the global permutation test remains statistically insignificant, while county-specific LISA labels change with the neighborhood definition.

## Limitation
The original raw EPA daily export and original classroom notebook were unavailable, so the rebuild uses a transparent county benchmark snapshot for the replication layer.
