"""
Technical indicators module.
All parameters use standard/textbook defaults - NO optimization.
"""

import pandas as pd
import numpy as np


def add_ema(df: pd.DataFrame, period: int, col: str = "Close") -> pd.Series:
    """Exponential Moving Average."""
    return df[col].ewm(span=period, adjust=False).mean()


def add_sma(df: pd.DataFrame, period: int, col: str = "Close") -> pd.Series:
    """Simple Moving Average."""
    return df[col].rolling(window=period).mean()


def add_rsi(df: pd.DataFrame, period: int = 14, col: str = "Close") -> pd.Series:
    """
    Relative Strength Index (Wilder's RSI).
    Standard period: 14 (Wilder, 1978).
    """
    delta = df[col].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    col: str = "Close",
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence).
    Standard parameters: 12, 26, 9 (Appel, 1979).
    Returns: (macd_line, signal_line, histogram)
    """
    ema_fast = df[col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[col].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def add_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    col: str = "Close",
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.
    Standard parameters: 20-period SMA, 2 standard deviations (Bollinger, 1983).
    Returns: (upper_band, middle_band, lower_band)
    """
    middle = df[col].rolling(window=period).mean()
    std = df[col].rolling(window=period).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return upper, middle, lower


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range.
    Standard period: 14 (Wilder, 1978).
    """
    high = df["High"]
    low = df["Low"]
    close = df["Close"].shift(1)

    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr


def add_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average Directional Index.
    Standard period: 14 (Wilder, 1978).
    """
    high = df["High"]
    low = df["Low"]

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    atr = add_atr(df, period)

    plus_di = 100 * (
        plus_dm.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean() / atr
    )
    minus_di = 100 * (
        minus_dm.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean() / atr
    )

    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
    adx = dx.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return adx


def add_stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """
    Stochastic Oscillator (%K and %D).
    Standard parameters: K=14, D=3 (Lane, 1950s).
    """
    low_min = df["Low"].rolling(window=k_period).min()
    high_max = df["High"].rolling(window=k_period).max()

    stoch_k = 100 * (df["Close"] - low_min) / (high_max - low_min)
    stoch_d = stoch_k.rolling(window=d_period).mean()
    return stoch_k, stoch_d


def add_obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume (Granville, 1963)."""
    obv = pd.Series(0.0, index=df.index)
    obv = np.where(
        df["Close"] > df["Close"].shift(1),
        df["Volume"],
        np.where(df["Close"] < df["Close"].shift(1), -df["Volume"], 0),
    )
    return pd.Series(np.cumsum(obv), index=df.index)


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators with standard (non-optimized) parameters.
    """
    result = df.copy()

    result["EMA_9"] = add_ema(df, 9)
    result["EMA_21"] = add_ema(df, 21)
    result["SMA_50"] = add_sma(df, 50)
    result["SMA_200"] = add_sma(df, 200)

    result["RSI_14"] = add_rsi(df, 14)

    macd_line, signal_line, histogram = add_macd(df, 12, 26, 9)
    result["MACD"] = macd_line
    result["MACD_Signal"] = signal_line
    result["MACD_Hist"] = histogram

    bb_upper, bb_middle, bb_lower = add_bollinger_bands(df, 20, 2.0)
    result["BB_Upper"] = bb_upper
    result["BB_Middle"] = bb_middle
    result["BB_Lower"] = bb_lower

    result["ATR_14"] = add_atr(df, 14)

    result["ADX_14"] = add_adx(df, 14)

    stoch_k, stoch_d = add_stochastic(df, 14, 3)
    result["Stoch_K"] = stoch_k
    result["Stoch_D"] = stoch_d

    result["OBV"] = add_obv(df)
    result["OBV_EMA_21"] = result["OBV"].ewm(span=21, adjust=False).mean()

    return result
