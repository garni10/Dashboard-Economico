# Paso 1. Importaciones
import numpy as np
import pandas as pd

#Paso 2. Función para eliminar outliers (IQR)
def eliminar_outliers_iqr(df, columna="Precio"):
    """
    Elimina outliers utilizando el criterio del
    Rango Intercuartílico (IQR).
    """

    q1 = df[columna].quantile(0.25)
    q3 = df[columna].quantile(0.75)

    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    return df[
        (df[columna] >= limite_inferior)
        &
        (df[columna] <= limite_superior)
    ].copy()

#Paso 3. Precio promedio robusto
def serie_precio_promedio_robusto(df):

    resultados = []

    for (timestamp, tipo), grupo in df.groupby(["Timestamp","Tipo"]):

        limpio = eliminar_outliers_iqr(grupo)

        resultados.append({

            "Timestamp": timestamp,

            "Tipo": tipo,

            "Precio": round(limpio["Precio"].mean(),4),

            "N_original": len(grupo),

            "N_utilizado": len(limpio)

        })

    return pd.DataFrame(resultados)
    
# Uso de Snapshot
from datetime import time
def crear_snapshot(timestamp):
    """
    Asigna cada observación al horario operativo
    más cercano del Dashboard.
    """

    hora = timestamp.time()

    fecha = timestamp.normalize()

    if hora < time(11, 30):

        return fecha + pd.Timedelta(hours=8, minutes=30)

    elif hora < time(16, 0):

        return fecha + pd.Timedelta(hours=14, minutes=30)

    else:

        return fecha + pd.Timedelta(hours=17, minutes=30)


# ÍNDICE DE TENSIÓN

def construir_indice_tension(df):
    """
    Construye las variables base del Índice de Tensión
    del Mercado P2P.
    """

    df = df.copy()
    df["Snapshot"] = df["Timestamp"].apply(crear_snapshot)
    
    # Serie de precios promedio robustos
    robusto = serie_precio_promedio_robusto(df)
    
    resultados = []

    for snapshot, grupo in df.groupby("Snapshot"):

        # ==========================
        # SBRECHA
        # ==========================

        buy = robusto[
            (robusto["Snapshot"] == snapshot)
            &
            (robusto["Tipo"] == "BUY")
        ]
        
        sell = robusto[
            (robusto["Snapshot"] == snapshot)
            &
            (robusto["Tipo"] == "SELL")
        ]
        if buy.empty or sell.empty:

            brecha = np.nan

        else:

            precio_buy = buy["Precio"].iloc[0]
            precio_sell = sell["Precio"].iloc[0]

            brecha = (precio_buy - precio_sell) / precio_sell * 100

        # ==========================
        # LIQUIDEZ
        # ==========================

        # Liquidez por snapshot
        liquidez = (
            df.groupby("Snapshot", as_index=False)["Disponible"]
              .sum()
              .rename(columns={"Disponible": "Liquidez"})
        )
        # Media móvil
        liquidez["Media60"] = (
            liquidez["Liquidez"]
            .rolling(
                window=60,
                min_periods=10
            )
            .mean()
        )
        # Desviación estándar móvil
        liquidez["Std60"] = (
            liquidez["Liquidez"]
            .rolling(
                window=60,
                min_periods=10
            )
            .std()
        )

        # Z- score
        liquidez["Z"] = (
            liquidez["Liquidez"] -
            liquidez["Media60"]
        ) / liquidez["Std60"]

        # Invertir signo (poca liquidez = ensión)
        liquidez["Liquidez_Z"] = -liquidez["Z"]

        # Incorporar al DF
        fila_liq = liquidez[
            liquidez["Snapshot"] == snapshot
        ]
        
        if fila_liq.empty:
        
            liquidez_z = np.nan
        
        else:
        
            liquidez_z = fila_liq["Liquidez_Z"].iloc[0]
        
        # ==========================
        # RESULTADOS
        # ==========================

        resultados.append({

            "Snapshot": snapshot,

            "Brecha": brecha,

            "Liquidez": liquidez_z,

            "CV": None,

            "Outliers": None

        })

    return pd.DataFrame(resultados)
    

