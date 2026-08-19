# Generated from the research notebook: SIC copy.ipynb
# Project: Momentum Trading Strategy
# NOTE: This file preserves the research logic from the notebook.
# It is intended for the repository and may require local data/configuration.


# ============================================================
# NOTEBOOK CELL 13
# ============================================================
# ============================================================
# HOLDOUT 80/20 — MOMENTUM SIC — 10 DÍAS
# ============================================================

capital_inicial = 100_000
horizonte = 10

bt = df_sic.sort_values(
    ["Date", "Ticker"]
).copy()

fechas = sorted(
    bt["Date"].dropna().unique()
)

# ------------------------------------------------------------
# CORTE 80/20
# ------------------------------------------------------------

punto_corte = int(len(fechas) * 0.80)

fecha_corte = fechas[punto_corte]

print("================================")
print("DIVISIÓN IS / HOLDOUT")
print("================================")
print("Inicio:", fechas[0])
print("Fecha corte:", fecha_corte)
print("Fin:", fechas[-1])

# ============================================================
# FUNCIÓN DE BACKTEST
# ============================================================

def ejecutar_backtest(data, fechas, horizonte):

    operaciones = []
    carteras = []

    i = 0

    while i < len(fechas) - horizonte:

        fecha_señal = fechas[i]

        dia = data[
            data["Date"] == fecha_señal
        ].dropna(
            subset=["Momentum"]
        ).copy()

        if len(dia) < 3:
            i += 1
            continue

        # ----------------------------------------------------
        # TERCIL SUPERIOR DE MOMENTUM
        # ----------------------------------------------------

        dia["Grupo_Momentum"] = pd.qcut(
            dia["Momentum"].rank(method="first"),
            3,
            labels=False
        ) + 1

        seleccion = dia[
            dia["Grupo_Momentum"] == 3
        ][["Ticker"]]

        # ----------------------------------------------------
        # ENTRADA Y SALIDA
        # ----------------------------------------------------

        fecha_entrada = fechas[i + 1]
        fecha_salida = fechas[i + horizonte]

        entrada = data[
            (data["Date"] == fecha_entrada) &
            (data["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ]

        salida = data[
            (data["Date"] == fecha_salida) &
            (data["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Close"]
        ]

        cartera = entrada.merge(
            salida,
            on="Ticker",
            how="inner"
        )

        if cartera.empty:
            i += horizonte
            continue

        # ----------------------------------------------------
        # RETORNO
        # ----------------------------------------------------

        cartera["Retorno"] = (
            cartera["Close"]
            / cartera["Open"]
            - 1
        )

        retorno_cartera = (
            cartera["Retorno"].mean()
        )

        carteras.append({
            "Fecha_Señal": fecha_señal,
            "Fecha_Entrada": fecha_entrada,
            "Fecha_Salida": fecha_salida,
            "Acciones": len(cartera),
            "Retorno": retorno_cartera
        })

        operaciones.extend(
            cartera.to_dict("records")
        )

        # No solapar carteras
        i += horizonte

    carteras = pd.DataFrame(carteras)
    operaciones = pd.DataFrame(operaciones)

    if carteras.empty:
        return None, None

    carteras = carteras.sort_values(
        "Fecha_Entrada"
    )

    # --------------------------------------------------------
    # CAPITAL
    # --------------------------------------------------------

    carteras["Capital"] = (
        capital_inicial
        * (1 + carteras["Retorno"]).cumprod()
    )

    carteras["Max_Capital"] = (
        carteras["Capital"].cummax()
    )

    carteras["Drawdown"] = (
        carteras["Capital"]
        / carteras["Max_Capital"]
        - 1
    )

    # --------------------------------------------------------
    # MÉTRICAS
    # --------------------------------------------------------

    ganadoras = operaciones[
        operaciones["Retorno"] > 0
    ]

    perdedoras = operaciones[
        operaciones["Retorno"] < 0
    ]

    profit_factor = (
        ganadoras["Retorno"].sum()
        / abs(perdedoras["Retorno"].sum())
        if len(perdedoras) > 0
        else np.nan
    )

    resultado = {
        "Capital_Final":
            carteras["Capital"].iloc[-1],

        "Retorno_Total":
            carteras["Capital"].iloc[-1]
            / capital_inicial - 1,

        "Max_Drawdown":
            carteras["Drawdown"].min(),

        "Profit_Factor":
            profit_factor,

        "Carteras":
            len(carteras),

        "Operaciones":
            len(operaciones),

        "Acciones_Promedio":
            carteras["Acciones"].mean(),

        "Ganadoras":
            len(ganadoras),

        "Perdedoras":
            len(perdedoras),

        "Ganancia_Promedio":
            ganadoras["Retorno"].mean(),

        "Perdida_Promedio":
            perdedoras["Retorno"].mean()
    }

    return carteras, resultado


# ============================================================
# ENTRENAMIENTO / IS
# ============================================================

fechas_is = [
    f for f in fechas
    if f < fecha_corte
]

df_is = bt[
    bt["Date"] < fecha_corte
].copy()

carteras_is, resultado_is = ejecutar_backtest(
    df_is,
    fechas_is,
    horizonte
)


# ============================================================
# HOLDOUT / OOS
# ============================================================

fechas_oos = [
    f for f in fechas
    if f >= fecha_corte
]

df_oos = bt[
    bt["Date"] >= fecha_corte
].copy()

carteras_oos, resultado_oos = ejecutar_backtest(
    df_oos,
    fechas_oos,
    horizonte
)


# ============================================================
# RESULTADOS
# ============================================================

print("\n")
print("=" * 60)
print("IN-SAMPLE — 80%")
print("=" * 60)

for clave, valor in resultado_is.items():

    if "Capital" in clave:
        print(f"{clave}: ${valor:,.2f}")

    elif "Retorno" in clave or "Drawdown" in clave:
        print(f"{clave}: {valor:.2%}")

    elif "Factor" in clave:
        print(f"{clave}: {valor:.3f}")

    elif "Promedio" in clave and clave != "Acciones_Promedio":
        print(f"{clave}: {valor:.4%}")

    else:
        print(f"{clave}: {valor:.2f}")


print("\n")
print("=" * 60)
print("HOLDOUT — 20%")
print("=" * 60)

for clave, valor in resultado_oos.items():

    if "Capital" in clave:
        print(f"{clave}: ${valor:,.2f}")

    elif "Retorno" in clave or "Drawdown" in clave:
        print(f"{clave}: {valor:.2%}")

    elif "Factor" in clave:
        print(f"{clave}: {valor:.3f}")

    elif "Promedio" in clave and clave != "Acciones_Promedio":
        print(f"{clave}: {valor:.4%}")

    else:
        print(f"{clave}: {valor:.2f}")

# ============================================================
# NOTEBOOK CELL 14
# ============================================================
# ============================================================
# WALK-FORWARD OOS — MOMENTUM SIC
# ============================================================

capital_inicial = 100_000
horizonte = 10
meses_oos = 3

bt = df_sic.sort_values(
    ["Date", "Ticker"]
).copy()

fechas = sorted(
    bt["Date"].dropna().unique()
)

# ------------------------------------------------------------
# CREAR BLOQUES OOS DE 3 MESES
# ------------------------------------------------------------

fechas_df = pd.DataFrame({
    "Date": fechas
})

fechas_df["Periodo"] = (
    fechas_df["Date"]
    .dt.to_period("Q")
)

periodos = sorted(
    fechas_df["Periodo"].unique()
)

resultados_wf = []
todas_carteras = []

capital = capital_inicial

# ------------------------------------------------------------
# CADA TRIMESTRE ES UN BLOQUE OOS
# ------------------------------------------------------------

for periodo in periodos:

    fechas_periodo = fechas_df.loc[
        fechas_df["Periodo"] == periodo,
        "Date"
    ].tolist()

    if len(fechas_periodo) < horizonte + 1:
        continue

    # Datos disponibles solamente dentro del período OOS
    data_periodo = bt[
        bt["Date"].isin(fechas_periodo)
    ].copy()

    i = 0
    carteras_periodo = []

    while i < len(fechas_periodo) - horizonte:

        fecha_señal = fechas_periodo[i]

        dia = data_periodo[
            data_periodo["Date"] == fecha_señal
        ].dropna(
            subset=["Momentum"]
        ).copy()

        if len(dia) < 3:
            i += 1
            continue

        # ----------------------------------------------------
        # SELECCIONAR GANADORES DE MOMENTUM
        # ----------------------------------------------------

        dia["Grupo_Momentum"] = pd.qcut(
            dia["Momentum"].rank(method="first"),
            3,
            labels=False
        ) + 1

        seleccion = dia[
            dia["Grupo_Momentum"] == 3
        ][["Ticker"]]

        # ----------------------------------------------------
        # ENTRADA / SALIDA
        # ----------------------------------------------------

        fecha_entrada = fechas_periodo[i + 1]
        fecha_salida = fechas_periodo[i + horizonte]

        entrada = data_periodo[
            (data_periodo["Date"] == fecha_entrada) &
            (data_periodo["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ]

        salida = data_periodo[
            (data_periodo["Date"] == fecha_salida) &
            (data_periodo["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Close"]
        ]

        cartera = entrada.merge(
            salida,
            on="Ticker",
            how="inner"
        )

        if cartera.empty:
            i += horizonte
            continue

        cartera["Retorno"] = (
            cartera["Close"]
            / cartera["Open"]
            - 1
        )

        retorno = cartera["Retorno"].mean()

        # Capital de la cartera
        capital *= (1 + retorno)

        carteras_periodo.append({
            "Periodo": str(periodo),
            "Fecha_Entrada": fecha_entrada,
            "Fecha_Salida": fecha_salida,
            "Acciones": len(cartera),
            "Retorno": retorno,
            "Capital": capital
        })

        todas_carteras.append(
            carteras_periodo[-1]
        )

        # No solapar posiciones
        i += horizonte

    # --------------------------------------------------------
    # MÉTRICAS DEL BLOQUE
    # --------------------------------------------------------

    if len(carteras_periodo) == 0:
        continue

    periodo_df = pd.DataFrame(
        carteras_periodo
    )

    ganadoras = periodo_df[
        periodo_df["Retorno"] > 0
    ]

    perdedoras = periodo_df[
        periodo_df["Retorno"] < 0
    ]

    profit_factor = (
        ganadoras["Retorno"].sum()
        / abs(perdedoras["Retorno"].sum())
        if len(perdedoras) > 0
        else np.nan
    )

    capital_inicio_periodo = (
        periodo_df["Capital"].iloc[0]
        / (1 + periodo_df["Retorno"].iloc[0])
    )

    retorno_periodo = (
        periodo_df["Capital"].iloc[-1]
        / capital_inicio_periodo
        - 1
    )

    # Drawdown dentro del período
    capital_periodo = periodo_df["Capital"]

    max_capital = (
        capital_periodo.cummax()
    )

    drawdown = (
        capital_periodo
        / max_capital
        - 1
    )

    resultados_wf.append({
        "Periodo": str(periodo),
        "Carteras": len(periodo_df),
        "Operaciones": int(
            periodo_df["Acciones"].sum()
        ),
        "Retorno": retorno_periodo,
        "Profit_Factor": profit_factor,
        "Max_Drawdown": drawdown.min(),
        "Acciones_Medias": periodo_df[
            "Acciones"
        ].mean()
    })


# ============================================================
# RESULTADOS POR PERÍODO
# ============================================================

resultados_wf = pd.DataFrame(
    resultados_wf
)

todas_carteras = pd.DataFrame(
    todas_carteras
)

print("================================")
print("WALK-FORWARD OOS")
print("================================")

print(
    resultados_wf.to_string(
        index=False,
        formatters={
            "Retorno":
                lambda x: f"{x:.2%}",
            "Profit_Factor":
                lambda x: f"{x:.3f}",
            "Max_Drawdown":
                lambda x: f"{x:.2%}",
            "Acciones_Medias":
                lambda x: f"{x:.1f}"
        }
    )
)

# ============================================================
# MÉTRICAS GLOBALES
# ============================================================

if not todas_carteras.empty:

    capital_inicial_wf = capital_inicial
    capital_final_wf = todas_carteras[
        "Capital"
    ].iloc[-1]

    retorno_total_wf = (
        capital_final_wf
        / capital_inicial_wf
        - 1
    )

    ganadoras = todas_carteras[
        todas_carteras["Retorno"] > 0
    ]

    perdedoras = todas_carteras[
        todas_carteras["Retorno"] < 0
    ]

    profit_factor_wf = (
        ganadoras["Retorno"].sum()
        / abs(perdedoras["Retorno"].sum())
    )

    capital_cummax = (
        todas_carteras["Capital"].cummax()
    )

    drawdown_wf = (
        todas_carteras["Capital"]
        / capital_cummax
        - 1
    )

    print("\n")
    print("================================")
    print("RESULTADO GLOBAL WALK-FORWARD")
    print("================================")

    print(
        f"Capital inicial:       ${capital_inicial_wf:,.2f}"
    )

    print(
        f"Capital final:         ${capital_final_wf:,.2f}"
    )

    print(
        f"Retorno total:         {retorno_total_wf:.2%}"
    )

    print(
        f"Máximo Drawdown:       {drawdown_wf.min():.2%}"
    )

    print(
        f"Profit Factor:         {profit_factor_wf:.3f}"
    )

    print(
        f"Carteras:              {len(todas_carteras):,}"
    )

    print(
        f"Ganadoras:             {len(ganadoras):,}"
    )

    print(
        f"Perdedoras:            {len(perdedoras):,}"
    )

    print(
        f"% Carteras ganadoras:  "
        f"{len(ganadoras) / len(todas_carteras):.2%}"
    )

# ============================================================
# NOTEBOOK CELL 20
# ============================================================
# ============================================================
# WALK-FORWARD OOS — MOMENTUM SIC + COSTOS GBM
# ============================================================

import numpy as np
import pandas as pd

capital_inicial = 10_000
horizonte = 10
comision_gbm = 0.0025
num_acciones_lista = [5, 10, 20, 30]

# ------------------------------------------------------------
# UNIVERSO OPERABLE
# ------------------------------------------------------------

tickers_operables = (
    sic_ibkr["Ticker_Yahoo"]
    .drop_duplicates()
    .tolist()
)

bt = df_sic[
    df_sic["Ticker"].isin(tickers_operables)
].copy()

bt = bt.sort_values(
    ["Date", "Ticker"]
)

fechas = sorted(
    bt["Date"].dropna().unique()
)

# ------------------------------------------------------------
# CREAR TRIMESTRES
# ------------------------------------------------------------

fechas_df = pd.DataFrame({
    "Date": pd.to_datetime(fechas)
})

fechas_df["Periodo"] = (
    fechas_df["Date"].dt.to_period("Q")
)

periodos = sorted(
    fechas_df["Periodo"].unique()
)

# ============================================================
# RESULTADOS
# ============================================================

resultados_wf = {}

carteras_globales = {}

for num_acciones in num_acciones_lista:

    capital = capital_inicial

    resultados_periodos = []
    todas_carteras = []

    # --------------------------------------------------------
    # RECORRER TRIMESTRES
    # --------------------------------------------------------

    for periodo in periodos:

        fechas_periodo = (
            fechas_df.loc[
                fechas_df["Periodo"] == periodo,
                "Date"
            ]
            .tolist()
        )

        if len(fechas_periodo) <= horizonte:
            continue

        carteras_periodo = []

        i = 0

        # ----------------------------------------------------
        # OPERACIONES DENTRO DEL TRIMESTRE
        # ----------------------------------------------------

        while i < len(fechas_periodo) - horizonte:

            fecha_señal = fechas_periodo[i]

            dia = bt[
                bt["Date"] == fecha_señal
            ].dropna(
                subset=["Momentum"]
            ).copy()

            if len(dia) < num_acciones:
                i += 1
                continue

            # ------------------------------------------------
            # RANKING DE MOMENTUM
            # ------------------------------------------------

            seleccion = (
                dia
                .sort_values(
                    "Momentum",
                    ascending=False
                )
                .head(num_acciones)
            )

            fecha_entrada = fechas_periodo[i + 1]

            fecha_salida = fechas_periodo[
                i + horizonte
            ]

            # ------------------------------------------------
            # PRECIOS DE ENTRADA
            # ------------------------------------------------

            entrada = bt[
                (bt["Date"] == fecha_entrada) &
                (bt["Ticker"].isin(
                    seleccion["Ticker"]
                ))
            ][
                ["Ticker", "Open"]
            ]

            # ------------------------------------------------
            # PRECIOS DE SALIDA
            # ------------------------------------------------

            salida = bt[
                (bt["Date"] == fecha_salida) &
                (bt["Ticker"].isin(
                    seleccion["Ticker"]
                ))
            ][
                ["Ticker", "Close"]
            ]

            cartera = entrada.merge(
                salida,
                on="Ticker",
                how="inner"
            )

            if len(cartera) < num_acciones:
                i += horizonte
                continue

            # ------------------------------------------------
            # RETORNO BRUTO
            # ------------------------------------------------

            cartera["Retorno_Bruto"] = (
                cartera["Close"]
                / cartera["Open"]
                - 1
            )

            # ------------------------------------------------
            # COSTOS GBM
            # 0.25% COMPRA
            # 0.25% VENTA
            # ------------------------------------------------

            cartera["Retorno_Neto"] = (
                (1 + cartera["Retorno_Bruto"])
                * (1 - comision_gbm)
                * (1 - comision_gbm)
                - 1
            )

            retorno_cartera = (
                cartera["Retorno_Neto"].mean()
            )

            # ------------------------------------------------
            # CAPITAL
            # ------------------------------------------------

            capital *= (
                1 + retorno_cartera
            )

            registro = {
                "Periodo": str(periodo),
                "Fecha_Señal": fecha_señal,
                "Fecha_Entrada": fecha_entrada,
                "Fecha_Salida": fecha_salida,
                "Acciones": len(cartera),
                "Retorno": retorno_cartera,
                "Capital": capital
            }

            carteras_periodo.append(
                registro
            )

            todas_carteras.append(
                registro
            )

            # No permitir solapamiento
            i += horizonte

        # ----------------------------------------------------
        # MÉTRICAS DEL TRIMESTRE
        # ----------------------------------------------------

        if not carteras_periodo:
            continue

        periodo_df = pd.DataFrame(
            carteras_periodo
        )

        capital_inicio = (
            periodo_df["Capital"].iloc[0]
            / (
                1
                + periodo_df["Retorno"].iloc[0]
            )
        )

        capital_fin = (
            periodo_df["Capital"].iloc[-1]
        )

        retorno_periodo = (
            capital_fin
            / capital_inicio
            - 1
        )

        ganadoras = periodo_df[
            periodo_df["Retorno"] > 0
        ]

        perdedoras = periodo_df[
            periodo_df["Retorno"] < 0
        ]

        if len(perdedoras) > 0:

            profit_factor = (
                ganadoras["Retorno"].sum()
                / abs(
                    perdedoras["Retorno"].sum()
                )
            )

        else:
            profit_factor = np.nan

        # Drawdown del período
        capital_cummax = (
            periodo_df["Capital"].cummax()
        )

        drawdown = (
            periodo_df["Capital"]
            / capital_cummax
            - 1
        )

        resultados_periodos.append({
            "Periodo": str(periodo),
            "Carteras": len(periodo_df),
            "Operaciones": int(
                periodo_df["Acciones"].sum()
            ),
            "Retorno": retorno_periodo,
            "Profit_Factor": profit_factor,
            "Max_Drawdown": drawdown.min(),
            "Acciones_Medias":
                periodo_df["Acciones"].mean()
        })

    # --------------------------------------------------------
    # GUARDAR RESULTADOS
    # --------------------------------------------------------

    resultados_wf[num_acciones] = (
        pd.DataFrame(resultados_periodos)
    )

    carteras_globales[num_acciones] = (
        pd.DataFrame(todas_carteras)
    )


# ============================================================
# MOSTRAR RESULTADOS POR TRIMESTRE
# ============================================================

for num_acciones in num_acciones_lista:

    print("\n")
    print("=" * 75)
    print(
        f"WALK-FORWARD — {num_acciones} POSICIONES"
    )
    print("=" * 75)

    tabla = resultados_wf[num_acciones]

    if tabla.empty:
        print("Sin resultados.")
        continue

    print(
        tabla.to_string(
            index=False,
            formatters={
                "Retorno":
                    lambda x: f"{x:.2%}",
                "Profit_Factor":
                    lambda x: (
                        f"{x:.3f}"
                        if pd.notna(x)
                        else "N/A"
                    ),
                "Max_Drawdown":
                    lambda x: f"{x:.2%}",
                "Acciones_Medias":
                    lambda x: f"{x:.1f}"
            }
        )
    )


# ============================================================
# MÉTRICAS GLOBALES
# ============================================================

print("\n")
print("=" * 75)
print("RESUMEN GLOBAL — WALK-FORWARD + GBM")
print("=" * 75)

resumen = []

for num_acciones in num_acciones_lista:

    cartera = carteras_globales[
        num_acciones
    ]

    if cartera.empty:
        continue

    capital_final = (
        cartera["Capital"].iloc[-1]
    )

    retorno_total = (
        capital_final
        / capital_inicial
        - 1
    )

    # --------------------------------------------------------
    # CAGR
    # --------------------------------------------------------

    fecha_inicio = pd.Timestamp(
        cartera["Fecha_Entrada"].iloc[0]
    )

    fecha_fin = pd.Timestamp(
        cartera["Fecha_Salida"].iloc[-1]
    )

    años = (
        fecha_fin - fecha_inicio
    ).days / 365.25

    cagr = (
        capital_final
        / capital_inicial
    ) ** (1 / años) - 1

    # --------------------------------------------------------
    # VOLATILIDAD
    # --------------------------------------------------------

    volatilidad = (
        cartera["Retorno"].std()
        * np.sqrt(252 / horizonte)
    )

    sharpe = (
        cagr / volatilidad
        if volatilidad > 0
        else np.nan
    )

    # --------------------------------------------------------
    # DRAWDOWN GLOBAL
    # --------------------------------------------------------

    max_capital = (
        cartera["Capital"].cummax()
    )

    drawdown = (
        cartera["Capital"]
        / max_capital
        - 1
    )

    max_drawdown = drawdown.min()

    # --------------------------------------------------------
    # PROFIT FACTOR
    # --------------------------------------------------------

    ganadoras = cartera[
        cartera["Retorno"] > 0
    ]

    perdedoras = cartera[
        cartera["Retorno"] < 0
    ]

    profit_factor = (
        ganadoras["Retorno"].sum()
        / abs(
            perdedoras["Retorno"].sum()
        )
        if len(perdedoras) > 0
        else np.nan
    )

    # --------------------------------------------------------
    # PORCENTAJE DE CARTERAS GANADORAS
    # --------------------------------------------------------

    porcentaje_ganadoras = (
        len(ganadoras)
        / len(cartera)
    )

    resumen.append({
        "Posiciones": num_acciones,
        "Capital_Final": capital_final,
        "Retorno_Total": retorno_total,
        "CAGR": cagr,
        "Volatilidad": volatilidad,
        "Sharpe": sharpe,
        "Max_Drawdown": max_drawdown,
        "Profit_Factor": profit_factor,
        "Carteras": len(cartera),
        "Ganadoras": len(ganadoras),
        "Perdedoras": len(perdedoras),
        "%_Ganadoras":
            porcentaje_ganadoras
    })


resumen = pd.DataFrame(resumen)

print(
    resumen.to_string(
        index=False,
        formatters={
            "Capital_Final":
                lambda x: f"${x:,.2f}",
            "Retorno_Total":
                lambda x: f"{x:.2%}",
            "CAGR":
                lambda x: f"{x:.2%}",
            "Volatilidad":
                lambda x: f"{x:.2%}",
            "Sharpe":
                lambda x: f"{x:.3f}",
            "Max_Drawdown":
                lambda x: f"{x:.2%}",
            "Profit_Factor":
                lambda x: f"{x:.3f}",
            "%_Ganadoras":
                lambda x: f"{x:.2%}"
        }
    )
)
