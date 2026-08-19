"""
Construcción del universo SIC y dataset histórico.

Entrada:
    data/infoDownload.csv

Salidas:
    data/universo.csv
    data/datos_sic.csv

El objetivo es reproducir la lógica utilizada en la investigación:
    SIC -> validación Yahoo -> filtro de liquidez 80%
    -> histórico de 2 años -> mínimo 450 observaciones
    -> dataset con Momentum 20D.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

ARCHIVO_SIC = BASE_DIR / "data" / "infoDownload.csv"
ARCHIVO_UNIVERSO = BASE_DIR / "data" / "universo.csv"
ARCHIVO_DATOS = BASE_DIR / "data" / "datos_sic.csv"

UMBRAL_LIQUIDEZ = 0.80
MIN_OBSERVACIONES = 450
PERIODO_HISTORICO = "2y"


# ============================================================
# 1. CARGAR SIC
# ============================================================

print("=" * 70)
print("1. CARGANDO SIC")
print("=" * 70)

sic = pd.read_csv(
    ARCHIVO_SIC,
    encoding="utf-8-sig"
)

sufijos = {
    "NASDAQ": "",
    "NEW YORK STOCK EXCHANGE": ""
}

sic["Ticker_Yahoo"] = (
    sic["CLAVE EMISORA"]
    .astype(str)
    .str.strip()
    .str.upper()
    + sic["BOLSA DONDE COTIZA"]
    .str.strip()
    .str.upper()
    .map(sufijos)
    .fillna("")
)

print(f"Emisoras SIC: {len(sic)}")


# ============================================================
# 2. VALIDAR TICKERS EN YAHOO
# ============================================================

print("\n" + "=" * 70)
print("2. VALIDANDO TICKERS EN YAHOO")
print("=" * 70)

tickers_sic = (
    sic["Ticker_Yahoo"]
    .dropna()
    .unique()
    .tolist()
)

datos_yahoo = yf.download(
    tickers_sic,
    period="5d",
    interval="1d",
    auto_adjust=False,
    progress=True,
    threads=True,
    group_by="ticker"
)

validos = []
no_encontrados = []

for ticker in tickers_sic:
    try:
        datos_ticker = datos_yahoo[ticker]

        if not datos_ticker.dropna(how="all").empty:
            validos.append(ticker)
        else:
            no_encontrados.append(ticker)

    except (KeyError, TypeError):
        no_encontrados.append(ticker)

print(f"Candidatos:     {len(tickers_sic)}")
print(f"Con datos:      {len(validos)}")
print(f"Sin datos:      {len(no_encontrados)}")

sic_validos = sic[
    sic["Ticker_Yahoo"].isin(validos)
].copy()

print(f"SIC válidos:    {len(sic_validos)}")


# ============================================================
# 3. LIQUIDEZ
# ============================================================

print("\n" + "=" * 70)
print("3. CALCULANDO LIQUIDEZ")
print("=" * 70)

tickers_validos = (
    sic_validos["Ticker_Yahoo"]
    .drop_duplicates()
    .tolist()
)

datos_liquidez = yf.download(
    tickers_validos,
    period="1mo",
    interval="1d",
    auto_adjust=False,
    progress=True,
    threads=True,
    group_by="ticker"
)

liquidez = []

for ticker in tickers_validos:
    try:
        temp = datos_liquidez[ticker][
            ["Close", "Volume"]
        ].dropna()

        if temp.empty:
            continue

        volumen_dolares = (
            temp["Close"] * temp["Volume"]
        )

        liquidez.append({
            "Ticker_Yahoo": ticker,
            "Volumen_Dolares_Medio": volumen_dolares.mean(),
            "Dias": len(temp)
        })

    except (KeyError, TypeError):
        continue

liquidez = pd.DataFrame(liquidez)

sic_liquidez = sic_validos.merge(
    liquidez,
    on="Ticker_Yahoo",
    how="inner"
)

umbral_liquidez = sic_liquidez[
    "Volumen_Dolares_Medio"
].quantile(UMBRAL_LIQUIDEZ)

sic_filtrado = sic_liquidez[
    sic_liquidez["Volumen_Dolares_Medio"] >= umbral_liquidez
].copy()

print(
    f"Percentil de liquidez: {UMBRAL_LIQUIDEZ:.0%}"
)

print(
    f"Umbral: ${umbral_liquidez:,.2f}"
)

print(
    f"Después del filtro: {len(sic_filtrado)}"
)


# ============================================================
# 4. DESCARGAR HISTÓRICO
# ============================================================

print("\n" + "=" * 70)
print("4. DESCARGANDO HISTÓRICOS")
print("=" * 70)

tickers_sic_final = (
    sic_filtrado["Ticker_Yahoo"]
    .drop_duplicates()
    .tolist()
)

historicos_sic = yf.download(
    tickers_sic_final,
    period=PERIODO_HISTORICO,
    interval="1d",
    auto_adjust=False,
    progress=True,
    threads=True,
    group_by="ticker"
)

datos_sic = []

for ticker in tickers_sic_final:
    try:
        temp = historicos_sic[ticker].copy()

        temp = temp.dropna(
            subset=["Close"]
        )

        if temp.empty:
            continue

        temp = temp.reset_index()
        temp["Ticker"] = ticker

        datos_sic.append(temp)

    except (KeyError, TypeError):
        continue

if not datos_sic:
    raise RuntimeError(
        "Yahoo Finance no devolvió históricos válidos."
    )

df_sic = pd.concat(
    datos_sic,
    ignore_index=True
)


# ============================================================
# 5. CALIDAD DEL HISTÓRICO
# ============================================================

print("\n" + "=" * 70)
print("5. VALIDANDO HISTÓRICOS")
print("=" * 70)

observaciones = (
    df_sic
    .groupby("Ticker")
    .size()
    .reset_index(name="Observaciones")
)

tickers_completos = observaciones.loc[
    observaciones["Observaciones"] >= MIN_OBSERVACIONES,
    "Ticker"
]

df_sic = df_sic[
    df_sic["Ticker"].isin(tickers_completos)
].copy()

print(
    f"Observaciones mínimas requeridas: "
    f"{MIN_OBSERVACIONES}"
)

print(
    f"Acciones con histórico suficiente: "
    f"{df_sic['Ticker'].nunique()}"
)


# ============================================================
# 6. PREPARAR DATASET
# ============================================================

print("\n" + "=" * 70)
print("6. CALCULANDO MOMENTUM")
print("=" * 70)

df_sic = df_sic.sort_values(
    ["Ticker", "Date"]
).reset_index(drop=True)

df_sic["Retorno_1D"] = (
    df_sic.groupby("Ticker")["Close"]
    .pct_change(1)
)

df_sic["Retorno_5D"] = (
    df_sic.groupby("Ticker")["Close"]
    .pct_change(5)
)

df_sic["Retorno_20D"] = (
    df_sic.groupby("Ticker")["Close"]
    .pct_change(20)
)

for h in [1, 3, 5, 10, 20]:
    df_sic[f"Futuro_{h}D"] = (
        df_sic.groupby("Ticker")["Close"]
        .shift(-h)
        / df_sic["Close"]
        - 1
    )

df_sic["Momentum"] = (
    df_sic.groupby("Ticker")["Close"]
    .pct_change(20)
)


# ============================================================
# 7. GRUPO DE MOMENTUM
# ============================================================

def clasificar_momentum(x):
    resultado = pd.Series(
        np.nan,
        index=x.index
    )

    validos = x.dropna()

    if len(validos) >= 3:
        grupos = pd.qcut(
            validos.rank(method="first"),
            3,
            labels=False
        ) + 1

        resultado.loc[validos.index] = grupos

    return resultado


df_sic["Grupo_Momentum"] = (
    df_sic
    .groupby("Date")["Momentum"]
    .transform(clasificar_momentum)
)


# ============================================================
# 8. GUARDAR UNIVERSO
# ============================================================

# Este es el universo definitivo utilizado por el estudio.
universo = sic_filtrado[
    [
        "Ticker_Yahoo",
        "CLAVE EMISORA",
        "RAZON SOCIAL",
        "BOLSA DONDE COTIZA",
        "Volumen_Dolares_Medio"
    ]
].drop_duplicates(
    subset=["Ticker_Yahoo"]
)

universo = universo[
    universo["Ticker_Yahoo"].isin(
        tickers_completos
    )
].copy()

universo.to_csv(
    ARCHIVO_UNIVERSO,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 9. GUARDAR DATASET
# ============================================================

df_sic.to_csv(
    ARCHIVO_DATOS,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# RESULTADO FINAL
# ============================================================

print("\n" + "=" * 70)
print("RESULTADO FINAL")
print("=" * 70)

print(
    f"Universo definitivo: "
    f"{len(universo)} acciones"
)

print(
    f"Observaciones históricas: "
    f"{len(df_sic):,}"
)

print(
    f"Fecha inicial: "
    f"{df_sic['Date'].min()}"
)

print(
    f"Fecha final: "
    f"{df_sic['Date'].max()}"
)

print("\nArchivos generados:")

print(
    f"  {ARCHIVO_UNIVERSO}"
)

print(
    f"  {ARCHIVO_DATOS}"
)

print("\nProceso terminado.")
