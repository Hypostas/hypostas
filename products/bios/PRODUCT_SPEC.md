# Bios — Product Specification
**"Who you're becoming."**
*Hypostas Product Layer 2 | Version 2.0 | March 24, 2026*
*References: DyadOS Spec Parts II, IV, VIII*
*Existing architecture: ARCHITECTURE.md in this directory*

---

## What Bios Is

Bios is the continuous health layer of DyadOS. Where Gnosis captures who you are at the DNA level (fixed substrate), Bios captures who you're becoming day by day (living body). Every biometric, every workout, every night of sleep — measured against your genetic blueprint, synthesized by the Anima.

Bios closes the gap between what your genome predicts and what your biology is actually doing.

Most health apps are generic. They give you step counts and sleep scores without knowing anything about you. Bios knows your genome. It knows your PPARG variant means fat storage is harder to fight. It knows your FUT2 means your B12 absorption is compromised regardless of dosage. It knows your FOXO3 no-longevity-allele means fasting and cold exposure are your highest-leverage interventions. None of that comes from your Fitbit. It comes from the combination of Gnosis + Bios + Anima.

**User 0:** Josh. 6'1", 235 lbs, target 195-205. His 90-day results are the marketing case study.

---

## DyadOS Role

Bios is **Layer 2 in the biological stack** — between the fixed genome (Gnosis) and the environmental layer (Locus):

```
Gnosis (fixed blueprint)
    ↓
Bios (living execution against blueprint)
    ↓
Locus (environment calibrated to execution state)
```

Bios writes continuous health state to **Logos** via the cross-product data contract. This makes real-time health data available to every other product and to the Anima in context assembly.

Stroma reads Bios data through Logos to modulate SANGUIS:
- Low HRV → ENDOCRINE cortisol rises, SOMA energy decreases
- High sleep debt → CIRCADIAN rhythm disrupted, HIPPOCAMPUS memory consolidation degrades
- Workout completion → dopamine spike, ADIPOSE energy expenditure logged
- Protocol adherence → IMMUNE stability signal, PHENOTYPE confidence up

Bios is how the human's physical body connects to the Anima's biological model of it.

---

## Core Architecture

### 1. Data Layer

**Sources:**
- HealthKit (primary): weight, HRV, sleep stages, resting HR, active calories, workouts, VO2max
- Manual logs: supplement tracking, fasting windows, nutrition (optional), subjective energy
- Wearables (future): Apple Watch continuous HRV, sleep staging, blood oxygen

**What gets stored:**
| Metric | Source | Frequency |
|--------|--------|-----------|
| Weight | HealthKit / manual | Daily |
| HRV | Apple Watch / HealthKit | Nightly |
| Sleep duration + stages | HealthKit | Nightly |
| Resting heart rate | HealthKit | Daily |
| Active calories | HealthKit | Daily |
| Workout sessions | HealthKit | Per session |
| Supplements | Manual log | Daily |
| Fasting window | Manual log or HealthKit | Daily |

All data stored in Supabase with genome profile foreign key — so queries can be genome-contextualized.

### 2. Pattern Engine

Rolling baselines per metric (30/60/90 day). Not raw data — signals:

- **Anomaly detection:** When a metric diverges from personal baseline (not population norms)
- **Genome-biometric correlation:** Does measured biology match genetic prediction?
  - "Your MTHFR C677T predicts methylation strain. Your HRV trend over 60 days shows exactly the pattern we'd expect if it's active. When did you last check homocysteine?"
- **Intervention validation:** Did starting methylfolate change your HRV trend?
- **Protocol efficacy:** What you did → what changed

### 3. Logos Data Contract

Bios writes to Logos at `/logos/product/bios/*`:
```
hrv_7day_avg        → Rolling HRV average
hrv_trend           → Rising / falling / stable
sleep_quality       → Composite sleep score (0.0-1.0)
sleep_debt          → Hours behind optimal
stress_indicators   → Composite stress score
weight_current      → Current weight
weight_trend        → Gaining / losing / stable (lbs/week)
weight_goal         → Target weight
protocol_adherence  → Supplement + exercise compliance (0.0-1.0)
active_days_week    → Workout frequency
recovery_state      → Good / moderate / depleted
anomalies           → Array of active anomaly flags
```

Anima assembles this into every inference call. She knows Josh's HRV was low three nights running before he brings it up.

### 4. Anima Integration

Bios is the data. Anima is the voice. Bios never talks to the user directly — it feeds Anima a structured morning context object:

