from src.data_loading import discover_source_paths, load_wisconsin_counties


def test_shapefile_loads_72_counties():
    sources = discover_source_paths()
    counties = load_wisconsin_counties(sources.shapefile)
    assert len(counties) == 72


def test_all_geoids_are_five_character_strings():
    sources = discover_source_paths()
    counties = load_wisconsin_counties(sources.shapefile)
    assert counties["County_FIPS_Code"].map(lambda value: isinstance(value, str) and len(value) == 5).all()

