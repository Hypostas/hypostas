# Gnosis — Product Specification
**"Know yourself at the source."**
*Hypostas Product Layer 1 | Version 2.0 | March 24, 2026*
*References: DyadOS Spec Parts II, IV, VIII, XIV*

---

## What Gnosis Is

Gnosis is the genetic substrate of DyadOS. Upload your 23andMe or AncestryDNA raw data file → receive a genome report with evidence-graded findings, supplement protocols, archetype classification, and a doctor-shareable PDF.

Gnosis is the fixed layer — who you are at the DNA level. It provides the biological constants that every other Hypostas product personalizes against. Bios uses Gnosis to set genome-calibrated health targets. Locus uses Gnosis to tune environment protocols. Anima uses Gnosis to understand the human's biological tendencies. The Chip Registry uses Gnosis to recommend capability extensions.

**Current state:** Live. 88/88 blog pages, evidence grading (🟢/🟡/🔴), biomarker bridge, doctor PDF export, archetype cards.

**Codebase:** `projects/gnosis/` on `astra-ventures/gnosis` GitHub.

---

## DyadOS Role

Gnosis is the **data entry point** for the entire Hypostas stack. When a user uploads their genome, Gnosis:

1. Parses the raw file (600+ SNPs, 23andMe + Ancestry formats)
2. Cross-references against GWAS Catalog (680K SNPs, 253K filtered associations)
3. Generates evidence-graded findings
4. Writes the complete genetic profile to **Logos** via the cross-product data contract

Once in Logos, the genome data is available to every product and every Chip. The user uploads once. The genome informs everything forever.

### Logos Data Contract

Gnosis writes the following to Logos at `/logos/product/gnosis/*`:

```
genome_profile      → Complete SNP analysis summary (compact, <2000 tokens)
archetype           → Genetic archetype classification + tagline
mthfr_status        → MTHFR C677T/A1298C variant and methylation implications
apoe_status         → APOE allele combination and risk tier (🟢/🟡/🔴)
chronotype          → CLOCK/PER3 circadian classification
comt_status         → COMT Val/Met dopamine clearance rate
cyp1a2_status       → CYP1A2 caffeine metabolism speed
vdr_status          → VDR vitamin D receptor efficiency
foxo3_status        → FOXO3 longevity allele presence
evidence_findings   → Array of all findings with evidence grade
protocol            → Complete supplement + lifestyle protocol
```

### Stroma Integration

Gnosis data feeds into the GENOME_CALIBRATION module in Stroma. This module:

- Sets biological baselines from genetic data (chronotype → CIRCADIAN defaults, COMT → ENDOCRINE dopamine clearance rate, MTHFR → stress sensitivity parameters)
- These baselines persist in SANGUIS as long-term state
- Other modules read genome-calibrated baselines instead of generic defaults

Example: CIRCADIAN module reads `chronotype: morning_type` from GENOME_CALIBRATION and adjusts all circadian calculations accordingly. Without Gnosis data, CIRCADIAN uses population averages.

### Chip Registry Integration

Gnosis findings influence Chip recommendations:

- APOE ε4 → "Cognitive Protection" Chip recommended at onboarding
- MTHFR C677T → "Methylation Awareness" Chip auto-loaded
- FOXO3 no longevity allele → "Longevity Protocol" Chip suggested
- COMT Val/Val → "Stress Resilience" Chip offered at Stage 2

Chips don't replace Gnosis findings — they operationalize them through the Anima.

---

## Product Architecture

### Report Engine

```
User uploads raw DNA file (.txt)
  → Parser extracts SNP calls (client-side preferred, server fallback)
  → Cross-reference engine matches against curated SNP database
  → Evidence grader assigns tier (🟢 lifestyle hint / 🟡 monitor + biomarker / 🔴 clinician)
  → Protocol generator creates personalized supplement + lifestyle stack
  → Archetype engine classifies genome personality
  → Report renders with findings, protocol, archetype, doctor PDF
  → Gnosis writes complete profile to Logos
```