# ==========================
# SNAPSHOT
# ==========================

def construir_snapshot(df):
    """
    Construye la base analítica del mercado Binance.
    Una fila por Snapshot.
    """

    df = df.copy()

    df["Snapshot"] = df["Timestamp"].apply(crear_snapshot)

    resultados = []

    for (snapshot, tipo), grupo in df.groupby(["Snapshot", "Tipo"]):

        limpio = eliminar_outliers_iqr(grupo)

        resultados.append({

            "Snapshot": snapshot,

            "Tipo": tipo,

            "Precio": limpio["Precio"].mean(),

            "Disponible": limpio["Disponible"].sum()

        })

    snapshot_df = pd.DataFrame(resultados)

    snapshot_df = snapshot_df.pivot(

        index="Snapshot",

        columns="Tipo",

        values=["Precio", "Disponible"]

    )

    snapshot_df.columns = [

        f"{col[0]}_{col[1]}"

        for col in snapshot_df.columns

    ]

    snapshot_df = snapshot_df.reset_index()

    return snapshot_df

# ======================================
# COMPONENTES DEL ÍNDICE DE TENSIÓN
# ======================================

# ======================================
# BRECHA PRECIO ROBUSTO
# ======================================

def calcular_spread(df):
    """
    Calcula el spread robusto entre BUY y SELL
    para cada Snapshot.
    """

    df = df.copy()

    df["Snapshot"] = df["Timestamp"].apply(crear_snapshot)

    resultados = []

    for snapshot, grupo_snapshot in df.groupby("Snapshot"):

        fila = {"Snapshot": snapshot}

        for tipo in ["BUY", "SELL"]:

            grupo = grupo_snapshot[
                grupo_snapshot["Tipo"] == tipo
            ]

            if grupo.empty:

                fila[f"Precio_{tipo}"] = np.nan
                continue

            grupo = eliminar_outliers_iqr(grupo)

            fila[f"Precio_{tipo}"] = grupo["Precio"].mean()

        resultados.append(fila)

    spread = pd.DataFrame(resultados)

    spread["Spread"] = (
        (spread["Precio_BUY"] - spread["Precio_SELL"])
        / spread["Precio_SELL"]
        * 100
    )

    return spread.sort_values("Snapshot").reset_index(drop=True)

# ======================================
# LIQUIDEZ
# ======================================

def calcular_liquidez(df, ventana=60):
    """
    Calcula la liquidez relativa del mercado.
    """

    df = df.copy()

    df["Snapshot"] = df["Timestamp"].apply(crear_snapshot)

    liquidez = (
        df.groupby("Snapshot", as_index=False)["Disponible"]
        .sum()
        .sort_values("Snapshot")
    )

    liquidez.rename(
        columns={"Disponible": "Liquidez"},
        inplace=True
    )

    liquidez["Liquidez_Base"] = (
        liquidez["Liquidez"]
        .rolling(
            window=ventana,
            min_periods=10
        )
        .mean()
    )

    liquidez["Liquidez_Relativa"] = (
        liquidez["Liquidez"]
        /
        liquidez["Liquidez_Base"]
    )

    return liquidez

# ======================================
# COEFICIENTE DE VARIACIÓN (CV)
# ======================================
def calcular_cv(df):
    """
    Calcula el coeficiente de variación (CV)
    del precio para BUY y SELL.
    """

    df = df.copy()

    df["Snapshot"] = df["Timestamp"].apply(crear_snapshot)

    resultados = []

    for snapshot, grupo_snapshot in df.groupby("Snapshot"):

        fila = {"Snapshot": snapshot}

        cvs = []

        for tipo in ["BUY", "SELL"]:

            grupo = grupo_snapshot[
                grupo_snapshot["Tipo"] == tipo
            ]

            if grupo.empty:

                fila[f"CV_{tipo}"] = np.nan
                continue

            grupo = eliminar_outliers_iqr(grupo)

            media = grupo["Precio"].mean()

            if media == 0 or np.isnan(media):

                cv = np.nan

            else:

                cv = (
                    grupo["Precio"].std()
                    /
                    media
                    * 100
                )

            fila[f"CV_{tipo}"] = cv

            cvs.append(cv)

        fila["CV_TOTAL"] = np.nanmean(cvs)

        resultados.append(fila)

    return (
        pd.DataFrame(resultados)
        .sort_values("Snapshot")
        .reset_index(drop=True)
    )

