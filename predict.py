import yfinance as yf
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, timedelta
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://rosbd:rosbd1234@rosbd.vu6gqbe.mongodb.net/?appName=rosbd"
client = MongoClient(MONGO_URI)
db = client["forex_dashboard"]

PAIRS = {
    "EUR/USD": {"ticker": "EURUSD=X", "model": "outputs_revisi/ridge_eurusd_multihorizon.pkl", "features": "outputs_revisi/features_eurusd.json"},
    "GBP/USD": {"ticker": "GBPUSD=X", "model": "outputs_revisi/ridge_gbpusd_multihorizon.pkl", "features": "outputs_revisi/features_gbpusd.json"},
    "CHF/USD": {"ticker": "CHFUSD=X", "model": "outputs_revisi/ridge_chfusd_multihorizon.pkl", "features": "outputs_revisi/features_chfusd.json"},
}

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

FEATURES = [
    "Open", "High", "Low", "Close",
    "return", "lag1", "lag7",
    "ma7", "ma21", "ma7_gap", "ma21_gap",
    "volatility7", "range_pct", "rsi14",
    "dow_sin", "dow_cos",
    "macd", "macd_signal", "macd_hist",
    "vol_regime",
]

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

def sync_raw_data(pair_name, cfg):
    """Download yfinance data and save to MongoDB.raw_prices, then return full DataFrame."""
    ticker = cfg["ticker"]
    existing = list(db["raw_prices"].find(
        {"pair": pair_name},
        {"_id": 0, "date": 1}
    ).sort("date", 1))

    if existing:
        last_date = existing[-1]["date"]
        print(f"  {pair_name}: last in DB = {last_date}, downloading new data...")
        raw = yf.download(ticker, start=last_date, progress=False, auto_adjust=False)
    else:
        print(f"  {pair_name}: no data in DB, downloading from 2005...")
        raw = yf.download(ticker, start="2005-01-01", progress=False, auto_adjust=False)

    raw.columns = ['_'.join(col).strip() for col in raw.columns.values]
    raw.columns = [c.replace(f'_{ticker}', '') for c in raw.columns]

    df = raw.reset_index().copy()
    if 'Date_' in df.columns:
        df = df.rename(columns={'Date_': 'Date'})
    if 'index' in df.columns and 'Date' not in df.columns:
        df = df.rename(columns={'index': 'Date'})

    if "Adj Close" in df.columns and "Close" not in df.columns:
        df = df.rename(columns={"Adj Close": "Close"})

    needed = ["Date", "Open", "High", "Low", "Close"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Got: {list(df.columns)}")

    df = df[needed].dropna().copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Filter out dates already in DB
    existing_dates = {d["date"] for d in existing}
    new_rows = df[~df["Date"].isin(existing_dates)]

    if len(new_rows) > 0:
        docs = []
        for _, r in new_rows.iterrows():
            docs.append({
                "pair": pair_name,
                "date": r["Date"],
                "open": float(r["Open"]),
                "high": float(r["High"]),
                "low": float(r["Low"]),
                "close": float(r["Close"]),
            })
        db["raw_prices"].insert_many(docs)
        print(f"  Inserted {len(docs)} new rows to raw_prices")
    else:
        print(f"  No new data")

    # Read all data back from DB
    all_docs = list(db["raw_prices"].find(
        {"pair": pair_name},
        {"_id": 0}
    ).sort("date", 1))

    result_df = pd.DataFrame(all_docs)
    result_df = result_df.rename(columns={
        "date": "Date", "open": "Open", "high": "High",
        "low": "Low", "close": "Close"
    })
    result_df["Date"] = pd.to_datetime(result_df["Date"])
    return result_df

def compute_metrics(performance):
    if len(performance) == 0:
        return {"mae": 0, "direction_accuracy": 0}
    actuals = np.array([p["actual"] for p in performance])
    preds = np.array([p["predicted"] for p in performance])
    mae = np.mean(np.abs(actuals - preds))

    actual_dirs = np.array([p["actual_return"] >= 0 for p in performance])
    pred_dirs = np.array([p["predicted_return"] >= 0 for p in performance])
    dir_acc = float(np.mean(actual_dirs == pred_dirs)) if len(performance) > 0 else 0
    return {"mae": round(mae, 5), "direction_accuracy": round(dir_acc, 4)}

def build_performance_7d(model, df, features, horizons, target_type="price"):
    """Generate performance data: for each date, compare actual close vs model prediction 7 days earlier."""
    df_feat = add_features(df)
    df_feat = df_feat.dropna(subset=features).copy()
    X_perf = df_feat[features]
    preds = model.predict(X_perf)

    h = 7
    h_idx = horizons.index(h)
    perf = []
    for i in range(len(df_feat)):
        future_idx = i + h
        if future_idx >= len(df_feat):
            break
        current_close = float(df_feat.iloc[i]["Close"])
        predicted_raw = float(preds[i, h_idx])
        if target_type == "return":
            predicted_price = current_close * (1 + predicted_raw)
            predicted_return = predicted_raw
        else:
            predicted_price = predicted_raw
            predicted_return = predicted_price / current_close - 1
        actual_price = float(df_feat.iloc[future_idx]["Close"])
        actual_return = actual_price / current_close - 1
        perf.append({
            "date": str(df_feat.iloc[future_idx]["Date"].date()),
            "actual": round(actual_price, 5),
            "predicted": round(predicted_price, 5),
            "actual_return": round(actual_return, 6),
            "predicted_return": round(predicted_return, 6),
        })

    return perf[-60:]

def predict_7days(pair_name, cfg):
    print(f"\n=== {pair_name} ===")

    # 1. Sync raw data from yfinance → MongoDB
    df = sync_raw_data(pair_name, cfg)

    # 2. Load model + features
    model_bundle = joblib.load(cfg["model"])
    model = model_bundle["model"]
    horizons = model_bundle.get("horizons", [1, 2, 3, 4, 5, 6, 7])
    features = FEATURES

    # 3. Feature engineering
    feature_df = add_features(df)
    latest_row = feature_df.dropna(subset=features).iloc[-1:].copy()
    latest_X = latest_row[features]
    latest_date = pd.to_datetime(latest_row["Date"].iloc[0])
    latest_close = float(latest_row["Close"].iloc[0])

    # 4. Predict 7 days (model predicts returns, convert to prices)
    forecast_raw = model.predict(latest_X)[0]

    # Check if model is return-based (target_type in bundle)
    target_type = model_bundle.get("target_type", "price")
    if target_type == "return":
        forecast_prices = latest_close * (1 + forecast_raw)
    else:
        forecast_prices = forecast_raw

    future_dates = pd.bdate_range(latest_date + pd.offsets.BDay(1), periods=len(horizons))

    forecast_7d = []
    for i, h in enumerate(horizons):
        forecast_7d.append({
            "day": int(h),
            "date": str(future_dates[i].date()),
            "price": round(float(forecast_prices[i]), 5),
        })

    # 5. History 30 days
    history_30d = []
    last_30 = df.dropna(subset=["Close"]).tail(30)
    for _, r in last_30.iterrows():
        history_30d.append({
            "date": str(r["Date"].date()),
            "close": round(float(r["Close"]), 5),
        })

    # 6. Performance (predicted vs actual, horizon 7)
    target_type = model_bundle.get("target_type", "price")
    performance = build_performance_7d(model, df, features, horizons, target_type=target_type)
    metrics = compute_metrics(performance)

    # 7. Save to forecasts collection
    forecast_day7 = forecast_7d[-1]["price"]
    change_pct = (forecast_day7 / latest_close - 1) * 100

    doc = {
        "pair": pair_name,
        "generated_at": datetime.utcnow(),
        "last_date": str(latest_date.date()),
        "last_close": round(latest_close, 5),
        "forecast_price": round(forecast_day7, 5),
        "change_pct": round(change_pct, 2),
        "history_30d": history_30d,
        "forecast_7d": forecast_7d,
        "performance": performance,
        "metrics": metrics,
    }

    db["forecasts"].replace_one({"pair": pair_name}, doc, upsert=True)
    print(f"  Saved to MongoDB -> forecasts.{pair_name}")
    return doc

if __name__ == "__main__":
    for name, cfg in PAIRS.items():
        try:
            r = predict_7days(name, cfg)
            print(f"  {r['last_date']}: {r['last_close']} -> day7={r['forecast_price']} ({r['change_pct']:+.2f}%)")
        except Exception as e:
            print(f"  ERROR: {e}")

    raw_count = db["raw_prices"].count_documents({})
    forecast_count = db["forecasts"].count_documents({})
    print(f"\nDone. raw_prices: {raw_count} docs, forecasts: {forecast_count} docs")