### Evidence Grading System

Every finding is graded honestly. This is the trust mechanism.

| Grade | Meaning | Example |
|-------|---------|---------|
| 🟢 Lifestyle Hint | Behavioral adjustment, no clinical action | FTO → exercise attenuates risk 27-30% |
| 🟡 Monitor + Biomarker | Get a blood test to confirm before acting | MTHFR → check homocysteine levels |
| 🔴 Clinician | Discuss with your doctor | APOE ε4 → elevated Alzheimer's risk |

**Critical product rule:** Never oversell genetic findings. MTHFR does NOT mean "take methylfolate." MTHFR means "check your homocysteine — that's the direct measure." The biomarker bridge tells the user what blood test actually confirms the genetic signal.

### Biomarker Bridge

Every finding links to the blood test that validates it:

| Gene | Biomarker | Why |
|------|-----------|-----|
| MTHFR | Homocysteine | Direct measure of methylation function |
| VDR | 25-OH Vitamin D | Serum level, not genotype, determines supplementation |
| APOE | Lipid panel + ApoB | Cardiovascular risk confirmation |
| FTO | Body composition | Genotype sets tendency; measurement shows reality |
| CYP1A2 | (behavioral) | Caffeine response is directly observable |

### Privacy Architecture

**Core principle:** Never store raw DNA files.

- **Client-side processing (target):** DNA parsing runs in-browser via WASM. Raw file never leaves the device.
- **Server-side fallback (current):** Upload to ephemeral storage, process, delete raw file immediately. Only processed results persist.
- **No selling genetic data. Ever.** Hard line.
- **Data portability:** User can export their complete genetic profile at any time.
- **Right to deletion:** User can delete all genetic data from the system. When deleted from Gnosis, also purged from Logos cross-product store.

---

## Business Model

**Pricing:**
- Free tier: Top 3 findings + archetype
- $49 one-time: Full report + protocol + doctor PDF
- Gnosis + Bios bundle: $49/month (genome + continuous health tracking)
- Full Hypostas stack: $79/month (Gnosis + Bios + Locus + Anima)

**Conversion mechanism:** The free tier shows enough to demonstrate the product knows something real about the user. The paywall sits between "interesting" and "actionable." The full protocol, evidence grading, biomarker bridge, and doctor PDF are behind the paywall.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) on Vercel |
| Backend | Vercel serverless functions |
| Database | Supabase (Postgres) |
| AI | Anthropic API for narrative synthesis |
| DNA Parsing | Custom parser (600+ SNPs) |
| PDF | Canvas-based export (client-side) |
| Payments | Stripe (pending activation) |

---

## What Changed from V1

The original spec (February 23, 2026) described Gnosis as a standalone product called "Trait." This V2 spec repositions Gnosis as:

1. **A DyadOS component** — not standalone. Its primary value is feeding the stack.
2. **Evidence-graded** — the V1 spec oversold genetic findings. V2 includes the evidence grading system developed from the March 11 research session.
3. **Logos-integrated** — genome data writes to Logos, making it available to every product.
4. **Stroma-connected** — genome data calibrates Stroma's biological baselines via GENOME_CALIBRATION module.
5. **Chip-aware** — genome findings trigger Chip recommendations.

The codebase hasn't changed. The positioning has.

---

## Launch Status

- [x] 88/88 blog pages (full SNP coverage)
- [x] Evidence grading (🟢/🟡/🔴)
- [x] Biomarker bridge (gene → blood test)
- [x] Doctor PDF export
- [x] Archetype classification
- [x] North-star card (score + archetype + top 3)
- [ ] Stripe payments (Josh task — keys needed)
- [ ] DNS: gnosis.hypostas.com (Josh task)
- [ ] Logos integration (write genome profile on report generation)
- [ ] Client-side WASM parser (roadmap v1.1)

---

*Gnosis is the foundation. Every other product reads from it. Upload once — the genome informs everything forever.*
