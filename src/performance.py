# Generated from the research notebook: SIC copy.ipynb
# Project: Momentum Trading Strategy
# NOTE: This file preserves the research logic from the notebook.
# It is intended for the repository and may require local data/configuration.


# ============================================================
# NOTEBOOK CELL 12
# ============================================================
# ============================================================
# MÉTRICAS COMPLETAS + BENCHMARK
# ============================================================

import numpy as np
import pandas as pd

metricas = []

for horizonte, r in resultados_backtest.items():

    # Recuperamos las carteras del backtest
    # Las reconstruimos para obtener la serie temporal
    # de rendimientos.
    
    operaciones = []
    
    fechas = sorted(
        df_sic["Date"].dropna().unique()
    )

    posiciones_fecha = 0

    while posiciones_fecha < len(fechas) - horizonte:

        fecha_señal = fechas[posiciones_fecha]

        dia = df_sic[
            df_sic["Date"] == fecha_señal
        ].dropna(
            subset=["Momentum"]
        ).copy()

        if len(dia) < 3:
            posiciones_fecha += 1
            continue

        dia["Grupo_Momentum"] = pd.qcut(
            dia["Momentum"].rank(method="first"),
            3,
            labels=False
        ) + 1

        seleccion = dia[
            dia["Grupo_Momentum"] == 3
        ]

        fecha_entrada = fechas[
            posiciones_fecha + 1
        ]

        fecha_salida = fechas[
            posiciones_fecha + horizonte
        ]

        entrada = df_sic[
            (df_sic["Date"] == fecha_entrada) &
            (df_sic["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ]

        salida = df_sic[
            (df_sic["Date"] == fecha_salida) &
            (df_sic["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Close"]
        ]

        cartera = entrada.merge(
            salida,
            on="Ticker"
        )

        if cartera.empty:
            posiciones_fecha += horizonte
            continue

        cartera["Retorno"] = (
            cartera["Close"]
            / cartera["Open"]
            - 1
        )

        operaciones.append({
            "Fecha": fecha_entrada,
            "Retorno": cartera["Retorno"].mean()
        })

        posiciones_fecha += horizonte

    estrategia = pd.DataFrame(
        operaciones
    ).sort_values("Fecha")

    # --------------------------------------------------------
    # MÉTRICAS DE LA ESTRATEGIA
    # --------------------------------------------------------

    retornos = estrategia["Retorno"]

    capital = (
        1 + retornos
    ).cumprod()

    años = (
        estrategia["Fecha"].iloc[-1]
        - estrategia["Fecha"].iloc[0]
    ).days / 365.25

    CAGR = (
        capital.iloc[-1] ** (1 / años)
        - 1
    )

    volatilidad = (
        retornos.std()
        * np.sqrt(252 / horizonte)
    )

    sharpe = CAGR / volatilidad

    drawdown = (
        capital
        / capital.cummax()
        - 1
    )

    # --------------------------------------------------------
    # BENCHMARK
    # --------------------------------------------------------

    benchmark_diario = (
        df_sic
        .groupby("Date")
        .apply(
            lambda x:
            (
                x["Close"] / x["Open"] - 1
            ).mean(),
            include_groups=False
        )
    )

    benchmark_diario = (
        benchmark_diario
        .reindex(estrategia["Fecha"])
        .dropna()
    )

    benchmark_capital = (
        1 + benchmark_diario
    ).cumprod()

    benchmark_años = (
        benchmark_diario.index[-1]
        - benchmark_diario.index[0]
    ).days / 365.25

    benchmark_CAGR = (
        benchmark_capital.iloc[-1]
        ** (1 / benchmark_años)
        - 1
    )

    benchmark_volatilidad = (
        benchmark_diario.std()
        * np.sqrt(252)
    )

    benchmark_sharpe = (
        benchmark_CAGR
        / benchmark_volatilidad
    )

    benchmark_drawdown = (
        benchmark_capital
        / benchmark_capital.cummax()
        - 1
    )

    metricas.append({
        "Horizonte": f"{horizonte}D",
        "CAGR_Estrategia": CAGR,
        "Volatilidad_Estrategia": volatilidad,
        "Sharpe_Estrategia": sharpe,
        "MaxDD_Estrategia": drawdown.min(),
        "CAGR_Benchmark": benchmark_CAGR,
        "Volatilidad_Benchmark": benchmark_volatilidad,
        "Sharpe_Benchmark": benchmark_sharpe,
        "MaxDD_Benchmark": benchmark_drawdown.min()
    })


metricas = pd.DataFrame(metricas)

print("================================")
print("ESTRATEGIA VS BENCHMARK")
print("================================")

print(
    metricas.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)
