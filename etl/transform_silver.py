# etl/transform_silver.py
import pandas as pd
import geopandas as gpd

from sqlalchemy import text
from geoalchemy2 import Geometry

from .config import get_engine

from shapely.errors import ShapelyDeprecationWarning
import warnings
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

# ---------- Helpers ----------

def _drop_nulls(df, desc: str):
    before = len(df)
    df = df.dropna()
    after = len(df)
    print(f"[{desc}] Filas antes: {before}, después de dropna(): {after}")
    return df


def _ensure_date_col(df, col_name: str, desc: str):
    df[col_name] = pd.to_datetime(df[col_name], errors="coerce")
    before = len(df)
    df = df.dropna(subset=[col_name])
    after = len(df)
    print(f"[{desc}] Fechas válidas en {col_name}: {after}/{before}")
    return df


def _drop_duplicates(df, subset, desc: str):
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    after = len(df)
    print(f"[{desc}] Filas antes: {before}, después de drop_duplicates({subset}): {after}")
    return df


def _remove_negative_numeric(df, cols, desc: str):
    mask = pd.Series([False] * len(df))
    for c in cols:
        if c in df.columns:
            mask = mask | (df[c] < 0)
    removed = mask.sum()
    if removed > 0:
        print(f"[{desc}] Filas con valores negativos removidas: {removed}")
    df = df[~mask]
    return df


# ---------- 1) Silver: Cantidad de tarjetas utilizadas por día en AMBA ----------

def build_silver_usuarios_amba():
    """
    Silver para: Cantidad de tarjetas utilizadas por día en AMBA.
    - Sin nulos.
    - Fechas con mismo formato.
    - Sin fechas duplicadas.
    - Sin valores numéricos negativos.
    """
    engine = get_engine()

    df = pd.read_sql_table("raw_total_usuarios_por_dia_AMBA", con=engine)
    print("[usuarios_amba] Columnas:", list(df.columns))

    # Ajusta estos nombres si tu CSV los trae distinto
    # Suponemos algo tipo: indice_tiempo, total_amba, colectivo_amba, subte_amba, tren_amba
    # 1) Nulos
    df = _drop_nulls(df, "usuarios_amba")

    # 2) Formato de fecha
    # Usamos la primera columna que parezca fecha si no es exactamente 'indice_tiempo'
    if "indice_tiempo" in df.columns:
        date_col = "indice_tiempo"
    else:
        # intenta detectar una columna de fecha
        candidates = [c for c in df.columns if "fecha" in c.lower() or "dia" in c.lower() or "time" in c.lower()]
        date_col = candidates[0] if candidates else df.columns[0]  # fallback salvaje
    df = _ensure_date_col(df, date_col, "usuarios_amba")

    # 3) Sin fechas duplicadas
    df = _drop_duplicates(df, subset=[date_col], desc="usuarios_amba")

    # 4) Sin negativos en columnas numéricas
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    df = _remove_negative_numeric(df, numeric_cols, "usuarios_amba")

    # Ordenar por fecha
    df = df.sort_values(by=date_col)

    # Guardar en tabla silver
    df.to_sql(
        "silver_sube_usuarios_amba_diario",
        con=engine,
        index=False,
        if_exists="replace"
    )
    print("[usuarios_amba] Cargada tabla: silver_sube_usuarios_amba_diario")


# ---------- 2) Silver: Cantidad de transacciones por fecha ----------

def build_silver_transacciones():
    """
    Silver para: Cantidad de transacciones por fecha.
    - Sin nulos.
    - Fechas consistentes.
    - Se eliminan columnas: linea, nombre_empresa, provincia, jurisdiccion, municipio, dato_preliminar.
    """
    engine = get_engine()

    df = pd.read_sql_table("raw_sube_transacciones", con=engine)
   

    

    # 2) Formato de fecha
    # 
    date_candidates = [c for c in df.columns if "dia" in c.lower() or "fecha" in c.lower() or "date" in c.lower()]
    date_col = date_candidates[0] if date_candidates else df.columns[0]
    df = _ensure_date_col(df, date_col, "transacciones")

    # 3) Eliminar columnas no necesarias
    drop_targets = {"linea", "nombre_empresa",  "jurisdiccion", "municipio", "dato_preliminar"}
    cols_to_drop = [c for c in df.columns if c.lower() in drop_targets]
    print(f"[transacciones] Columnas a eliminar: {cols_to_drop}")
    df = df.drop(columns=cols_to_drop, errors="ignore")

    #3.2) eliminar lanchas y circular
    tipos_excluir = ["Lanchas", "Circular"]


    df = df[~df["TIPO_TRANSPORTE"].str.lower().isin([t.lower() for t in tipos_excluir])]
    
    # 4) Sin negativos en columnas numéricas
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    df = _remove_negative_numeric(df, numeric_cols, "transacciones")
    # 1) Nulos
     # 3) Rellenar nulos en campos de texto con 'NI' (control de nulos)
    fill_targets = ["provincia",]
    for target in fill_targets:
        for real_col in df.columns:
            if real_col.lower() == target:
                df[real_col] = df[real_col].fillna("NI")
                print(f"[puntos_carga] Columna '{real_col}' – NULL rellenados con 'NI'")
                break
    ##df = _drop_nulls(df, "transacciones")
    # Guardar en tabla silver
    df.to_sql(
        "silver_sube_transacciones",
        con=engine,
        index=False,
        if_exists="replace"
    )
    print("[transacciones] Cargada tabla: silver_sube_transacciones")


# ---------- 3) Silver: Puntos de carga (GeoJSON) ----------


