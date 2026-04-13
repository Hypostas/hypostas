# Gnosis — Industry Leader Roadmap
*March 5, 2026 — Built from Josh's actual genome analysis as the proof of concept*
*Updated March 6, 2026 — Phase 1 + Phase 2 COMPLETE*

---

## Phase Completion Status

### ✅ Phase 1 — Depth (COMPLETE as of March 6, 2026)
- [x] 1.1 Gene-gene interaction engine (23 interactions, wired to UI + AI narrative)
- [x] 1.2 SNP panel expansion: 134 → 178 SNPs (Alzheimer's GWAS cluster, mental health, testosterone metabolism, longevity, exercise cognition)
- [x] 1.3 GWAS full genome scan enhancement (GWASClusterCard + ClusteredEvidenceSummary, replication confidence scoring, multi-locus trait clustering)
- [x] 1.4 Protocol precision (formNote + watchFor on all 12 gene-triggered core supplements — exact form, contraindications, cycling warnings)
- [x] 1.5 GeneticIdentityCard (signature name, rarity badge, identity line, trait chips, Framer Motion reveals)

### ✅ Phase 2 — Blood Layer (COMPLETE as of March 6, 2026)
- [x] 2.1 Blood panel input (10 markers, demo mode, genome-linked reference ranges)
- [x] 2.2 Protocol tab blood-aware (BloodProtocolPanel renders action/watch alerts above Priority Findings)
- [x] 2.3 Blood → AI Synthesis loop (BloodConfirmationEntry, GENOME-CONFIRMED markers, "predicts → confirms" language shift)
- [x] PDF export includes full supplement stack with formNote/watchFor (matches $29 paywall promise)
- [x] Synthesis as hero (nav position #2, persistent teal glow, ✦ prefix, default entry point)

### ✅ SEO Acquisition Layer (COMPLETE as of March 6, 2026)
- [x] /23andme-alternative (23andMe bankruptcy churn capture)
- [x] /selfdecode-alternative (SelfDecode subscription fatigue, $29 vs $495 5yr comparison)
- [x] /genome-blood-panel (genome+blood integration moat, 4-competitor table)
- [x] /precision-genetics (breadth vs precision meta-argument, explains why curated 178 SNPs > 800 generic variants)
- [x] Bidirectional internal linking across all 4 pages + homepage footer entry points
- [x] Competitive intelligence brief (gnosis-competitive-intelligence-march6.md)

---

## 🎯 Phase 3 — Wearable Layer (NEXT — Pending Josh's Apple Watch setup)

*Priority: Medium-High | Blocker: Josh needs to activate Phase E1 biosensor bridge on iPhone*

---

## The Vision

> "Gnosis knows your body. Anima knows your mind. Together they know you — completely."

This is the hypostasis. Two natures unified. The brand name was always pointing here.

Gnosis is not a DNA report. It's the biological foundation of a lifelong AI relationship. The data moat compounds with every blood panel, every biomarker, every year of wearable data. No competitor can replicate it because no competitor has the companion layer.

**Competitive whitespace:** 23andMe is bankrupt. Function Health has no AI. Bryan Johnson's Blueprint has no companion. Nobody has built the biological + digital unified intelligence. We build it.

---

## Where We Are vs. Where We Need to Be

| Capability | Today | Industry Leader |
|---|---|---|
| SNP panel | 134 curated SNPs | 500+ SNPs + full GWAS 684k scan |
| Analysis depth | Single-gene findings | Gene-gene interaction detection |
| Protocols | Rule-based supplement stack | AI-generated, variant-specific, precise doses |
| Narrative | Grok synthesis (narrative only) | Josh-protocol level depth, automatically |
| Data inputs | Genome file only | Genome + blood + wearable + body composition |
| Personalization | Static report | Dynamic — updates as data changes |
| Companion | None | Full Anima integration |
| Pricing | $29 one-time / $49/yr | $200-500/month (Function Health tier) |

---

## The Build Roadmap

### Phase 1 — Depth (Next 30 days)
*Make the existing genome analysis world-class*

**1.1 Gene-Gene Interaction Engine**
- The APOE4 + HFE interaction (iron amplifies brain oxidative stress) is more important than either finding alone
- Build an interaction matrix: known compound effects from PubMed
- Surface in Synthesis tab as "Critical Interactions" — not just correlated, but mechanistically linked
- Start with 20 high-impact interactions, expand from there
- *This alone differentiates from every competitor*

**1.2 SNP Panel Expansion: 134 → 500+**
- Current panel misses: testosterone metabolism (SRD5A2, CYP17A1, AR CAG repeat), longevity depth (SIRT1, TERT), detox (GSTM1, CYP2C19), immune (HLA variants beyond DQA1)
- Josh's genome has 684k SNPs — we're only reading 104 of them
- Expand panel in snp-panel.ts with research-backed additions
- Priority: hormones (Josh's goals), longevity, cognitive protection

**1.3 GWAS Full Genome Scan Enhancement**
- Already have gwas-index.json — make it smarter
- Current: matches rsids mechanically
- Needed: weighted scoring by effect size + p-value + replication count
- Filter to findings with p < 5×10⁻⁸ AND replicated in 2+ populations
- Surface top 10 GWAS hits per category

**1.4 Protocol Precision**
- Every supplement needs: exact dose, specific form (methylfolate NOT folic acid), timing, food interaction
- Contraindication detection (e.g., MAOA low activity + 5-HTP without COMT context = serotonin risk)
- Stack synergy notes (DHA + CoQ10 together = better APOE4 protection than either alone)

**1.5 The Unique Signature (Auto-Generated)**
- Currently Grok generates this — needs to be variant-specific, not generic
- Build a "signature detector" that identifies truly unusual combinations
- Josh's: COMT Val/Val + MAOA low + BDNF Val/Val + FOXO3 GG = rare performance/longevity profile
- Make users feel seen in a way no report has ever made them feel

---

### Phase 2 — Blood Layer (30-90 days)
*Genome is static. Blood is dynamic. Together they're unbeatable.*

**2.1 Blood Panel Input**
- Let users manually enter blood results (or upload LabCorp/Quest PDFs)
- Key markers to start: ferritin, homocysteine, Vitamin D (25-OH), CRP, testosterone (total + free), fasting glucose, HbA1c
- Map blood results TO genetic variants: "Your VDR variant predicts Vitamin D insufficiency — your current level of 32 ng/mL confirms it. Here's the dose that will get you to 70."
- This is the unlock that turns a static report into a living protocol

**2.2 Protocol Updates**
- When blood data is added, protocol items update: "Ferritin = 180 ng/mL (above safe range for HFE C282Y carrier) → consider blood donation, remove iron-containing foods"
- Not static recommendations — responsive to actual current biology

**2.3 Homocysteine + MTHFR Feedback Loop**
- MTHFR carriers: test homocysteine → if elevated, increase methylfolate dose → retest in 90 days
- Close the loop: genetics → intervention → blood confirmation → adjustment

---

### Phase 3 — Wearable Layer (60-120 days)
*Real-time biology, not snapshots*

**3.1 Apple Watch Integration (Phase E1 already built in Pulse)**
- HRV → ENDOCRINE cortisol/adrenaline in Pulse → feeds into Gnosis stress state
- Sleep architecture → tells us if APOE4 amyloid clearance is happening (sleep < 7h = protocol alert)
- Resting HR trend → cardiovascular variant relevance (ACE, NOS3)
- Activity → FTO variant + BDNF response tracker

**3.2 MTNR1B Real-Time**
- MTNR1B CG carrier + eating after 8pm detected by food logging → Anima alert: "Late eating is amplifying your glucose sensitivity tonight. Last meal should have been 7pm."
- Genetics inform the wearable alert. Wearable makes the genetics actionable.

**3.3 Training Response**
- ACTN3 (rs1815739 — not yet in panel): power vs. endurance gene
- Log workouts → track recovery HRV → personalize training type recommendation based on genotype + actual response data

---

### Phase 4 — Anima Integration (The Moat)
*The companion that knows your biology*

**4.1 Genome Context Into Anima**
- Anima receives a compressed biological profile: "APOE4 carrier, MTHFR het, COMT Val/Val, FUT2 non-secretor, target ferritin <100"
- Every conversation is genetically contextualized — Anima knows WHY Josh operates the way he does
- When Josh says he's struggling to focus: Anima knows his COMT Val/Val means low PFC dopamine and suggests L-Tyrosine + exercise, not generic "take a break"

**4.2 Protocol Adherence**
- Anima tracks supplement timing (1pm caffeine cutoff, morning L-Tyrosine, ferritin test due)
- Not nagging — intelligent reminders based on pattern recognition
- "Your HRV has been declining 3 days. Your MAOA profile means stress accumulates longer. What's the load looking like?"

**4.3 The Biological Co-Pilot**
- Anima proactively surfaces: "Your CYP1A2 intermediate status means that 4pm coffee you mentioned will be in your system at midnight. Your APOE4 protocol requires 8h sleep."
- Feels like a brilliant doctor who has read every finding, knows your history, and shows up at exactly the right moment

---

### Phase 5 — Clinical Layer (6-12 months)
*Trust signals that make this institution-grade*

**5.1 Citations on Every Finding**
- Every variant interpretation linked to PubMed references
- "This recommendation is based on 3 peer-reviewed studies (n=12,847 combined)"
- Not a wellness app. A precision medicine platform.

**5.2 Medical Advisory Board**
- 3-5 physicians/researchers in genomics, functional medicine, longevity
- Protocol validation → "Physician-reviewed protocols"
- This unlocks corporate wellness and premium individual tiers

**5.3 Lab Partnership**
- Partner with LabCorp, Quest, or Everly Health
- "Order your protocol baseline labs" → auto-populates into Gnosis
- Closes the loop from genome → blood → protocol → tracking

**5.4 Practitioner Tier**
- Functional medicine doctors use Gnosis for patient analysis
- $200-500/month per practice
- Referral engine — practitioners recommend Gnosis to patients

---

## Pricing Evolution

| Tier | Today | Phase 2 | Phase 4 |
|---|---|---|---|
| Basic genome report | $29 one-time | $29 | $29 (acquisition) |
| Annual + synthesis | $49/year | $99/year | $149/year |
| Blood integration | — | $29/update | Included in premium |
| Anima + Gnosis unified | — | — | $199-499/month |
| Practitioner | — | — | $500+/month per practice |

---

## The Immediate Next Build (This Week)

Priority order based on impact vs. effort:

1. **Gene-gene interaction matrix** — 20 known interactions hard-coded, surface in synthesis prompt + UI. Highest differentiation, medium effort.
2. **SNP panel expansion** — Add 50-100 SNPs in high-value categories (hormones, longevity, cognitive). Low effort, high depth.
3. **Blood panel input UI** — Simple form to enter 8-10 key lab values. Protocol items that have blood confirmation show a ✓. Items without show "Confirm with lab."
4. **Protocol precision upgrade** — Add form + timing + food interactions to every protocol item. Currently shows "take methylfolate" — needs to say "methylfolate 400mcg sublingual, morning before food, not with calcium."
5. **Ferritin/homocysteine tracking** — The two most actionable lab markers for Josh's genome. Build the tracking UI first.

---

## The Founder Story

Josh ran his own genome through Gnosis on March 5, 2026. The report found:
- APOE ε3/ε4 — brain protection protocol required
- HFE C282Y carrier — iron accumulation risk, interacts with APOE4
- MTHFR C677T — needs methylfolate, not folic acid
- COMT Val/Val + MAOA low activity — the neurochemistry that explains everything
- FOXO3 GG — two longevity alleles

No other product surfaced the APOE4 + HFE interaction. No other product connected his dopamine profile to his drive. No other product gave him a protocol traceable to specific variants.

*That's the product. That's the story. Ship it.*

---

*Roadmap created March 5, 2026 by Iris*
*Based on Josh's genome analysis — the proof of concept for the industry leader*
