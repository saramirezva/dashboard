# 6. Visualización de resultados

# Librerías necesarias
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de pandas
pd.set_option('display.max_columns', None)

# Configuración general de la app
st.set_page_config(
    page_title="Dashboard - Servicios Fijos CRC",
    layout="wide"
)

st.title("📊 Dashboard Servicios Fijos Individuales y Empaquetados")
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #F7F9FB;
}
</style>
""", unsafe_allow_html=True)
st.write("Análisis de la base de empaquetamiento de servicios fijos para los años 2023 y 2024.")

# ==============================
# CARGA DE DATOS (CON CACHE)
# ==============================

@st.cache_data
def cargar_datos():
    # Importación de los datos desde CSV
    emp_fijo = pd.read_csv('EMPAQUETAMIENTO_FIJO_11.csv', sep=';', low_memory=False)

    # Filtrar años 2023 y 2024 (como en tu notebook)
    emp_fijo_23_24 = emp_fijo[emp_fijo['ANNO'].isin([2023, 2024])].copy()

    # Conversión de columnas numéricas (adaptando tu código)
    # Nota: uso astype(str) y reemplazo '' por NaN para evitar errores
    emp_fijo_23_24['VELOCIDAD_EFECTIVA_DOWNSTREAM'] = (
        emp_fijo_23_24['VELOCIDAD_EFECTIVA_DOWNSTREAM']
        .astype(str)
        .str.replace(',', '.', regex=False)
        .replace('', np.nan)
        .astype(float)
    )

    emp_fijo_23_24['VELOCIDAD_EFECTIVA_UPSTREAM'] = (
        emp_fijo_23_24['VELOCIDAD_EFECTIVA_UPSTREAM']
        .astype(str)
        .str.replace(',', '.', regex=False)
        .replace('', np.nan)
        .astype(float)
    )

    # Para valores económicos es mejor mantener float para evitar problemas con NaN
    emp_fijo_23_24['VALOR_FACTURADO_O_COBRADO'] = (
        emp_fijo_23_24['VALOR_FACTURADO_O_COBRADO']
        .astype(str)
        .str.replace(',', '.', regex=False)
        .replace('', np.nan)
        .astype(float)
    )

    emp_fijo_23_24['OTROS_VALORES_FACTURADOS'] = (
        emp_fijo_23_24['OTROS_VALORES_FACTURADOS']
        .astype(str)
        .str.replace(',', '.', regex=False)
        .replace('', np.nan)
        .astype(float)
    )

    # Eliminar registros con valores facturados negativos (como en tu código)
    emp_fijo_23_24 = emp_fijo_23_24[
        (emp_fijo_23_24['VALOR_FACTURADO_O_COBRADO'] >= 0) &
        (emp_fijo_23_24['OTROS_VALORES_FACTURADOS'] >= 0)
    ]

    # Calcular valor por línea para análisis de anomalías
    emp_fijo_23_24['VALOR_POR_LINEA'] = (
        emp_fijo_23_24['VALOR_FACTURADO_O_COBRADO'] /
        emp_fijo_23_24['CANTIDAD_LINEAS_ACCESOS'].replace(0, np.nan)
    )

    return emp_fijo_23_24

emp_fijo_23_24 = cargar_datos()

st.caption(f"Registros totales (2023–2024) después de limpieza: {len(emp_fijo_23_24):,}")

# ==============================
# SIDEBAR – FILTROS
# ==============================

st.sidebar.header("🔎 Filtros")

# Años
anios_disponibles = sorted(emp_fijo_23_24['ANNO'].dropna().unique())
sel_anios = st.sidebar.multiselect(
    "Selecciona año(s)",
    options=anios_disponibles,
    default=anios_disponibles
)

# Operadores
operadores_disponibles = sorted(emp_fijo_23_24['EMPRESA'].dropna().unique())
sel_operadores = st.sidebar.multiselect(
    "Selecciona operador(es)",
    options=operadores_disponibles,
    default=operadores_disponibles[:10] if len(operadores_disponibles) > 10 else operadores_disponibles
)

# Servicio / Paquete (si existe la columna)
if 'SERVICIO_PAQUETE' in emp_fijo_23_24.columns:
    paquetes_disponibles = sorted(emp_fijo_23_24['SERVICIO_PAQUETE'].dropna().unique())
    sel_paquetes = st.sidebar.multiselect(
        "Selecciona servicio/paquete",
        options=paquetes_disponibles,
        default=paquetes_disponibles
    )
else:
    sel_paquetes = None

# Departamento (opcional)
if 'DEPARTAMENTO' in emp_fijo_23_24.columns:
    deptos_disponibles = sorted(emp_fijo_23_24['DEPARTAMENTO'].dropna().unique())
    sel_deptos = st.sidebar.multiselect(
        "Selecciona departamento(s)",
        options=deptos_disponibles,
        default=deptos_disponibles
    )
else:
    sel_deptos = None

# Aplicar filtros sobre el DataFrame
df_filtrado = emp_fijo_23_24.copy()

if sel_anios:
    df_filtrado = df_filtrado[df_filtrado['ANNO'].isin(sel_anios)]

if sel_operadores:
    df_filtrado = df_filtrado[df_filtrado['EMPRESA'].isin(sel_operadores)]

if sel_paquetes is not None and sel_paquetes:
    df_filtrado = df_filtrado[df_filtrado['SERVICIO_PAQUETE'].isin(sel_paquetes)]

if sel_deptos is not None and sel_deptos:
    df_filtrado = df_filtrado[df_filtrado['DEPARTAMENTO'].isin(sel_deptos)]

if df_filtrado.empty:
    st.warning("⚠ No hay datos para la combinación de filtros seleccionada.")
    st.stop()

# ==============================
# MÉTRICAS RESUMEN
# ==============================

col1, col2, col3, col4 = st.columns(4)

total_registros = len(df_filtrado)
total_lineas = df_filtrado['CANTIDAD_LINEAS_ACCESOS'].sum()
total_valor = df_filtrado['VALOR_FACTURADO_O_COBRADO'].sum()
num_operadores = df_filtrado['EMPRESA'].nunique()

col1.metric("Registros filtrados", f"{total_registros:,}")
col2.metric("Cantidad total de líneas/accesos", f"{int(total_lineas):,}" if not np.isnan(total_lineas) else "N/A")
col3.metric("Valor facturado total", f"${int(total_valor):,}" if not np.isnan(total_valor) else "N/A")
col4.metric("Operadores reportados", num_operadores)

st.markdown("---")

# ==============================
# TABS PRINCIPALES
# ==============================

tab1, tab2, tab3 = st.tabs([
    "📌 Análisis general",
    "📈 Tendencias trimestrales",
    "📡 Cantidad de líneas"
])

# ------------------------------------
# TAB 1 – ANÁLISIS GENERAL
# ------------------------------------
with tab1:
    st.subheader("Distribución general")

    col_a, col_b = st.columns(2)

    # Registros por año
    with col_a:
        st.markdown("**Registros por año**")
        registros_por_anio = df_filtrado.groupby('ANNO').size()
        st.bar_chart(registros_por_anio)

    # Valor facturado por departamento
    with col_b:
        if 'DEPARTAMENTO' in df_filtrado.columns:
            st.markdown("**Valor facturado por departamento (Top 15)**")
            valor_depto = (
                df_filtrado.groupby('DEPARTAMENTO')['VALOR_FACTURADO_O_COBRADO']
                .sum()
                .sort_values(ascending=False)
                .head(15)
            )
            st.bar_chart(valor_depto)

    st.markdown("**Distribución de servicios/paquetes (frecuencia de registros)**")
    if 'SERVICIO_PAQUETE' in df_filtrado.columns:
        freq_serv = df_filtrado['SERVICIO_PAQUETE'].value_counts().head(20)
        st.bar_chart(freq_serv)

    st.markdown("**Vista previa de los datos filtrados**")
    st.dataframe(df_filtrado.head(50))

# ------------------------------------
# TAB 2 – TENDENCIAS TRIMESTRALES
# ------------------------------------
with tab2:
    st.subheader("Evolución trimestral del valor facturado")

    if {'ANNO', 'TRIMESTRE', 'VALOR_FACTURADO_O_COBRADO'}.issubset(df_filtrado.columns):
        tendencia = (
            df_filtrado
            .groupby(['ANNO', 'TRIMESTRE'])['VALOR_FACTURADO_O_COBRADO']
            .sum()
            .reset_index()
            .sort_values(['ANNO', 'TRIMESTRE'])
        )
        tendencia['ANNO_TRIM'] = tendencia['ANNO'].astype(str) + '-T' + tendencia['TRIMESTRE'].astype(str)
        tendencia = tendencia.set_index('ANNO_TRIM')

        st.line_chart(tendencia['VALOR_FACTURADO_O_COBRADO'])

    st.markdown("**Top 10 operadores por valor facturado (según filtros)**")
    top_ops = (
        df_filtrado
        .groupby('EMPRESA')['VALOR_FACTURADO_O_COBRADO']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(top_ops)

# ------------------------------------
# TAB 3 – CANTIDAD DE LÍNEAS
# ------------------------------------
with tab3:
    st.subheader("Distribución de la cantidad de líneas")

    col_x, col_y = st.columns(2)

    # Cantidad de líneas por segmento
    if 'SEGMENTO' in df_filtrado.columns:
        with col_x:
            st.markdown("**Cantidad de líneas por segmento**")
            lineas_seg = (
                df_filtrado
                .groupby('SEGMENTO')['CANTIDAD_LINEAS_ACCESOS']
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(lineas_seg)

    # Cantidad de líneas por tipo de paquete
    if 'SERVICIO_PAQUETE' in df_filtrado.columns:
        with col_y:
            st.markdown("**Cantidad de líneas por servicio/paquete (Top 15)**")
            lineas_paq = (
                df_filtrado
                .groupby('SERVICIO_PAQUETE')['CANTIDAD_LINEAS_ACCESOS']
                .sum()
                .sort_values(ascending=False)
                .head(15)
            )
            st.bar_chart(lineas_paq)

    st.markdown("**Distribución del valor por línea (detección de posibles anomalías)**")

    # Histograma de valor por línea usando matplotlib
    df_hist = df_filtrado.replace([np.inf, -np.inf], np.nan).dropna(subset=['VALOR_POR_LINEA'])

    if not df_hist.empty:
        fig, ax = plt.subplots()
        ax.hist(df_hist['VALOR_POR_LINEA'], bins=40)
        ax.set_xlabel("Valor por línea")
        ax.set_ylabel("Frecuencia")
        ax.set_title("Histograma del valor por línea")
        st.pyplot(fig)
    else:
        st.info("No hay datos suficientes para calcular valor por línea.")
