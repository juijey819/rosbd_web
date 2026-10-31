from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
import pandas as pd
import requests
import time
import logging
from config import (
    BACKEND_URL,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from signal_engine import RealTimeMonitor, DecisionLayer, SignalEngine, add_features
from es_logger import ESLogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("spark_consumer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("spark_consumer")

es = ESLogger()


def send_telegram(msg: str, retries=2):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram is not configured; skipping notification")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for attempt in range(retries):
        try:
            resp = requests.post(
                url,
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            
            result = resp.json()
            
            # IMPORTANT: Check API response, not just HTTP status code
            if not result.get("ok"):
                error_code = result.get("error_code")
                description = result.get("description")
                logger.error(f"Telegram API error {error_code}: {description}")
                
                # Don't retry for auth/permission errors
                if error_code in [401, 403, 404, 400]:
                    return False
                
                # Retry for other errors
                if attempt < retries - 1:
                    logger.info(f"Telegram: retrying (attempt {attempt + 1}/{retries})...")
                    time.sleep(1)
                    continue
                return False
            
            message_id = result.get("result", {}).get("message_id")
            logger.debug(f"Telegram message sent successfully (ID: {message_id})")
            return True
            
        except requests.exceptions.Timeout:
            logger.warning(f"Telegram: timeout (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return False
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Telegram: connection error - {e}")
            return False
            
        except Exception as e:
            logger.error(f"Telegram: unexpected error - {e}", exc_info=True)
            return False
    
    return False

spark = SparkSession.builder \
    .appName("ForexStreamingAnalytics") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("symbol", StringType(), True),
    StructField("price", DoubleType(), True),
    StructField("change", DoubleType(), True),
    StructField("change_percent", DoubleType(), True),
    StructField("timestamp", LongType(), True)
])

monitor = RealTimeMonitor()
decision = DecisionLayer()
engine = SignalEngine(decision, monitor, entry_thresh=2.0, spread=0.8)

price_buffer = []
BUFFER_MIN = 55
last_batch_time = [0]
BATCH_INTERVAL = 300
last_vol_regime = [None]
SPIKE_THRESH = 2.0
RECOVERY_THRESH = 0.5
RECOVERY_BARS = 3
spike_state = [False]
spike_clear_count = [0]
spike_tick_count = [0]
last_price = [None]


def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    rows = batch_df.toPandas()
    first = rows.iloc[0]
    last_r = rows.iloc[-1]
    symbol = first["symbol"]
    price_open = float(first["price"])
    price_close = float(last_r["price"])
    price_high = float(rows["price"].max())
    price_low = float(rows["price"].min())
    ts = int(last_r["timestamp"])
    batch_change = price_close - price_open

    # --- Compute ATR dari buffer (sebelum bar baru) ---
    buf_df = None
    if len(price_buffer) >= 14:
        buf_df = pd.DataFrame(price_buffer[-200:])
        buf_df = add_features(buf_df)
        atr_est = float(buf_df["atr"].iloc[-1]) if not buf_df["atr"].isna().iloc[-1] else price_close * 0.0003
    else:
        atr_est = price_close * 0.0003

    # --- Spike detection: tick-to-tick dalam batch ---
    for _, row in rows.iterrows():
        p = float(row["price"])
        if last_price[0] is not None:
            tick_change = p - last_price[0]
            spike_ratio = abs(tick_change) / atr_est
            spike_pips = tick_change / 0.0001

            # --- Trigger spike alert ---
            if spike_ratio > SPIKE_THRESH:
                spike_tick_count[0] += 1
                if not spike_state[0]:
                    es.log_spike(symbol, p, atr_est, spike_ratio, spike_pips)
                    sm = (
                        f"SPIKE {spike_ratio:.1f}x ATR\n"
                        f"{symbol}  {p:.5f}  {'+' if tick_change > 0 else ''}{spike_pips:.1f}p in {spike_tick_count[0]}t\n"
                        f"ATR {atr_est/0.0001:.1f}p"
                    )
                    print(sm)
                    send_telegram(sm)
                    spike_state[0] = True
                    spike_clear_count[0] = 0
            elif spike_tick_count[0] > 0:
                spike_tick_count[0] = 0

            # --- Recovery check (selama dalam spike_state, tiap tick) ---
            if spike_state[0]:
                if spike_ratio < RECOVERY_THRESH:
                    spike_clear_count[0] += 1
                else:
                    spike_clear_count[0] = 0

                if spike_clear_count[0] >= RECOVERY_BARS:
                    es.log_recovery(symbol, p, atr_est, spike_ratio, spike_pips)
                    cm = (
                        f"Normal kembali\n"
                        f"{symbol}  {p:.5f}  ({spike_pips:.1f}p | {spike_ratio:.1f}x ATR)"
                    )
                    print(cm)
                    send_telegram(cm)
                    spike_state[0] = False
                    spike_clear_count[0] = 0

        last_price[0] = p

    # --- Periodic notification (tiap 10s, hanya saat tidak spike) ---
    if not spike_state[0]:
        pips = batch_change / 0.0001
        arrow = "^" if pips > 0.3 else ("v" if pips < -0.3 else "-")
        pm = (
            f"Normal\n"
            f"{symbol}  {price_close:.5f}  |  {pips:+.1f}p {arrow}\n"
            f"ATR {atr_est/0.0001:.1f}p"
        )
        print(pm)
        send_telegram(pm)

        try:
            vz_local = 0.0
            if buf_df is not None:
                full = buf_df.dropna(subset=["vol_zscore"])
                if not full.empty:
                    vz_local = float(full.iloc[-1]["vol_zscore"])
            reg = "HIGH_VOL" if vz_local > 1.0 else ("LOW_VOL" if vz_local < -0.8 else "MED_VOL")
            es.log_normal_tick(symbol, price_close, atr_est, pips, reg)
            requests.post(f"{BACKEND_URL}/api/signal", json={
                "pair": "EUR/USD",
                "signal": "NORMAL",
                "score": 0,
                "confidence": 0,
                "regime": reg,
                "reason": f"{pips:+.1f}p {arrow.strip()}",
                "price": float(price_close),
                "atr": float(atr_est),
                "rsi": None,
            }, timeout=3)
        except requests.exceptions.Timeout:
            logger.warning(f"Backend API timeout (normal tick for {symbol})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Backend API connection error (normal tick for {symbol})")
        except Exception as e:
            logger.error(f"Error in normal tick logging: {e}", exc_info=True)

    # --- Vol regime change ---
    if buf_df is not None:
        last_full = buf_df.dropna(subset=["vol_zscore"])
        if not last_full.empty:
            vz = float(last_full.iloc[-1]["vol_zscore"])
            if vz > 1.0:
                vol_regime = "HIGH_VOL"
            elif vz < -0.8:
                vol_regime = "LOW_VOL"
            else:
                vol_regime = "MED_VOL"

            if vol_regime != last_vol_regime[0] and last_vol_regime[0] is not None:
                es.log_regime_change(symbol, price_close, last_vol_regime[0], vol_regime)
                vm = (
                    f"REGIME BERUBAH\n"
                    f"{last_vol_regime[0]} -> {vol_regime}\n"
                    f"{symbol}  {price_close:.5f}"
                )
                print(vm)
                send_telegram(vm)
            last_vol_regime[0] = vol_regime

    # --- Append OHLC bar 10 detik ---
    bar = {
        "date": pd.to_datetime(ts, unit="ms"),
        "open": price_open,
        "high": price_high,
        "low": price_low,
        "close": price_close,
        "atr": atr_est,
    }
    price_buffer.append(bar)
    es.log_bar(symbol, bar)

    # --- Decision layer (5 menit) ---
    if len(price_buffer) < BUFFER_MIN:
        return

    now = time.time()
    if now - last_batch_time[0] < BATCH_INTERVAL:
        sisa = int(BATCH_INTERVAL - (now - last_batch_time[0]))
        print(f"[decision] next batch in {sisa}s")
        return

    last_batch_time[0] = now

    df = pd.DataFrame(price_buffer[-200:])
    df = add_features(df)
    df = df.dropna(subset=["atr", "ema20", "ema50", "rsi"])

    if df.empty:
        return

    last_row = df.iloc[-1].to_dict()
    result = engine.step(last_row)
    signal = result["signal"]

    icon = signal

    dec_msg = (
        f"SINYAL 5 MENIT\n"
        f"Signal     : {icon}\n"
        f"Symbol     : {symbol}\n"
        f"Price      : {last_row['close']:.5f}\n"
        f"Score      : {result['score']}\n"
        f"Confidence : {result['confidence']}%\n"
        f"Regime     : {result['regime'][0]} | {result['regime'][1]}\n"
        f"Reason     : {result['reason']}"
    )

    if signal != "HOLD":
        dec_msg += (
            f"\n\nEntry : {result['entry']}\n"
            f"SL    : {result['sl']}\n"
            f"TP    : {result['tp']}\n"
            f"RR    : {result['rr']}"
        )

    print(dec_msg)
    send_telegram(dec_msg)

    try:
        atr_val = float(last_row.get("atr", 0))
        rsi_val = float(last_row.get("rsi", 0))
        es.log_signal(symbol, result, last_row)
        requests.post(f"{BACKEND_URL}/api/signal", json={
            "pair": "EUR/USD",
            "signal": signal,
            "score": float(result["score"]),
            "confidence": float(result["confidence"]),
            "regime": result["regime"][0] if isinstance(result["regime"], (list, tuple)) else str(result["regime"]),
            "reason": result["reason"],
            "price": float(last_row["close"]),
            "atr": atr_val,
            "rsi": rsi_val,
            "entry": float(result["entry"]) if signal != "HOLD" else None,
            "sl": float(result["sl"]) if signal != "HOLD" else None,
            "tp": float(result["tp"]) if signal != "HOLD" else None,
            "rr": float(result["rr"]) if signal != "HOLD" else None,
        }, timeout=5)
    except Exception as e:
        print(f"[signal_api] error: {e}")

    es.flush()


kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

string_df = kafka_df.selectExpr("CAST(value AS STRING) as json_payload")
parsed_df = string_df.select(from_json(col("json_payload"), schema).alias("data")).select("data.*")

query = parsed_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_batch) \
    .trigger(processingTime="10 seconds") \
    .start()

query.awaitTermination()