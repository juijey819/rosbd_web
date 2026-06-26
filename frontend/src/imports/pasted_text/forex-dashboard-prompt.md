# FIGMA AI PROMPT — FOREX DASHBOARD, HUMAN-CRAFTED UI

Create a dark theme forex trading dashboard for a swing trader.

Canvas:

* Desktop frame 1440 × 900
* Background: #0D1117
* Use a 12-column grid with 32px outer margin and 20px gutters
* Keep the layout calm, readable, and intentional
* The interface should feel like a real trading tool used daily by a serious trader, not a generic AI-generated dashboard

Design direction:

* Professional dark trading terminal
* Minimal, focused, human-crafted
* Data-dense but not crowded
* Use spacing and hierarchy to guide the eye
* Avoid perfectly generic dashboard patterns
* Avoid decorative visuals, fake glossy effects, heavy shadows, gradients, or unnecessary icons
* Make the design feel hand-composed, with clear visual rhythm and believable data

Typography:

* Font: JetBrains Mono
* Use strong numeric hierarchy
* Prices should feel precise and important
* Labels should be small, calm, and useful
* Avoid oversized headings everywhere
* Use uppercase only for small labels, not for everything

Color system:

* Background: #0D1117
* Card surface: #161B22
* Secondary surface: #1C2333
* Border: #30363D
* Grid lines: #21262D
* Primary text: #F0F6FC
* Secondary text: #8B949E
* Muted text: #6E7681
* Green / bullish: #3FB950
* Red / bearish: #F85149
* Blue / actual price: #58A6FF
* Orange / actual model line: #F0883E
* Neutral gray: #8B949E

Do not use emojis. Use small colored status dots instead.

---

## TOP BAR

Create a compact top bar with strong alignment and enough breathing room.

Left side:

* Logo text: “ForexPro”
* Small outlined badge: “Swing Trader”
* Under it, show selected pair indicator:

  * Small EU + US flag mark or subtle currency icon
  * “EUR/USD” bold 20px
  * Small muted label: “Euro / US Dollar”

Right side:

* Small green status dot + “LIVE”
* Timestamp: “24 Jun 2026, 14:32 UTC”
* Small muted label below: “Data refreshes every 5s”

Keep the top bar clean. It should feel like a product header, not a landing page header.

---

## SECTION 1 — REAL-TIME SIGNAL

Create one full-width prominent card.

Card style:

* Background: #161B22
* Border: 1px solid #30363D
* Border radius: 12px
* Padding: 24px
* Add a subtle 3px left accent border matching the current signal color
* No decorative glow; the accent should be restrained and premium

Layout:
Use 3 horizontal areas, but not equal visual weight:

* Left area: pair information
* Center area: price, visually dominant
* Right area: signal and confidence

Left area:

* “EUR/USD” bold 28px, #F0F6FC
* Below: “Spread 0.8 pip” small, #8B949E
* Below that: “London session active” very small, #6E7681

Center area:

* Current price: “1.10845”
* 48px bold, #F0F6FC
* Align this area visually as the main focal point
* Below price: “+12.3 pips” in #3FB950
* Add tiny muted context: “since daily open”

Right area:

* Large pill badge:

  * BUY: background #3FB950, dark text
  * SELL: background #F85149, white text
  * HOLD: background #8B949E, dark text
* Current state: BUY
* Below badge: “Confidence 78%”
* Below that: small muted text “Signal updated 2 min ago”

Bottom row inside card:
Create 4 compact info chips across the bottom, separated by thin borders:

* ATR: 0.0008
* Vol Regime: Normal
* RSI(7): 62
* Signals Today: 14

These chips should feel useful, not decorative. Keep labels muted and values bright.

---

## SECTION 2 — 7-DAY FORECAST

Create a full-width section below the signal card.

Section header:

* Left: “7-Day Forecast”
* Under title: small muted text “Forecast based on recent swing structure”
* Right: small green outlined pill “Backtest accuracy 92%”
* Make the badge subtle, not promotional

Main layout:

* Left chart area: 70%
* Right forecast data card: 30%
* Use 20px gap between chart and card

Left card — Forecast chart:

* Background: #161B22
* Border: 1px solid #30363D
* Border radius: 12px
* Padding: 20px

Chart details:

* Show last 30 days of actual price as a solid blue line
* Show next 7 days forecast as a dashed green line
* Add a thin vertical divider where forecast begins
* Add a very subtle green projection zone behind the forecast area
* Do not make the line too smooth; make it feel like real market movement with small irregular changes
* X-axis: compact dates
* Y-axis: price values
* Grid lines: #21262D
* Add one small hover tooltip:

  * Date
  * Price
  * Forecast label if in forecast area

Legend:

* Actual Price
* Forecast
* Projection Zone

Right card — Forecast data:

* Background: #161B22
* Border: 1px solid #30363D
* Border radius: 12px
* Padding: 20px

Content:

* Last Close: 1.10845
* Forecast 7D: 1.11230
* Change: +0.35%
* Direction: Bullish

Direction should use a small green dot and a subtle pill, not an emoji.

Small prediction table:

* Day 1, Mon: 1.10910
* Day 2, Tue: 1.10980
* Day 3, Wed: 1.11045
* Day 4, Thu: 1.11100
* Day 5, Fri: 1.11160
* Day 6, Sat: Market closed
* Day 7, Sun: Market closed

Use muted gray for day labels and bold white for price values.
Weekend rows should look disabled but still readable.

---

## SECTION 3 — PREDICTED VS ACTUAL

Create a full-width model performance section.

Section header:

* Left: “Model Performance”
* Small subtitle: “Ridge Regression · recent prediction fit”
* Keep this section analytical and understated

Main card:

* Background: #161B22
* Border: 1px solid #30363D
* Border radius: 12px
* Padding: 20px

Chart:

* Line chart comparing actual price and predicted price
* Solid orange line = actual price
* Dashed blue line = model predicted price
* Keep both lines close but not identical
* Add small visible prediction error gaps in a few places so it feels believable
* X-axis: dates
* Y-axis: price
* Grid lines: #21262D
* Add a small legend in the top-right of the chart

Below chart:
Create 3 compact metric cards in one row:

1. R² Score

   * Value: 0.93
   * Green status: “Strong fit”

2. MAE

   * Value: 0.0094
   * Green status: “Low error”

3. RMSE

   * Value: 0.0120
   * Green status: “Stable”

Metric cards should be quiet and analytical. Do not make them look like marketing stats.

---

## HUMAN-CRAFT DETAILS

Make the design feel manually crafted by following these rules:

* Use consistent spacing, but avoid making every section feel mechanically identical
* Keep chart labels small and realistic
* Use believable forex numbers and minor decimal variations
* Do not overuse bright colors
* Leave enough negative space around the main price and signal
* Make inactive or secondary information clearly quieter
* Use subtle separators instead of heavy boxes everywhere
* Align numbers carefully by decimal feel
* Avoid generic dashboard filler text
* Avoid random icons
* Avoid perfectly symmetrical composition when hierarchy should be stronger
* Every visible element should have a reason to exist

Final visual impression:
A polished, calm, serious forex analytics dashboard that feels designed by a thoughtful UI/UX designer for real swing traders.
