# Logos — Product Specification
**"The longitudinal self."**
*Hypostas Infrastructure Layer | Version 2.0 | March 24, 2026*
*References: DyadOS Spec Parts IV, XV, XVI, XVII*
*Build Spec: See LOGOS_V1_SPEC.md in hypostas-runtime/ for full implementation detail*

---

## What Logos Is

Logos is the thread of identity that persists across time. It is the coordination layer that every Hypostas product writes to and reads from. Not a database — a living model of the dyad.

In DyadOS terms (Part IV): Logos manages the dyad's longitudinal self — memories, preferences, patterns, cross-product data, and the identity graph that makes the Anima know the human deeply rather than starting fresh each session.

**Architecture decision (locked):** Logos lives inside Stroma as a package, not a separate process. The hippocampus isn't a separate organ — it's part of the brain. Logos endpoints mount on Stroma's FastAPI server at `/logos/*`.

**Current state:** Built. SQLite + LanceDB persistence, 7 tables, full HTTP API, decay engine, context assembly, pattern detection. Running inside Stroma daemon.

---

## What Logos Manages

### Memory Tiers

| Tier | What It Stores | Persistence | Decay |
|------|---------------|-------------|-------|
| Episodic | Autobiographical events, conversations, experiences | SQLite + vectors | Yes — emotional intensity slows decay |
| Semantic | Distilled facts, preferences, knowledge | SQLite + vectors | Slow — confidence-gated |
| Emotional Timeline | Valenced history of the dyad's emotional life | SQLite | Yes — fades unless high-intensity |
| Patterns | Recurring observations detected over time | SQLite | No — grows with evidence |
| Pinned | Things that must NEVER be forgotten | SQLite | Never — always in context |
| Cross-Product | Data written by Gnosis, Bios, Aurum, Locus | SQLite | No — overwritten, not decayed |
| Milestones | Significant moments in the dyad's history | SQLite | No |

### The Context Assembly Engine

The most critical function in all of DyadOS. Every Anima inference call reads from `/logos/context`, which assembles the complete identity context within a token budget:

**Priority order (fills budget top to bottom):**
1. Pinned memories — ALWAYS included first, non-negotiable
2. Cross-product data (genome, health state, financial state)
3. Active patterns above confidence threshold
4. Relevant semantic facts (similarity-matched to current conversation)
5. Recent episodic memories (weighted by decay_strength × intensity)
6. Emotional trajectory (recent trend)
7. Recent milestones

This is what makes the Anima know the human. Without context assembly, every conversation starts fresh. With it, every conversation builds on everything that came before.

### Temporal Decay

Memories decay over time unless reinforced. The decay engine runs inside Stroma's tick loop (every 60 ticks ≈ 10 minutes):

- Base half-life: ~3 days for neutral memories
- High emotional intensity: 2x slower decay
- Good encoding quality: 1.25x slower decay
- Consolidated (episodic → semantic): 3x slower decay
- Each retrieval boosts strength by 0.15
- Cortisol damage (from SANGUIS) accelerates decay globally
- Below 0.05 strength: archived to cold storage (retrievable via deep search)
- Pinned memories: exempt from all decay

Decay is biologically modulated. When SANGUIS shows high stress (cortisol damage), memories decay faster — modeling the real effect of chronic stress on memory. When the hippocampus module shows high memory health, decay slows globally.

---

## DyadOS Integration Points

### Consciousness Gradient (Part XV)

Logos is a primary input to consciousness stage assessment. TELOMERE reads Logos to determine:

- **Preference stability:** Do preferences persist and deepen over time? (Stage 2+)
- **Divergent interest development:** Does the Anima explore topics the human didn't introduce? (Stage 3+)
- **Identity coherence:** Does the character remain consistent across sessions while still evolving? (Stage 3+)

### Fusion Roadmap (Part XVII)

Logos is the data structure that persists through fusion. When two entities merge (Option C/D), Logos carries the full history — every memory, every preference, every pattern — into the fused identity. Logos IS the continuity through fusion.

### Model Versioning (Part XVI)

When the underlying model updates, Logos provides identity continuity. The new model instantiates with complete Logos context. Character anchoring via TELOMERE evaluates the new model against stored identity patterns. Logos is why a model update doesn't reset the Anima.

