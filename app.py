import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Económico",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# CARGA DE DATOS
# ==========================================

@st.cache_data(ttl=300)
def cargar_binance():
    df = pd.read_csv("data/detalle_binance3.csv")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df

@st.cache_data(ttl=300)
def cargar_hipermaxi():
    df = pd.read_csv("data/hipermaxi_detallado_suc.csv")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

# ==========================================
# DATOS
# ==========================================

df_binance = cargar_binance()
df_hiper = cargar_hipermaxi()

# ==========================================
# TITULO
# ==========================================

st.title("📊 Dashboard Económico")
st.markdown("---")

tab1, tab2 = st.tabs([
    "💵 Binance USDT/BOB",
    "🛒 Hipermaxi"
])

# ====================================================
# BINANCE
# ====================================================

with tab1:

    st.header("Mercado Binance P2P USDT/BOB")

    tipo = st.selectbox(
        "Tipo de operación",
        sorted(df_binance["Tipo"].unique())
    )

    df_b = df_binance[df_binance["Tipo"] == tipo]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Precio Promedio",
        f"{df_b['Precio'].mean():.2f}"
    )

    col2.metric(
        "Precio Mínimo",
        f"{df_b['Precio'].min():.2f}"
    )

    col3.metric(
        "Precio Máximo",
        f"{df_b['Precio'].max():.2f}"
    )

    col4.metric(
        "Oferta Total",
        f"{df_b['Disponible'].sum():,.0f}"
    )

    st.markdown("---")

    precio_diario = (
        df_b
        .groupby(df_b["Timestamp"].dt.date)
        ["Precio"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        precio_diario,
        x="Timestamp",
        y="Precio",
        markers=True,
        title="Precio promedio diario"
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:

        fig = px.histogram(
            df_b,
            x="Precio",
            nbins=30,
            title="Distribución de precios"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        vendedores = (
            df_b.groupby("Vendedor")
            ["Disponible"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .reset_index()
        )

        fig = px.bar(
            vendedores,
            x="Vendedor",
            y="Disponible",
            title="Top vendedores por oferta"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detalle")

    st.dataframe(
        df_b.sort_values(
            "Timestamp",
            ascending=False
        ),
        use_container_width=True
    )

# ====================================================
# HIPERMAXI
# ====================================================

with tab2:

    st.header("Monitoreo de Precios Hipermaxi")

    ciudades = sorted(
        df_hiper["Ciudad"].dropna().unique()
    )

    ciudad = st.selectbox(
        "Ciudad",
        ["Todas"] + ciudades
    )

    df_h = df_hiper.copy()

    if ciudad != "Todas":
        df_h = df_h[df_h["Ciudad"] == ciudad]

    sucursales = sorted(
        df_h["Sucursal"].dropna().unique()
    )

    sucursal = st.selectbox(
        "Sucursal",
        ["Todas"] + sucursales
    )

    if sucursal != "Todas":
        df_h = df_h[df_h["Sucursal"] == sucursal]

    categorias = sorted(
        df_h["Categoría"].dropna().unique()
    )

    categoria = st.selectbox(
        "Categoría",
        ["Todas"] + categorias
    )

    if categoria != "Todas":
        df_h = df_h[df_h["Categoría"] == categoria]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Productos",
        len(df_h["Producto"].unique())
    )

    col2.metric(
        "Precio Promedio",
        round(df_h["Precio"].mean(), 2)
    )

    col3.metric(
        "Stock Promedio",
        round(df_h["Stock"].mean(), 2)
    )

    col4.metric(
        "Variación Promedio",
        f"{100*df_h['Variación diaria precio'].mean():.2f}%"
    )

    st.markdown("---")

    precios = (
        df_h.groupby("Fecha")
        ["Precio"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        precios,
        x="Fecha",
        y="Precio",
        markers=True,
        title="Precio promedio"
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:

        top_subidas = (
            df_h.sort_values(
                "Variación diaria precio",
                ascending=False
            )
            .head(15)
        )

        fig = px.bar(
            top_subidas,
            x="Producto",
            y="Variación diaria precio",
            title="Mayores incrementos"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        top_bajadas = (
            df_h.sort_values(
                "Variación diaria precio",
                ascending=True
            )
            .head(15)
        )

        fig = px.bar(
            top_bajadas,
            x="Producto",
            y="Variación diaria precio",
            title="Mayores reducciones"
        )

        st.plotly_chart(fig, use_container_width=True)

    categorias_df = (
        df_h.groupby("Categoría")
        ["Producto"]
        .count()
        .reset_index()
    )

    fig = px.pie(
        categorias_df,
        names="Categoría",
        values="Producto",
        title="Participación por categoría"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detalle de productos")

    st.dataframe(
        df_h.sort_values(
            "Fecha",
            ascending=False
        ),
        use_container_width=True
    )