export const C = {
  bg: "#F8FAFC",
  card: "#FFFFFF",
  surface2: "#F1F5F9",
  border: "#E2E8F0",
  grid: "#E2E8F0",
  text: "#0F172A",
  secondary: "#64748B",
  muted: "#94A3B8",
  green: "#16A34A",
  red: "#DC2626",
  blue: "#2563EB",
  orange: "#EA580C",
};

export function makeActualData() {
  const base = 1.10200;
  const days: { date: string; price: number; label: string }[] = [];
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
  let val = base;
  for (let i = 29; i >= 0; i--) {
    const d = new Date(2026, 5, 24 - i);
    const month = months[d.getMonth()];
    const day = d.getDate();
    val += (Math.random() - 0.48) * 0.00120 + (Math.random() - 0.5) * 0.00060;
    val = Math.max(1.0960, Math.min(1.1200, val));
    days.push({
      date: `${day} ${month}`,
      price: parseFloat(val.toFixed(5)),
      label: "actual",
    });
  }
  return days;
}

export function makeForecastData(lastPrice: number) {
  const dayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const prices = [1.10910, 1.10980, 1.11045, 1.11100, 1.11160, null, null];
  return dayLabels.map((d, i) => ({ day: d, price: prices[i], dayNum: i + 1 }));
}

export function makeModelPerfData() {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
  const data: { date: string; actual: number; predicted: number }[] = [];
  let actual = 1.0980;
  for (let i = 29; i >= 0; i--) {
    const d = new Date(2026, 5, 24 - i);
    actual += (Math.random() - 0.47) * 0.00110 + (Math.random() - 0.5) * 0.00050;
    actual = Math.max(1.095, Math.min(1.118, actual));
    const err = (Math.random() - 0.5) * 0.0018;
    const predicted = parseFloat((actual + err).toFixed(5));
    data.push({
      date: `${d.getDate()} ${months[d.getMonth()]}`,
      actual: parseFloat(actual.toFixed(5)),
      predicted,
    });
  }
  return data;
}
