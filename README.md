# ROSBD Web

Dashboard forex untuk forecast 7 hari dan sinyal real-time. Repositori ini berisi
backend FastAPI, frontend React/Vite, pipeline training dan forecasting, serta
pipeline streaming Kafka dan Spark.

## Alur sistem

Forecast harian:

```
yfinance -> retrain_flow.py / predict.py -> MongoDB (raw_prices, forecasts)
                                                |
                                                v
                                        FastAPI -> React dashboard
```

Sinyal real-time:

```
yfinance websocket -> kafka-prod.py -> Kafka -> spark_consumer.py
                                                   |-> signal_engine.py
                                                   |-> Telegram
                                                   |-> Elasticsearch (opsional)
                                                   |-> POST /api/signal -> FastAPI
```

## Komponen

| Path | Fungsi |
| --- | --- |
| `backend/main.py` | API forecast dan sinyal. Forecast dibaca dari MongoDB, sinyal real-time disimpan di memori. |
| `frontend/` | Dashboard React/Vite. Proxy `/api` diarahkan ke backend port 5050. |
| `predict.py` | Sinkronisasi data harian, load model, dan simpan forecast ke MongoDB. |
| `retrain_flow.py` | Pipeline Prefect untuk sinkronisasi data, training Ridge multi-horizon, dan regenerasi forecast. |
| `features.py` | Definisi fitur yang dipakai model. |
| `outputs/` | Model, daftar fitur, dan metrik hasil training. |
| `kafka-prod.py` | Producer data tick EUR/USD ke Kafka. |
| `spark_consumer.py` | Konsumen Spark Structured Streaming untuk agregasi OHLC, deteksi spike, dan sinyal 5 menit. |
| `signal_engine.py` | Logika indikator dan state machine sinyal. |
| `es_logger.py` | Pengiriman log ke Elasticsearch. Bersifat opsional. |
| `notebooks/` | Notebook training dan evaluasi model EUR/USD, GBP/USD, dan CHF/USD. |
| `docker-compose.yml` | Kafka dan Zookeeper. |
| `docker-compose-spark.yml` | Container PySpark. |

## Prasyarat

- Python 3.10 atau lebih baru
- Node.js 18 atau lebih baru
- Docker dan Docker Compose
- MongoDB, lokal atau Atlas
- Elasticsearch, hanya jika ingin menyimpan log streaming

## Konfigurasi

Salin file contoh konfigurasi:

```powershell
Copy-Item .env.example .env
```

Isi variabel berikut di `.env`:

| Variabel | Keterangan |
| --- | --- |
| `MONGO_URI` | Connection string MongoDB. |
| `MONGO_DB` | Nama database. Default `forex_dashboard`. |
| `MODEL_DIR` | Direktori model dan fitur. Default `outputs`. |
| `CORS_ORIGINS` | Origin frontend yang diizinkan, dipisahkan koma. |
| `KAFKA_BOOTSTRAP_SERVERS` | Alamat Kafka dari proses yang berjalan. Default `localhost:9093`. |
| `KAFKA_TOPIC` | Topic data tick. Default `eurusd-stream`. |
| `BACKEND_URL` | URL backend yang diakses Spark untuk mengirim sinyal. |
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram. Kosongkan jika tidak dipakai. |
| `TELEGRAM_CHAT_ID` | ID chat Telegram tujuan. |
| `ES_URL` | URL Elasticsearch. Kosongkan jika tidak dipakai. |

File `.env` tidak boleh di-commit. `.env.example` hanya berisi placeholder.

## Instalasi

Backend dan pipeline:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

## Menjalankan forecast

Model yang ada di `outputs/` sudah bisa dipakai langsung. Untuk melatih ulang
dan membuat forecast baru:

```powershell
python retrain_flow.py
```

Perintah tersebut menjalankan sinkronisasi data dari yfinance, training model
Ridge untuk EUR/USD, GBP/USD, dan CHF/USD, menyimpan model ke `outputs/`, lalu
memperbarui collection `forecasts` di MongoDB.

