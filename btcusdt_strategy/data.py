"""
Module for downloading and preparing BTCUSDT historical data.
"""

import pandas as pd
import yfinance as yf


def download_btcusdt_data(
    period: str = "2y",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Download BTCUSDT historical data from Yahoo Finance.

    Args:
        period: Data period (e.g., '1y', '2y', '5y', 'max').
        interval: Data interval (e.g., '1d', '1h', '1wk').

    Returns:
        DataFrame with OHLCV data.
    """
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError("No data downloaded for BTC-USD.")

    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df[required_cols].dropna()
    return df
