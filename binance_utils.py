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
def precio_promedio_robusto(df):

    limpio = eliminar_outliers_iqr(df)

    return limpio["Precio"].mean()

