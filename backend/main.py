from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb+srv://rosbd:rosbd1234@rosbd.vu6gqbe.mongodb.net/?appName=rosbd"
client = MongoClient(MONGO_URI)
db = client["forex_dashboard"]

app = FastAPI(title="Forex Forecast API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

last_signals: dict[str, dict] = {}

class SignalPayload(BaseModel):
    pair: str
    signal: str
    score: float
    confidence: float
    regime: str
    reason: str
    price: float
    atr: float | None = None
    rsi: float | None = None
    entry: float | None = None
    sl: float | None = None
    tp: float | None = None
    rr: float | None = None

@app.get("/api/forecast/{pair_id}")
def get_forecast(pair_id: str):
    pair_map = {"eur-usd": "EUR/USD", "gbp-usd": "GBP/USD", "chf-usd": "CHF/USD"}
    pair = pair_map.get(pair_id)
    if not pair:
        return {"error": "Unknown pair"}, 404

    doc = db["forecasts"].find_one({"pair": pair}, {"_id": 0})
    if not doc:
        return JSONResponse({"error": "No forecast data yet. Run predict.py first."}, 404)

    return doc

@app.post("/api/signal")
def receive_signal(payload: SignalPayload):
    pair_id_map = {"EUR/USD": "eur-usd", "GBP/USD": "gbp-usd", "CHF/USD": "chf-usd"}
    pid = pair_id_map.get(payload.pair, payload.pair.lower().replace("/", "-"))

    data = payload.model_dump()
    data["timestamp"] = datetime.utcnow().isoformat()

    # Periodic (NORMAL) → hanya update real-time fields, jaga decision terakhir
    if data["signal"] == "NORMAL" and pid in last_signals:
        last_signals[pid]["price"] = data["price"]
        last_signals[pid]["atr"] = data["atr"]
        last_signals[pid]["rsi"] = data["rsi"]
        last_signals[pid]["regime"] = data["regime"]
        last_signals[pid]["timestamp"] = data["timestamp"]
    else:
        # Decision (BUY/SELL/HOLD) → overwrite semua
        last_signals[pid] = data

    return {"status": "ok"}

@app.get("/api/signal/{pair_id}")
def get_signal(pair_id: str):
    sig = last_signals.get(pair_id)
    if not sig:
        return JSONResponse({"signal": "HOLD", "confidence": 0, "price": 0, "reason": "No signal yet"}, 200)
    return sig

@app.get("/api/pairs")
def list_pairs():
    return [
        {"id": "eur-usd", "label": "EUR/USD"},
        {"id": "gbp-usd", "label": "GBP/USD"},
        {"id": "chf-usd", "label": "CHF/USD"},
    ]

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
