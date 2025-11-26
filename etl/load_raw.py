# etl/load_raw_sube.py (agregamos esto)
import geopandas as gpd
from geoalchemy2 import Geometry
from .utils_geo import load_geojson

def load_puntos_carga_raw():
    """
    Carga el GeoJSON de puntos de carga SUBE a una tabla raw en PostGIS.
    """
    engine = get_engine()

    file_path = os.path.join(DATA_RAW, "sube_red_de_carga_activa_2019-10-01.geojson")

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
def load_terminales_autoservicio():
    """
    Carga el GeoJSON de puntos de carga SUBE a una tabla raw en PostGIS.
    """
    engine = get_engine()

    file_path = os.path.join(DATA_RAW, "sube_terminales_autoservicio_activas_2019-10-01.geojson")

    gdf = load_geojson(file_path)  # gdf con CRS EPSG:4326

    # Renombrar columnas a snake_case si querés (ejemplo)
    gdf.rename(
        columns=lambda c: c.strip().lower().replace(" ", "_"),
        inplace=True,
    )

    # Guardar en PostGIS
    gdf.to_postgis(
        "raw_sube_terminales_autoservicio",
        engine,
        if_exists="replace",
        index=False,
        dtype={"geometry": Geometry("POINT", srid=4326)},
    )

    print("Carga completa: raw_sube_terminales_autoservicio")

import os
import pandas as pd
from .config import DATA_RAW, get_engine

def load_transacciones_raw():
    """
    Carga todos los CSV de transacciones SUBE por año:
    sube_transacciones_2020.csv ... sube_transacciones_2024.csv

    Se concatenan y se guardan en raw_sube_transacciones.
    """
    engine = get_engine()

    years = [2020, 2021, 2022, 2023, 2024,2025]

    dfs = []
    for y in years:
        filename = f"sube_transacciones_{y}.csv"
        file_path = os.path.join(DATA_RAW, filename)

        if os.path.exists(file_path):
            print(f"→ Cargando {filename} ...")
            df = pd.read_csv(file_path)

            # Registrar año de origen
            df["anio"] = y

            dfs.append(df)
        else:
            print(f"⚠ Archivo no encontrado: {filename}")

    if not dfs:
        print("❌ No se encontraron archivos de transacciones.")
        return

    # Unificar
    df_full = pd.concat(dfs, ignore_index=True)
    print("Columnas finales:", list(df_full.columns))
    print(f"Total de filas cargadas: {len(df_full)}")

    df_full.to_sql(
        "raw_sube_transacciones",
        con=engine,
        index=False,
        if_exists="replace"
    )

    print("✅ Tabla cargada: raw_sube_transacciones")
def load_total_usuarios_amba_raw():
    engine = get_engine()
    file_path = os.path.join(DATA_RAW, "total-usuarios-por-dia-AMBA.csv")

    df = pd.read_csv(file_path)
    print("Columnas CSV:", list(df.columns))

    df.to_sql(
        "raw_total_usuarios_por_dia_AMBA",
        con=engine,
        index=False,
        if_exists="replace"
    )

    print("Tabla cargada: total-usuarios-por-dia-AMBA")