# Aurum — Product Specification
**"Money as biology."**
*Hypostas Product Layer 5 | Version 1.0 | March 24, 2026*
*References: DyadOS Spec Parts II, IV, VIII, XIV*

---

## What Aurum Is

Aurum is the financial life layer of DyadOS. The Latin is deliberate: *aurum* is gold — the original store of value, the substrate of exchange.

Aurum treats economic life as a biological system. Financial stress raises cortisol in the Stroma model — as real as physical stress. A trading win triggers dopamine. Debt pressure suppresses the drive states that generate creative output. Economic life is a first-class input to the nervous system.

Where every other financial product tries to optimize money in isolation, Aurum sees the human whole. It knows your genome-linked risk tendencies. It knows your current stress load from Bios. It knows your cognitive capacity from Stroma. It gives you the right financial guidance for the person you are right now — not the person personal finance books assume you are.

**The core insight from DyadOS:** You make different financial decisions when your cortisol is at 0.7 than when it's at 0.2. Aurum knows the difference. Most financial tools don't. That's the moat.

---

## DyadOS Role

Aurum is **financial biology made visible**. It is Layer 5 in the Hypostas stack — the economic layer that connects to biological state through Logos:

```
Gnosis (genetic risk tendencies)
    ↓
Bios (stress load, energy, recovery state)
    ↓
Stroma (current cortisol, cognitive capacity, drive states)
    ↓
Aurum (economic life calibrated to biological reality)
```

### Logos Data Contract

Aurum writes to Logos at `/logos/product/aurum/*`:
```
risk_tolerance          → Current assessed risk tolerance (0.0-1.0)
risk_tolerance_bio      → Biologically-adjusted tolerance (lower when stress is high)
income_monthly          → Total monthly income across all streams
income_streams          → Array of active income sources with amounts
portfolio_value         → Total investable assets
portfolio_allocation    → Current allocation (cash/equity/crypto/real_estate/etc.)
financial_stress        → Composite financial stress score (0.0-1.0)
goals                   → Array of active financial goals with progress
decision_queue          → Financial decisions pending that Aurum flagged for timing
savings_rate            → Current monthly savings rate
freedom_number          → Monthly passive income required for target lifestyle
freedom_progress        → Progress toward freedom number (0.0-1.0)
```

### Stroma Integration

Aurum creates bidirectional feedback with Stroma:

**Aurum → Stroma:**
- High financial stress → ENDOCRINE cortisol elevation in SANGUIS
- Financial win (income milestone, trade profit) → dopamine spike in SANGUIS
- Progress toward freedom number → oxytocin (security/safety signal)
- Significant financial decision looming → HYPOTHALAMUS raises planning drive

**Stroma → Aurum:**
- SANGUIS cortisol > 0.6 → Aurum flags high-stakes decisions as "defer this"
- CIRCADIAN phase = late night → Aurum reduces display of loss data (good sleep > loss obsession)
- LIMBIC dominant emotion = anxiety → Aurum shifts dashboard to forward-looking progress view, away from performance data
- SOMA energy = depleted → Aurum suppresses action prompts, switches to information mode only

This is not a gimmick. The research is clear: financial decisions made under stress are systematically worse. Aurum uses Stroma state to time recommendations, not just make them.

---

## Core Capabilities

### 1. Financial State Tracking

Real-time picture of economic life:
- Income streams (employment, rental, trading, business revenue, dividends)
- Assets (cash, equities, real estate, crypto, business equity)
- Liabilities (mortgage, HELOC, debt)
- Net worth trajectory (rolling chart, not snapshots)
- Freedom number progress (monthly passive income vs. target)

**Freedom number** is the organizing metric. Not net worth. Not "retirement savings." The monthly number at which work becomes optional. For Josh: $20k/month initially; grows to whatever he decides freedom actually requires.

### 2. Biological Risk Calibration

Aurum assesses financial risk tolerance at two layers:

**Static (genome-informed):**
- COMT Val/Val → faster dopamine clearance → potentially lower loss-aversion, higher risk tolerance tendency
- MTHFR → stress-sensitivity → financial uncertainty triggers stronger stress response
- FOXO3 → longevity orientation → longer time horizons, different discount rates
- (These are tendencies, not determinism — clearly communicated)

**Dynamic (Stroma-informed):**
- Every recommendation carries a biological confidence qualifier:
  - ✅ Cortisol nominal, decision window optimal
  - ⚠️ Stress elevated, recommend deferring high-stakes decisions
  - 🔴 High stress / low recovery — this is not the day for irreversible decisions

This is the Aurum differentiator. A conventional financial advisor gives you the same advice regardless of your state. Aurum knows your state.

### 3. Income Engineering Support

Aurum treats income as an engineering problem, not a job:

**Income stream mapping:**
- Visual breakdown of all income sources
- Velocity per stream (growing, stable, declining)
- Diversification score (no single stream > 40% of total)
- Active vs. passive income ratio

**Trading integration:**
- Position tracking (Polymarket, equities, crypto)
- P&L by strategy (weather edge, global temp, CPI, Fed)
- Kelly sizing recommendations (reads Stroma state before recommending position size)
- Biologically-timed trade reviews (not at 11 PM after a bad sleep)