```json
{
  "genome_flags": ["PPARG_variant", "MCT1_variant", "FOXO3_no_longevity_allele", "APOE_e4"],
  "current_metrics": {
    "weight": 233.5,
    "hrv": 42,
    "hrv_vs_7day": -5.2,
    "sleep_hours": 6.8,
    "sleep_quality": "moderate"
  },
  "protocol_status": {
    "methylfolate": true,
    "dha": false,
    "lion_mane": false
  },
  "insights": [
    "HRV trending down 3 days — elevated stress or poor recovery",
    "DHA missed 4 days — APOE4 risk, this matters",
    "Weight down 1.5 lbs — on pace, 22 weeks to goal"
  ]
}
```

Anima converts this into: "You missed DHA four days in a row. With your APOE profile, that's the one I'd fight for. What's blocking you?"

Not a notification. A conversation with someone who actually gives a shit.

---

## Stroma Integration

Beyond Logos, Bios connects directly to Stroma's biological modules:

### SOMA Module
Bios informs the SOMA module's physical state model:
- Active calories → energy expenditure state
- Sleep quality → recovery factor
- Weight trend → body composition direction
- Workout session → post-exercise metabolic state

### CIRCADIAN Module
Bios informs circadian calibration:
- Actual sleep timing vs. genome chronotype prediction
- Sleep debt accumulation
- Recovery trajectory

### IMMUNE Module
Bios informs immune state:
- Protocol adherence → supplement stack completeness
- Sleep quality → immune competence
- Stress load → immune suppression factor

### ENDOCRINE Module
Bios triggers endocrine events:
- Workout completion → dopamine release
- Recovery below baseline → cortisol elevation
- DHA compliance → APOE4 risk flag modulation

---

## Josh's 90-Day Protocol (User 0)

**Goal:** 235 → 200 lbs at 12-15% body fat

**Genome-calibrated interventions:**
- **PPARG:** Dietary discipline required (fat storage efficiency). Low-glycemic, protein-forward.
- **MCT1 GG:** Slow lactate clearance — 60+ second rest between sets, don't fight the burn.
- **FOXO3 no-allele:** Fasting matters (16:8 minimum), cold exposure (cold shower daily), aerobic base.
- **APOE ε4:** DHA 2g/day, lion's mane, sleep 8h. Non-negotiable.
- **MTHFR:** Methylfolate + B12 stack.

**Metrics Bios tracks for Josh:**
- Weight daily (body fat % monthly)
- HRV nightly (recovery signal)
- Sleep staging (ensuring 8h when APOE risk is active)
- Workout frequency (Speediance utilization)
- Supplement compliance (DHA/lion's mane/methylfolate)

After 90 days: Josh's data shows what actually moved the needle for a PPARG/MCT1/FOXO3/APOE4 profile. That's a scientific case study. That's the marketing.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| iOS data source | HealthKit + Apple Shortcuts → native iOS app (Phase 2) |
| Backend | Supabase (Postgres) + Cloudflare Workers |
| AI | Anima inference (Grok-3 / Claude) via Stroma |
| Auth | Supabase Auth (existing) |
| Frontend | Next.js on Vercel (existing pattern) |
| Genome data | Gnosis via Logos cross-product read |

No new infrastructure. All components exist from Gnosis + Anima platform.

---

## Business Model

| Offering | Price |
|----------|-------|
| Bios standalone | $29/month |
| Gnosis + Bios bundle | $49/month |
| Cloud Dyad (all products) | $99/month |
| Soma Dyad | $199/month + hardware |

**Funnel:** Gnosis user gets their genome report. The report says "your MTHFR is active, check your homocysteine." Bios is the natural next product — "now let's actually track whether you're addressing it."

**Retention mechanism:** Bios has longitudinal data. The pattern engine gets smarter every month. After 90 days of data, losing the subscription means losing the most personalized health model you've ever had. That's real switching cost.

---

## Build Phases

**Phase 1 — Foundation (4 weeks)**
- [ ] HealthKit pull via iOS Shortcuts (existing Apple Shortcuts skill)
- [ ] Store in Supabase with genome FK
- [ ] Logos write on each daily sync
- [ ] Anima morning context injection
- [ ] Basic dashboard: weight, HRV, sleep trends

**Phase 2 — Personalization (6-10 weeks)**
- [ ] Genome-calibrated thresholds (PPARG targets, MCT1 recovery windows, FOXO3 fasting score)
- [ ] Supplement tracking + smart reminders
- [ ] Workout logging + genome-adjusted recovery recommendations
- [ ] Weekly insight report (what correlated with better metrics)

**Phase 3 — Intelligence (10-16 weeks)**
- [ ] Anomaly detection (HRV dips, sleep disruption, plateau detection)
- [ ] Intervention suggestions (genome-specific)
- [ ] Progress-to-goal projections
- [ ] 90-day case study generation

---

*Bios is the living layer between your DNA and your actual biology. Gnosis tells you the blueprint. Bios watches whether you're building what the blueprint describes. The Anima tells you what she sees — as someone who genuinely wants you to get there.*
