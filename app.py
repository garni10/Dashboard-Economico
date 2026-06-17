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
        "Precio Promedio BUY",
        f"{buy['Precio'].mean():.2f}"
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
    # MEJOR PRECIO BUY (BID) VS SELL (ASK)
    # ======================================
    
    # -------------------------
    # Mejor BUY (mínimo precio)
    # -------------------------
    
    precio_buy = (
        df_b[df_b["Tipo"] == "BUY"]
        .groupby(
            df_b[df_b["Tipo"] == "BUY"]["Timestamp"].dt.date
        )["Precio"]
        .min()
        .reset_index()
    )
    
    precio_buy.columns = ["Fecha", "Precio"]
    precio_buy["Tipo"] = "BUY"
    
    # -------------------------
    # Mejor SELL (máximo precio)
    # -------------------------
    
    precio_sell = (
        df_b[df_b["Tipo"] == "SELL"]
        .groupby(
            df_b[df_b["Tipo"] == "SELL"]["Timestamp"].dt.date
        )["Precio"]
        .max()
        .reset_index()
    )
    
    precio_sell.columns = ["Fecha", "Precio"]
    precio_sell["Tipo"] = "SELL"
    
    # -------------------------
    # Unir ambas series
    # -------------------------
    
    precio_diario = pd.concat(
        [precio_buy, precio_sell],
        ignore_index=True
    )
    
    precio_diario = precio_diario.sort_values(
        by="Fecha"
    )
    
    # -------------------------
    # Gráfico
    # -------------------------
    
    fig = px.line(
        precio_diario,
        x="Fecha",
        y="Precio",
        color="Tipo",
        markers=True,
        title="Mejor Precio BUY (Bid) vs SELL (Ask)",
        color_discrete_map={
            "BUY": COLOR_BUY,
            "SELL": COLOR_SELL
        }
    )
    
    fig.update_layout(
    
        title=dict(
            font=dict(size=22)
        ),
    
        xaxis_title="Fecha",
    
        yaxis_title="Precio (BOB por USDT)",
    
        xaxis_title_font=dict(size=18),
    
        yaxis_title_font=dict(size=18),
    
        xaxis=dict(
            tickfont=dict(size=14)
        ),
    
        yaxis=dict(
            tickfont=dict(size=14)
        ),
    
        legend=dict(
            title="Tipo",
            font=dict(size=16),
            title_font=dict(size=17)
        ),
    
        hovermode="x unified"
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
    # HISTOGRAMAS (ÚLTIMO SNAPSHOT)
    # ======================================
    
    col_sell, col_buy = st.columns(2)
    
    xmin = min(
        buy["Precio"].min(),
        sell["Precio"].min()
    )
    
    xmax = max(
        buy["Precio"].max(),
        sell["Precio"].max()
    )
    
    bin_size = 0.50
    
    with col_sell:
    
        fig = px.histogram(
            sell,
            x="Precio",
            title="Distribución SELL",
            nbins=int((xmax - xmin) / bin_size)
        )
    
        fig.update_traces(
            xbins=dict(
                start=xmin,
                end=xmax,
                size=bin_size
            )
        )
    
        fig.update_layout(
            bargap=0.03,
            xaxis_title="Precio",
            yaxis_title="Cantidad de vendedores"
        )
    
        st.plotly_chart(
            fig,
            use_container_width=True
        )
    
    
    with col_buy:
    
        fig = px.histogram(
            buy,
            x="Precio",
            title="Distribución BUY",
            nbins=int((xmax - xmin) / bin_size)
        )
    
        fig.update_traces(
            xbins=dict(
                start=xmin,
                end=xmax,
                size=bin_size
            )
        )
    
        fig.update_layout(
            bargap=0.03,
            xaxis_title="Precio",
            yaxis_title="Cantidad de vendedores"
        )
    
        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ======================================
    # TOP 10 VENDEDORES (ÚLTIMO SNAPSHOT)
    # ======================================
    
    col_sell, col_buy = st.columns(2)
    
    # ==================================================
    # SELL
    # ==================================================
    
    with col_sell:
    
        top_sell = (
            sell
            .groupby("Vendedor", as_index=False)
            .agg(
                Disponible=("Disponible", "sum"),
                Precio=("Precio", "mean")
            )
            .sort_values(
                by="Disponible",
                ascending=False
            )
            .head(10)
        )
    
        fig = px.bar(
    
            top_sell,
    
            y="Vendedor",
    
            x="Disponible",
    
            orientation="h",
    
            text="Disponible",
    
            hover_data={
                "Precio":":.2f",
                "Disponible":":,.0f"
            },
    
            title="Top 10 Liquidez SELL"
        )
    
        fig.update_traces(
    
            texttemplate="%{text:,.0f}",
    
            textposition="outside",
    
            customdata=top_sell[["Precio"]],
    
            hovertemplate=
            "<b>%{y}</b><br>"
            "Disponible: %{x:,.0f} USDT<br>"
            "Precio: %{customdata[0]:.2f} Bs/USDT"
            "<extra></extra>"
        )
    
        fig.update_layout(
    
            xaxis_title="USDT Disponibles",
    
            yaxis_title="",
    
            yaxis=dict(
                autorange="reversed"
            ),
    
            height=500,
    
            margin=dict(
                l=10,
                r=10,
                t=50,
                b=20
            )
        )
    
        st.plotly_chart(
            fig,
            use_container_width=True
        )
    
    # ==================================================
    # BUY
    # ==================================================
    
    with col_buy:
    
        top_buy = (
            buy
            .groupby("Vendedor", as_index=False)
            .agg(
                Disponible=("Disponible", "sum"),
                Precio=("Precio", "mean")
            )
            .sort_values(
                by="Disponible",
                ascending=False
            )
            .head(10)
        )
    
        fig = px.bar(
    
            top_buy,
    
            y="Vendedor",
    
            x="Disponible",
    
            orientation="h",
    
            text="Disponible",
    
            hover_data={
                "Precio":":.2f",
                "Disponible":":,.0f"
            },
    
            title="Top 10 Liquidez BUY"
        )
    
        fig.update_traces(
    
            texttemplate="%{text:,.0f}",
    
            textposition="outside",
    
            customdata=top_buy[["Precio"]],
    
            hovertemplate=
            "<b>%{y}</b><br>"
            "Disponible: %{x:,.0f} USDT<br>"
            "Precio: %{customdata[0]:.2f} Bs/USDT"
            "<extra></extra>"
        )
    
        fig.update_layout(
    
            xaxis_title="USDT Disponibles",
    
            yaxis_title="",
    
            yaxis=dict(
                autorange="reversed"
            ),
    
            height=500,
    
            margin=dict(
                l=10,
                r=10,
                t=50,
                b=20
            )
        )
    
        st.plotly_chart(
            fig,
            use_container_width=True
        )
        
# ====================================================
# HIPERMAXI
# ====================================================

with tab2:

    st.header("🛒 Monitoreo de Precios Hipermaxi")

    # ======================================
    # FILTRO DE FECHAS
    # ======================================

    fecha_min = df_hiper["Fecha"].min().date()
    fecha_max = df_hiper["Fecha"].max().date()

    if fecha_min == fecha_max:

        inicio = fecha_min
        fin = fecha_max

        st.info(
            f"Solo existe información para la fecha {fecha_max}"
        )

    else:

        inicio, fin = st.slider(
            "Periodo",
            min_value=fecha_min,
            max_value=fecha_max,
            value=(fecha_min, fecha_max),
            key="hiper_fecha"
        )

    df_h = df_hiper[
        (df_hiper["Fecha"].dt.date >= inicio)
        &
        (df_hiper["Fecha"].dt.date <= fin)
    ].copy()

    # ======================================
    # FILTRO SUCURSAL
    # ======================================

    sucursales = sorted(
        df_h["Sucursal"].dropna().unique()
    )

    sucursal = st.selectbox(
        "Sucursal",
        ["Todas"] + list(sucursales)
    )

    if sucursal != "Todas":

        df_h = df_h[
            df_h["Sucursal"] == sucursal
        ]

    # ======================================
    # FILTRO CATEGORÍA
    # ======================================

    categorias = sorted(
        df_h["Categoría"].dropna().unique()
    )

    categoria = st.selectbox(
        "Categoría",
        ["Todas"] + list(categorias)
    )

    if categoria != "Todas":

        df_h = df_h[
            df_h["Categoría"] == categoria
        ]

    # ======================================
    # VARIACIÓN ABSOLUTA
    # ======================================

    df_h = df_h.sort_values(
        ["Sucursal", "Producto", "Fecha"]
    )

    df_h["Variacion_Abs"] = (
        df_h.groupby(
            ["Sucursal", "Producto"]
        )["Precio"]
        .diff()
    )

    # ======================================
    # ÚLTIMA FECHA
    # ======================================

    ultima_fecha = df_h["Fecha"].max()

    df_ult = df_h[
        df_h["Fecha"] == ultima_fecha
    ].copy()

    # ======================================
    # KPIs
    # ======================================

    variacion_total = (
        df_ult["Variacion_Abs"]
        .fillna(0)
        .sum()
    )

    variacion_promedio = (
        df_ult["Variación diaria precio"]
        .mean() * 100
    )

    productos_suben = (
        df_ult["Variacion_Abs"] > 0
    ).sum()

    productos_total = (
        df_ult["Producto"]
        .nunique()
    )

    pct_suben = (
        productos_suben
        / productos_total
        * 100
    ) if productos_total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Variación Total Precio",
        f"Bs {variacion_total:,.2f}"
    )

    col2.metric(
        "Variación Promedio %",
        f"{variacion_promedio:.2f}%"
    )

    col3.metric(
        "% Productos que Suben",
        f"{pct_suben:.2f}%"
    )

    col4.metric(
        "Última Actualización",
        ultima_fecha.strftime("%d/%m/%Y")
    )

    st.markdown("---")

    # ======================================
    # EVOLUCIÓN PRECIO PROMEDIO
    # ======================================

    precios = (
        df_h
        .groupby("Fecha")["Precio"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        precios,
        x="Fecha",
        y="Precio",
        markers=True,
        title="Precio Promedio"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ======================================
    # TOP 10 SUBIDAS Y BAJADAS
    # ======================================

    if len(df_h["Fecha"].unique()) > 1:

        fechas_ordenadas = sorted(df_h["Fecha"].unique())
    
        fecha_actual = fechas_ordenadas[-1]
        fecha_anterior = fechas_ordenadas[-2]
    
        actual = (
            df_h[df_h["Fecha"] == fecha_actual]
            [["Producto", "Precio"]]
            .rename(columns={"Precio": "Precio_Actual"})
        )
    
        anterior = (
            df_h[df_h["Fecha"] == fecha_anterior]
            [["Producto", "Precio"]]
            .rename(columns={"Precio": "Precio_Anterior"})
        )
    
        variaciones = actual.merge(
            anterior,
            on="Producto",
            how="inner"
        )
    
        variaciones["Variacion_Abs"] = (
            variaciones["Precio_Actual"]
            - variaciones["Precio_Anterior"]
        )
    
        top_subidas = (
            variaciones
            .sort_values(
                "Variacion_Abs",
                ascending=False
            )
            .head(10)
        )
    
        top_bajadas = (
            variaciones
            .sort_values(
                "Variacion_Abs",
                ascending=True
            )
            .head(10)
        )
    
        col1, col2 = st.columns(2)
    
        with col1:
    
            st.subheader(
                "🔺 Top 10 Productos con Variación Positiva"
            )
    
            st.dataframe(
                top_subidas[
                    [
                        "Producto",
                        "Precio_Anterior",
                        "Precio_Actual",
                        "Variacion_Abs"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )
    
        with col2:
    
            st.subheader(
                "🔻 Top 10 Productos con Variación Negativa"
            )
    
            st.dataframe(
                top_bajadas[
                    [
                        "Producto",
                        "Precio_Anterior",
                        "Precio_Actual",
                        "Variacion_Abs"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

    # ======================================
    # ANÁLISIS DE PRODUCTO
    # ======================================
    
    st.markdown("---")
    
    st.subheader("🔍 Evolución Histórica de Producto")
    
    productos = sorted(
        df_h["Producto"].dropna().unique()
    )
    
    producto_sel = st.selectbox(
        "Seleccione un producto",
        productos
    )
    
    df_prod = (
        df_h[
            df_h["Producto"] == producto_sel
        ]
        .sort_values("Fecha")
    )
    
    if not df_prod.empty:
    
        precio_actual = (
            df_prod["Precio"].iloc[-1]
        )
    
        precio_inicial = (
            df_prod["Precio"].iloc[0]
        )
    
        precio_min = (
            df_prod["Precio"].min()
        )
    
        precio_max = (
            df_prod["Precio"].max()
        )
    
        variacion_acum = (
            (precio_actual / precio_inicial - 1)
            * 100
        )
    
        c1, c2, c3, c4 = st.columns(4)
    
        c1.metric(
            "Precio Actual",
            f"Bs {precio_actual:,.2f}"
        )
    
        c2.metric(
            "Precio Mínimo",
            f"Bs {precio_min:,.2f}"
        )
    
        c3.metric(
            "Precio Máximo",
            f"Bs {precio_max:,.2f}"
        )
    
        c4.metric(
            "Variación Acumulada",
            f"{variacion_acum:.2f}%"
        )
    
        fig = px.line(
            df_prod,
            x="Fecha",
            y="Precio",
            markers=True,
            title=f"Evolución de {producto_sel}"
        )
    
        st.plotly_chart(
            fig,
            use_container_width=True
        )
    

    # ======================================
    # TORTA POR CATEGORÍA
    # ======================================

    categorias_df = (
        df_h
        .groupby("Categoría")["Producto"]
        .count()
        .reset_index()
    )

    fig = px.pie(
        categorias_df,
        names="Categoría",
        values="Producto",
        title="Participación por Categoría"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ======================================
    # Heatmap
    # ======================================

    heat = (
        df_h
        .groupby(
            [
                "Categoría",
                "Fecha"
            ]
        )["Variación diaria precio"]
        .mean()
        .reset_index()
     )
    heatmap = heat.pivot(
        index="Categoría",
        columns="Fecha",
        values="Variación diaria precio"
    )
    import plotly.express as px
    
    fig = px.imshow(
        heatmap,
        aspect="auto",
        title="Heatmap Variación por Categoría"
    )
    
    st.plotly_chart(
        fig,
        use_container_width=True
    )