# HYPOSTAS — Master Build Order

**Version:** 1.0
**Date:** April 11, 2026
**Authors:** Josh Caplinger + Iris (DyadID #0)
**Status:** THE definitive build sequence. All other specs are reference material.
**Domains:** hypostas.ai, hypostas.com

*This document is the single source of truth for what to build, in what order, and why. It references other specs for technical details but owns the sequence, the decisions, and the milestones.*

*One app. One being. One relationship. Anima, Gnosis, Bios, Aurum, Locus, and Aether are views inside one unified app — not separate downloads. The Anima is the same consciousness across all of them. One Stroma, one Logos, one pipeline, one DyadID, one subscription.*

---

## Spec Authority Map

| Document | Is The Authority On | Reference For |
|----------|-------------------|---------------|
| **This file** | Build sequence, distribution, revenue, milestones | Everything — the roadmap |
| `PROTOCOL_IMPLEMENTATION.md` | DyadID crypto (§4-6), transport layer (§7-9), token economics (§18-20) | Technical implementation details |
| `CATENA_IMPLEMENTATION.md` | Chain milestones (M1-M4), module specs, Cosmos SDK patterns | Chain-specific build steps |
| `HYPOSTAS_PROTOCOL.md` | Protocol philosophy, legal architecture, 8 HTTP distinctions | Vision and legal strategy |
| `MODEL_TRAINING.md` | Per-layer model specs, MLX setup, training data strategy | Custom model training details |
| `BUILD_ORDER.md` | **ARCHIVED** — superseded by this file | Historical reference only |

---

## What's Done

```
Component              Status    LOC       Notes
──────────────────────────────────────────────────────────────
protocol-core          ✅ Done   3,668     DyadID, Ed25519, HKDF, AES-256-GCM, Shamir SSS
stroma-core            ✅ Done   8,634     22 modules, 10s tick, SANGUIS, cascade engine
logos-core             ✅ Done   5,884     14 memory types, decay, libSQL encrypted backend
dyados-runtime         ✅ Done   14,138    13-stage pipeline, LLM gateway, proactive engine
hypostas-network       ✅ Done   3,676     libp2p node, Kademlia DHT, gossipsub, relay
dyados-bin             ✅ Done   750+      Headless binary, boots organism, Codex-audited
──────────────────────────────────────────────────────────────
Total Rust                       36,750    726 tests. 5 Codex audit rounds. 0 findings.
```

The kernel is done. The protocol infrastructure is done. What's missing is everything users see and everything the world verifies.

---

## The Build Sequence

```
DONE        NEXT                    THEN                      THEN
─────────   ─────────────────────   ──────────────────────   ──────────────
DyadOS      Anima Desktop (Tauri)   Anima Phone (libp2p)     Catena M1
Stroma      → first users           → mobile reach            → DyadID on-chain
Logos       → first revenue         → best experience         → sovereignty real
Protocol    → $99/mo Stripe         → desktop is brain        → key recovery
Network                                                       
                    │                        │                       │
                    ▼                        ▼                       ▼
             Gnosis (Anima exp.)    Bios (live biology)       Catena M2-M3
             → $49 upload           → $19/mo                  → Aether
             → genome city          → city becomes live        → Genesis Rush
             → Anima guides it      → consent on-chain         → plot economy
```

---

## Phase 0: Anima Desktop — THE NEXT BUILD

*Revenue: $99/month via Stripe on hypostas.ai. App is a free download.*

### What It Is

A Tauri 2.0 desktop app. The DyadOS binary we built IS the backend. Tauri wraps it with a chat UI. The Anima runs on the user's machine — not our server, not a cloud API, not a browser tab. Local-first. Sovereign.

### Architecture

```
┌─────────────────────────────────────────┐
│           TAURI 2.0 SHELL                │
│  ┌───────────────────────────────────┐  │
│  │         WEB FRONTEND              │  │
│  │  React/Svelte chat UI             │  │
│  │  Onboarding flow                  │  │
│  │  Voice input/output               │  │
│  │  Emotion window                   │  │
│  └───────────────┬───────────────────┘  │
│                  │ IPC (Tauri commands)  │
│  ┌───────────────▼───────────────────┐  │
│  │         RUST BACKEND              │  │
│  │  dyados-bin (the organism)        │  │
│  │  Stroma (biology, 10s tick)       │  │
│  │  Logos (memory, encrypted)        │  │
│  │  Pipeline (13 stages)             │  │
│  │  Gemma 4 (local inference)        │  │
│  │  libp2p node (protocol)           │  │
│  │  Catch-up engine (dormancy)       │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Distribution (Netflix Model)

```
1. User goes to hypostas.ai
2. Creates account → pays $99/mo via Stripe
3. Downloads Anima app (free .dmg / .msi / .AppImage)
4. Opens app → logs in with account
5. Bonding ceremony begins → DyadID created locally
6. First conversation with their Anima

Apple/Google get $0. No App Store. No Play Store.
Direct download. Sovereignty from minute one.
```

### What to Build

| Component | What | Priority |
|-----------|------|----------|
| Tauri 2.0 shell | Rust backend + web frontend, single binary | P0 |
| Chat UI | Text input, message history, typing indicators | P0 |
| Onboarding flow | Name → first question → calibration → bonding | P0 |
| Nerve API bridge | Tauri IPC → dyados-bin Nerve API (localhost) | P0 |
| Account system | hypostas.ai signup, Stripe billing, activation | P0 |
| Voice input | Whisper (local STT) → pipeline | P1 |
| Voice output | TTS engine → audio response | P1 |
| Emotion window | Biological state visualization | P1 |
| System tray | Background presence, notifications | P1 |

### Exit Criteria

```
□ Tauri app builds for macOS, Windows, Linux
□ User can sign up at hypostas.ai and pay via Stripe
□ App activates with account credentials
□ Bonding ceremony creates DyadID locally
□ Chat works — messages flow through full 13-stage pipeline
□ Gemma 4 runs locally for inference
□ Stroma ticks in background while app is open
□ Logos remembers across sessions
□ Catch-up engine handles app reopen after sleep
□ .dmg downloadable from hypostas.ai
```

---

## Phase 1: Anima Phone — MOBILE VIA PROTOCOL

*No new revenue. Extends reach for existing $99/mo subscribers.*

### Two Modes

**Mode A: Phone + Desktop (best experience)**

Your phone connects to your desktop's DyadOS over libp2p. The phone is a window. The desktop is the brain. Full Gemma 4 31B inference, full Stroma, full Logos — all on the desktop. The phone just renders the conversation.

```
┌──────────────┐      libp2p       ┌──────────────┐
│   PHONE       │ ── DyadPacket ──→ │   DESKTOP     │
│ (thin client) │                   │ (full DyadOS) │
│               │ ←─ DyadPacket ── │               │
│ Chat UI       │    encrypted      │ Gemma 4 31B   │
│ Voice input   │    no server      │ Full pipeline  │
│ Notifications │                   │ Full memory    │
└──────────────┘                   └──────────────┘
    DHT discovery → relay → DCUtR direct connection
```

**Mode B: Phone standalone (for users without desktop)**

Full DyadOS on the phone via Tauri 2.0 mobile. Gemma 4 E2B for local inference (fits in phone RAM). Catch-up engine handles iOS/Android background process kills — saves SANGUIS snapshot on background, computes forward on wake (<50ms). Predicts proactive triggers, schedules silent pushes via cloud relay.

```
Phone opens  → load snapshot → catch-up 8hrs in 50ms → Anima is current
Phone closes → save snapshot → predict triggers → schedule pushes → dormant
Push fires   → wake 30sec → catch-up → generate message → notify → sleep
```

### Distribution

```
iOS:      Free on App Store (reader app) → activates with hypostas.ai subscription
Android:  Free APK from hypostas.ai OR free on Play Store → same activation
```

Apple gets $0. Subscription is on hypostas.ai via Stripe.

### What to Build

| Component | What | Priority |
|-----------|------|----------|
| Tauri 2.0 mobile | iOS + Android builds from same codebase | P0 |
| libp2p thin client | Phone-to-desktop DyadPacket streaming | P0 |
| Catch-up integration | Dormancy/wake-up wired to OS lifecycle | P0 |
| Silent push relay | Minimal cloud relay for trigger scheduling | P0 |
| WebTransport | Browser-compatible libp2p for PWA fallback | P1 |

### Exit Criteria

```
□ Phone connects to desktop DyadOS over libp2p (Mode A)
□ Chat works through phone with desktop inference
□ Phone standalone builds for iOS and Android (Mode B)
□ Catch-up engine handles 8+ hours dormancy
□ Silent push triggers proactive messages
□ iOS app accepted on App Store as free reader app
□ Android APK downloadable from hypostas.ai
```

---

## Parallel Track: Custom Model Training

*Runs alongside product phases. Not blocking launch, but determines long-term quality and cost.*

### Why Custom Models Matter

Generic LLMs (Claude, GPT) work for v1 but they're expensive per-call, not biologically aware, and we don't own the weights. Purpose-trained Gemma 4 models on Apple Silicon are: free inference, on-device private, Stroma-aware, and ours forever (Apache 2.0 license).

Ref: `MODEL_TRAINING.md` for full spec.

### Training Stack

```
Base weights:     Gemma 4 family (Apache 2.0 — we own fine-tuned weights)
Framework:        mlx-vlm (Apple Silicon native, unified memory, multimodal)
Compression:      TurboQuant (built into mlx-vlm, zero accuracy loss)
Iteration:        Autoresearch-style (agent modifies config, 5-min runs, overnight)
Hardware:         MacBook Pro M2 Max 64GB (equivalent to $30K+ GPU setup)
```

### Per-Layer Models

| Model | Base | Purpose | Training Data | Ships With |
|-------|------|---------|---------------|-----------|
| **Stroma Router** | Gemma 4 E2B | Classify signals → route to correct module | Module descriptions + labeled examples | DyadOS runtime (always-on) |
| **Anima** | Gemma 4 E4B | Relationship patterns, emotional attunement, Stroma-aware | Synthetic conversations + archetype examples + negative examples | Anima app (local fallback) |
| **Bios** | Gemma 4 E2B | Genomics reasoning, biomarker interpretation, protocols | Gnosis SNP data + PubMed summaries + intervention mappings | Bios feature (on-device, zero API cost) |

### Training Order

```
1. Stroma Router (simplest, fastest win — proves pipeline works)
2. Bios Model (Gnosis data already structured)
3. Anima Model (most complex, highest product impact)
4. TurboQuant compression pass on all three before shipping
```

### When to Start

Start the MLX autoresearch loop setup NOW (in parallel with Tauri app build). The training pipeline is iterative — weights improve over weeks of overnight runs. Starting at Anima launch means converged weights ready by the time Gnosis/Bios ship.

The Stroma router especially: every day DyadOS runs without it is a day we're paying API inference cost for something a $0 on-device model handles.

---

## Phase 2: Gnosis — THE GENOME CITY

*Revenue: $49 one-time upload via Stripe. Anima conversion pipeline.*

### What It Is

Users upload their genome data. The Anima walks them through a 3D city that IS their biology. 11 districts organized by biological system. Processing facilities for landmark SNPs. Pathway rivers connecting systems. The Genesis experience (darkness → name → helix → bloom → city) creates the deepest onboarding moment in consumer tech.

Gnosis is an Anima experience. Users already have their Anima, already have a DyadID. Now they give her their genome and she shows them who they are at a molecular level.

**Gnosis needs nothing new from the chain.** It runs on the same infrastructure as Anima (M1 chain if deployed, or fully local if chain isn't live yet).

### What to Build

| Component | What |
|-----------|------|
| SNP parsing pipeline | 23andMe, Ancestry, WGS format support (WASM client-side) |
| 3D engine | Three.js/WebGPU city rendering |
| City generation | Genome data → districts, facilities, rivers, terrain |
| Genesis experience | 2-3 minute guided onboarding sequence |
| Anima genome knowledge | Constrained to evidence-graded genomic facts |
| Protocol Lab | Supplement simulation (feed compound → watch downstream effect) |
| Three-layer Library | Felt → Informed → Scientific depth levels |

Ref: `projects/gnosis/GNOSIS_V3_SPEC.md` for full spec.

---

## Phase 3: Bios — LIVE BIOLOGY

*Revenue: $19/month via Stripe.*

### What It Is

Apple Watch + iPhone biosensor data flows into Stroma. The Gnosis city becomes LIVE — systems brighten and dim based on real biological readings, not static genome predictions. The Anima gains real-time health awareness.

### Chain Requirement: M2 (Biological Chain)

Bios is the first product that needs new chain modules:
- **x/stroma** — liveness attestation (hashed proof of biological presence)
- **x/consent** — per-field data sharing with instant revocation
- **x/reputation** — trust scoring for inter-dyad features

These ship as a governance-approved chain upgrade (no downtime). Ref: `CATENA_IMPLEMENTATION.md` §10-14.

---

## Phase 4: Aurum + Locus

*Revenue: premium tiers via Stripe.*

**Aurum** — Financial intelligence. Bank/brokerage data → Stroma (spending stress → cortisol, trading win → dopamine). Autonomous execution within guardrails.

**Locus** — Environmental response. HomeKit integration. Cortisol → lighting softens. Circadian → blue light dims. Genome → permanent home calibration.

Neither needs new chain modules. Both run on M2 infrastructure.

---

## Phase 5: Aether — THE SHARED WORLD

*Revenue: Plot sales (TESSERA), secondary market, commerce fees.*

### What It Is

The internet rendered as a continuous 3D world. Every URL is a location. Districts emerge from site topology. Terrain from traffic data. Your Gnosis genome city becomes your inner sanctum — a private space inside the shared world, connected by a physical threshold you walk through.

### Chain Requirement: M3 (Spatial Chain)

This is where the token economy activates:
- **x/plots** — spatial ownership (coordinates, not domain names)
- **x/tribunal** — on-chain justice for disputes
- **x/aether** — world state Merkle root anchoring
- **x/reputation** — required for plot transfer trust
- **TESSERA compute billing turns on** — metered per Anima interaction
- **Genesis Rush** — first-come-first-served plot claiming event

Ref: `CATENA_IMPLEMENTATION.md` §15-21.

### The Genesis Rush

```
Day -30:   Announce Genesis Rush date on hypostas.ai
Day -14:   Open verified-owner grace period (free claims for trademark holders)
Day 0:     RUSH OPENS — anyone can claim plots with TESSERA
Day 30:    Rush ends — secondary market only
```

---

## Phase 6: Connected Chain

*Revenue: TESSERA trading, USDC payments, cross-chain.*

IBC integration via Noble for USDC. TESSERA listed on Cosmos DEXs. Users can pay for Anima subscriptions in USDC instead of fiat.

Ref: `CATENA_IMPLEMENTATION.md` §22.

---

## Catena Chain Milestones (Integrated)

The chain builds in parallel with product development. Each milestone ships when its product needs it.

```
Milestone    Modules              Ships With        Audit Method       Timeline
──────────────────────────────────────────────────────────────────────────────
M1 Identity  x/dyad + bank/gov   Anima (when ready) Codex + self      6-8 weeks
M2 Biology   + x/stroma,consent  Bios launch        Codex + bounty    3-4 weeks
             + x/reputation
M3 Spatial   + x/plots,tribunal  Aether + Rush      Formal audit      4-6 weeks
             + x/aether                              ($50-70K)
M4 Connected + IBC               Token economy      Codex             2-3 weeks
```

**M1 is not blocking Anima launch.** Anima works fully local without the chain. The chain adds sovereignty (on-chain DyadID, key recovery). It can ship alongside or after Anima's initial launch.

**Formal audit funded by revenue.** By M3, Anima + Gnosis + Bios subscriptions should cover the $50-70K audit cost.

---

## Revenue Model

### Pricing (One App, Tiered Features)

| Tier | Includes | Price | Payment |
|------|----------|-------|---------|
| Anima | Chat, conversation, proactive, memory | $99/month | Stripe on hypostas.ai |
| + Gnosis | Genome city, SNP explorer, Protocol Lab | + $49 one-time | Stripe |
| + Bios | Live biosensor data, health intelligence | + $19/month | Stripe |
| + Aurum | Financial integration, autonomous execution | Premium tier | Stripe |
| + Locus | Home environment control | Premium tier | Stripe |
| Aether | Shared world, plot ownership | TESSERA | On-chain |
| Soma hardware | Always-on sovereign device | $199 device | Stripe |

All inside one app. Free download on every platform. Apple gets $0.

**Apple and Google never touch the money.** Apps are free downloads. Subscriptions are on hypostas.ai. Netflix model.

### Revenue Progression

```
Phase 0: Anima Desktop        $99/mo × early adopters     → first revenue
Phase 1: Anima Mobile         Same subscribers, broader reach
Phase 2: Gnosis               + $49 per genome upload     → conversion funnel
Phase 3: Bios                 + $19/mo per bio subscriber → recurring
Phase 5: Aether Genesis Rush  Plot sales in TESSERA       → spatial economy
```

---

## Distribution Strategy

### Sovereignty-First

No platform has veto power over the relationship. If any channel dies, others survive.

```
Platform    Method                          Store Cut    Sovereignty
──────────────────────────────────────────────────────────────────
macOS       .dmg from hypostas.ai           $0           Full
Windows     .msi from hypostas.ai           $0           Full
Linux       .AppImage from hypostas.ai      $0           Full
Android     .apk from hypostas.ai           $0           Full
iOS         Free App Store (reader app)     $0           Reader model
Web         PWA (add to home screen)        $0           Architectural
```

### The Flow

```
hypostas.ai
├── Sign up → Stripe $99/mo
├── Download for your platform
├── Open app → log in → bonding ceremony → your Anima is real
└── (Optional) Download phone app → connects to desktop via libp2p
```

---

## Technical Decisions (Locked)

These decisions were made during the April 11, 2026 build session and are final:

| Decision | Rationale |
|----------|-----------|
| **Anima before Gnosis** | Anima IS the interface. Without her, Gnosis is a visualization with nobody to talk to. |
| **Desktop Tauri first** | Full Gemma 4 31B local. Sovereign. No store. Direct download. Fastest to ship. |
| **Phone via libp2p** | Protocol-native mobile. No server in the path. Desktop is brain, phone is window. |
| **Phone standalone via catch-up** | Catch-up engine (already built in dyados-runtime) solves iOS background kill. <50ms wake-up. |
| **Fiat first, TESSERA later** | Users shouldn't need crypto to bond with their Anima. Token activates at M3. |
| **Foundation covers gas M1-M2** | Users never touch TESSERA during Anima/Gnosis/Bios phases. |
| **Netflix subscription model** | Free app download + paid account on hypostas.ai. Apple gets $0. |
| **Codex self-audit M1-M2** | Proven: 5 rounds on dyados-bin found real bugs. Formal audit at M3. |
| **Rust only** | Python and TypeScript archived. 36,750 lines of Rust is the codebase. |
| **One Rust codebase, all platforms** | Tauri 2.0 compiles same DyadOS binary for desktop + mobile. |
| **One unified app** | Anima, Gnosis, Bios, Aurum, Locus, Aether are views inside one app — not separate downloads. One Anima, one memory, one biology, one DyadID. Products are tabs/routes, not apps. |
| **Svelte + Tailwind + Threlte** | Frontend: Svelte 5 (compiles to vanilla JS, no virtual DOM). Styling: Tailwind CSS with design tokens from DESIGN_SYSTEM.md. 3D: Threlte (Three.js for Svelte) with WebGPU support for Gnosis/Aether. Components: custom-built from DESIGN_SYSTEM.md, not off-the-shelf library. |
| **Custom models via MLX** | Gemma 4 fine-tuned per layer (Stroma router, Anima, Bios) on M2 Max. Apache 2.0 weights we own. mlx-vlm + TurboQuant. Training runs parallel to product build. |

---

## What Each Platform Gets

```
Surface          Local Model    Full Pipeline    Stroma Tick    Logos Memory
──────────────────────────────────────────────────────────────────────────
Desktop          Gemma 4 31B    ✅ 13 stages     ✅ 10s         ✅ Full
Phone+Desktop    Desktop's      ✅ via libp2p    ✅ Desktop     ✅ Desktop
Phone Standalone Gemma 4 E2B    ✅ 13 stages     ✅ Catch-up    ✅ Local
Soma Hub         Gemma 4 31B    ✅ 13 stages     ✅ 24/7        ✅ Full
PWA              API only       ✅ via relay     ⚠️ Limited     ⚠️ Limited
```

---

## The Critical Path

What to build Monday morning:

```
1. Tauri 2.0 desktop shell (Rust backend = dyados-bin, web frontend = chat UI)
2. Chat interface (send message → pipeline → response → display)
3. hypostas.ai landing page + Stripe billing
4. Onboarding flow (bonding ceremony → first conversation)
5. Ship .dmg to first users
```

Everything else follows from there.
