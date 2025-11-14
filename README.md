# ETL SUBE – Procesamiento de Datos de Transporte (Python + PostgreSQL + PostGIS)

Este repositorio contiene el proceso ETL (Extract–Transform–Load) para los conjuntos de datos públicos del sistema SUBE en Argentina.  
El objetivo es extraer los datasets originales (CSV y GeoJSON), limpiarlos, estandarizarlos y cargarlos en una base de datos PostgreSQL con PostGIS para análisis posteriores.

## 🚀 Objetivo del Proyecto
- Construir un pipeline ETL reproducible y ordenado.
- Integrar datos geográficos (puntos SUBE) usando GeoPandas + PostGIS.
- Centralizar los datos en un Data Warehouse propio.
- Preparar una capa *Silver* con los datos limpios y normalizados.
- Facilitar análisis, dashboards o modelos que utilicen estos datos.

---

## 📦 Datasets Utilizados

### 1. **SUBE – Transacciones por fecha**
- Cantidad de validaciones (usos) de la tarjeta SUBE.
- Por empresa, línea, jurisdicción, provincia y tipo de transporte.

### 2. **SUBE – Cantidad de tarjetas activas por día en AMBA**
- Cuántas tarjetas diferentes realizaron al menos un viaje diario.
- Desglosado por medio: colectivo, subte, tren.

### 3. **Puntos de carga SUBE (GeoJSON)**
- Ubicaciones de los puntos de recarga y venta activos.

### 4. **Terminales Automáticas SUBE (GeoJSON)**
- Ubicaciones de las terminales TAS (autoservicio).

---

## 🧱 Arquitectura ETL

El pipeline sigue las etapas clásicas:

### **🟫 Bronze (RAW)**
- Los archivos originales se almacenan sin modificaciones en `data/raw/`.
- Se cargan a PostgreSQL tal como vienen.

### **⬜ Silver (Limpieza & Normalización)**
- Correcciones de coordenadas geográficas.
- Estandarización de nombres y campos.
- Normalización de ubicaciones: provincia, municipio, AMBA.
- Eliminación de duplicados.
- Validación de tipos y rangos.

### **🟨 Gold (Métricas/KPIs)**
- Tablas resumidas.
- Usuarios vs viajes.
- Transacciones por medio y ubicación.
- Densidad de puntos de carga.

*(La capa Gold se construirá en próximos pasos.)*

---

## 🛠 Tecnologías Utilizadas
- **Python 3.11+**
- **pandas**
- **geopandas**
- **SQLAlchemy**
- **psycopg2**
- **PostgreSQL 15+**
- **PostGIS**

---

---

## ⚙️ Instalación

### 1️⃣ Crear entorno virtual
Python 3.11+

```bash
python -m venv venv
venv\Scripts\activate       # Windows activate entorno virtual 

2️⃣ Instalar dependencias

pip install -r requirements.txt

3️⃣ Crear archivo .env

DB_HOST=localhost
DB_PORT=5432
DB_NAME=sube_dw
DB_USER=postgres
DB_PASSWORD=tu_password

🗄 Preparar la base de datos

Entrar a PostgreSQL:

CREATE DATABASE sube_dw;
\c sube_dw;
CREATE EXTENSION postgis;

▶️ Ejecutar el ETL (etapa RAW)
python main.py
