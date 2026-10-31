import json
import asyncio
from yfinance import AsyncWebSocket
from kafka import KafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

TOPIC = KAFKA_TOPIC

async def terima_data(data):
    try:
        payload = {
            "symbol": data.get("id"),
            "price": float(data.get("price")),
            "change": float(data.get("change")),
            "change_percent": float(data.get("change_percent")),
            "timestamp": int(data.get("time"))
        }
        producer.send(TOPIC, payload)
        print("sent to kafka:", payload)
    except Exception as e:
        print("error:", e)

async def main():
    client = AsyncWebSocket()
    await client.subscribe(["EURUSD=X"])
    await client.listen(terima_data)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Berhenti.")