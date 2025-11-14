from etl.load_raw import load_transacciones_raw, load_puntos_carga_raw

if __name__ == "__main__":
    load_transacciones_raw()
    load_puntos_carga_raw()
