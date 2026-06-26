import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
  Area,
  ComposedChart,
} from "recharts";
import { ArrowLeft, Info, AlertCircle } from "lucide-react";
import { C } from "../data";
import { fetchForecast, fetchSignal, ForecastData, SignalData } from "../api";

const PAIRS = [
  { id: "eur-usd", label: "EUR/USD" },
  { id: "gbp-usd", label: "GBP/USD" },
  { id: "chf-usd", label: "CHF/USD" },
];

function makeDateLabel(d: string) {
  const parts = d.split("-");
  if (parts.length !== 3) return d;
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${parseInt(parts[2])} ${months[parseInt(parts[1])-1]}`;
}

function ForecastTooltip({ active, payload, label, lastClose }: any) {
  if (!active || !payload?.length) return null;
  const price = payload.find((p: any) => p.dataKey === "price")?.value;
  const forecast = payload.find((p: any) => p.dataKey === "forecast")?.value;
  const val = price ?? forecast;
  if (!val) return null;
  const isForecast = forecast !== undefined && price === undefined;
  const change = lastClose ? val - lastClose : 0;
  const changePips = (change * 10000).toFixed(1);
  const changePct = lastClose ? ((change / lastClose) * 100).toFixed(2) : "0.00";
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 12px", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)", fontFamily: "'Inter', sans-serif" }}>
      <div style={{ color: C.secondary, fontSize: 12, marginBottom: 4, fontWeight: 500 }}>{label}</div>
      <div style={{ color: C.text, fontSize: 14, fontWeight: 600 }}>{val.toFixed(5)}</div>
      <div style={{ color: isForecast ? "#0D9488" : C.blue, fontSize: 11, marginTop: 2, fontWeight: 500 }}>
        {isForecast ? "Forecast" : "Actual"}
      </div>
      {lastClose && (
        <div style={{ color: change >= 0 ? C.green : C.red, fontSize: 12, marginTop: 4, fontWeight: 600 }}>
          {change >= 0 ? "+" : ""}{changePips}p ({changePct}%) from close
        </div>
      )}
    </div>
  );
}

function ModelTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const actual = payload.find((p: any) => p.dataKey === "actual")?.value;
  const predicted = payload.find((p: any) => p.dataKey === "predicted")?.value;
  const error = actual != null && predicted != null ? Math.abs(actual - predicted) * 10000 : null;
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 12px", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)", fontFamily: "'Inter', sans-serif" }}>
      <div style={{ color: C.secondary, fontSize: 12, marginBottom: 6, fontWeight: 500 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} style={{ color: p.color, fontSize: 13, marginBottom: 2, fontWeight: 500 }}>
          {p.dataKey === "actual" ? "Actual" : "Predicted"}: {p.value?.toFixed(5)}
        </div>
      ))}
      {error != null && (
        <div style={{ color: C.muted, fontSize: 11, marginTop: 4, fontWeight: 500 }}>
          Error: {"\u00B1"}{error.toFixed(1)}p
        </div>
      )}
    </div>
  );
}

export function Dashboard() {
  const { pairId } = useParams();
  const navigate = useNavigate();
  const pairTitle = pairId ? pairId.replace("-", "/").toUpperCase() : "EUR/USD";

  const [data, setData] = useState<ForecastData | null>(null);
  const [signal, setSignal] = useState<SignalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pairId) return;
    setLoading(true);
    setError(null);
    fetchForecast(pairId)
      .then((d) => setData(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [pairId]);

  useEffect(() => {
    if (!pairId) return;
    const poll = async () => {
      try {
        const s = await fetchSignal(pairId);
        if (s.signal) setSignal(s);
      } catch {}
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [pairId]);

  if (loading) {
    return (
      <div style={{ padding: 64, textAlign: "center", color: C.secondary, fontSize: 18 }}>
        Loading forecast data...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: 64, textAlign: "center", color: C.secondary }}>
        <AlertCircle size={32} style={{ margin: "0 auto 16px" }} />
        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
          {error || "No data available"}
        </div>
        <div style={{ fontSize: 14, color: C.muted, maxWidth: 400, margin: "0 auto" }}>
          Run <code>python predict.py</code> and restart backend.
        </div>
      </div>
    );
  }

  const actualData = data.history_30d.slice(-7).map((d) => ({
    date: makeDateLabel(d.date),
    rawDate: d.date,
    price: d.close,
  }));
  const lastActual = actualData[actualData.length - 1]?.price ?? data.last_close;

  const forecastDays = data.forecast_7d.map((d) => ({
    date: makeDateLabel(d.date),
    rawDate: d.date,
    price: undefined as number | undefined,
    forecast: d.price,
  }));

  const combinedChartData = [
    ...actualData.map((d) => ({
      date: d.date,
      rawDate: d.rawDate,
      price: d.price,
      forecast: undefined as number | undefined,
      forecastZone: undefined as number | undefined,
    })),
    ...forecastDays.map((d) => ({
      date: d.date,
      rawDate: d.rawDate,
      price: d.price,
      forecast: d.forecast,
      forecastZone: d.forecast,
    })),
  ];

  combinedChartData[actualData.length - 1] = {
    ...combinedChartData[actualData.length - 1],
    forecast: lastActual,
    forecastZone: lastActual,
  };

  const performanceData = (data as any).performance?.map((p: any) => ({
    ...p,
    date: makeDateLabel(p.date),
  })) ?? [];

  const metrics = data.metrics;
  const dirAcc = metrics ? (metrics.direction_accuracy * 100).toFixed(1) : null;
  const maePips = metrics ? (metrics.mae * 10000).toFixed(1) : null;

  const dirAccNum = dirAcc ? parseFloat(dirAcc) : null;
  const dirAccColor = dirAccNum !== null && dirAccNum >= 60 ? C.green : C.muted;

  const maePipsNum = maePips ? parseFloat(maePips) : null;

  const sig = signal?.signal;
  const isSignalReady = signal && signal.signal && signal.signal !== "NORMAL" && signal.score !== undefined && signal.confidence !== undefined;
  const signalBg = sig === "BUY" ? "#DCFCE7" : sig === "SELL" ? "#FEE2E2" : sig === "NORMAL" ? "#EFF6FF" : "#F1F5F9";
  const signalColor = sig === "BUY" ? C.green : sig === "SELL" ? C.red : C.secondary;

  const dirLabel = data.change_pct > 0.1 ? "Bullish" : data.change_pct < -0.1 ? "Bearish" : "Neutral";
  const dirEmoji = data.change_pct > 0.1 ? "\u2197" : data.change_pct < -0.1 ? "\u2198" : "\u2192";
  const dirBg = data.change_pct > 0.1 ? "#DCFCE7" : data.change_pct < -0.1 ? "#FEE2E2" : "#F1F5F9";
  const dirTextColor = data.change_pct > 0.1 ? C.green : data.change_pct < -0.1 ? C.red : C.secondary;
  const dirText = data.change_pct > 0.1 ? "Upward" : data.change_pct < -0.1 ? "Downward" : "Sideways";

  return (
    <div style={{ paddingBottom: 64 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <button onClick={() => navigate("/")} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, color: C.secondary, fontSize: 13, fontWeight: 500, padding: "6px 10px 6px 0" }}>
          <ArrowLeft size={15} />
          Back
        </button>
        <select
          value={pairId}
          onChange={(e) => navigate(`/dashboard/${e.target.value}`)}
          style={{ fontSize: 13, padding: "5px 10px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.card, color: C.text, fontWeight: 500, cursor: "pointer", outline: "none" }}
        >
          {PAIRS.map((p) => (
            <option key={p.id} value={p.id}>{p.label}</option>
          ))}
        </select>
      </div>

      <h1 style={{ fontSize: 28, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 4 }}>
        {pairTitle} Outlook
      </h1>
      <p style={{ fontSize: 14, color: C.secondary, marginBottom: 32 }}>
        {dirText} trend forecast for the next 7 days. {data.change_pct > 0 ? "+" : ""}{data.change_pct}% expected change.
      </p>

      {/* ── SECTION 1: SIGNAL ── */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, letterSpacing: "-0.01em" }}>Live Signal</h2>
          <p style={{ fontSize: 13, color: C.secondary, display: "flex", alignItems: "center", gap: 6, marginTop: 4 }}>
            <Info size={14} />
            Updates every 5 minutes from streaming data.
          </p>
        </div>

        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 32, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 14, color: C.secondary, fontWeight: 500 }}>Current Price</span>
              <span style={{ fontSize: 44, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", lineHeight: 1 }}>
                {signal?.price ? signal.price.toFixed(5) : data.last_close.toFixed(5)}
              </span>
              <span style={{ fontSize: 14, color: signalColor, fontWeight: 500, marginTop: 4 }}>
                {!signal ? "Waiting for signal..." :
                 signal.signal === "NORMAL" ? "No strong signal detected" :
                 isSignalReady ? `${signal.signal} \u00B7 Score ${signal.score} \u00B7 ${signal.confidence}% confidence` :
                 `${signal.signal} signal`}
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
              <div style={{ background: signalBg, color: signalColor, fontSize: 20, fontWeight: 700, letterSpacing: "0.02em", padding: "12px 32px", borderRadius: 12 }}>
                {signal?.signal || "\u2014"}
              </div>
              <div style={{ fontSize: 13, color: C.secondary, fontWeight: 500 }}>
                {signal?.reason || ""}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", marginTop: 24, paddingTop: 24, borderTop: `1px solid ${C.border}`, gap: 16 }}>
            {[
              { label: "ATR (14)", value: signal?.atr != null ? signal.atr.toFixed(4) : "\u2014" },
              { label: "Vol Regime", value: signal?.regime || "\u2014" },
              { label: "RSI(7)", value: signal?.rsi != null ? signal.rsi.toFixed(1) : "\u2014" },
              { label: "Last Updated", value: signal?.timestamp ? new Date(signal.timestamp).toLocaleTimeString() : "\u2014" },
            ].map((chip, i) => (
              <div key={chip.label} style={{ flex: 1, paddingLeft: i === 0 ? 0 : 20, borderLeft: i === 0 ? "none" : `1px solid ${C.border}` }}>
                <div style={{ fontSize: 12, color: C.secondary, fontWeight: 500, marginBottom: 4 }}>{chip.label}</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: C.text }}>{chip.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── SECTION 2: 7-DAY FORECAST ── */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, letterSpacing: "-0.01em" }}>7-Day Price Forecast</h2>
            <span style={{ fontSize: 13, fontWeight: 600, color: dirTextColor, background: dirBg, padding: "4px 12px", borderRadius: 20 }}>
              {dirLabel}
            </span>
          </div>
          <p style={{ fontSize: 13, color: C.secondary, marginTop: 4 }}>
            Last close: {data.last_close.toFixed(5)} {"\u2192"} Forecast: {data.forecast_price.toFixed(5)} ({data.change_pct > 0 ? "+" : ""}{data.change_pct}%)
          </p>
        </div>

        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={combinedChartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fill: C.secondary, fontSize: 12 }}
                tickLine={false}
                axisLine={{ stroke: C.border }}
                angle={-25}
                textAnchor="end"
                height={50}
                interval={0}
                dy={5}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fill: C.secondary, fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => v.toFixed(5)}
                width={75}
                dx={-10}
              />
              <Tooltip content={<ForecastTooltip lastClose={data.last_close} />} />
              <Area dataKey="forecastZone" fill={C.green} fillOpacity={0.2} stroke="none" isAnimationActive={false} />
              <Line dataKey="price" stroke={C.blue} strokeWidth={2.5} dot={false} isAnimationActive={false} />
              <Line dataKey="forecast" stroke="#0D9488" strokeWidth={3.5} strokeDasharray="6 3" dot={{ r: 5, fill: "#0D9488", stroke: "#FFF", strokeWidth: 1.5 }} isAnimationActive={false} />
              <ReferenceLine x={makeDateLabel(data.last_date)} stroke={C.muted} strokeDasharray="3 3" label={{ value: "Forecast Start", position: "top", fill: C.secondary, fontSize: 11 }} />
              <ReferenceLine y={data.last_close} stroke={C.muted} strokeDasharray="2 2" strokeOpacity={0.4} />
            </ComposedChart>
          </ResponsiveContainer>

          <div style={{ display: "flex", gap: 24, marginTop: 20, justifyContent: "center" }}>
            {[
              { color: C.blue, label: "Actual Price", dash: false, fill: false },
              { color: "#0D9488", label: "Forecast", dash: true, fill: false },
              { color: C.green, label: "Forecast Range", dash: false, fill: true },
            ].map((l) => (
              <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {l.fill ? (
                  <div style={{ width: 14, height: 10, background: l.color, opacity: 0.2, borderRadius: 2 }} />
                ) : l.dash ? (
                  <div style={{ width: 18, height: 0, borderTop: `2.5px dashed ${l.color}` }} />
                ) : (
                  <div style={{ width: 18, height: 2.5, background: l.color, borderRadius: 1 }} />
                )}
                <span style={{ fontSize: 12, color: C.secondary, fontWeight: 500 }}>{l.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── SECTION 3: MODEL ACCURACY ── */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, letterSpacing: "-0.01em" }}>Model Accuracy</h2>
          <p style={{ fontSize: 13, color: C.secondary, marginTop: 4 }}>
            Shows what the model predicted 7 days ago vs what actually happened over the last {performanceData.length} days.
          </p>
        </div>

        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fill: C.secondary, fontSize: 12 }}
                tickLine={false}
                axisLine={{ stroke: C.border }}
                angle={-25}
                textAnchor="end"
                height={50}
                interval={Math.max(1, Math.floor(performanceData.length / 6))}
                dy={5}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fill: C.secondary, fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => v.toFixed(5)}
                width={75}
              />
              <Tooltip content={<ModelTooltip />} />
              <Legend verticalAlign="top" align="right" wrapperStyle={{ fontSize: 12, paddingBottom: 16 }}
                formatter={(value: any) =>
                  value === "actual"
                    ? <span style={{ color: C.orange, fontWeight: 500 }}>Actual</span>
                    : <span style={{ color: C.blue, fontWeight: 500 }}>Predicted (7d ago)</span>
                }
              />
              <Line dataKey="actual" stroke={C.orange} strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line dataKey="predicted" stroke={C.blue} strokeWidth={2} strokeDasharray="4 4" dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>

          <div style={{ display: "flex", gap: 16, marginTop: 24, justifyContent: "center", flexWrap: "wrap" }}>
            <div style={{ flex: 1, maxWidth: 240, background: C.surface2, borderRadius: 12, padding: "16px 20px", textAlign: "center", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 13, color: C.secondary, fontWeight: 500, marginBottom: 4 }}>Direction Accuracy</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: dirAccColor, letterSpacing: "-0.02em" }}>{dirAcc ?? "\u2014"}%</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 6 }}>of directional predictions correct</div>
            </div>
            <div style={{ flex: 1, maxWidth: 240, background: C.surface2, borderRadius: 12, padding: "16px 20px", textAlign: "center", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 13, color: C.secondary, fontWeight: 500, marginBottom: 4 }}>Average Error (MAE)</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: C.text, letterSpacing: "-0.02em" }}>{maePips ?? "\u2014"}p</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 6 }}>typical distance from actual price</div>
            </div>
            <div style={{ flex: 1, maxWidth: 240, background: C.surface2, borderRadius: 12, padding: "16px 20px", textAlign: "center", border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 13, color: C.secondary, fontWeight: 500, marginBottom: 4 }}>Forecast Change</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: data.change_pct >= 0 ? C.green : C.red, letterSpacing: "-0.02em" }}>{data.change_pct > 0 ? "+" : ""}{data.change_pct}%</div>
              <div style={{ fontSize: 12, color: dirTextColor, marginTop: 6 }}>expected {dirText.toLowerCase()} over 7 days</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── DISCLAIMER ── */}
      <div style={{ fontSize: 12, color: C.muted, textAlign: "center", paddingTop: 16, borderTop: `1px solid ${C.border}` }}>
        <p style={{ margin: 0, lineHeight: 1.6 }}>
          <strong>Disclaimer:</strong> Forecasts and signals are statistical estimates based on historical data. They are not financial advice. Past performance does not guarantee future results. Trade at your own risk.
        </p>
      </div>
    </div>
  );
}
