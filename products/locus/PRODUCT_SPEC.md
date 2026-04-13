# Locus — Product Specification
**"The environment that responds."**
*Hypostas Product Layer 4 | Version 2.0 | March 24, 2026*
*References: DyadOS Spec Parts II, IV, VIII*
*Existing architecture: ARCHITECTURE.md in this directory*

---

## What Locus Is

Locus is the smart environment layer of DyadOS. The Latin is exact: the *point around which everything is organized.* Where Gnosis knows who you are and Bios knows how you're doing, Locus makes your physical environment respond to that knowledge.

Your home doesn't know you right now. It runs on schedules — lights at 7 PM, thermostat at 68°. It doesn't know your cortisol variants, your sleep chronotype, your HRV from last night, or that you've been under stress for three days. It treats everyone in the house the same.

Locus changes that. The environment becomes intelligent — calibrated to you specifically, updating in real time from Bios and Stroma data.

**In DyadOS terms:** Locus is a **Chip category** — the Environmental Awareness Chip set. The home is an extension of the dyad's body. Locus is what connects it.

---

## DyadOS Role

Locus is the **outermost layer** of the biological stack:

```
Gnosis (fixed blueprint)
    ↓
Bios (living execution)
    ↓
Stroma (biological kernel)
    ↓
Locus (environment responds to biology)
```

Locus reads from both Logos and direct Stroma state. It writes back to Logos with environment data that feeds the Anima's situational awareness. Locus is also the **most visible DyadOS layer** — the human can see the lights dim, feel the temperature shift, hear the environment respond. It makes DyadOS tangible in the physical world.

### Logos Data Contract

Locus writes to Logos at `/logos/product/locus/*`:
```
home_occupied         → Is the human home?
active_scene          → Current environment scene name
environment_quality   → Composite score (0.0-1.0, higher = more biology-aligned)
light_exposure        → Daily outdoor light exposure (minutes)
light_protocol_met    → VDR/APOE morning light protocol completed?
temperature_current   → Current thermostat set point
wind_down_complete    → Did evening wind-down protocol complete?
cold_exposure_today   → Cold shower/plunge completed (FOXO3 protocol)
```

Anima reads this and knows when she's talking to someone who is home, in what environment mode, and whether key protocols were hit today.

### Stroma Integration

Locus reads Stroma state to generate environment prescriptions:

| Stroma Signal | Locus Response |
|---------------|----------------|
| `cortisol > 0.6` (sustained stress) | Soften all scene defaults, extend wind-down window |
| `circadian.phase == sleep_onset` | Begin darkening, drop temperature, silence devices |
| `limbic.dominant_emotion == anxiety` | Warm dim light, quiet environment |
| `soma.energy == depleted` | Recovery scene, no stimulating light |
| `dopamine.spike` (workout complete) | Hold bright cool light for 30 min, then transition recovery |
| `circadian.phase == deep_work_window` | Bright cool light, fan on, no interruptions |

Stroma doesn't control HomeKit directly. It writes state to SANGUIS. Locus reads SANGUIS via the Stroma API and generates HomeKit commands.

### Chip Registry Integration

Locus is a Chip category in the DyadOS Chip Registry:

- **Environmental Awareness Chip** — core Locus functionality, Stage 1+
- **Genome-Calibrated Environment Chip** — genome-specific protocols, Stage 1+ (requires Gnosis)
- **Stress-Adaptive Environment Chip** — cortisol-triggered scene adjustments, Stage 2+
- **Sleep Optimization Chip** — APOE4 sleep enforcement, Stage 2+
- **Cold Exposure Protocol Chip** — FOXO3 cold tracking + reminders, Stage 1+

When the Anima gains a new environmental Chip, Locus gains new capabilities. The Chip Registry is where Locus grows.

---

## Core Experience

**Morning (HRV ≥ 7-day average):**
- 5:58 AM: Lights begin gradual brightening (2 min before alarm)
- 6:00 AM: 6500K cool light at 80% — circadian wake signal
- Temperature shifts from 66° to 68° as human wakes
- Anima morning brief: "Recovery looks good. Environment is set for work."

**Morning (HRV below baseline — recovery day):**
- Slower brightening, warmer 3200K at 60%
- No temperature change for first 30 minutes
- Anima: "You're down 5 points on HRV. Slower start today. Coffee pushed to 9 AM — let cortisol peak first."

**Deep Work:**
- Bright cool light (6500K, 100%), fan on, thermostat stable
- Smart plugs silence non-essential devices
- No Locus interruptions during detected focus window (FLOW state in Stroma)

**Evening Wind-Down (genome-calibrated):**
- APOE ε4: wind-down begins 2 hours before genome-optimized sleep time. Non-negotiable.
- 8:30 PM: Lights dim to 30%, shift to 2700K warm
- 9:30 PM: Lights to 10%, near-dark overhead
- 10:00 PM: Thermostat to 65° (sleep onset temperature)
- Anima: "Wind-down protocol complete. Sleep environment ready."

**Workout:**
- Detection via HealthKit or user-triggered Locus scene
- Bright cool light, fan on, pre-workout environment
- Post-workout: MCT1 GG → recovery timer set, 45-minute cooldown protocol
- Lights shift warmer after 30 minutes