def build_silver_puntos_carga():
    """
    Silver para puntos de carga:
    - Se reconstruye geometry desde latitud / longitud (EPSG:4326).
    - Se rellenan algunos campos textuales con 'NI' para controlar nulos.
    - Se eliminan columnas: id_entidad, entidad, nrocuit, id_ubicacion, ubicacion,
      facultad, direccion, numero, barrio, comuna, pais, partido, localidad y cp.
    - La tabla silver no tiene valores NULL (después de las transformaciones).
    """
    engine = get_engine()

    # Leemos tabla RAW sin usar geometry cruda
    df = pd.read_sql_table("raw_sube_puntos_carga", con=engine)
    print("[puntos_carga] Columnas RAW:", list(df.columns))

    # 1) Detectar columnas de latitud / longitud
    lon_col = next((c for c in df.columns if "long" in c.lower()), None)
    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    if lon_col is None or lat_col is None:
        raise ValueError("No se encontraron columnas de latitud/longitud en raw_sube_puntos_carga")

    # 2) Asegurar que sean numéricas y eliminar filas sin lat/long
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    before = len(df)
    df = df.dropna(subset=[lon_col, lat_col])
    print(f"[puntos_carga] Filas después de eliminar lat/long NULL: {len(df)} (antes {before})")

    # 3) Rellenar nulos en campos de texto con 'NI' (control de nulos)
    fill_targets = ["barrio", "comuna", "partido", "localidad"]
    for target in fill_targets:
        for real_col in df.columns:
            if real_col.lower() == target:
                df[real_col] = df[real_col].fillna("NI")
                print(f"[puntos_carga] Columna '{real_col}' – NULL rellenados con 'NI'")
                break

    # 4) Eliminar columnas que no deben estar en Silver (incluye barrio/comuna/etc.)
    drop_targets = {
        "id_entidad", "entidad",
        "nrocuit", "nro_cuit",
        "id_ubicacion", "ubicaci�",
        "facultad", "direcci�", "n�mero",
        "barrio", "comuna", "pa�s",
        "partido", "localidad", "cp",
        "geometry",
    }
    cols_to_drop = [c for c in df.columns if c.lower() in drop_targets]
    print(f"[puntos_carga] Columnas a eliminar: {cols_to_drop}")
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # 5) Eliminar cualquier NULL restante en otras columnas
    nulls_before = df.isna().sum().sum()
    if nulls_before > 0:
        print(f"[puntos_carga] Valores NULL restantes antes de dropna: {nulls_before}")
    df = df.dropna()
    print(f"[puntos_carga] Filas después de dropna final: {len(df)}")

    # 6) Construir GeoDataFrame con geometry correcta
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326"
    )

    # 7) Guardar en tabla Silver
    gdf.to_postgis(
        "silver_sube_puntos_carga",
        engine,
        if_exists="replace",
        index=False,
        dtype={"geometry": Geometry("POINT", srid=4326)},
    )
    print("[puntos_carga] Cargada tabla: silver_sube_puntos_carga")

# ---------- 4) Silver: Terminales automáticas (GeoJSON) ----------
def build_silver_terminales_autoservicio():
    """
    Silver para terminales automáticas (TAS):
    - Se reconstruye geometry desde latitud / longitud (EPSG:4326).
    - Se rellenan algunos campos textuales con 'NI' para controlar nulos.
    - Se eliminan columnas: id_entidad, entidad, nrocuit, id_ubicacion, ubicacion,
      facultad, direccion, numero, barrio, comuna, pais, partido, localidad y cp.
    - La tabla silver no tiene valores NULL (después de las transformaciones).
    """
    engine = get_engine()

    df = pd.read_sql_table("raw_sube_terminales_autoservicio", con=engine)
    print("[terminales] Columnas RAW:", list(df.columns))

    # 1) Detectar columnas lat / long
    lon_col = next((c for c in df.columns if "long" in c.lower()), None)
    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    if lon_col is None or lat_col is None:
        raise ValueError("No se encontraron columnas de latitud/longitud en raw_sube_terminales_autoservicio")

    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    before = len(df)
    df = df.dropna(subset=[lon_col, lat_col])
    print(f"[terminales] Filas después de eliminar lat/long NULL: {len(df)} (antes {before})")

    # 2) Rellenar nulos en campos de texto con 'NI'
    fill_targets = ["barrio", "comuna", "partido", "localidad"]
    for target in fill_targets:
        for real_col in df.columns:
            if real_col.lower() == target:
                df[real_col] = df[real_col].fillna("NI")
                print(f"[terminales] Columna '{real_col}' – NULL rellenados con 'NI'")
                break

    # 3) Eliminar columnas que no deben estar en Silver
    drop_targets = {
        "id_entidad", "entidad",
        "nrocuit", "nro_cuit",
        "id_ubicacion", "ubicaci�",
        "facultad", "direcci�", "n�mero",
        "barrio", "comuna", "pa�s",
        "partido", "localidad", "cp",
        "geometry",
    }
    cols_to_drop = [c for c in df.columns if c.lower() in drop_targets]
    print(f"[terminales] Columnas a eliminar: {cols_to_drop}")
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # 4) Eliminar NULL restantes
    nulls_before = df.isna().sum().sum()
    if nulls_before > 0:
        print(f"[terminales] Valores NULL restantes antes de dropna: {nulls_before}")
    df = df.dropna()
    print(f"[terminales] Filas después de dropna final: {len(df)}")

    # 5) Construir GeoDataFrame con geometry correcta
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326"
    )

    # 6) Guardar en tabla Silver
    gdf.to_postgis(
        "silver_sube_terminales_autoservicio",
        engine,
        if_exists="replace",
        index=False,
        dtype={"geometry": Geometry("POINT", srid=4326)},
    )
    print("[terminales] Cargada tabla: silver_sube_terminales_autoservicio")
