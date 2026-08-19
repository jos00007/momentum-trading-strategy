# Generated from the research notebook: SIC copy.ipynb
# Project: Momentum Trading Strategy
# NOTE: This file preserves the research logic from the notebook.
# It is intended for the repository and may require local data/configuration.


# ============================================================
# NOTEBOOK CELL 0
# ============================================================
import pandas as pd
# ============================================================
# SIC → TICKERS YAHOO
# ============================================================

sic = pd.read_csv(
    "infoDownload.csv",
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

print("Emisoras:", len(sic))

print("\nEjemplos:")
print(
    sic[
        [
            "CLAVE EMISORA",
            "RAZON SOCIAL",
            "BOLSA DONDE COTIZA",
            "Ticker_Yahoo"
        ]
    ].head(30)
)

print("\nBolsas sin equivalencia:")
print(
    sic.loc[
        ~sic["BOLSA DONDE COTIZA"].str.strip().str.upper().isin(
            sufijos.keys()
        ),
        "BOLSA DONDE COTIZA"
    ].value_counts()
)

# ============================================================
# NOTEBOOK CELL 1
# ============================================================
import yfinance as yf
# ============================================================
# VALIDAR TICKERS SIC EN YAHOO — DESCARGA MASIVA
# ============================================================

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

print("\n================================")
print("VALIDACIÓN YAHOO")
print("================================")
print(f"Candidatos:      {len(tickers_sic)}")
print(f"Encontrados:     {len(validos)}")
print(f"No encontrados:  {len(no_encontrados)}")

print("\nPrimeros encontrados:")
print(validos[:20])

print("\nPrimeros no encontrados:")
print(no_encontrados[:20])

# ============================================================
# NOTEBOOK CELL 2
# ============================================================
# ============================================================
# REVISIÓN DE LA DESCARGA MASIVA
# ============================================================

print("Columnas descargadas:", len(datos_yahoo.columns))

# Verificar algunos tickers que sabemos que deberían existir
for ticker in ["AAPL", "AMZN", "MSFT", "TSLA"]:
    try:
        print(
            ticker,
            "->",
            datos_yahoo[ticker].dropna(how="all").shape
        )
    except KeyError:
        print(ticker, "-> NO ESTÁ EN LA DESCARGA")

# Tickers que realmente aparecen en la descarga
tickers_descargados = set(
    datos_yahoo.columns.get_level_values(0)
)

print("\nTickers en descarga:", len(tickers_descargados))

# ============================================================
# NOTEBOOK CELL 3
# ============================================================
# ============================================================
# VALIDACIÓN REAL DEL UNIVERSO SIC
# ============================================================

validos = []
no_encontrados = []

for ticker in tickers_sic:

    datos_ticker = datos_yahoo[ticker]

    if datos_ticker["Close"].notna().any():
        validos.append(ticker)
    else:
        no_encontrados.append(ticker)

print("================================")
print("VALIDACIÓN REAL")
print("================================")
print(f"Candidatos:       {len(tickers_sic)}")
print(f"Con datos:        {len(validos)}")
print(f"Sin datos:        {len(no_encontrados)}")

# Guardamos solamente los candidatos válidos
sic_validos = sic[
    sic["Ticker_Yahoo"].isin(validos)
].copy()

print("\nEmisoras SIC válidas:", len(sic_validos))

print("\nDistribución por bolsa:")
print(
    sic_validos["BOLSA DONDE COTIZA"]
    .value_counts()
)

# ============================================================
# NOTEBOOK CELL 4
# ============================================================
# ============================================================
# LIQUIDEZ DEL UNIVERSO SIC
# ============================================================

tickers_validos = sic_validos["Ticker_Yahoo"].tolist()

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

        if len(temp) == 0:
            continue

        volumen_dolares = (
            temp["Close"] * temp["Volume"]
        )

        liquidez.append({
            "Ticker": ticker,
            "Volumen_Dolares_Medio": volumen_dolares.mean(),
            "Dias": len(temp)
        })

    except (KeyError, TypeError):
        continue

liquidez = pd.DataFrame(liquidez)

# Unir con la información original del SIC
sic_liquidez = sic_validos.merge(
    liquidez,
    left_on="Ticker_Yahoo",
    right_on="Ticker",
    how="inner"
)

print("================================")
print("LIQUIDEZ SIC")
print("================================")
print(
    sic_liquidez[
        "Volumen_Dolares_Medio"
    ].describe(
        percentiles=[
            .50,
            .75,
            .80,
            .90,
            .95,
            .99
        ]
    )
)

# ============================================================
# NOTEBOOK CELL 5
# ============================================================
# ============================================================
# FILTRO DE LIQUIDEZ — SIC
# ============================================================

umbral_liquidez = sic_liquidez[
    "Volumen_Dolares_Medio"
].quantile(0.80)

sic_filtrado = sic_liquidez[
    sic_liquidez["Volumen_Dolares_Medio"] >= umbral_liquidez
].copy()

print("================================")
print("UNIVERSO SIC FILTRADO")
print("================================")
print("Umbral:", f"${umbral_liquidez:,.2f}")
print("Emisoras:", len(sic_filtrado))

print("\nDistribución por bolsa:")
print(
    sic_filtrado[
        "BOLSA DONDE COTIZA"
    ].value_counts()
)

print("\nMayor volumen:")
print(
    sic_filtrado[
        [
            "Ticker_Yahoo",
            "RAZON SOCIAL",
            "BOLSA DONDE COTIZA",
            "Volumen_Dolares_Medio"
        ]
    ]
    .sort_values(
        "Volumen_Dolares_Medio",
        ascending=False
    )
    .head(20)
)

# ============================================================
# NOTEBOOK CELL 6
# ============================================================
# ============================================================
# HISTÓRICOS SIC — 2 AÑOS
# ============================================================

tickers_sic_final = (
    sic_filtrado["Ticker_Yahoo"]
    .drop_duplicates()
    .tolist()
)

print("Emisoras a descargar:", len(tickers_sic_final))

historicos_sic = yf.download(
    tickers_sic_final,
    period="2y",
    interval="1d",
    auto_adjust=False,
    progress=True,
    threads=True,
    group_by="ticker"
)

# ============================================================
# CONVERTIR A FORMATO LONG
# ============================================================

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

df_sic = pd.concat(
    datos_sic,
    ignore_index=True
)

# ============================================================
# RESUMEN
# ============================================================

print("\n================================")
print("HISTÓRICOS SIC")
print("================================")

print("Observaciones:", len(df_sic))
print("Acciones:", df_sic["Ticker"].nunique())
print("Inicio:", df_sic["Date"].min())
print("Fin:", df_sic["Date"].max())

print("\nObservaciones por acción:")
print(
    df_sic
    .groupby("Ticker")
    .size()
    .describe()
)

# ============================================================
# NOTEBOOK CELL 7
# ============================================================
# ============================================================
# CALIDAD DEL HISTÓRICO
# ============================================================

observaciones = (
    df_sic
    .groupby("Ticker")
    .size()
    .reset_index(name="Observaciones")
)

# Exigir al menos 90% del historial
min_observaciones = 450

tickers_completos = observaciones.loc[
    observaciones["Observaciones"] >= min_observaciones,
    "Ticker"
]

df_sic = df_sic[
    df_sic["Ticker"].isin(tickers_completos)
].copy()

print("================================")
print("UNIVERSO DEFINITIVO")
print("================================")
print("Acciones:", df_sic["Ticker"].nunique())
print("Observaciones:", len(df_sic))

print("\nObservaciones por acción:")
print(
    df_sic
    .groupby("Ticker")
    .size()
    .describe()
)

# ============================================================
# NOTEBOOK CELL 8
# ============================================================
import numpy as np
# ============================================================
# PREPARACIÓN DEL DATASET SIC
# ============================================================

df_sic = df_sic.sort_values(
    ["Ticker", "Date"]
).reset_index(drop=True)

# Retornos históricos
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

# ============================================================
# RETORNOS FUTUROS
# ============================================================

for h in [1, 3, 5, 10, 20]:

    df_sic[f"Futuro_{h}D"] = (
        df_sic.groupby("Ticker")["Close"]
        .shift(-h)
        / df_sic["Close"]
        - 1
    )

# ============================================================
# MOMENTUM
# ============================================================

# Usamos 20 días como momentum de referencia,
# igual que nuestra investigación original.

df_sic["Momentum"] = (
    df_sic.groupby("Ticker")["Close"]
    .pct_change(20)
)

# ============================================================
# CLASIFICACIÓN POR FECHA
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
# RESULTADOS
# ============================================================

resultado_sic = (
    df_sic
    .dropna(
        subset=[
            "Grupo_Momentum",
            "Futuro_1D",
            "Futuro_3D",
            "Futuro_5D",
            "Futuro_10D",
            "Futuro_20D"
        ]
    )
    .groupby("Grupo_Momentum")
    .agg(
        Observaciones=("Ticker", "count"),

        Media_1D=("Futuro_1D", "mean"),
        Mediana_1D=("Futuro_1D", "median"),

        Media_3D=("Futuro_3D", "mean"),
        Mediana_3D=("Futuro_3D", "median"),

        Media_5D=("Futuro_5D", "mean"),
        Mediana_5D=("Futuro_5D", "median"),

        Media_10D=("Futuro_10D", "mean"),
        Mediana_10D=("Futuro_10D", "median"),

        Media_20D=("Futuro_20D", "mean"),
        Mediana_20D=("Futuro_20D", "median")
    )
)

print("================================")
print("REVERSIÓN — SIC")
print("================================")
print(resultado_sic)
