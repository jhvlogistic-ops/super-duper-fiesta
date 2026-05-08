"""
Visualization module for strategy results.
Generates charts for equity curve, indicators, and trade analysis.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import pandas as pd


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_full_report(
    data: pd.DataFrame,
    equity_df: pd.DataFrame,
    trades: list[dict],
    metrics: dict,
) -> str:
    """Generate a comprehensive multi-panel chart."""
    ensure_output_dir()

    fig = plt.figure(figsize=(20, 28))
    gs = gridspec.GridSpec(6, 2, hspace=0.35, wspace=0.3)

    # --- Panel 1: Price + EMAs + Bollinger + Trades ---
    ax1 = fig.add_subplot(gs[0:2, :])
    ax1.plot(data.index, data["Close"], label="BTC Close", color="black", linewidth=1)
    ax1.plot(data.index, data["EMA_9"], label="EMA 9", color="blue", linewidth=0.8, alpha=0.7)
    ax1.plot(data.index, data["EMA_21"], label="EMA 21", color="orange", linewidth=0.8, alpha=0.7)
    ax1.plot(data.index, data["SMA_50"], label="SMA 50", color="green", linewidth=0.8, alpha=0.5)
    ax1.plot(data.index, data["SMA_200"], label="SMA 200", color="red", linewidth=1, alpha=0.7)
    ax1.fill_between(
        data.index, data["BB_Upper"], data["BB_Lower"],
        alpha=0.1, color="grey", label="Bollinger Bands",
    )

    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    if not trades_df.empty:
        long_entries = trades_df[trades_df["Direction"] == "LONG"]
        short_entries = trades_df[trades_df["Direction"] == "SHORT"]

        if not long_entries.empty:
            ax1.scatter(
                long_entries["Entry Date"],
                long_entries["Entry Price"],
                marker="^", color="lime", s=80, zorder=5, label="Long Entry",
                edgecolors="black", linewidth=0.5,
            )
        if not short_entries.empty:
            ax1.scatter(
                short_entries["Entry Date"],
                short_entries["Entry Price"],
                marker="v", color="red", s=80, zorder=5, label="Short Entry",
                edgecolors="black", linewidth=0.5,
            )

        wins = trades_df[trades_df["PnL"] > 0]
        losses = trades_df[trades_df["PnL"] <= 0]
        if not wins.empty:
            ax1.scatter(
                wins["Exit Date"], wins["Exit Price"],
                marker="o", color="lime", s=40, zorder=5, alpha=0.6,
            )
        if not losses.empty:
            ax1.scatter(
                losses["Exit Date"], losses["Exit Price"],
                marker="o", color="red", s=40, zorder=5, alpha=0.6,
            )

    ax1.set_title("BTCUSDT Price Action + Technical Indicators + Trade Entries/Exits", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Price (USD)")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    # --- Panel 2: RSI ---
    ax2 = fig.add_subplot(gs[2, 0])
    ax2.plot(data.index, data["RSI_14"], color="purple", linewidth=1)
    ax2.axhline(y=70, color="red", linestyle="--", alpha=0.5, label="Overbought (70)")
    ax2.axhline(y=30, color="green", linestyle="--", alpha=0.5, label="Oversold (30)")
    ax2.axhline(y=40, color="orange", linestyle=":", alpha=0.3)
    ax2.fill_between(data.index, 30, 70, alpha=0.05, color="grey")
    ax2.set_title("RSI (14)", fontsize=11)
    ax2.set_ylabel("RSI")
    ax2.set_ylim(0, 100)
    ax2.legend(fontsize=7)
    ax2.grid(True, alpha=0.3)

    # --- Panel 3: MACD ---
    ax3 = fig.add_subplot(gs[2, 1])
    ax3.plot(data.index, data["MACD"], label="MACD", color="blue", linewidth=1)
    ax3.plot(data.index, data["MACD_Signal"], label="Signal", color="orange", linewidth=1)
    colors = ["green" if v >= 0 else "red" for v in data["MACD_Hist"]]
    ax3.bar(data.index, data["MACD_Hist"], color=colors, alpha=0.4, width=1)
    ax3.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax3.set_title("MACD (12, 26, 9)", fontsize=11)
    ax3.legend(fontsize=7)
    ax3.grid(True, alpha=0.3)

    # --- Panel 4: ADX ---
    ax4 = fig.add_subplot(gs[3, 0])
    ax4.plot(data.index, data["ADX_14"], color="brown", linewidth=1)
    ax4.axhline(y=20, color="grey", linestyle="--", alpha=0.5, label="Trend threshold (20)")
    ax4.axhline(y=40, color="orange", linestyle="--", alpha=0.5, label="Strong trend (40)")
    ax4.fill_between(data.index, 0, 20, alpha=0.05, color="red")
    ax4.set_title("ADX (14) - Trend Strength", fontsize=11)
    ax4.set_ylabel("ADX")
    ax4.legend(fontsize=7)
    ax4.grid(True, alpha=0.3)

    # --- Panel 5: Stochastic ---
    ax5 = fig.add_subplot(gs[3, 1])
    ax5.plot(data.index, data["Stoch_K"], label="%K", color="blue", linewidth=1)
    ax5.plot(data.index, data["Stoch_D"], label="%D", color="orange", linewidth=1)
    ax5.axhline(y=80, color="red", linestyle="--", alpha=0.5)
    ax5.axhline(y=20, color="green", linestyle="--", alpha=0.5)
    ax5.set_title("Stochastic Oscillator (14, 3)", fontsize=11)
    ax5.set_ylim(0, 100)
    ax5.legend(fontsize=7)
    ax5.grid(True, alpha=0.3)

    # --- Panel 6: Equity Curve ---
    ax6 = fig.add_subplot(gs[4, :])
    if not equity_df.empty:
        ax6.plot(equity_df.index, equity_df["Equity"], color="darkblue", linewidth=1.5)
        ax6.fill_between(equity_df.index, equity_df["Equity"].min() * 0.95, equity_df["Equity"], alpha=0.1, color="blue")
        ax6.axhline(y=metrics.get("Initial Capital (USD)", 10000), color="grey", linestyle="--", alpha=0.5, label="Initial Capital")
    ax6.set_title("Equity Curve", fontsize=11, fontweight="bold")
    ax6.set_ylabel("Equity (USD)")
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.3)
    ax6.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    # --- Panel 7: Metrics Table ---
    ax7 = fig.add_subplot(gs[5, :])
    ax7.axis("off")
    metrics_text = format_metrics_text(metrics)
    ax7.text(
        0.5, 0.95, metrics_text,
        transform=ax7.transAxes, fontsize=10, verticalalignment="top",
        horizontalalignment="center", fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", edgecolor="grey"),
    )
    ax7.set_title("Performance Metrics Summary", fontsize=11, fontweight="bold")

    filepath = os.path.join(OUTPUT_DIR, "btcusdt_strategy_report.png")
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return filepath


def plot_trade_distribution(trades: list[dict]) -> str:
    """Generate trade PnL distribution chart."""
    ensure_output_dir()

    if not trades:
        return ""

    trades_df = pd.DataFrame(trades)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # PnL Distribution
    ax = axes[0, 0]
    pnl_values = trades_df["PnL"]
    colors = ["green" if p > 0 else "red" for p in pnl_values]
    ax.bar(range(len(pnl_values)), pnl_values, color=colors, alpha=0.7)
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.set_title("PnL per Trade", fontsize=11)
    ax.set_ylabel("PnL (USD)")
    ax.set_xlabel("Trade #")
    ax.grid(True, alpha=0.3)

    # PnL Histogram
    ax = axes[0, 1]
    ax.hist(pnl_values, bins=20, color="steelblue", edgecolor="black", alpha=0.7)
    ax.axvline(x=0, color="red", linewidth=1)
    ax.axvline(x=pnl_values.mean(), color="orange", linestyle="--", label=f"Mean: ${pnl_values.mean():.2f}")
    ax.set_title("PnL Distribution", fontsize=11)
    ax.set_xlabel("PnL (USD)")
    ax.set_ylabel("Frequency")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Cumulative PnL
    ax = axes[1, 0]
    cum_pnl = pnl_values.cumsum()
    ax.plot(range(len(cum_pnl)), cum_pnl, color="darkblue", linewidth=1.5)
    ax.fill_between(range(len(cum_pnl)), 0, cum_pnl, alpha=0.1, color="blue")
    ax.axhline(y=0, color="grey", linewidth=0.5)
    ax.set_title("Cumulative PnL", fontsize=11)
    ax.set_ylabel("Cumulative PnL (USD)")
    ax.set_xlabel("Trade #")
    ax.grid(True, alpha=0.3)

    # Win/Loss by Exit Reason
    ax = axes[1, 1]
    reasons = trades_df.groupby("Exit Reason")["PnL"].agg(["sum", "count"])
    bar_colors = ["green" if s > 0 else "red" for s in reasons["sum"]]
    bars = ax.bar(reasons.index, reasons["sum"], color=bar_colors, alpha=0.7, edgecolor="black")
    for bar, count in zip(bars, reasons["count"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height(),
            f"n={count}", ha="center", va="bottom", fontsize=9,
        )
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.set_title("PnL by Exit Reason", fontsize=11)
    ax.set_ylabel("Total PnL (USD)")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, "btcusdt_trade_distribution.png")
    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return filepath


def format_metrics_text(metrics: dict) -> str:
    """Format metrics into a readable text block."""
    lines = [
        "=" * 60,
        f"{'BTCUSDT STRATEGY PERFORMANCE REPORT':^60}",
        f"{'(No Optimization - Standard Parameters)':^60}",
        "=" * 60,
        "",
        f"  Capital Inicial:     ${metrics.get('Initial Capital (USD)', 0):>12,.2f}",
        f"  Capital Final:       ${metrics.get('Final Equity (USD)', 0):>12,.2f}",
        f"  Ganancia Neta:       ${metrics.get('Net Profit (USD)', 0):>12,.2f}",
        f"  Retorno Total:        {metrics.get('Total Return %', 0):>11.2f}%",
        f"  CAGR:                 {metrics.get('CAGR %', 0):>11.2f}%",
        "",
        "-" * 60,
        f"  Total Trades:         {metrics.get('Total Trades', 0):>11}",
        f"  Trades Ganadores:     {metrics.get('Winning Trades', 0):>11}",
        f"  Trades Perdedores:    {metrics.get('Losing Trades', 0):>11}",
        f"  Win Rate:             {metrics.get('Win Rate %', 0):>10.2f}%",
        "",
        f"  Profit Factor:        {metrics.get('Profit Factor', 0):>11.2f}",
        f"  Reward/Risk Ratio:    {metrics.get('Reward/Risk Ratio', 0):>11.2f}",
        f"  Sharpe Ratio:         {metrics.get('Sharpe Ratio', 0):>11.2f}",
        f"  Max Drawdown:         {metrics.get('Max Drawdown %', 0):>10.2f}%",
        "",
        "-" * 60,
        f"  Gan. Promedio:       ${metrics.get('Avg Win (USD)', 0):>12,.2f}",
        f"  Perd. Promedio:      ${metrics.get('Avg Loss (USD)', 0):>12,.2f}",
        f"  Mayor Ganancia:      ${metrics.get('Largest Win (USD)', 0):>12,.2f}",
        f"  Mayor Perdida:       ${metrics.get('Largest Loss (USD)', 0):>12,.2f}",
        "",
        "-" * 60,
        f"  Trades Long:          {metrics.get('Long Trades', 0):>11}",
        f"  Win Rate Long:        {metrics.get('Long Win Rate %', 0):>10.2f}%",
        f"  Trades Short:         {metrics.get('Short Trades', 0):>11}",
        f"  Win Rate Short:       {metrics.get('Short Win Rate %', 0):>10.2f}%",
        f"  Dias Totales:         {metrics.get('Total Days', 0):>11}",
        "=" * 60,
    ]
    return "\n".join(lines)
