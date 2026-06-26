# FIGMA AI EVALUATION PROMPT — UI/UX IMPROVEMENT NOTES

Evaluate and adjust the current forex dashboard design based on these UI/UX directions.

Do not redesign everything from scratch. Improve the existing structure so it feels cleaner, simpler, more modern, more human-crafted, and easier to read.

MAIN DESIGN CHANGE:
Move away from dark futuristic trading-terminal style.
Use a clean modern light theme instead.

Visual direction:

* Simple, clean, modern, calm, and easy to look at
* Human-crafted dashboard, not AI-generated dashboard
* Avoid futuristic, cyber, neon, overly technical styling
* Avoid tiny font sizes
* Prioritize readability, trust, and clarity
* Use more whitespace and softer card layouts
* Make the product feel friendly but still professional

Suggested light theme:

* Page background: #F6F8FA or #F8FAFC
* Main card background: #FFFFFF
* Secondary card background: #F1F5F9
* Border: #E2E8F0
* Primary text: #0F172A
* Secondary text: #64748B
* Muted text: #94A3B8
* Green: #16A34A
* Red: #DC2626
* Blue: #2563EB
* Orange: #EA580C

Typography:

* Replace small terminal-style typography with a readable modern font
* Use Inter, Geist, or SF Pro instead of JetBrains Mono
* Minimum body font size should be 14px
* Important numbers should be 32–44px, not too compressed
* Labels should be readable and not overly tiny
* Use clear hierarchy between title, subtitle, metric, and helper text

USER FLOW:
The first screen should feel like a Home Page, not immediately a complex dashboard.

HOME PAGE STRUCTURE:

1. Top header

   * Logo: “ForexPro”
   * Small subtitle: “Swing trading forecast assistant”
   * Right side: system status and timestamp

2. Overview system section

   * Title: “Forex Market Overview”
   * Short friendly description:
     “View forecast, signal, and model performance for selected currency pairs.”
   * Add 3–4 simple overview cards:

     * Available Pair: EUR/USD
     * Forecast Window: 7 Days
     * Signal Type: Scalp Signal
     * Model: Ridge Regression

3. Pair selection area
   User should choose which pair they want to analyze.
   Use either:

   * Clean pair cards, or
   * A simple horizontal slide panel

PAIR SELECTION CARDS:
Create three pair cards:

* EUR/USD
* GBP/USD
* CHF/USD

EUR/USD:

* Active and available
* Show small status: “Available”
* CTA button: “Open Dashboard”

GBP/USD:

* Disabled or coming soon state
* Status: “Not available yet”
* CTA button disabled

CHF/USD:

* Disabled or coming soon state
* Status: “Not available yet”
* CTA button disabled

The pair cards should feel clickable, clean, and spacious.
Do not make them look like crypto/trading neon cards.

DASHBOARD PAGE:
After user selects EUR/USD, show the dashboard content.

IMPORTANT:
Only EUR/USD currently has signal data.

For GBP/USD and CHF/USD dashboard:

* Keep the dashboard page accessible
* But inside the Signal card, show an empty state:
  “Signal not available yet”
  “Scalp signal is currently only available for EUR/USD.”
* Do not show fake BUY/SELL/HOLD signal for GBP/USD or CHF/USD

SIGNAL SECTION:
Add a clear title above the signal card:
“Scalp Signal”

Under the title, add a small disclaimer:
“Signal is generated from short-term market indicators and should not be treated as financial advice.”

Signal card for EUR/USD:

* Show pair name
* Show current price
* Show BUY / SELL / HOLD badge
* Show confidence
* Keep layout simple and readable
* Avoid overloading the card with too many small metrics

For unavailable pairs:

* Show a calm empty state inside the card
* Use soft gray icon or simple placeholder
* Text:
  “Signal not available yet”
  “Currently, scalp signal is only supported for EUR/USD.”
* Do not use red warning styling because this is not an error

7-DAY FORECAST SECTION:
Add a disclaimer near the section title:
“Forecast is based on historical price patterns and model output. It does not guarantee future market movement.”

Keep the forecast chart clean:

* Use fewer grid lines
* Use readable axis labels
* Avoid over-detailed chart decoration
* Make the chart look like a product dashboard, not a finance terminal

MODEL PERFORMANCE SECTION:
Keep this section but make it more beginner-friendly.
Use title:
“Model Performance”

Subtitle:
“Recent prediction fit using Ridge Regression.”

Metrics:

* R² Score
* MAE
* RMSE

Add helper text:
“These metrics help estimate how closely the model follows recent market movement.”

HUMAN-CRAFT UI RULES:

* Use generous spacing
* Use soft cards
* Use clear labels
* Use readable font sizes
* Avoid crowded technical layouts
* Avoid unnecessary badges
* Avoid fake complexity
* Avoid too many colors competing at once
* Make empty states feel intentional
* Make the dashboard understandable for a first-time user
* Make the design feel like a real SaaS product for forex forecasting, not an AI-generated concept screen

FINAL GOAL:
The result should feel like a clean, modern forex web app where users first understand the system, choose a currency pair, and then view forecast, scalp signal, and model performance in a readable and trustworthy way.
