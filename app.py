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

    st.header("💵 Mercado Binance P2P USDT/BOB")

    # ======================================
    # FILTRO DE FECHAS
    # ======================================

    fecha_min = df_binance["Timestamp"].min().date()
    fecha_max = df_binance["Timestamp"].max().date()

    rango = st.slider(
        "Periodo",
        min_value=fecha_min,
        max_value=fecha_max,
        value=(fecha_min, fecha_max)
    )

    inicio, fin = rango

    df_b = df_binance[
        (df_binance["Timestamp"].dt.date >= inicio)
        &
        (df_binance["Timestamp"].dt.date <= fin)
    ]

    # ======================================
    # ÚLTIMA ACTUALIZACIÓN
    # ======================================

    ultimo_buy_ts = (
    df_b[df_b["Tipo"] == "BUY"]["Timestamp"]
    .max()
    )

    ultimo_sell_ts = (
    df_b[df_b["Tipo"] == "SELL"]["Timestamp"]
    .max()
    )

    buy = df_b[
    (df_b["Tipo"] == "BUY")
    &
    (df_b["Timestamp"] == ultimo_buy_ts)
    ]

    sell = df_b[
    (df_b["Tipo"] == "SELL")
    &
    (df_b["Timestamp"] == ultimo_sell_ts)
    ]

    ultimo_ts = max(
    ultimo_buy_ts,
    ultimo_sell_ts
    )
    # ======================================
    # KPIS
    # ======================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Precio Máximo BUY",
        f"{buy['Precio'].max():.2f}"
    )

    col2.metric(
        "Precio Mínimo BUY",
        f"{buy['Precio'].min():.2f}"
    )

    col3.metric(
        "Disponible BUY",
        f"{buy['Disponible'].sum():,.0f}"
    )

    col4.metric(
        "Disponible SELL",
        f"{sell['Disponible'].sum():,.0f}"
    )

    col5, col6, col7 = st.columns(3)

    col5.metric(
        "Vendedores BUY",
        buy["Vendedor"].nunique()
    )

    col6.metric(
        "Vendedores SELL",
        sell["Vendedor"].nunique()
    )

    col7.metric(
        "Actualizado",
        ultimo_ts.strftime("%d/%m %H:%M")
    )

    st.markdown("---")

    # ======================================
    # PRECIO PROMEDIO BUY VS SELL
    # ======================================

    precio_diario = (
        df_b
        .groupby(
            [
                df_b["Timestamp"].dt.date,
                "Tipo"
            ]
        )["Precio"]
        .mean()
        .reset_index()
    )

    precio_diario.rename(
        columns={"Timestamp": "Fecha"},
        inplace=True
    )

    fig = px.line(
        precio_diario,
        x="Fecha",
        y="Precio",
        color="Tipo",
        markers=True,
        title="Precio Promedio USDT/BOB"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ======================================
    # DISPONIBILIDAD BUY VS SELL
    # ======================================

    disponibilidad = (
        df_b
        .groupby(
            [
                df_b["Timestamp"].dt.date,
                "Tipo"
            ]
        )["Disponible"]
        .sum()
        .reset_index()
    )

    disponibilidad.rename(
        columns={"Timestamp": "Fecha"},
        inplace=True
    )

    fig = px.line(
        disponibilidad,
        x="Fecha",
        y="Disponible",
        color="Tipo",
        markers=True,
        title="Disponibilidad USDT"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ======================================
    # HISTOGRAMAS
    # ======================================

    col1, col2 = st.columns(2)

    with col1:

        fig = px.histogram(
            df_b[df_b["Tipo"]=="BUY"],
            x="Precio",
            nbins=30,
            title="Distribución BUY"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.histogram(
            df_b[df_b["Tipo"]=="SELL"],
            x="Precio",
            nbins=30,
            title="Distribución SELL"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ======================================
    # TOP VENDEDORES
    # ======================================

    col1, col2 = st.columns(2)

    with col1:

        top_buy = (
            df_b[df_b["Tipo"]=="BUY"]
            .groupby("Vendedor")["Disponible"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig = px.bar(
            top_buy,
            x="Vendedor",
            y="Disponible",
            title="Top Disponibilidad BUY"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        top_sell = (
            df_b[df_b["Tipo"]=="SELL"]
            .groupby("Vendedor")["Disponible"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig = px.bar(
            top_sell,
            x="Vendedor",
            y="Disponible",
            title="Top Disponibilidad SELL"
        )

        st.plotly_chart(
            fig,
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