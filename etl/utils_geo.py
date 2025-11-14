# bdd/utils_geo.py
import geopandas as gpd


def read_geojson(path):
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    else:
        gdf = gdf.to_crs("EPSG:4326")

    return gdf

def load_geojson(path: str, crs_expected: str = "EPSG:4326") -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)

    # Si no tiene CRS, lo seteamos manualmente (supuesto)
    if gdf.crs is None:
        gdf.set_crs(crs_expected, inplace=True)
    else:
        # si viene en otro, lo reproyectamos
        gdf = gdf.to_crs(crs_expected)

    return gdf
