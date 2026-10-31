import warnings
warnings.filterwarnings("ignore")

import json
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pymongo import MongoClient
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_absolute_error

from prefect import flow, task

from config import MODEL_DIR, MONGO_DB, MONGO_URI
from features import FEATURES, add_features

OUTPUT_DIR = MODEL_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PAIRS = {
    "EUR/USD": {"ticker": "EURUSD=X"},
    "GBP/USD": {"ticker": "GBPUSD=X"},
    "CHF/USD": {"ticker": "CHFUSD=X"},
}

HORIZONS = list(range(1, 8))
TARGET_COLS = [f"target_price_{h}d" for h in HORIZONS]


@task(retries=2, retry_delay_seconds=60)
def sync_data():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]

    results = {}
    for pair_name, cfg in PAIRS.items():
        ticker = cfg["ticker"]
        existing = list(db["raw_prices"].find(
            {"pair": pair_name},
            {"_id": 0, "date": 1}
        ).sort("date", 1))

        if existing:
            last_date = existing[-1]["date"]
            raw = yf.download(ticker, start=last_date, progress=False, auto_adjust=False)
        else:
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
        results[pair_name] = result_df

    client.close()
    return results


@task
def train_pair(pair_name, df):
    feature_df = add_features(df)

    for h in HORIZONS:
        feature_df[f"target_price_{h}d"] = feature_df["Close"].shift(-h)

    model_df = feature_df.dropna(subset=FEATURES + TARGET_COLS).copy()

    if len(model_df) > 5000:
        model_df = model_df.tail(5000).reset_index(drop=True)

    X = model_df[FEATURES]
    y = model_df[TARGET_COLS]

    split_idx = int(len(model_df) * 0.8)
    X_train = X.iloc[:split_idx]
    y_train = y.iloc[:split_idx]
    X_val = X.iloc[split_idx:]
    y_val = y.iloc[split_idx:]

    ridge = Pipeline([
        ("scaler", StandardScaler()),
        ("ridge", Ridge())
    ])

    param_grid = {
        "ridge__alpha": np.logspace(-3, 3, 13),
        "ridge__fit_intercept": [True, False]
    }

    tscv = TimeSeriesSplit(n_splits=5)
    grid = GridSearchCV(
        estimator=ridge,
        param_grid=param_grid,
        cv=tscv,
        scoring="neg_mean_absolute_error",
        n_jobs=-1
    )
    grid.fit(X_train, y_train)
    best_model = grid.best_estimator_

    y_pred_val = best_model.predict(X_val)
    val_mae = {}
    for i, h in enumerate(HORIZONS):
        mae = mean_absolute_error(y_val.iloc[:, i], y_pred_val[:, i])
        val_mae[f"horizon_{h}d"] = round(mae, 6)
    avg_mae = float(np.mean(list(val_mae.values())))

    final_model = clone(best_model)
    final_model.fit(X, y)

    model_bundle = {
        "model": final_model,
        "features": FEATURES,
        "horizons": HORIZONS,
        "target_type": "multi_horizon_price",
        "pair": PAIRS[pair_name]["ticker"],
        "pair_name": pair_name,
        "best_params": grid.best_params_,
        "model_name": "Ridge (grid search)",
        "training_date": datetime.utcnow().isoformat(),
        "training_rows": len(model_df),
        "val_mae": val_mae,
        "val_avg_mae": avg_mae,
    }

    return model_bundle


@task
def promote_model(pair_name, new_bundle):
    model_filename = f"ridge_{pair_name.replace('/', '').lower()}_multihorizon.pkl"
    model_path = OUTPUT_DIR / model_filename
    features_path = OUTPUT_DIR / f"features_{pair_name.replace('/', '').lower()}.json"

    joblib.dump(new_bundle, model_path)
    with open(features_path, "w") as f:
        json.dump(FEATURES, f)

    return {
        "pair": pair_name,
        "promoted": True,
        "new_val_mae": new_bundle["val_avg_mae"],
        "training_rows": new_bundle["training_rows"],
    }


@task
def build_performance_7d(model, df, features, horizons, target_type="price"):
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


def regenerate_forecast(model_bundles):
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]

    for pair_name, bundle in model_bundles.items():
        model = bundle["model"]
        features_list = bundle["features"]
        horizons = bundle["horizons"]

        all_docs = list(db["raw_prices"].find(
            {"pair": pair_name},
            {"_id": 0}
        ).sort("date", 1))

        df = pd.DataFrame(all_docs)
        df = df.rename(columns={
            "date": "Date", "open": "Open", "high": "High",
            "low": "Low", "close": "Close"
        })
        df["Date"] = pd.to_datetime(df["Date"])

        feature_df = add_features(df)
        latest_row = feature_df.dropna(subset=features_list).iloc[-1:].copy()
        latest_X = latest_row[features_list]
        latest_date = pd.to_datetime(latest_row["Date"].iloc[0])
        latest_close = float(latest_row["Close"].iloc[0])

        forecast_raw = model.predict(latest_X)[0]

        target_type = bundle.get("target_type", "price")
        if target_type == "return":
            forecast_prices = latest_close * (1 + forecast_raw)
        else:
            forecast_prices = forecast_raw

        future_dates = pd.bdate_range(
            latest_date + pd.offsets.BDay(1), periods=len(horizons)
        )

        forecast_7d = []
        for i, h in enumerate(horizons):
            forecast_7d.append({
                "day": int(h),
                "date": str(future_dates[i].date()),
                "price": round(float(forecast_prices[i]), 5),
            })

        history_30d = []
        last_30 = df.dropna(subset=["Close"]).tail(30)
        for _, r in last_30.iterrows():
            history_30d.append({
                "date": str(r["Date"].date()),
                "close": round(float(r["Close"]), 5),
            })

        target_type = bundle.get("target_type", "price")
        performance = build_performance_7d(model, df, features_list, horizons, target_type=target_type)
        metrics = compute_metrics(performance)

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

    client.close()


@flow(log_prints=True)
def retrain_pipeline():
    print("Starting daily retrain pipeline...")

    data = sync_data()

    results = {}
    for pair_name, df in data.items():
        print(f"\n=== {pair_name} ===")
        bundle = train_pair(pair_name, df)
        result = promote_model(pair_name, bundle)
        print(f"  {pair_name}: PROMOTED (MAE={result['new_val_mae']:.6f}, rows={result['training_rows']})")
        results[pair_name] = bundle

    regenerate_forecast(results)
    print("\nDaily retrain pipeline completed. Forecast updated.")


if __name__ == "__main__":
    import sys

    if "--serve" in sys.argv:
        retrain_pipeline.serve(
            name="daily-retrain",
            cron="0 2 * * *",
            tags=["forex", "retrain"],
        )
    else:
        retrain_pipeline()