# ======================================
# OUTLIERS 
# ======================================
def calcular_outliers(df):
    """
    Calcula el porcentaje de anuncios eliminados
    por el filtro IQR.
    """

    df = df.copy()

    df["Snapshot"] = df["Timestamp"].apply(crear_snapshot)

    resultados = []

    for snapshot, grupo_snapshot in df.groupby("Snapshot"):

        fila = {"Snapshot": snapshot}

        tasas = []

        for tipo in ["BUY", "SELL"]:

            grupo = grupo_snapshot[
                grupo_snapshot["Tipo"] == tipo
            ]

            if grupo.empty:

                fila[f"Outliers_{tipo}"] = np.nan
                continue

            n_original = len(grupo)

            limpio = eliminar_outliers_iqr(grupo)

            n_limpio = len(limpio)

            tasa = (
                (n_original - n_limpio)
                /
                n_original
                * 100
            )

            fila[f"Outliers_{tipo}"] = tasa

            tasas.append(tasa)

        fila["Outliers_TOTAL"] = np.nanmean(tasas)

        resultados.append(fila)

    return (
        pd.DataFrame(resultados)
        .sort_values("Snapshot")
        .reset_index(drop=True)
    )

# ======================================
# CONSTRUIR COMPONENTES
# ======================================

def construir_componentes(df):
    """
    Une todos los componentes del Índice de Tensión.
    """

    spread = calcular_spread(df)

    liquidez = calcular_liquidez(df)

    cv = calcular_cv(df)

    outliers = calcular_outliers(df)
    
    componentes = spread.merge(
        liquidez[
            [
                "Snapshot",
                "Liquidez",
                "Liquidez_Base",
                "Liquidez_Relativa"
            ]
        ],
        on="Snapshot",
        how="left"
    )

    componentes = componentes.merge(
        cv,
        on="Snapshot",
        how="left"
    )

    componentes = componentes.merge(
        outliers,
        on="Snapshot",
        how="left"
    )    

    # =====================================
    # NORMALIZACIÓN DE COMPONENTES
    # =====================================
    
    componentes["Score_Spread"] = normalizar_percentil(
        componentes["Spread"]
    )

    # Mayor liquidez = menor tensión
    componentes["Score_Liquidez"] = (
        100
        - normalizar_percentil(
            componentes["Liquidez_Relativa"]
        )
    )

    componentes["Score_CV"] = normalizar_percentil(
        componentes["CV_TOTAL"]
    )
    
    componentes["Score_Outliers"] = normalizar_percentil(
        componentes["Outliers_TOTAL"]
    )
        
    return (
        componentes
        .sort_values("Snapshot")
        .reset_index(drop=True)
    )

# ======================================
# NORMALIZACIÓN COMPONENTES
# ======================================
#from scipy.stats import rankdata

def normalizar_percentil(serie):
    """
    Convierte una serie en percentiles (0-100)
    sin depender de SciPy.
    """

    serie = serie.copy()

    return (
        serie.rank(method="average", pct=True)
        * 100
    )

    resultado.loc[mascara] = percentiles

    return resultado

# ======================================
# ÍNDICE DE TENSIÓN
# ======================================
def calcular_indice_tension(componentes):
    """
    Calcula el Índice de Tensión Cambiaria P2P.
    """

    componentes = componentes.copy()

    componentes["Indice_Tension"] = (
        
        componentes["Score_Spread"] * 0.40

        +

        componentes["Score_Liquidez"] * 0.25

        +

        componentes["Score_CV"] * 0.20

        +

        componentes["Score_Outliers"] * 0.15

    )

    componentes["Estado"] = pd.cut(

        componentes["Indice_Tension"],
    
        bins=[0,20,40,60,80,100],
    
        labels=[
            "Muy Baja",
            "Baja",
            "Moderada",
            "Alta",
            "Extrema"
        ],
    
        include_lowest=True
    )
    
    return componentes












