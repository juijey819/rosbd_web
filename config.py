import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent


def _load_env_file():
    path = ROOT_DIR / ".env"
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _path_from_env(name, default):
    path = Path(os.getenv(name, default))
    return path if path.is_absolute() else ROOT_DIR / path


_load_env_file()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "forex_dashboard")

MODEL_DIR = _path_from_env("MODEL_DIR", "outputs")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9093")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "eurusd-stream")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5050")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ES_URL = os.getenv("ES_URL", "http://127.0.0.1:9200")
