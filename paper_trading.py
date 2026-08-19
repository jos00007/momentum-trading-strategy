# Generated from the research notebook: SIC copy.ipynb
# Project: Momentum Trading Strategy
# NOTE: This file preserves the research logic from the notebook.
# It is intended for the repository and may require local data/configuration.


# ============================================================
# NOTEBOOK CELL 23
# ============================================================
# ============================================================
# PAPER TRADING — SEÑAL MOMENTUM 20D
# TOP 10 — CAPITAL $588 USD
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from pandas.tseries.offsets import BDay

# ============================================================
# CONFIGURACIÓN
# ============================================================

CAPITAL_USD = 588
NUM_POSICIONES = 10
MOMENTUM_DIAS = 20

tickers = (
    sic_ibkr["Ticker_Yahoo"]
    .dropna()
    .drop_duplicates()
    .tolist()
)

print("=" * 70)
print("PAPER TRADING — MOMENTUM 20D")
print("=" * 70)

print(f"Capital virtual: ${CAPITAL_USD:,.2f} USD")
print(f"Posiciones: {NUM_POSICIONES}")
print(f"Momentum: {MOMENTUM_DIAS} sesiones")
print(f"Universo: {len(tickers)} acciones")


# ============================================================
# DESCARGA
# ============================================================

print("\nDescargando datos...")

data = yf.download(
    tickers=tickers,
    period="3mo",
    interval="1d",
    auto_adjust=False,
    progress=False,
    threads=True
)


# ============================================================
# CLOSE
# ============================================================

if isinstance(data.columns, pd.MultiIndex):

    close = data["Close"].copy()

else:

    close = data[["Close"]].copy()

    if len(tickers) == 1:
        close.columns = tickers


close = close.sort_index()

close = close.dropna(
    axis=1,
    how="all"
)


# ============================================================
# HISTÓRICO SUFICIENTE
# ============================================================

close = close.dropna(
    axis=1,
    thresh=MOMENTUM_DIAS + 1
)


# ============================================================
# MOMENTUM 20D
# ============================================================

momentum = (
    close
    / close.shift(MOMENTUM_DIAS)
    - 1
)


# ============================================================
# FECHA DE SEÑAL
# ============================================================

fecha_señal = close.index[-1]


# ============================================================
# MOMENTUM DEL ÚLTIMO CIERRE
# ============================================================

señales = (
    momentum.loc[fecha_señal]
    .dropna()
    .sort_values(
        ascending=False
    )
)


# ============================================================
# TOP 10
# ============================================================

top10 = (
    señales
    .head(NUM_POSICIONES)
    .rename("Momentum")
    .reset_index()
)

top10.columns = [
    "Ticker",
    "Momentum"
]


# ============================================================
# PRECIO DE CIERRE
# ============================================================

precios = (
    close.loc[fecha_señal]
    .rename("Close")
    .reset_index()
)

precios.columns = [
    "Ticker",
    "Close"
]

top10 = top10.merge(
    precios,
    on="Ticker",
    how="left"
)


# ============================================================
# CAPITAL POR POSICIÓN
# ============================================================

capital_por_posicion = (
    CAPITAL_USD / NUM_POSICIONES
)

top10["Capital_USD"] = (
    capital_por_posicion
)

top10["Cantidad_Teorica"] = (
    top10["Capital_USD"]
    / top10["Close"]
)


# ============================================================
# SIGUIENTE SESIÓN
# ============================================================

# Como todavía no existe el dato de mañana,
# utilizamos el siguiente día hábil.

fecha_entrada = (
    fecha_señal
    + BDay(1)
)


# ============================================================
# FECHA DE SALIDA
# 10 SESIONES DESPUÉS DE LA ENTRADA
# ============================================================

fecha_salida = (
    fecha_entrada
    + BDay(10)
)


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

print("\n")
print("=" * 70)
print("SEÑAL GENERADA")
print("=" * 70)

print(
    "Fecha de señal:",
    fecha_señal.strftime("%Y-%m-%d")
)

print(
    "Fecha de entrada:",
    fecha_entrada.strftime("%Y-%m-%d")
)

print(
    "Fecha de salida:",
    fecha_salida.strftime("%Y-%m-%d")
)

print(
    f"\nCapital por posición: "
    f"${capital_por_posicion:,.2f} USD"
)

print("\nTOP 10")
print("-" * 70)

mostrar = top10.copy()

mostrar["Momentum"] = (
    mostrar["Momentum"]
    .map(
        lambda x: f"{x:.2%}"
    )
)

mostrar["Close"] = (
    mostrar["Close"]
    .map(
        lambda x: f"${x:.2f}"
    )
)

mostrar["Capital_USD"] = (
    mostrar["Capital_USD"]
    .map(
        lambda x: f"${x:.2f}"
    )
)

mostrar["Cantidad_Teorica"] = (
    mostrar["Cantidad_Teorica"]
    .map(
        lambda x: f"{x:.4f}"
    )
)

print(
    mostrar.to_string(
        index=False
    )
)


# ============================================================
# GUARDAR SEÑAL
# ============================================================

registro = top10.copy()

registro["Fecha_Señal"] = (
    fecha_señal
)

registro["Fecha_Entrada"] = (
    fecha_entrada
)

registro["Fecha_Salida"] = (
    fecha_salida
)

registro["Capital_Total_USD"] = (
    CAPITAL_USD
)

registro["Capital_Por_Posicion_USD"] = (
    capital_por_posicion
)

registro.to_csv(
    "paper_trading_señal.csv",
    index=False
)

print("\n")
print("=" * 70)
print("SEÑAL GUARDADA")
print("=" * 70)

print(
    "Archivo: paper_trading_señal.csv"
)
