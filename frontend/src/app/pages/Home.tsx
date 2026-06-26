import { useNavigate } from "react-router";
import { C } from "../data";
import { ArrowRight, Activity } from "lucide-react";

const pairs = [
  { id: "eur-usd", label: "EUR/USD", desc: "Euro / US Dollar" },
  { id: "gbp-usd", label: "GBP/USD", desc: "British Pound / US Dollar" },
  { id: "chf-usd", label: "CHF/USD", desc: "Swiss Franc / US Dollar" },
];

export function Home() {
  const navigate = useNavigate();

  return (
    <div style={{ paddingBottom: 64 }}>
      <div style={{ marginBottom: 48 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 8, letterSpacing: "-0.02em" }}>
          Forex Market Overview
        </h1>
        <p style={{ fontSize: 15, color: C.secondary, marginBottom: 24, maxWidth: 600 }}>
          View forecast, signal, and model performance for selected currency pairs.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          {[
            { label: "Available Pairs", value: "EUR, GBP, CHF" },
            { label: "Forecast Window", value: "7 Days" },
            { label: "Signal Type", value: "Scalp Signal" },
            { label: "Model", value: "Ridge Regression" },
          ].map((stat, i) => (
            <div key={i} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: "16px 20px", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
              <div style={{ fontSize: 12, color: C.secondary, marginBottom: 4, fontWeight: 500 }}>{stat.label}</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: C.text }}>{stat.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 16, letterSpacing: "-0.01em" }}>
          Select a Currency Pair
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
          {pairs.map((p) => (
            <div key={p.id} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24, boxShadow: "0 4px 6px -1px rgba(0,0,0,0.05)", display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: C.text, letterSpacing: "-0.02em" }}>{p.label}</div>
                  <div style={{ fontSize: 14, color: C.secondary, marginTop: 2 }}>{p.desc}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 4, background: "#DCFCE7", color: C.green, padding: "4px 8px", borderRadius: 6, fontSize: 12, fontWeight: 500 }}>
                  <Activity size={14} />
                  <span>Active</span>
                </div>
              </div>
              <div style={{ marginTop: "auto" }}>
                <button
                  onClick={() => navigate(`/dashboard/${p.id}`)}
                  style={{ width: "100%", background: C.blue, color: "#fff", border: "none", borderRadius: 8, padding: "12px 16px", fontSize: 14, fontWeight: 500, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
                  onMouseOver={(e) => (e.currentTarget.style.background = "#1D4ED8")}
                  onMouseOut={(e) => (e.currentTarget.style.background = C.blue)}
                >
                  Open Dashboard
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
