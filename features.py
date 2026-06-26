import numpy as np
import pandas as pd

FEATURES = [
    "Open", "High", "Low", "Close",
    "return", "lag1", "lag7",
    "ma7", "ma21", "ma7_gap", "ma21_gap",
    "volatility7", "range_pct", "rsi14",
    "dow_sin", "dow_cos",
    "macd", "macd_signal", "macd_hist",
    "vol_regime",
]


def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def add_features(data):
    out = data.copy().sort_values("Date").reset_index(drop=True)
    out["return"] = out["Close"].pct_change()
    out["lag1"] = out["Close"].shift(1)
    out["lag7"] = out["Close"].shift(7)
    out["ma7"] = out["Close"].rolling(7).mean()
    out["ma21"] = out["Close"].rolling(21).mean()
    out["ma7_gap"] = (out["ma7"] - out["Close"]) / out["Close"]
    out["ma21_gap"] = (out["ma21"] - out["Close"]) / out["Close"]
    out["volatility7"] = out["return"].rolling(7).std()
    out["range_pct"] = (out["High"] - out["Low"]) / out["Close"]
    out["rsi14"] = calculate_rsi(out["Close"], 14)
    out["day_of_week"] = out["Date"].dt.dayofweek
    out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 5)
    out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 5)
    exp12 = out["Close"].ewm(span=12, adjust=False).mean()
    exp26 = out["Close"].ewm(span=26, adjust=False).mean()
    out["macd"] = exp12 - exp26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    vol_med = out["volatility7"].rolling(252, min_periods=50).median()
    out["vol_regime"] = (out["volatility7"] > vol_med * 1.5).astype(float)
    return out
