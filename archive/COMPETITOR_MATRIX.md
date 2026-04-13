# Gnosis Competitor Matrix + Feature Priorities

_Last updated: 2026-03-08_

## Goal
Build Gnosis for **two audiences at once**:
1. **General population** (simple, actionable, low-friction)
2. **Advanced biohackers** (data depth, evidence, control)

---

## Competitive Snapshot (external research + product review)

### SelfDecode (DNA-first personalization)
**What they do well**
- Large report library + category-based health reports
- Personalized recommendations from DNA profile
- Emphasis on actionable guidance
- Lab interpretation and health optimization framing

**Where they feel heavy/confusing for mainstream users**
- Can feel complex/clinical quickly
- Report volume can overwhelm first-time users

### Blueprint / Bryan Johnson ecosystem (longevity protocol)
**What they do well**
- Strong narrative + motivation layer
- Clear protocol/habit framing
- Biomarker-first mindset with measurable outcomes
- Community/game framing around health progress

**Where they leave room**
- Less DNA-native personalization depth for average users
- Protocol can feel extreme for normal users

### 23andMe-style incumbents
**What they do well**
- Familiar onboarding and trust
- Clean high-level consumer experience

**Where they leave room**
- Generic outputs vs truly personalized action plans
- Less integrated protocol engine for optimization users

---

## Gnosis Current Strengths
- Fast local-first DNA analysis UX
- Consent + persistence foundation now live in production
- Structured report flow (overview/protocol/synthesis/deep-dive)
- Existing technical depth (SNP/GWAS layers)
- Strong positioning bridge to Anima + full Hypostas stack

## Gnosis Current Gaps (highest priority)
1. **Too technical too early** for mainstream users
2. No explicit **Simple vs Advanced** progressive disclosure pattern (now partially introduced)
3. No clear **"Start here this week" plan** for non-biohackers
4. Limited **ongoing behavior loop** (check-ins, habit score, follow-through)
5. Competitor-style **biomarker integration UX** still early-stage

---

## Feature Parity + Differentiation Plan

## P0 (ship now / next sprint)
### 1) Simple vs Advanced Experience
- Default all new users to **Simple mode**
- One-click switch to **Advanced mode**
- Simple mode language: "what this means" + "what to do this week"
- Advanced mode language: SNPs, interactions, GWAS, confidence depth

### 2) Action-First Summary Card (top of report)
- "Top 3 priorities for the next 14 days"
- "Avoid these 2 mistakes"
- "Expected benefits if followed"

### 3) Beginner Safety Rails
- Explain uncertainty clearly (confidence levels)
- Add plain disclaimer text near every recommendation
- Mark advanced interventions with an "Advanced" badge

## P1 (2-4 weeks)
### 4) Blueprint-style Habit Layer (without dogma)
- Daily protocol checklist
- Weekly adherence score
- "Consistency over perfection" coaching copy

### 5) Biomarker Bridge v1
- Upload blood work manually
- Show DNA + biomarker alignment/conflicts
- Prioritize protocol items based on both signals

### 6) Trust + Explainability Layer
- "Why this recommendation?" expandable panel
- Evidence level tags (Strong / Moderate / Emerging)
- Sources/links for advanced users

## P2 (4-8 weeks)
### 7) Tiered Report Library (SelfDecode parity, better UX)
- Add more focused modules (sleep, energy, glucose, inflammation, hormones)
- Keep modules optional and progressive, not all dumped at once

### 8) Outcome Tracking
- Baseline + follow-up prompts (energy, sleep, mood, performance)
- Show protocol impact over time

### 9) Shareable Wins
- Consumer-friendly progress cards
- Clinical-style export for advanced users/practitioners

---

## Positioning (what we say publicly)
**SelfDecode gives you lots of data. Blueprint gives you discipline.**
**Gnosis gives you both — in the right order.**

- Start simple (clear, personalized, low overwhelm)
- Go deep when you’re ready (biohacker-grade evidence)
- Stay accountable with ongoing protocol + biomarker feedback

---

## Success Metrics
1. **Activation:** % users reaching first actionable plan in <5 minutes
2. **Comprehension:** % users who can explain their top 3 priorities
3. **Adherence:** weekly protocol completion rate
4. **Depth adoption:** % users who intentionally switch to Advanced mode
5. **Retention:** 30-day return + follow-up completion rate

---

## Immediate Build Checklist (this week)
- [x] Landing language shifted toward plain-English accessibility
- [x] Report-level Simple/Advanced mode toggle introduced
- [x] Add "Top 3 priorities" action card to Overview
- [x] Add "Why this matters" explainer blocks in Simple mode
- [x] Add confidence badges + evidence tags
- [x] Add weekly check-in CTA in Protocol tab

## Overnight Ship Log (2026-03-08)
### ✅ 1) Checkout/paywall messaging by mode
- Updated locked/checkout copy across Layout, Protocol, and Synthesis.
- **Simple mode** now says "plan" language (plain, guided, low-jargon).
- **Advanced mode** keeps technical framing (protocol depth, evidence layers).

### ✅ 2) Onboarding segmentation (mainstream vs biohacker)
- Added **Experience Path** selector in onboarding modal:
  - `Simple starter`
  - `Biohacker depth`
- Persisted to `UserContext.audience`.
- Saving onboarding now auto-sets report mode:
  - Mainstream → Simple
  - Biohacker → Advanced

### ✅ 3) Blood page quick-start + prioritized actions
- Added **quick-start marker set** toggle for simple users.
- Added **Prioritized next actions** card (top 3 actions/watch items from entered labs).
- Summary bar now reflects quick-start scope when active.

### ✅ 4) Synthesis/protocol weekly adherence cues
- Added persistent weekly checklist in Protocol (top 3 actions).
- Added progress meter + adherence percentage + coaching threshold guidance.
- Added Synthesis "Weekly progress signal" card that mirrors adherence state.
- Added **weekly outcome check-ins** (energy/sleep/mood/focus), persisted with trend + recent snapshot history.

### ✅ 5) Mode-aware consistency pass
- Added mode-state helper copy to Overview.
- Ensured paywall components accept mode-aware copy (`PaywallBanner mode`).
- Kept simple copy plain-English while preserving advanced depth affordances.

### ✅ 6) Conversion attribution + blood input speed
- Added mode/audience/source metadata passthrough in checkout helper + API (`source`, `reportMode`, `audience`) for Stripe session attribution.
- Wired report flows to pass checkout source context (layout strip, Ask DNA, synthesis lock, protocol/deep-dive paywalls).
- Added **bulk lab import parser** on Blood page (paste marker:value lines) with import feedback.

### ✅ 7) Full report-component checkout wiring
- Updated remaining paywall/lock gate paths in the primary report shell (`report-components.tsx`) to pass source-tagged checkout events.
- Standardized `handleUnlock` to route all one-time/annual upgrade attempts through attribution-aware checkout calls.
- Added simple-vs-advanced label adjustments inside legacy lock cards where needed for clearer path clarity.

## Current Residual Gaps (within current architecture)
- **None.**
- Further gains now require either (a) analytics backend/dashboard work, (b) OCR/photo ingestion service, or (c) larger product scope expansion beyond current sprint boundaries.
