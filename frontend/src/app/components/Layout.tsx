import { Outlet } from "react-router";
import { C } from "../data";
import { Clock, Activity } from "lucide-react";

export function Layout() {
  return (
    <div
      style={{
        background: C.bg,
        minHeight: "100vh",
        fontFamily: "'Inter', system-ui, sans-serif",
        color: C.text,
      }}
    >
      <div style={{ maxWidth: 1080, margin: "0 auto", padding: "0 32px" }}>
        {/* ── TOP BAR ── */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "24px 0",
            borderBottom: `1px solid ${C.border}`,
            marginBottom: 32,
          }}
        >
          {/* Left */}
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: C.blue,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#fff",
                }}
              >
                <Activity size={18} strokeWidth={2.5} />
              </div>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", lineHeight: 1.2 }}>
                  ForexPro
                </div>
                <div style={{ fontSize: 13, color: C.secondary, marginTop: 2 }}>
                  Swing trading forecast assistant
                </div>
              </div>
            </div>
          </div>

          {/* Right */}
          <div style={{ textAlign: "right", display: "flex", alignItems: "center", gap: 12 }}>
          </div>
        </div>

        {/* ── MAIN CONTENT ── */}
        <Outlet />
      </div>
    </div>
  );
}
