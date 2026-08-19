# momentum-trading-strategy
Estrategia para trading a partir del momentum
# Momentum Trading Strategy

Systematic equity trading strategy based on cross-sectional price momentum.

## Overview

This project develops and evaluates a systematic momentum strategy for U.S. equities.

The strategy ranks stocks according to their 20-session price momentum and selects the top-ranked stocks for a 10-session holding period.

The research process includes historical backtesting, statistical testing, out-of-sample validation, walk-forward analysis, transaction-cost analysis, and paper trading.

## Strategy

- Signal: 20-session price momentum
- Selection: Top 10 stocks by momentum
- Holding period: 10 trading sessions
- Portfolio construction: Equal-weighted positions
- Rebalancing: Daily, creating overlapping portfolios
- Benchmark: QQQ
- Transaction costs: GBM Trading USA commission assumptions
- Current status: Paper trading in progress

## Research Process

The strategy was evaluated through several stages:

1. Construction of the investment universe from the Mexican SIC.
2. Validation of securities and liquidity filtering.
3. Historical data collection using Yahoo Finance.
4. Momentum calculation and statistical significance testing.
5. Historical backtesting.
6. In-sample / out-of-sample validation.
7. Walk-forward analysis.
8. Transaction-cost analysis.
9. Paper trading with real market prices and execution times.

## Repository Structure

momentum-trading-strategy/
│
├── data/
│   ├── infoDownload.csv
│   ├── universo.csv
│   └── datos_sic.csv
│
├── src/
│   ├── signal.py
│   ├── backtest.py
│   ├── walk_forward.py
│   └── paper_trading.py
│
├── analysis/
│   ├── statistical_tests.py
│   └── performance.py
│
├── results/
│   ├── backtest/
│   ├── walk_forward/
│   └── paper_trading/
│
└── notebooks/
    └── SIC_research.ipynb

Validation
The strategy is not evaluated solely on historical backtest performance.

The validation framework includes:
Statistical significance of momentum returns.
In-sample / holdout testing.
Walk-forward out-of-sample testing.
Transaction-cost assumptions.
Comparison against QQQ.
Paper trading.
Paper Trading

Paper trading began in August 2026.
The live experiment generates a new Top 10 portfolio after each market close. Portfolios are held for 10 trading sessions, resulting in overlapping portfolios.
The objective is to compare actual paper-trading execution with the standardized historical model and evaluate the effect of execution timing and transaction costs.

Disclaimer
This project is an independent research and educational project.
The results shown in this repository are not investment advice and past performance does not guarantee future results.
Paper-trading results should not be interpreted as live trading performance.
