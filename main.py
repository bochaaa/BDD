# main.py
from etl.load_raw import (
    load_transacciones_raw,
    load_total_usuarios_amba_raw,
    load_puntos_carga_raw,
    load_terminales_autoservicio,
)

from etl.transform_silver import (
    build_silver_usuarios_amba,
    build_silver_transacciones,
    build_silver_puntos_carga,
    build_silver_terminales_autoservicio,
)

if __name__ == "__main__":
    # 1) Carga RAW
    load_transacciones_raw()
    load_total_usuarios_amba_raw()
    load_puntos_carga_raw()
    load_terminales_autoservicio()

    # 2) Construcción Silver
    build_silver_usuarios_amba()
    build_silver_transacciones()
    build_silver_puntos_carga()
    build_silver_terminales_autoservicio()
