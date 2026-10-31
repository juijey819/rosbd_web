import numpy as np
import pandas as pd


def load_data(path, freq="15min"):
    raw = pd.read_csv(path)
    raw["Date"] = pd.to_datetime(raw["Date"])
    raw = raw.sort_values("Date")
    raw = raw.drop_duplicates(subset="Date").set_index("Date")
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    df = raw[["Open", "High", "Low", "Close"]].resample(freq).agg(agg).dropna().reset_index()
    df.columns = [c.lower() for c in df.columns]
    return df[["date", "open", "high", "low", "close"]]


def add_features(df):
    h, l, c, o = df["high"], df["low"], df["close"], df["open"]
    df["body"] = abs(c - o)
    df["hl_range"] = h - l
    df["ret"] = c.pct_change()
    df["vol_20"] = df["ret"].rolling(20).std()

    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean().ffill().clip(lower=1e-10)

    for s in [10, 20, 50]:
        df[f"ema{s}"] = c.ewm(span=s, adjust=False).mean()

    delta = c.diff()
    ag = delta.clip(lower=0).rolling(7).mean()
    al = (-delta).clip(lower=0).rolling(7).mean()
    df["rsi"] = 100 - (100 / (1 + ag / al.replace(0, np.nan)))

    a = df["atr"]
    vol_mean = a.rolling(100).mean().ffill()
    vol_std = a.rolling(100).std().ffill().clip(lower=1e-10)
    df["vol_zscore"] = (a - vol_mean) / vol_std

    df["hour"] = df["date"].dt.hour

    price_pos = (c - df["ema50"]) / a.clip(lower=1e-10)
    df["trend_regime"] = "CHOP"
    df.loc[price_pos > 0.5, "trend_regime"] = "BULL"
    df.loc[price_pos < -0.5, "trend_regime"] = "BEAR"

    daily = df[["date", "close"]].copy()
    daily = daily.set_index("date").resample("1D").last().dropna()
    daily["d_ema50"] = daily["close"].ewm(span=50, adjust=False).mean()
    daily["d_trend"] = ((daily["close"] - daily["d_ema50"]) > 0).astype(int) * 2 - 1
    daily["d_trend"] = daily["d_trend"].fillna(0).astype(int).shift(1)

    df["date_only"] = df["date"].dt.date
    dm = daily[["d_trend"]].copy()
    dm.index = dm.index.date
    df = df.merge(dm, left_on="date_only", right_index=True, how="left")
    df = df.drop(columns=["date_only"])
    df["d_trend"] = df["d_trend"].fillna(0).astype(int)
    return df


class RealTimeMonitor:
    def update(self, row):
        atr = float(row.get("atr", 1e-10))
        rng = float(row.get("hl_range", 0))
        ret = float(row.get("ret", 0))
        vr = float(row.get("vol_20", 1e-10))

        spike = rng > max(atr * 2.5, 0.002) or abs(ret) > vr * 3.0

        vz = float(row.get("vol_zscore", 0))
        if vz > 1.0:
            vol_regime = "HIGH_VOL"
        elif vz < -0.8:
            vol_regime = "LOW_VOL"
        else:
            vol_regime = "MED_VOL"

        return dict(
            spike=spike,
            vol_regime=vol_regime,
            trend_regime=str(row.get("trend_regime", "CHOP")),
            atr=atr,
        )