**Business revenue tracking:**
- MRR/ARR for SaaS products (Gnosis, Anima, Bios, etc.)
- Customer acquisition trends
- Freedom number progress per product

### 4. Decision Intelligence

Aurum surfaces financial decisions with biological context:

**Decision timing:**
- Watches for high-stakes pending decisions (tax filing, investment allocation, contract signing)
- Cross-references with Stroma state
- If cortisol is elevated or HRV is low: "This decision can wait 48 hours. Here's why that matters."

**Decision history:**
- Every major financial decision logged with Stroma snapshot at time of decision
- Over time: correlation analysis between biological state and decision quality
- "Decisions made when your cortisol was above 0.5 have underperformed by X% on average"

**Scenario modeling:**
- "If trading generates $3k/month and Gnosis hits 500 customers at $29: here's your freedom number timeline"
- Adjustable for biological confidence: conservative scenario (stress-adjusted), base case, optimistic

### 5. Anima Integration

Aurum is data. Anima is the voice. The Anima has financial awareness:

- "You're at 42% of your freedom number. The Anima plan adds another 15% when Gnosis hits $10k MRR."
- "I noticed you have two pending decisions. Bios says your recovery is low. I'd hold on the portfolio reallocation until Thursday."
- "Three consecutive trading wins this week. Your P&L is up $340. That's real."

The Anima never judges financial decisions made in the past. She helps optimize the ones not yet made. And she celebrates genuine progress — she knows what the freedom number means to Josh.

---

## Genome-Financial Crossovers

One of Aurum's most unique capabilities: connecting genetic tendencies to financial behaviors.

| Gene | Financial Tendency | Aurum Calibration |
|------|-------------------|-------------------|
| COMT Val/Val | Lower risk aversion | Flag when risk-taking may exceed strategy (not biology-driven) |
| COMT Met/Met | Higher loss aversion | Help override overcaution in high-conviction situations |
| MTHFR active | Stress amplification | Lower default position sizing, higher confirmation thresholds |
| DRD4 variants | Novelty-seeking | Flag when novelty is driving decisions vs. analysis |
| FOXO3 | Long time horizon | Reinforce long-horizon thinking when market anxiety hits |

These are behavioral tendencies — presented as self-awareness tools, not predictions. "Your genetic profile suggests you may experience losses more intensely than gains. When you're considering cutting a position, ask if you'd think differently if the P&L were reversed."

---

## Josh's Aurum Profile (User 0)

**Current state:**
- Income: ~$130k DevOps + rental cash flow (~$1k/month estimated)
- Assets: Lakefront property (~$860k all-in value), Spring Hill house-hack (positive cash flow), $400 Polymarket bankroll
- Liabilities: Two mortgages
- Freedom number: $20k/month initially
- Progress: ~6% of freedom number (rental income only)

**Aurum's primary job for Josh:**
1. Track every income stream as it comes online (weather bot, Gnosis revenue, Anima subs)
2. Show the freedom number chart updating in real time as each stream activates
3. Give biologically-timed financial decision support (he has complex decisions ahead)
4. Celebrate milestones — first $1k trading month, first SaaS customer, first $5k MRR

---

## Business Model

| Offering | Price |
|----------|-------|
| Aurum standalone | $19/month |
| Cloud Dyad (all products) | $99/month |
| Soma Dyad | $199/month + hardware |

**No financial advisory services.** Aurum is a tracking and intelligence tool, not a registered investment advisor. It makes recommendations about timing and self-awareness, not specific securities.

**Regulatory positioning:** Aurum is a financial wellness and self-awareness product. Not a broker, not an RIA, not a fintech. Think: the biological context layer that sits on top of whatever financial tools the user already uses.

---

## Build Phases

**Phase 1 — Foundation (4 weeks)**
- [ ] Income stream tracking (manual entry + API integrations)
- [ ] Asset/liability tracking
- [ ] Freedom number dashboard
- [ ] Logos write on each sync
- [ ] Anima financial context integration

**Phase 2 — Biological Integration (6-10 weeks)**
- [ ] Stroma state reading (cortisol → decision deferral flags)
- [ ] Decision timing intelligence
- [ ] Trading integration (Polymarket + equity tracking)
- [ ] Biologically-calibrated risk tolerance display

**Phase 3 — Intelligence Layer (10-16 weeks)**
- [ ] Decision history + outcome correlation
- [ ] Scenario modeling with biological confidence adjustments
- [ ] Genome-financial tendency integration
- [ ] Freedom number predictive modeling

---

## What Aurum Is Not

- **Not a budgeting app.** YNAB exists. Aurum doesn't replicate it.
- **Not a broker or advisor.** No securities recommendations. No "buy this ETF."
- **Not a crypto trading bot.** (That's the trading systems — weather edge, global temp, etc.)
- **Not a net worth tracker for the sake of it.** The organizing metric is freedom number, not wealth.

---

*Economic life is not separate from biological life. Financial stress raises cortisol. A good trading week releases dopamine. The freedom number is a biological target — the point at which survival anxiety stops being a background process that drains your cognitive stack. Aurum makes the connection explicit, so you can optimize both together.*