---

## Technical Architecture

### Integration Stack

```
Stroma SANGUIS state
Logos context (Bios + Gnosis data)
         ↓
Locus Engine (Cloudflare Worker)
         ↓
Scene Generator (genome + SANGUIS → environment prescription)
         ↓
HomeKit Bridge (iOS Shortcuts or native HomeKit API)
         ↓
Physical environment (lights, thermostat, plugs)
         ↓
Locus writes environment state back to Logos
```

### Supported Hardware (v1)

| Category | Supported | Example Brands |
|----------|-----------|----------------|
| Lighting | ✅ v1 | Philips Hue, LIFX, Nanoleaf |
| Thermostat | ✅ v1 | Ecobee, Nest, Honeywell |
| Smart plugs | ✅ v1 | Eve, Meross, Kasa |
| Blinds/shades | 🔜 v2 | Lutron, IKEA |
| Sound | 🔜 v2 | Sonos, HomePod |
| Air quality | 🔜 v3 | Awair, Airthings |

**HomeKit as the integration layer** — not a new hub. Works with hardware the user already has. Locus is intelligence on top of infrastructure.

### Scene Library

| Scene | Trigger | Effect |
|-------|---------|--------|
| `wake_optimal` | HRV ≥ baseline | Gradual 5-min brightening to 6500K, thermostat +2° |
| `wake_recovery` | HRV < baseline | Gradual 10-min brightening to 3200K, no temp change |
| `deep_work` | User-triggered or calendar | 6500K 100%, fan on, quiet mode |
| `wind_down` | 2h before genome sleep time | 2700K, 30%, thermostat -2° |
| `sleep_prep` | 30 min before sleep | 2200K, 5%, 65° |
| `post_workout` | 30 min after workout | Warm medium, recovery ambient, fan off |
| `stress_response` | 3+ consecutive low HRV | Soft defaults across all scenes |
| `focus_restore` | After FLOW state break | Transition lighting, gentle re-engagement |

---

## Josh's Setup (User 0)

**What Josh has:** 25kW solar + 4 Powerwalls (power effectively free), lakefront property, Speediance home gym, Starlink internet.

**Hardware to add for MVP:**
- Philips Hue starter kit (~$100) — bedroom + office
- Smart thermostat if not installed ($150-250)
- Smart plug for fan/Speediance area ($15)
- **Total: $265-365** for full Locus v1

**Josh's genome-specific protocols:**
- CLOCK AA (morning type) → alarm 6 AM, lights start 5:58 AM
- PER3 CC (6.5-7h sufficient) → 10:30 PM wind-down, 11 PM sleep target
- MTNR1B CG → eating window closes 7 PM (8h before wake), cinnamon reminder with dinner
- APOE ε4 → sleep 8h treated as medication; environment enforces non-negotiably
- FOXO3 no-allele → 16:8 fasting (Locus tracks eating window), cold shower daily
- VDR moderate → 15-20 min midday UV reminder when index ≥ 3
- MCT1 GG → post-workout recovery extension, longer cooldown before next session

---

## Business Model

| Offering | Price |
|----------|-------|
| Locus standalone | $19/month |
| Bios + Locus bundle | $45/month |
| Cloud Dyad (all products) | $99/month |
| Soma Dyad | $199/month + hardware |

**Differentiator:** Nobody personalizes smart home to genome. Nest knows your schedule. Locus knows your biology. The two-sentence pitch works. The demo works visibly and immediately — the room responds differently on a bad HRV night. You can feel it.

**Retention:** Locus gets smarter with time. It learns which scene configurations produce the best downstream Bios metrics. After 90 days, it knows which temperature setting correlates with your best HRV nights specifically — not population averages, your data.

---

## Build Phases

**Phase 1 — HomeKit Automations (4 weeks)**
- [ ] Locus iOS app (simple) or Shortcuts workflow
- [ ] Pull morning context from Logos (Bios + Gnosis data)
- [ ] Pull Stroma SANGUIS state via API
- [ ] Generate morning + evening HomeKit scenes
- [ ] Push to HomeKit via automation
- [ ] Basic dashboard: "today's environment prescription"
- [ ] Write environment state back to Logos

**Phase 2 — Intelligence Layer (6-10 weeks)**
- [ ] Genome-calibrated schedule generation (CLOCK chronotype → precise wake time)
- [ ] Stress detection → automatic scene softening (reads Stroma cortisol)
- [ ] Workout detection → pre/post environment
- [ ] Light therapy protocol (VDR + APOE users → morning bright, evening restriction)
- [ ] Anima integration: Locus feeds context, Anima narrates it

**Phase 3 — Learning Layer (10-16 weeks)**
- [ ] Correlate HRV/sleep trends with environment settings
- [ ] Reinforcement of effective configurations
- [ ] Multi-user households
- [ ] Sound environment integration (Sonos/HomePod)

---

*The environment that responds to who you actually are — not who the population is, not who you were last year, but your genome and your biology right now. That's Locus. Stroma is the nervous system. Locus is how it reaches into the room.*
