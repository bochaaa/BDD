from etl.load_raw import load_terminales_autoservicio, load_total_usuarios_amba_raw, load_transacciones_raw, load_puntos_carga_raw

if __name__ == "__main__":
    load_transacciones_raw()
    load_puntos_carga_raw()
    load_total_usuarios_amba_raw()
    load_terminales_autoservicio()
