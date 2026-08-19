# Generated from the research notebook: SIC copy.ipynb
# Project: Momentum Trading Strategy
# NOTE: This file preserves the research logic from the notebook.
# It is intended for the repository and may require local data/configuration.


# ============================================================
# NOTEBOOK CELL 10
# ============================================================
# ============================================================
# BACKTEST MOMENTUM — SIC
# ============================================================

# Parámetros
horizontes = [5, 10, 20]
capital_inicial = 100_000

# Trabajamos sobre copia ordenada
bt = df_sic.sort_values(
    ["Date", "Ticker"]
).copy()

# Momentum de 20 días ya calculado
# La señal se genera al cierre de cada día.
# La entrada será en el OPEN del día siguiente.

resultados_backtest = {}

for horizonte in horizontes:

    operaciones = []

    fechas = sorted(
        bt["Date"].dropna().unique()
    )

    for fecha in fechas:

        dia = bt[
            bt["Date"] == fecha
        ].copy()

        # ----------------------------------------------------
        # SEÑAL
        # ----------------------------------------------------

        dia = dia.dropna(
            subset=["Momentum"]
        )

        if len(dia) < 3:
            continue

        # Tercil superior = mejor momentum
        dia["Grupo"] = pd.qcut(
            dia["Momentum"].rank(method="first"),
            3,
            labels=False
        ) + 1

        seleccion = dia[
            dia["Grupo"] == 3
        ].copy()

        if seleccion.empty:
            continue

        # ----------------------------------------------------
        # FECHA DE ENTRADA
        # ----------------------------------------------------

        fechas_futuras = fechas[
            fechas.index(fecha) + 1:
            ]

        if len(fechas_futuras) < horizonte:
            continue

        fecha_entrada = fechas_futuras[0]
        fecha_salida = fechas_futuras[horizonte - 1]

        entrada = bt[
            (bt["Date"] == fecha_entrada) &
            (bt["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ].copy()

        salida = bt[
            (bt["Date"] == fecha_salida) &
            (bt["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Close"]
        ].copy()

        operaciones_dia = entrada.merge(
            salida,
            on="Ticker",
            how="inner"
        )

        if operaciones_dia.empty:
            continue

        # ----------------------------------------------------
        # RETORNO DE CADA ACCIÓN
        # ----------------------------------------------------

        operaciones_dia["Retorno"] = (
            operaciones_dia["Close"]
            / operaciones_dia["Open"]
            - 1
        )

        operaciones_dia["Fecha_Entrada"] = fecha_entrada
        operaciones_dia["Fecha_Salida"] = fecha_salida

        operaciones.extend(
            operaciones_dia.to_dict("records")
        )

    operaciones = pd.DataFrame(operaciones)

    # --------------------------------------------------------
    # RETORNO DE CADA CARTERA
    # --------------------------------------------------------

    cartera = (
        operaciones
        .groupby("Fecha_Entrada")["Retorno"]
        .mean()
        .sort_index()
    )

    # Capital compuesto
    capital = capital_inicial * (
        1 + cartera
    ).cumprod()

    # Drawdown
    maximo = capital.cummax()

    drawdown = (
        capital / maximo - 1
    )

    # Ganadoras/perdedoras
    ganadoras = operaciones[
        operaciones["Retorno"] > 0
    ]

    perdedoras = operaciones[
        operaciones["Retorno"] < 0
    ]

    ganancia_promedio = (
        ganadoras["Retorno"].mean()
        if len(ganadoras) > 0
        else 0
    )

    perdida_promedio = (
        perdedoras["Retorno"].mean()
        if len(perdedoras) > 0
        else 0
    )

    profit_factor = (
        ganadoras["Retorno"].sum()
        / abs(perdedoras["Retorno"].sum())
        if len(perdedoras) > 0
        else np.nan
    )

    retorno_total = (
        capital.iloc[-1]
        / capital_inicial
        - 1
        if len(capital) > 0
        else np.nan
    )

    resultados_backtest[horizonte] = {
        "Operaciones": len(operaciones),
        "Carteras": len(cartera),
        "Capital_Final": (
            capital.iloc[-1]
            if len(capital) > 0
            else capital_inicial
        ),
        "Retorno_Total": retorno_total,
        "Max_Drawdown": (
            drawdown.min()
            if len(drawdown) > 0
            else np.nan
        ),
        "Profit_Factor": profit_factor,
        "Ganadoras": len(ganadoras),
        "Perdedoras": len(perdedoras),
        "Ganancia_Promedio": ganancia_promedio,
        "Perdida_Promedio": perdida_promedio
    }


# ============================================================
# RESULTADOS
# ============================================================

for horizonte, r in resultados_backtest.items():

    print("\n" + "=" * 60)
    print(f"HORIZONTE: {horizonte} DÍAS")
    print("=" * 60)

    print(
        f"Capital inicial:   ${capital_inicial:,.2f}"
    )

    print(
        f"Capital final:      ${r['Capital_Final']:,.2f}"
    )

    print(
        f"Retorno total:      {r['Retorno_Total']:.2%}"
    )

    print(
        f"Máximo Drawdown:    {r['Max_Drawdown']:.2%}"
    )

    print(
        f"Profit Factor:      {r['Profit_Factor']:.3f}"
    )

    print(
        f"Carteras:           {r['Carteras']:,}"
    )

    print(
        f"Operaciones:        {r['Operaciones']:,}"
    )

    print(
        f"Ganadoras:          {r['Ganadoras']:,}"
    )

    print(
        f"Perdedoras:         {r['Perdedoras']:,}"
    )

    print(
        f"Ganancia promedio:  {r['Ganancia_Promedio']:.4%}"
    )

    print(
        f"Pérdida promedio:   {r['Perdida_Promedio']:.4%}"
    )

# ============================================================
# NOTEBOOK CELL 11
# ============================================================
# ============================================================
# BACKTEST MOMENTUM SIC — CAPITAL FIJO, SIN SOLAPAMIENTO
# ============================================================

capital_inicial = 100_000
horizontes = [5, 10, 20]

bt = df_sic.sort_values(
    ["Date", "Ticker"]
).copy()

fechas = sorted(
    bt["Date"].dropna().unique()
)

resultados_backtest = {}

for horizonte in horizontes:

    operaciones = []
    carteras = []

    # Avanzamos en bloques del horizonte.
    # Esto evita tener varias carteras abiertas simultáneamente.
    posiciones_fecha = 0

    while posiciones_fecha < len(fechas) - horizonte:

        fecha_señal = fechas[posiciones_fecha]

        dia = bt[
            bt["Date"] == fecha_señal
        ].copy()

        dia = dia.dropna(
            subset=["Momentum"]
        )

        if len(dia) < 3:
            posiciones_fecha += 1
            continue

        # ----------------------------------------------------
        # SELECCIONAR TERCIL SUPERIOR DE MOMENTUM
        # ----------------------------------------------------

        dia["Grupo_Momentum"] = pd.qcut(
            dia["Momentum"].rank(method="first"),
            3,
            labels=False
        ) + 1

        seleccion = dia[
            dia["Grupo_Momentum"] == 3
        ][["Ticker"]].copy()

        if seleccion.empty:
            posiciones_fecha += 1
            continue

        # ----------------------------------------------------
        # ENTRADA: SIGUIENTE SESIÓN
        # ----------------------------------------------------

        fecha_entrada = fechas[
            posiciones_fecha + 1
        ]

        fecha_salida = fechas[
            posiciones_fecha + horizonte
        ]

        entrada = bt[
            (bt["Date"] == fecha_entrada) &
            (bt["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ].copy()

        salida = bt[
            (bt["Date"] == fecha_salida) &
            (bt["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Close"]
        ].copy()

        cartera = entrada.merge(
            salida,
            on="Ticker",
            how="inner"
        )

        if cartera.empty:
            posiciones_fecha += horizonte
            continue

        # ----------------------------------------------------
        # RETORNO DE CADA POSICIÓN
        # ----------------------------------------------------

        cartera["Retorno"] = (
            cartera["Close"]
            / cartera["Open"]
            - 1
        )

        cartera["Fecha_Señal"] = fecha_señal
        cartera["Fecha_Entrada"] = fecha_entrada
        cartera["Fecha_Salida"] = fecha_salida

        # Cartera igualmente ponderada
        retorno_cartera = cartera["Retorno"].mean()

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

        # Pasamos al siguiente bloque
        posiciones_fecha += horizonte

    # --------------------------------------------------------
    # RESULTADOS DE CARTERAS
    # --------------------------------------------------------

    operaciones = pd.DataFrame(operaciones)
    carteras = pd.DataFrame(carteras)

    if carteras.empty:
        continue

    carteras = carteras.sort_values(
        "Fecha_Entrada"
    )

    # Capital compuesto
    carteras["Capital"] = (
        capital_inicial
        * (1 + carteras["Retorno"]).cumprod()
    )

    # Drawdown
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
    )

    resultados_backtest[horizonte] = {
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


# ============================================================
# RESULTADOS
# ============================================================

for horizonte, r in resultados_backtest.items():

    print("\n" + "=" * 60)
    print(f"HORIZONTE: {horizonte} DÍAS")
    print("=" * 60)

    print(
        f"Capital inicial:       ${capital_inicial:,.2f}"
    )

    print(
        f"Capital final:         ${r['Capital_Final']:,.2f}"
    )

    print(
        f"Retorno total:         {r['Retorno_Total']:.2%}"
    )

    print(
        f"Máximo Drawdown:       {r['Max_Drawdown']:.2%}"
    )

    print(
        f"Profit Factor:         {r['Profit_Factor']:.3f}"
    )

    print(
        f"Carteras:              {r['Carteras']:,}"
    )

    print(
        f"Operaciones:           {r['Operaciones']:,}"
    )

    print(
        f"Acciones por cartera:  {r['Acciones_Promedio']:.2f}"
    )

    print(
        f"Ganadoras:             {r['Ganadoras']:,}"
    )

    print(
        f"Perdedoras:            {r['Perdedoras']:,}"
    )

    print(
        f"Ganancia promedio:     {r['Ganancia_Promedio']:.4%}"
    )

    print(
        f"Pérdida promedio:      {r['Perdida_Promedio']:.4%}"
    )

# ============================================================
# NOTEBOOK CELL 15
# ============================================================
# ============================================================
# UNIVERSO OPERABLE CON $10,000 MXN
# ============================================================

# Mercados donde IBKR permite operar acciones fraccionarias
# según su documentación actual.
bolsas_fracciones_ibkr = [
    "NEW YORK STOCK EXCHANGE",
    "NASDAQ",
]

sic_ibkr = sic_filtrado[
    sic_filtrado["BOLSA DONDE COTIZA"].isin(
        bolsas_fracciones_ibkr
    )
].copy()

print("================================")
print("UNIVERSO IBKR — FRACCIONES")
print("================================")

print(
    "Acciones:",
    sic_ibkr["Ticker_Yahoo"].nunique()
)

print("\nDistribución por bolsa:")
print(
    sic_ibkr[
        "BOLSA DONDE COTIZA"
    ].value_counts()
)

# Mercados excluidos
sic_no_fracciones = sic_filtrado[
    ~sic_filtrado["BOLSA DONDE COTIZA"].isin(
        bolsas_fracciones_ibkr
    )
]

print("\n================================")
print("EXCLUIDAS")
print("================================")

print(
    "Acciones:",
    sic_no_fracciones[
        "Ticker_Yahoo"
    ].nunique()
)

print(
    sic_no_fracciones[
        "BOLSA DONDE COTIZA"
    ].value_counts()
)

# ============================================================
# NOTEBOOK CELL 16
# ============================================================
# ============================================================
# BACKTEST — CUENTA $10,000 MXN
# MOMENTUM 20D — HOLDING 10D
# 5 / 10 / 20 / 30 ACCIONES
# ============================================================

capital_inicial = 10_000
horizonte = 10
num_acciones_lista = [5, 10, 20, 30]

# ------------------------------------------------------------
# UNIVERSO OPERABLE
# ------------------------------------------------------------

tickers_ibkr = (
    sic_ibkr["Ticker_Yahoo"]
    .drop_duplicates()
    .tolist()
)

bt = df_sic[
    df_sic["Ticker"].isin(tickers_ibkr)
].sort_values(
    ["Date", "Ticker"]
).copy()

fechas = sorted(
    bt["Date"].dropna().unique()
)

resultados_concentracion = {}

# ------------------------------------------------------------
# BACKTEST
# ------------------------------------------------------------

for num_acciones in num_acciones_lista:

    carteras = []
    operaciones = []

    i = 0

    while i < len(fechas) - horizonte:

        fecha_señal = fechas[i]

        dia = bt[
            bt["Date"] == fecha_señal
        ].dropna(
            subset=["Momentum"]
        ).copy()

        if len(dia) < num_acciones:
            i += 1
            continue

        # ----------------------------------------------------
        # RANKING DE MOMENTUM
        # ----------------------------------------------------

        seleccion = (
            dia
            .sort_values(
                "Momentum",
                ascending=False
            )
            .head(num_acciones)
        )

        # ----------------------------------------------------
        # ENTRADA / SALIDA
        # ----------------------------------------------------

        fecha_entrada = fechas[i + 1]
        fecha_salida = fechas[i + horizonte]

        entrada = bt[
            (bt["Date"] == fecha_entrada) &
            (bt["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ]

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

        # ----------------------------------------------------
        # RETORNO POR ACCIÓN
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
        continue

    # --------------------------------------------------------
    # CAPITAL
    # --------------------------------------------------------

    carteras = carteras.sort_values(
        "Fecha_Entrada"
    )

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

    resultados_concentracion[num_acciones] = {
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

# ------------------------------------------------------------
# RESULTADOS
# ------------------------------------------------------------

print("================================")
print("MOMENTUM SIC — CUENTA $10,000")
print("================================")

for n, r in resultados_concentracion.items():

    print("\n" + "=" * 55)
    print(f"ACCIONES EN CARTERA: {n}")
    print("=" * 55)

    print(
        f"Capital final:       ${r['Capital_Final']:,.2f}"
    )

    print(
        f"Retorno total:       {r['Retorno_Total']:.2%}"
    )

    print(
        f"Máximo Drawdown:     {r['Max_Drawdown']:.2%}"
    )

    print(
        f"Profit Factor:       {r['Profit_Factor']:.3f}"
    )

    print(
        f"Carteras:            {r['Carteras']}"
    )

    print(
        f"Operaciones:         {r['Operaciones']}"
    )

    print(
        f"Ganancia promedio:   {r['Ganancia_Promedio']:.4%}"
    )

    print(
        f"Pérdida promedio:    {r['Perdida_Promedio']:.4%}"
    )

# ============================================================
# NOTEBOOK CELL 17
# ============================================================
# ============================================================
# BACKTEST CON COSTOS — GBM
# ============================================================

capital_inicial = 10_000
horizonte = 10
num_acciones_lista = [5, 10, 20, 30]

comision_gbm = 0.0025   # 0.25% por lado

resultados_gbm = {}

for num_acciones in num_acciones_lista:

    capital = capital_inicial
    carteras = []

    i = 0

    while i < len(fechas) - horizonte:

        fecha_señal = fechas[i]

        dia = bt[
            bt["Date"] == fecha_señal
        ].dropna(
            subset=["Momentum"]
        ).copy()

        if len(dia) < num_acciones:
            i += 1
            continue

        seleccion = (
            dia
            .sort_values(
                "Momentum",
                ascending=False
            )
            .head(num_acciones)
        )

        fecha_entrada = fechas[i + 1]
        fecha_salida = fechas[i + horizonte]

        entrada = bt[
            (bt["Date"] == fecha_entrada) &
            (bt["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ]

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

        cartera["Retorno_Bruto"] = (
            cartera["Close"]
            / cartera["Open"]
            - 1
        )

        # ----------------------------------------------------
        # COSTO DE COMPRA + VENTA
        # ----------------------------------------------------

        cartera["Retorno_Neto"] = (
            (1 + cartera["Retorno_Bruto"])
            * (1 - comision_gbm)
            * (1 - comision_gbm)
            - 1
        )

        retorno_cartera = (
            cartera["Retorno_Neto"].mean()
        )

        capital *= (
            1 + retorno_cartera
        )

        carteras.append({
            "Fecha": fecha_entrada,
            "Retorno": retorno_cartera,
            "Capital": capital
        })

        i += horizonte

    carteras = pd.DataFrame(carteras)

    carteras["Max_Capital"] = (
        carteras["Capital"].cummax()
    )

    carteras["Drawdown"] = (
        carteras["Capital"]
        / carteras["Max_Capital"]
        - 1
    )

    resultados_gbm[num_acciones] = {
        "Capital_Final":
            capital,

        "Retorno_Total":
            capital / capital_inicial - 1,

        "Max_Drawdown":
            carteras["Drawdown"].min(),

        "Carteras":
            len(carteras)
    }


# ============================================================
# RESULTADOS
# ============================================================

print("================================")
print("MOMENTUM SIC — COSTOS GBM")
print("================================")

for n, r in resultados_gbm.items():

    print("\n" + "=" * 50)
    print(f"ACCIONES: {n}")
    print("=" * 50)

    print(
        f"Capital final:    ${r['Capital_Final']:,.2f}"
    )

    print(
        f"Retorno total:    {r['Retorno_Total']:.2%}"
    )

    print(
        f"Máximo Drawdown:  {r['Max_Drawdown']:.2%}"
    )

# ============================================================
# NOTEBOOK CELL 18
# ============================================================
# ============================================================
# BACKTEST — IBKR
# CUENTA $10,000 MXN
# MOMENTUM 20D — HOLDING 10D
# ============================================================

capital_inicial = 10_000
horizonte = 10
num_acciones_lista = [5, 10, 20, 30]

# USD/MXN de referencia
usd_mxn = 17.00

# Comisión para operaciones fraccionarias IBKR
comision_ibkr = 0.01

resultados_ibkr = {}

for num_acciones in num_acciones_lista:

    capital_mxn = capital_inicial
    carteras = []

    i = 0

    while i < len(fechas) - horizonte:

        fecha_señal = fechas[i]

        dia = bt[
            bt["Date"] == fecha_señal
        ].dropna(
            subset=["Momentum"]
        ).copy()

        if len(dia) < num_acciones:
            i += 1
            continue

        # ----------------------------------------------------
        # MEJORES ACCIONES POR MOMENTUM
        # ----------------------------------------------------

        seleccion = (
            dia
            .sort_values(
                "Momentum",
                ascending=False
            )
            .head(num_acciones)
        )

        fecha_entrada = fechas[i + 1]
        fecha_salida = fechas[i + horizonte]

        entrada = bt[
            (bt["Date"] == fecha_entrada) &
            (bt["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ]

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

        # ----------------------------------------------------
        # CAPITAL POR POSICIÓN
        # ----------------------------------------------------

        capital_por_accion_mxn = (
            capital_mxn / num_acciones
        )

        capital_por_accion_usd = (
            capital_por_accion_mxn / usd_mxn
        )

        # ----------------------------------------------------
        # RETORNO BRUTO
        # ----------------------------------------------------

        cartera["Retorno_Bruto"] = (
            cartera["Close"]
            / cartera["Open"]
            - 1
        )

        # ----------------------------------------------------
        # COSTOS IBKR
        #
        # Al utilizar fracciones:
        # 1% compra + 1% venta
        # ----------------------------------------------------

        cartera["Retorno_Neto"] = (
            (1 + cartera["Retorno_Bruto"])
            * (1 - comision_ibkr)
            * (1 - comision_ibkr)
            - 1
        )

        retorno_cartera = (
            cartera["Retorno_Neto"].mean()
        )

        capital_mxn *= (
            1 + retorno_cartera
        )

        carteras.append({
            "Fecha": fecha_entrada,
            "Retorno": retorno_cartera,
            "Capital": capital_mxn
        })

        # No solapar carteras
        i += horizonte

    carteras = pd.DataFrame(carteras)

    if carteras.empty:
        continue

    # --------------------------------------------------------
    # DRAWDOWN
    # --------------------------------------------------------

    carteras["Max_Capital"] = (
        carteras["Capital"].cummax()
    )

    carteras["Drawdown"] = (
        carteras["Capital"]
        / carteras["Max_Capital"]
        - 1
    )

    resultados_ibkr[num_acciones] = {
        "Capital_Final":
            carteras["Capital"].iloc[-1],

        "Retorno_Total":
            carteras["Capital"].iloc[-1]
            / capital_inicial - 1,

        "Max_Drawdown":
            carteras["Drawdown"].min(),

        "Carteras":
            len(carteras)
    }


# ============================================================
# RESULTADOS
# ============================================================

print("================================")
print("MOMENTUM SIC — COSTOS IBKR")
print("================================")

print(
    f"USD/MXN utilizado: {usd_mxn:.2f}"
)

print(
    f"Comisión por lado: {comision_ibkr:.2%}"
)

for n, r in resultados_ibkr.items():

    print("\n" + "=" * 50)
    print(f"ACCIONES: {n}")
    print("=" * 50)

    print(
        f"Capital final:    ${r['Capital_Final']:,.2f}"
    )

    print(
        f"Retorno total:    {r['Retorno_Total']:.2%}"
    )

    print(
        f"Máximo Drawdown:  {r['Max_Drawdown']:.2%}"
    )

# ============================================================
# NOTEBOOK CELL 19
# ============================================================
# ============================================================
# OOS — MOMENTUM SIC + GBM
# CAPITAL: $10,000 MXN
# HOLDING: 10 DÍAS
# POSICIONES: 5 / 10 / 20 / 30
# COSTO GBM: 0.25% POR LADO
# ============================================================

capital_inicial = 10_000
horizonte = 10
num_acciones_lista = [5, 10, 20, 30]
comision_gbm = 0.0025

# ------------------------------------------------------------
# UNIVERSO OPERABLE
# ------------------------------------------------------------

tickers_ibkr = (
    sic_ibkr["Ticker_Yahoo"]
    .drop_duplicates()
    .tolist()
)

bt = df_sic[
    df_sic["Ticker"].isin(tickers_ibkr)
].sort_values(
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

fechas_oos = [
    f for f in fechas
    if f >= fecha_corte
]

df_oos = bt[
    bt["Date"] >= fecha_corte
].copy()

print("================================")
print("DIVISIÓN IS / OOS")
print("================================")
print("Inicio:", fechas[0])
print("Fecha corte:", fecha_corte)
print("Fin:", fechas[-1])

# ============================================================
# BACKTEST OOS
# ============================================================

resultados_oos = {}

for num_acciones in num_acciones_lista:

    capital = capital_inicial

    carteras = []
    operaciones = []

    i = 0

    while i < len(fechas_oos) - horizonte:

        fecha_señal = fechas_oos[i]

        dia = df_oos[
            df_oos["Date"] == fecha_señal
        ].dropna(
            subset=["Momentum"]
        ).copy()

        if len(dia) < num_acciones:
            i += 1
            continue

        # ----------------------------------------------------
        # RANKING
        # ----------------------------------------------------

        seleccion = (
            dia
            .sort_values(
                "Momentum",
                ascending=False
            )
            .head(num_acciones)
        )

        # ----------------------------------------------------
        # ENTRADA / SALIDA
        # ----------------------------------------------------

        fecha_entrada = fechas_oos[i + 1]
        fecha_salida = fechas_oos[i + horizonte]

        entrada = df_oos[
            (df_oos["Date"] == fecha_entrada) &
            (df_oos["Ticker"].isin(
                seleccion["Ticker"]
            ))
        ][
            ["Ticker", "Open"]
        ]

        salida = df_oos[
            (df_oos["Date"] == fecha_salida) &
            (df_oos["Ticker"].isin(
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

        # ----------------------------------------------------
        # RETORNO BRUTO
        # ----------------------------------------------------

        cartera["Retorno_Bruto"] = (
            cartera["Close"]
            / cartera["Open"]
            - 1
        )

        # ----------------------------------------------------
        # COSTO GBM
        # ----------------------------------------------------
        # 0.25% compra + 0.25% venta
        # Aplicado a cada posición.

        cartera["Retorno_Neto"] = (
            (1 + cartera["Retorno_Bruto"])
            * (1 - comision_gbm)
            * (1 - comision_gbm)
            - 1
        )

        # ----------------------------------------------------
        # RETORNO DE LA CARTERA
        # ----------------------------------------------------

        retorno_cartera = (
            cartera["Retorno_Neto"].mean()
        )

        capital *= (
            1 + retorno_cartera
        )

        carteras.append({
            "Fecha_Señal": fecha_señal,
            "Fecha_Entrada": fecha_entrada,
            "Fecha_Salida": fecha_salida,
            "Acciones": len(cartera),
            "Retorno": retorno_cartera,
            "Capital": capital
        })

        operaciones.extend(
            cartera.to_dict("records")
        )

        # No solapar carteras
        i += horizonte

    carteras = pd.DataFrame(carteras)
    operaciones = pd.DataFrame(operaciones)

    if carteras.empty:
        continue

    # --------------------------------------------------------
    # DRAWDOWN
    # --------------------------------------------------------

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
        operaciones["Retorno_Neto"] > 0
    ]

    perdedoras = operaciones[
        operaciones["Retorno_Neto"] < 0
    ]

    profit_factor = (
        ganadoras["Retorno_Neto"].sum()
        / abs(
            perdedoras["Retorno_Neto"].sum()
        )
        if len(perdedoras) > 0
        else np.nan
    )

    # CAGR del OOS
    fecha_inicio = (
        carteras["Fecha_Entrada"].iloc[0]
    )

    fecha_fin = (
        carteras["Fecha_Salida"].iloc[-1]
    )

    años = (
        fecha_fin - fecha_inicio
    ).days / 365.25

    CAGR = (
        carteras["Capital"].iloc[-1]
        / capital_inicial
    ) ** (1 / años) - 1

    # Retornos de cartera
    retornos = carteras["Retorno"]

    volatilidad = (
        retornos.std()
        * np.sqrt(252 / horizonte)
    )

    sharpe = (
        CAGR / volatilidad
        if volatilidad > 0
        else np.nan
    )

    resultados_oos[num_acciones] = {
        "Capital_Final":
            carteras["Capital"].iloc[-1],

        "Retorno_Total":
            carteras["Capital"].iloc[-1]
            / capital_inicial - 1,

        "CAGR":
            CAGR,

        "Volatilidad":
            volatilidad,

        "Sharpe":
            sharpe,

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
            ganadoras["Retorno_Neto"].mean(),

        "Perdida_Promedio":
            perdedoras["Retorno_Neto"].mean()
    }


# ============================================================
# RESULTADOS
# ============================================================

print("\n")
print("=" * 60)
print("OOS — MOMENTUM SIC + COSTOS GBM")
print("=" * 60)

for n, r in resultados_oos.items():

    print("\n" + "=" * 55)
    print(f"POSICIONES: {n}")
    print("=" * 55)

    print(
        f"Capital inicial:      ${capital_inicial:,.2f}"
    )

    print(
        f"Capital final:        ${r['Capital_Final']:,.2f}"
    )

    print(
        f"Retorno total:        {r['Retorno_Total']:.2%}"
    )

    print(
        f"CAGR:                 {r['CAGR']:.2%}"
    )

    print(
        f"Volatilidad anual:    {r['Volatilidad']:.2%}"
    )

    print(
        f"Sharpe:               {r['Sharpe']:.3f}"
    )

    print(
        f"Máximo Drawdown:      {r['Max_Drawdown']:.2%}"
    )

    print(
        f"Profit Factor:        {r['Profit_Factor']:.3f}"
    )

    print(
        f"Carteras:             {r['Carteras']}"
    )

    print(
        f"Operaciones:          {r['Operaciones']}"
    )

    print(
        f"Acciones por cartera: {r['Acciones_Promedio']:.1f}"
    )

    print(
        f"Ganadoras:            {r['Ganadoras']}"
    )

    print(
        f"Perdedoras:           {r['Perdedoras']}"
    )

    print(
        f"Ganancia promedio:    {r['Ganancia_Promedio']:.4%}"
    )

    print(
        f"Pérdida promedio:     {r['Perdida_Promedio']:.4%}"
    )
