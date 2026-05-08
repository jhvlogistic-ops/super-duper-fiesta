"""
Multi-indicator BTCUSDT trading strategy WITHOUT optimization.

Strategy Logic:
- Trend filter: Price above SMA 200 for longs, below for shorts
- Entry signals combine EMA crossover + RSI + MACD confirmation + ADX trend strength
- Exit via trailing stop based on ATR, or indicator reversal
- Position sizing: fixed fraction of equity per trade
- Risk management: ATR-based stop-loss and take-profit

All indicator parameters are standard textbook values.
"""

import pandas as pd
import numpy as np



RISK_PER_TRADE = 0.02  # 2% risk per trade (standard risk management)
ATR_SL_MULTIPLIER = 2.0  # Stop loss at 2x ATR
ATR_TP_MULTIPLIER = 3.0  # Take profit at 3x ATR (1.5:1 R:R ratio)
INITIAL_CAPITAL = 10000.0


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals based on multiple indicator confluence.

    Entry LONG conditions (all must be true):
    1. Close > SMA_200 (bullish trend)
    2. EMA_9 > EMA_21 (short-term momentum bullish)
    3. RSI_14 > 40 and RSI_14 < 70 (not oversold, not overbought)
    4. MACD_Hist > 0 (MACD bullish)
    5. ADX_14 > 20 (trend has strength)

    Entry SHORT conditions (all must be true):
    1. Close < SMA_200 (bearish trend)
    2. EMA_9 < EMA_21 (short-term momentum bearish)
    3. RSI_14 < 60 and RSI_14 > 30 (not overbought, not oversold)
    4. MACD_Hist < 0 (MACD bearish)
    5. ADX_14 > 20 (trend has strength)

    Exit conditions:
    - Stop loss hit (ATR-based)
    - Take profit hit (ATR-based)
    - Signal reversal
    """
    data = df.copy()

    long_condition = (
        (data["Close"] > data["SMA_200"])
        & (data["EMA_9"] > data["EMA_21"])
        & (data["RSI_14"] > 40)
        & (data["RSI_14"] < 70)
        & (data["MACD_Hist"] > 0)
        & (data["ADX_14"] > 20)
    )

    short_condition = (
        (data["Close"] < data["SMA_200"])
        & (data["EMA_9"] < data["EMA_21"])
        & (data["RSI_14"] < 60)
        & (data["RSI_14"] > 30)
        & (data["MACD_Hist"] < 0)
        & (data["ADX_14"] > 20)
    )

    data["Signal"] = 0
    data.loc[long_condition, "Signal"] = 1
    data.loc[short_condition, "Signal"] = -1

    return data


def backtest(df: pd.DataFrame, initial_capital: float = INITIAL_CAPITAL) -> dict:
    """
    Run backtest simulation with ATR-based risk management.

    Returns a dictionary with:
    - trades: list of all trades
    - equity_curve: Series of equity over time
    - metrics: performance metrics dictionary
    """
    data = df.dropna().copy()

    equity = initial_capital
    equity_curve = []
    trades = []

    position = 0  # 1=long, -1=short, 0=flat
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    entry_date = None
    position_size = 0.0

    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]
        current_date = data.index[i]
        current_price = row["Close"]
        current_atr = row["ATR_14"]

        if position != 0:
            if position == 1:
                if current_price <= stop_loss:
                    pnl = (stop_loss - entry_price) * position_size
                    exit_reason = "Stop Loss"
                    exit_price = stop_loss
                elif current_price >= take_profit:
                    pnl = (take_profit - entry_price) * position_size
                    exit_reason = "Take Profit"
                    exit_price = take_profit
                elif row["Signal"] == -1 or (
                    prev_row["EMA_9"] > prev_row["EMA_21"]
                    and row["EMA_9"] <= row["EMA_21"]
                ):
                    pnl = (current_price - entry_price) * position_size
                    exit_reason = "Signal Reversal"
                    exit_price = current_price
                else:
                    equity_curve.append(
                        {
                            "Date": current_date,
                            "Equity": equity
                            + (current_price - entry_price) * position_size,
                        }
                    )
                    continue

            elif position == -1:
                if current_price >= stop_loss:
                    pnl = (entry_price - stop_loss) * position_size
                    exit_reason = "Stop Loss"
                    exit_price = stop_loss
                elif current_price <= take_profit:
                    pnl = (entry_price - take_profit) * position_size
                    exit_reason = "Take Profit"
                    exit_price = take_profit
                elif row["Signal"] == 1 or (
                    prev_row["EMA_9"] < prev_row["EMA_21"]
                    and row["EMA_9"] >= row["EMA_21"]
                ):
                    pnl = (entry_price - current_price) * position_size
                    exit_reason = "Signal Reversal"
                    exit_price = current_price
                else:
                    equity_curve.append(
                        {
                            "Date": current_date,
                            "Equity": equity
                            + (entry_price - current_price) * position_size,
                        }
                    )
                    continue

            equity += pnl
            trades.append(
                {
                    "Entry Date": entry_date,
                    "Exit Date": current_date,
                    "Direction": "LONG" if position == 1 else "SHORT",
                    "Entry Price": round(entry_price, 2),
                    "Exit Price": round(exit_price, 2),
                    "Stop Loss": round(stop_loss, 2),
                    "Take Profit": round(take_profit, 2),
                    "PnL": round(pnl, 2),
                    "PnL %": round((pnl / (entry_price * position_size)) * 100, 2),
                    "Exit Reason": exit_reason,
                    "Equity": round(equity, 2),
                }
            )
            position = 0
            entry_price = 0.0

        if position == 0 and row["Signal"] != 0:
            if np.isnan(current_atr) or current_atr <= 0:
                equity_curve.append({"Date": current_date, "Equity": equity})
                continue

            risk_amount = equity * RISK_PER_TRADE
            position_size = risk_amount / (ATR_SL_MULTIPLIER * current_atr)

            if position_size * current_price > equity:
                position_size = equity / current_price

            if row["Signal"] == 1:
                position = 1
                entry_price = current_price
                stop_loss = entry_price - ATR_SL_MULTIPLIER * current_atr
                take_profit = entry_price + ATR_TP_MULTIPLIER * current_atr
            elif row["Signal"] == -1:
                position = -1
                entry_price = current_price
                stop_loss = entry_price + ATR_SL_MULTIPLIER * current_atr
                take_profit = entry_price - ATR_TP_MULTIPLIER * current_atr

            entry_date = current_date

        equity_curve.append({"Date": current_date, "Equity": equity})

    equity_df = pd.DataFrame(equity_curve)
    if not equity_df.empty:
        equity_df.set_index("Date", inplace=True)

    metrics = compute_metrics(trades, equity_df, initial_capital)

    return {
        "trades": trades,
        "equity_curve": equity_df,
        "metrics": metrics,
        "data": data,
    }


def compute_metrics(
    trades: list[dict],
    equity_df: pd.DataFrame,
    initial_capital: float,
) -> dict:
    """Compute comprehensive performance metrics."""
    if not trades:
        return {
            "Total Trades": 0,
            "Net Profit": 0,
            "Return %": 0,
        }

    trades_df = pd.DataFrame(trades)
    winning_trades = trades_df[trades_df["PnL"] > 0]
    losing_trades = trades_df[trades_df["PnL"] < 0]

    total_trades = len(trades_df)
    win_count = len(winning_trades)
    loss_count = len(losing_trades)
    win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0

    net_profit = trades_df["PnL"].sum()
    final_equity = initial_capital + net_profit
    total_return = ((final_equity - initial_capital) / initial_capital) * 100

    avg_win = winning_trades["PnL"].mean() if not winning_trades.empty else 0
    avg_loss = abs(losing_trades["PnL"].mean()) if not losing_trades.empty else 0
    profit_factor = (
        (winning_trades["PnL"].sum() / abs(losing_trades["PnL"].sum()))
        if not losing_trades.empty and losing_trades["PnL"].sum() != 0
        else float("inf")
    )

    reward_risk_ratio = avg_win / avg_loss if avg_loss > 0 else float("inf")

    max_drawdown = 0.0
    if not equity_df.empty:
        equity_series = equity_df["Equity"]
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak * 100
        max_drawdown = drawdown.min()

    long_trades = trades_df[trades_df["Direction"] == "LONG"]
    short_trades = trades_df[trades_df["Direction"] == "SHORT"]

    long_wins = long_trades[long_trades["PnL"] > 0]
    short_wins = short_trades[short_trades["PnL"] > 0]

    if not equity_df.empty and len(equity_df) > 1:
        days = (equity_df.index[-1] - equity_df.index[0]).days
        years = days / 365.25 if days > 0 else 1
        cagr = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
    else:
        cagr = 0.0
        days = 0

    daily_returns = equity_df["Equity"].pct_change().dropna() if not equity_df.empty else pd.Series()
    sharpe_ratio = 0.0
    if not daily_returns.empty and daily_returns.std() > 0:
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

    return {
        "Total Trades": total_trades,
        "Winning Trades": win_count,
        "Losing Trades": loss_count,
        "Win Rate %": round(win_rate, 2),
        "Net Profit (USD)": round(net_profit, 2),
        "Total Return %": round(total_return, 2),
        "CAGR %": round(cagr, 2),
        "Max Drawdown %": round(max_drawdown, 2),
        "Profit Factor": round(profit_factor, 2),
        "Reward/Risk Ratio": round(reward_risk_ratio, 2),
        "Sharpe Ratio": round(sharpe_ratio, 2),
        "Avg Win (USD)": round(avg_win, 2),
        "Avg Loss (USD)": round(avg_loss, 2),
        "Largest Win (USD)": round(winning_trades["PnL"].max(), 2) if not winning_trades.empty else 0,
        "Largest Loss (USD)": round(losing_trades["PnL"].min(), 2) if not losing_trades.empty else 0,
        "Long Trades": len(long_trades),
        "Long Win Rate %": round(
            (len(long_wins) / len(long_trades)) * 100 if len(long_trades) > 0 else 0, 2
        ),
        "Short Trades": len(short_trades),
        "Short Win Rate %": round(
            (len(short_wins) / len(short_trades)) * 100 if len(short_trades) > 0 else 0, 2
        ),
        "Total Days": days if not equity_df.empty else 0,
        "Initial Capital (USD)": initial_capital,
        "Final Equity (USD)": round(final_equity, 2),
    }