class DecisionLayer:
    MAX_RAW = 3.0

    def compute(self, row, mon):
        s, why = 0.0, []
        atr = mon["atr"]
        e20 = row.get("ema20")
        e50 = row.get("ema50")
        c = row.get("close")

        # 1. Trend — primary driver
        if pd.notna(e20) and pd.notna(e50) and atr > 0:
            gap = abs(e20 - e50) / atr
            strength = min(gap * 3.0, 2.0)
            if e20 > e50:
                s += strength
                why.append(f"trend_bull_{gap:.2f}")
            else:
                s -= strength
                why.append(f"trend_bear_{gap:.2f}")

        # 2. RSI(7) — oversold/overbought confirmation
        r = row.get("rsi")
        if pd.notna(r):
            if r < 25:
                s += 0.8
                why.append("rsi_oversold")
            elif r > 75:
                s -= 0.8
                why.append("rsi_overbought")

        # 3. Price vs EMA20 — structure check
        if pd.notna(c) and pd.notna(e20) and atr > 0:
            gap = abs(c - e20) / atr
            aligned = (c > e20 > e50) or (c < e20 < e50)
            if aligned:
                pts = 0.6 if gap > 0.5 else (0.3 if gap > 0.2 else 0.15)
                direction = 1 if c > e20 else -1
                s += direction * pts
                why.append(f"struct_{'bull' if direction > 0 else 'bear'}_{gap:.2f}")

        # 4. Spike block — safety, prevent entry saat lonjakan
        if mon["spike"]:
            s = min(s, 0.0)
            why.append("spike_block")

        return dict(
            raw_score=round(s, 2),
            confidence=self._confidence(s, atr),
            reason=" | ".join(why),
            regime=(mon["trend_regime"], mon["vol_regime"]),
        )

    def _confidence(self, score, atr):
        if abs(score) < self.MAX_RAW * 0.12:
            return 0

        base = abs(score) / self.MAX_RAW * 100

        if atr < 0.00015:
            base *= 0.5

        tp_pips = (1.5 * atr) / 0.0001
        if tp_pips > 0:
            spread_ratio = 0.8 / tp_pips
            if spread_ratio > 0.3:
                base *= 0.3

        return round(max(0, min(100, base)), 0)


SPREAD_PIP = 0.00001


class SignalEngine:
    def __init__(self, decision, monitor, entry_thresh=2.0, spread=0.8):
        self.dl = decision
        self.mon = monitor
        self.entry = entry_thresh
        self.spread = spread * SPREAD_PIP
        self._position = "HOLD"
        self._entry_price = None

    def step(self, row):
        mon_snap = self.mon.update(row)
        dec = self.dl.compute(row, mon_snap)
        score = dec["raw_score"]
        atr = mon_snap["atr"]
        c = float(row.get("close", 0))

        signal = self._position
        conf = dec["confidence"]

        if self._position == "HOLD":
            if conf < 30:
                signal = "HOLD"
            elif score >= self.entry:
                signal = "BUY"
                self._entry_price = c
            elif score <= -self.entry:
                signal = "SELL"
                self._entry_price = c
        elif self._position == "BUY":
            sl = self._entry_price - 1.0 * atr
            tp = self._entry_price + 1.5 * atr
            if c <= sl or c >= tp:
                signal = "HOLD"
            elif score < 0.5:
                signal = "HOLD"
            elif score <= -self.entry:
                signal = "SELL"
                self._entry_price = c
            if signal == "HOLD":
                self._entry_price = None
        elif self._position == "SELL":
            sl = self._entry_price + 1.0 * atr
            tp = self._entry_price - 1.5 * atr
            if c >= sl or c <= tp:
                signal = "HOLD"
            elif score > -0.5:
                signal = "HOLD"
            elif score >= self.entry:
                signal = "BUY"
                self._entry_price = c
            if signal == "HOLD":
                self._entry_price = None

        self._position = signal

        sl = tp = 0.0
        if signal == "BUY":
            sl = round(c - 1.0 * atr, 5)
            tp = round(c + 1.5 * atr, 5)
        elif signal == "SELL":
            sl = round(c + 1.0 * atr, 5)
            tp = round(c - 1.5 * atr, 5)

        return dict(
            signal=signal,
            score=dec["raw_score"],
            confidence=dec["confidence"],
            reason=dec["reason"],
            regime=dec["regime"],
            entry=c,
            sl=sl,
            tp=tp,
            rr=round(1.5 / 1.0, 2) if signal != "HOLD" else 0,
            cost_pips=round(self.spread / SPREAD_PIP * 1.6, 1) if signal != "HOLD" else 0,
        )