Untuk membuat forecast harian tanpa training:

```powershell
python predict.py
```

Untuk menjalankan retrain sebagai layanan Prefect dengan jadwal 02.00:

```powershell
python retrain_flow.py --serve
```

Notebook di `notebooks/` dipakai untuk eksperimen dan evaluasi. Pipeline produksi
tetap berada di `retrain_flow.py` dan `predict.py`.

## Menjalankan dashboard

Backend:

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 5050
```

Frontend:

```powershell
cd frontend
npm run dev -- --port 5173
```

Buka `http://localhost:5173`.

Di Windows, backend dan frontend bisa dijalankan sekaligus dengan:

```powershell
.\run.ps1
```

## Menjalankan pipeline real-time

1. Jalankan Kafka dan Zookeeper.

```powershell
docker compose up -d
```

2. Jalankan producer tick.

```powershell
python kafka-prod.py
```

3. Jalankan container Spark.

```powershell
docker compose -f docker-compose-spark.yml up -d
```

4. Kirim job Spark ke container.

```powershell
docker exec pyspark-container bash -c "cd /home/jovyan/work && spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_consumer.py"
```

`docker-compose-spark.yml` mengatur `KAFKA_BOOTSTRAP_SERVERS` ke
`host.docker.internal:9093`, `BACKEND_URL` ke `host.docker.internal:5050`, dan
`ES_URL` ke `host.docker.internal:9200`. Jika Spark dijalankan langsung di host,
ubah nilai tersebut menjadi `localhost` lewat `.env`.

Elasticsearch tidak wajib. Jika `ES_URL` tidak dapat dihubungi, logger akan
menonaktifkan pengiriman log dan pipeline tetap berjalan.

## Endpoint API

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| GET | `/health` | Status backend. |
| GET | `/api/pairs` | Daftar pair yang tersedia. |
| GET | `/api/forecast/{pair_id}` | Forecast terakhir untuk `eur-usd`, `gbp-usd`, atau `chf-usd`. |
| GET | `/api/signal/{pair_id}` | Sinyal terakhir yang diterima dari Spark. |
| POST | `/api/signal` | Menerima sinyal dari Spark. |

Contoh:

```powershell
curl http://localhost:5050/api/forecast/eur-usd
curl http://localhost:5050/api/signal/eur-usd
```

## Model dan data

Model forecast adalah Ridge regression multi-output untuk horizon 1 sampai 7
hari. Setiap pair memiliki model dan daftar fitur sendiri di `outputs/`.
Fitur mencakup return, lag, moving average, volatilitas, RSI, komponen hari,
MACD, dan regime volatilitas.

Data harian disimpan di collection `raw_prices`. Hasil forecast disimpan di
collection `forecasts`. Sinyal real-time tidak disimpan di MongoDB; data tersebut
berada di memori backend dan akan kembali ke `HOLD` setelah backend restart.

Metrik evaluasi model per pair tersedia di `outputs/metrics_*.csv`.

## Struktur repositori

```
.
|-- backend/
|   `-- main.py
|-- frontend/
|-- notebooks/
|-- outputs/
|-- config.py
|-- docker-compose.yml
|-- docker-compose-spark.yml
|-- es_logger.py
|-- features.py
|-- kafka-prod.py
|-- predict.py
|-- requirements.txt
|-- retrain_flow.py
|-- run.ps1
|-- signal_engine.py
`-- spark_consumer.py
```

## Catatan

- Producer dan consumer saat ini hanya memproses EUR/USD.
- Backend menyimpan sinyal terakhir di memori, bukan di database.
- Forecast dihasilkan dari model statistik dan bukan rekomendasi investasi.
- Kredensial MongoDB, token Telegram, dan API key yang pernah ditulis langsung
  di kode harus dianggap bocor. Rotasi kredensial tersebut sebelum menggunakan
  repositori ini di lingkungan produksi.
