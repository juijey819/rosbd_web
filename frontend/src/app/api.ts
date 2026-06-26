export interface HistoryDay {
  date: string;
  close: number;
}

export interface ForecastDay {
  day: number;
  date: string;
  price: number;
}

export interface PerformancePoint {
  date: string;
  actual: number;
  predicted: number;
}

export interface ForecastMetrics {
  mae: number;
  direction_accuracy: number;
}

export interface ForecastData {
  pair: string;
  last_date: string;
  last_close: number;
  forecast_price: number;
  change_pct: number;
  history_30d: HistoryDay[];
  forecast_7d: ForecastDay[];
  performance: PerformancePoint[];
  metrics?: ForecastMetrics;
}

export interface SignalData {
  signal: string;
  score: number;
  confidence: number;
  regime: string;
  reason: string;
  price: number;
  atr: number | null;
  rsi: number | null;
  entry: number | null;
  sl: number | null;
  tp: number | null;
  rr: number | null;
  timestamp: string;
}

export async function fetchForecast(pairId: string): Promise<ForecastData> {
  const res = await fetch(`/api/forecast/${pairId}`);
  if (!res.ok) throw new Error("Forecast not available");
  return res.json();
}

export async function fetchSignal(pairId: string): Promise<SignalData> {
  const res = await fetch(`/api/signal/${pairId}`);
  if (!res.ok) throw new Error("Signal not available");
  return res.json();
}
