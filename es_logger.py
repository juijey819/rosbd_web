import os
import time
import json
from datetime import datetime

from config import ES_URL

FLUSH_INTERVAL = int(os.getenv("ES_FLUSH_INTERVAL", 30))
BATCH_SIZE = int(os.getenv("ES_BATCH_SIZE", 50))


RETRY_INTERVAL = int(os.getenv("ES_RETRY_INTERVAL", 300))

class ESLogger:
    def __init__(self):
        self._buffer = []
        self._last_flush = time.time()
        self._http = None
        self._last_fail = 0
        self._enabled = True

    def _reset(self):
        self._http = None
        self._last_fail = time.time()

    def _get_http(self):
        if self._http is not None:
            return self._http
        if time.time() - self._last_fail < RETRY_INTERVAL:
            return None
        try:
            import urllib3
            self._http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=3, read=15))
            resp = self._http.request("GET", ES_URL)
            if resp.status >= 400:
                raise Exception(f"ES returned {resp.status}")
            self._enabled = True
            return self._http
        except Exception as e:
            print(f"[es_logger] cannot connect to {ES_URL}: {e}")
            self._reset()
            return None

    def _add(self, index, doc):
        if not self._enabled:
            return
        if "timestamp" not in doc:
            doc["timestamp"] = datetime.utcnow().isoformat()
        self._buffer.append({"index": {"_index": index}})
        self._buffer.append(doc)
        if (len(self._buffer) >= BATCH_SIZE * 2
                or time.time() - self._last_flush >= FLUSH_INTERVAL):
            self.flush()

    def flush(self):
        if not self._buffer:
            return
        http = self._get_http()
        if http is None:
            return
        lines = "\n".join(json.dumps(d) for d in self._buffer) + "\n"
        try:
            resp = http.request(
                "POST", f"{ES_URL}/_bulk",
                body=lines.encode(),
                headers={"Content-Type": "application/x-ndjson"},
            )
            if resp.status >= 400:
                print(f"[es_logger] bulk error: HTTP {resp.status}")
                self._reset()
        except Exception as e:
            print(f"[es_logger] request error: {e}")
            self._reset()
        finally:
            self._buffer.clear()
            self._last_flush = time.time()

    def log_bar(self, symbol, bar):
        self._add("bars", {
            "symbol": symbol,
            "open": float(bar["open"]),
            "high": float(bar["high"]),
            "low": float(bar["low"]),
            "close": float(bar["close"]),
            "atr": float(bar.get("atr", 0)),
            "type": "10s_bar",
        })

    def log_spike(self, symbol, price, atr, spike_ratio, spike_pips):
        self._add("signals", {
            "symbol": symbol,
            "event": "spike",
            "price": float(price),
            "atr": float(atr),
            "spike_ratio": round(float(spike_ratio), 2),
            "spike_pips": round(float(spike_pips), 1),
        })

    def log_recovery(self, symbol, price, atr, spike_ratio, spike_pips):
        self._add("signals", {
            "symbol": symbol,
            "event": "recovery",
            "price": float(price),
            "atr": float(atr),
            "spike_ratio": round(float(spike_ratio), 2),
            "spike_pips": round(float(spike_pips), 1),
        })

    def log_normal_tick(self, symbol, price, atr, batch_pips, regime):
        self._add("ticks", {
            "symbol": symbol,
            "price": float(price),
            "atr": float(atr),
            "batch_pips": round(float(batch_pips), 1),
            "regime": str(regime),
            "type": "normal",
        })

    def log_regime_change(self, symbol, price, old_regime, new_regime):
        self._add("signals", {
            "symbol": symbol,
            "event": "regime_change",
            "price": float(price),
            "old_regime": str(old_regime),
            "new_regime": str(new_regime),
        })

    def log_signal(self, symbol, result, last_row):
        doc = {
            "symbol": symbol,
            "event": "signal_5min",
            "signal": result["signal"],
            "score": float(result["score"]),
            "confidence": float(result["confidence"]),
            "regime": str(result["regime"]),
            "reason": result["reason"],
            "price": float(last_row.get("close", 0)),
            "atr": float(last_row.get("atr", 0)),
            "rsi": float(last_row.get("rsi", 0)),
            "trend_regime": str(last_row.get("trend_regime", "")),
            "vol_zscore": float(last_row.get("vol_zscore", 0)),
        }
        if "entry" in result and result.get("signal") != "HOLD":
            doc.update({
                "entry": float(result["entry"]),
                "sl": float(result["sl"]),
                "tp": float(result["tp"]),
                "rr": float(result["rr"]),
            })
        self._add("signals", doc)
