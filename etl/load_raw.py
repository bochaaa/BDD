# etl/load_raw_sube.py (agregamos esto)
import geopandas as gpd
from geoalchemy2 import Geometry
from .utils_geo import load_geojson

def load_puntos_carga_raw():
    """
    Carga el GeoJSON de puntos de carga SUBE a una tabla raw en PostGIS.
    """
    engine = get_engine()

    file_path = os.path.join(DATA_RAW_DIR, "sube_red_de_carga_activa_2019-10-01.geojson")

    gdf = load_geojson(file_path)  # gdf con CRS EPSG:4326

    # Renombrar columnas a snake_case si querés (ejemplo)
    gdf.rename(
        columns=lambda c: c.strip().lower().replace(" ", "_"),
        inplace=True,
    )

    # Guardar en PostGIS
    gdf.to_postgis(
        "raw_sube_puntos_carga",
        engine,
        if_exists="replace",
        index=False,
        dtype={"geometry": Geometry("POINT", srid=4326)},
    )

    print("Carga completa: raw_sube_puntos_carga")

import os
import pandas as pd
from .config import DATA_RAW, get_engine

def load_transacciones_raw():
    engine = get_engine()
    file_path = os.path.join(DATA_RAW, "sube_transacciones.csv")

    df = pd.read_csv(file_path)
    print("Columnas CSV:", list(df.columns))

    df.to_sql(
        "raw_sube_transacciones",
        con=engine,
        index=False,
        if_exists="replace"
    )

    print("Tabla cargada: raw_sube_transacciones")
