#!/usr/bin/env python3
"""
BTCUSDT Trading Strategy - Sin Optimizacion
=============================================

Multi-indicator confluence strategy using standard textbook parameters.
No curve-fitting or parameter optimization applied.

Indicators used:
- EMA 9/21 crossover (entry trigger)
- SMA 200 (trend filter)
- RSI 14 (momentum filter)
- MACD 12/26/9 (momentum confirmation)
- ADX 14 (trend strength filter)
- Bollinger Bands 20/2 (volatility context)
- ATR 14 (risk management: stop-loss & take-profit)
- Stochastic 14/3 (additional context)
- OBV (volume confirmation)

Risk Management:
- 2% risk per trade
- Stop-loss: 2x ATR
- Take-profit: 3x ATR (1.5:1 reward/risk)
"""

import sys
import os

import pandas as pd

from btcusdt_strategy.data import download_btcusdt_data
from btcusdt_strategy.indicators import compute_all_indicators
from btcusdt_strategy.strategy import generate_signals, backtest
from btcusdt_strategy.visualization import (
    plot_full_report,
    plot_trade_distribution,
    format_metrics_text,
)


def main() -> None:
    print("=" * 60)
    print("  BTCUSDT TRADING STRATEGY - SIN OPTIMIZACION")
    print("=" * 60)
    print()

    # Step 1: Download data
    print("[1/5] Descargando datos historicos de BTCUSDT...")
    try:
        df = download_btcusdt_data(period="2y", interval="1d")
        print(f"      Datos descargados: {len(df)} velas diarias")
        print(f"      Desde: {df.index[0].strftime('%Y-%m-%d')}")
        print(f"      Hasta: {df.index[-1].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"      Error descargando datos: {e}")
        sys.exit(1)

    # Step 2: Compute indicators
    print("\n[2/5] Calculando indicadores tecnicos (parametros estandar)...")
    df_indicators = compute_all_indicators(df)
    print("      Indicadores calculados:")
    print("        - EMA 9, EMA 21, SMA 50, SMA 200")
    print("        - RSI 14")
    print("        - MACD (12, 26, 9)")
    print("        - Bollinger Bands (20, 2.0)")
    print("        - ATR 14, ADX 14")
    print("        - Stochastic (14, 3)")
    print("        - OBV + OBV EMA 21")

    # Step 3: Generate signals
    print("\n[3/5] Generando senales de trading...")
    df_signals = generate_signals(df_indicators)
    long_signals = (df_signals["Signal"] == 1).sum()
    short_signals = (df_signals["Signal"] == -1).sum()
    neutral = (df_signals["Signal"] == 0).sum()
    print(f"      Senales LONG:    {long_signals}")
    print(f"      Senales SHORT:   {short_signals}")
    print(f"      Sin senal:       {neutral}")

    # Step 4: Run backtest
    print("\n[4/5] Ejecutando backtest...")
    results = backtest(df_signals, initial_capital=10000.0)
    trades = results["trades"]
    equity_df = results["equity_curve"]
    metrics = results["metrics"]

    # Print metrics
    print("\n" + format_metrics_text(metrics))

    # Step 5: Generate visualizations
    print("\n[5/5] Generando visualizaciones...")
    report_path = plot_full_report(
        results["data"], equity_df, trades, metrics,
    )
    print(f"      Reporte principal: {report_path}")

    dist_path = plot_trade_distribution(trades)
    if dist_path:
        print(f"      Distribucion de trades: {dist_path}")

    # Save trades to CSV
    if trades:
        trades_df = pd.DataFrame(trades)
        csv_path = os.path.join("output", "btcusdt_trades.csv")
        trades_df.to_csv(csv_path, index=False)
        print(f"      Trades CSV: {csv_path}")

    # Save metrics to CSV
    metrics_df = pd.DataFrame([metrics])
    metrics_csv = os.path.join("output", "btcusdt_metrics.csv")
    metrics_df.to_csv(metrics_csv, index=False)
    print(f"      Metricas CSV: {metrics_csv}")

    print("\n" + "=" * 60)
    print("  ESTRATEGIA COMPLETADA EXITOSAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    main()
