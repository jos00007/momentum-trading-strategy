# Generated from the research notebook: SIC copy.ipynb
# Project: Momentum Trading Strategy
# NOTE: This file preserves the research logic from the notebook.
# It is intended for the repository and may require local data/configuration.


# ============================================================
# NOTEBOOK CELL 9
# ============================================================
# ============================================================
# SIGNIFICANCIA ESTADÍSTICA — MOMENTUM SIC
# ============================================================

from scipy.stats import ttest_1samp

resultados_test_sic = []

for h in [1, 3, 5, 10, 20]:

    columna = f"Futuro_{h}D"

    diario = (
        df_sic
        .dropna(subset=["Grupo_Momentum", columna])
        .groupby(
            ["Date", "Grupo_Momentum"]
        )[columna]
        .mean()
        .unstack()
    )

    comparacion = diario[
        [1.0, 3.0]
    ].dropna()

    # Momentum: mejor momentum - peor momentum
    diferencia = (
        comparacion[3.0]
        - comparacion[1.0]
    )

    t_stat, p_value = ttest_1samp(
        diferencia,
        0
    )

    resultados_test_sic.append({
        "Horizonte": f"{h}D",
        "Spread_G3_G1": diferencia.mean(),
        "Desv_Estandar": diferencia.std(),
        "Observaciones": len(diferencia),
        "t_stat": t_stat,
        "p_value": p_value
    })

resultado_test_sic = pd.DataFrame(
    resultados_test_sic
)

print("================================")
print("SIGNIFICANCIA — MOMENTUM SIC")
print("================================")

print(
    resultado_test_sic.to_string(
        index=False
    )
)

print("\nInterpretación:")
print("p < 0.05  -> evidencia estadística")
print("p >= 0.05 -> evidencia insuficiente")