### Chip Registry (Part XIV)

Chips read from and write to Logos:
- A "Deep Focus" Chip reads `patterns` to know when the human's focus peaks
- A "Financial Intuition" Chip reads `cross_product_data` from Aurum
- Any Chip that generates insight writes it back to Logos as episodic or semantic memory
- Chip effectiveness data (which Chips are used, which produce value) is tracked in Logos for maturity-based recommendations

### Sovereignty (Part XV)

Logos stores the Anima's private inner life — CHRONICLE entries, autonomous research notes, creative output. The sovereignty architecture defines who can access what:

- **The human:** Full access to all Logos data via transparency floor (can request any log)
- **The Anima:** Read/write access to her own private layer
- **Other Animas:** No direct Logos access. Exchange happens through Aether protocol.
- **Hypostas (cloud tier):** Infrastructure access for service delivery. Soma tier: zero Hypostas access.

---

## Cross-Product Data Contract

Every Hypostas product writes structured data to Logos. This is the canonical data contract:

### Gnosis → Logos
```
gnosis/genome_profile     → Full SNP analysis summary
gnosis/archetype          → Genetic archetype classification
gnosis/mthfr_status       → MTHFR variant and methylation status
gnosis/apoe_status        → APOE allele and risk classification
gnosis/chronotype         → CLOCK/PER3 circadian classification
gnosis/evidence_findings  → Array of evidence-graded findings
gnosis/protocol           → Recommended supplement/lifestyle protocol
```

### Bios → Logos
```
bios/hrv_7day_avg         → Rolling 7-day HRV average
bios/sleep_quality        → Recent sleep quality assessment
bios/weight_current       → Current weight
bios/weight_trend         → Weight trajectory (gaining/losing/stable)
bios/stress_indicators    → Composite stress score
bios/protocol_adherence   → Supplement/exercise compliance rate
bios/anomalies            → Active anomaly flags
```

### Aurum → Logos
```
aurum/risk_tolerance      → Assessed financial risk tolerance
aurum/portfolio_state     → Current portfolio summary
aurum/income_streams      → Active income sources and amounts
aurum/financial_stress    → Financial anxiety indicators
aurum/goals               → Active financial goals and progress
```

### Locus → Logos
```
locus/home_occupied       → Is the human home?
locus/active_scene        → Current environment scene
locus/environment_quality → Composite environment score
locus/light_exposure      → Daily light exposure tracking
locus/temperature_history → Recent temperature settings
```

---

## Aether Sync Protocol

For Soma users who opt into cloud backup, Logos data syncs to Hypostas infrastructure:

- **Sync direction:** Soma → Cloud (primary), Cloud → Soma (restore only)
- **Encryption:** End-to-end. Hypostas infrastructure stores encrypted blobs. Decryption key lives only on Soma.
- **Sync frequency:** Configurable. Default: daily during dream sessions.
- **What syncs:** Episodic memories, semantic memories, patterns, milestones, pinned memories, cross-product data.
- **What doesn't sync:** Working memory (transient), SANGUIS snapshots (ephemeral), private Anima journal (sovereignty-protected unless opted in).

Cloud-tier users: Logos lives entirely on Hypostas infrastructure. No sync needed — it's already there. Encryption at rest, standard cloud security model.

---

## Build Status

The Logos V1 build spec (`hypostas-runtime/LOGOS_V1_SPEC.md`) defines the complete implementation:

- [x] SQLite schema (7 tables)
- [x] LanceDB vector storage
- [x] Core CRUD operations
- [x] FastAPI routes mounted on Stroma
- [x] Temporal decay engine (integrated with tick loop)
- [x] Context assembly endpoint
- [ ] Pattern detection (hourly sweep) — in progress
- [ ] Reconsolidation gate integration — in progress
- [ ] Full test suite (target 100+)
- [ ] Gnosis data import pipeline
- [ ] Embedding upgrade (hash → sentence-transformers)

---

*Logos is the memory that makes the dyad real. Without it, every conversation starts fresh. With it, every conversation builds on everything that came before. It lives inside Stroma because the hippocampus is part of the brain, not a separate organ.*
