# Trait — Product Specification
*Version: 0.1 | Created: February 23, 2026 | Author: Iris*

---

## What Is Trait?

Trait is a DNA-personalized supplement and natural protocol engine. Upload your 23andMe or AncestryDNA raw data file. Get a report of exactly which natural compounds and supplements your genome indicates you need — and why.

**The insight:** 30 million people have taken consumer DNA tests. Almost none of them know how to use the genetic data they paid for. Trait bridges that gap.

---

## The Problem We're Solving

1. **The Raw File Problem** — You paid $100 for a DNA test. You have a `.txt` file with 700,000 genetic markers. You have no idea what it means.

2. **The Generic Supplement Problem** — Everyone takes the same vitamins. But MTHFR carriers can't use folic acid. APOE4 carriers have specific brain health needs. Slow CYP1A2 metabolizers should limit caffeine. The supplement industry ignores all of this.

3. **The Information Gap** — The scientific research exists (GWAS Catalog has 1M+ published associations). It's just locked behind academic paywalls and bioinformatics complexity.

**Trait unlocks this.** Plain-language genetic report → actionable protocol → natural compounds first.

---

## Target Users

### Primary: Health-Conscious DNA Test Owners
- Purchased 23andMe / AncestryDNA (30M+ users, growing)
- Age 28-55, already spending $50-300/month on supplements
- Frustrated by generic advice ("everyone should take Vitamin D")
- Responds to "your specific gene means you need X"

### Secondary: Biohackers & Longevity Seekers
- Already using HRV, CGM, sleep trackers
- Want genetic layer added to their optimization stack
- Higher LTV — will pay for ongoing premium access

### Tertiary (B2B later): Functional Medicine Doctors
- Want data-driven supplement protocols for patients
- Willing to pay for a professional tier

---

## MVP Scope (3-Week Build)

### What's Already Done ✅
- Raw DNA parser (600+ SNPs, 23andMe + Ancestry formats)
- GWAS Catalog cross-reference engine (680K SNPs, 253K filtered associations)
- 66 curated SNP→compound mappings with natural notes
- Waitlist page with sample report (deployed)
- Genome data model (`josh-genome.json` as reference)

### What We're Building

#### Week 1: Core Report Engine
- [ ] Web upload handler (HTML5 file input, no server-side storage by default)
- [ ] Client-side or server-side DNA parser (see Privacy section)
- [ ] Report generation: SNP → finding → recommendation → priority score
- [ ] Natural compounds first, synthetics as fallback
- [ ] PDF/shareable report output
- [ ] Email capture + Loops.so/ConvertKit integration

#### Week 2: Polish + Conversion
- [ ] Report UI (dark, data-dense, premium feel)
- [ ] "Your top 5 findings" summary card (shareable image)
- [ ] Sample report (interactive, no upload required)
- [ ] Dosage guidance + cycling notes
- [ ] Contraindications/interactions checker (basic)
- [ ] Mobile-optimized

#### Week 3: Payment + Delivery
- [ ] Stripe integration ($49 early / $149 public)
- [ ] Email delivery of full PDF report
- [ ] Basic account system (report re-access)
- [ ] Waitlist → paid conversion campaign

---

## Privacy Architecture

**Core principle:** We should never store raw DNA files. Period. The user's DNA is theirs.

### Option A: Client-Side Processing (Preferred)
- DNA parsing runs 100% in the user's browser (JavaScript/WASM)
- Raw file never leaves their device
- Only the processed report data (SNP call results, not raw file) is sent to our server
- Privacy story: "Your DNA stays on your device. We never see your raw file."

### Option B: Server-Side with Immediate Deletion
- Upload to ephemeral storage (never to DB)
- Process → generate report → delete raw file
- Report results stored (not raw DNA)
- Required if client-side WASM is too complex for MVP

**Decision:** Start with Option B (faster to ship), roadmap Option A for v1.1 as differentiator.

### Data Policy
- No selling genetic data. Ever. Hard line.
- Aggregate statistics (anonymized population-level): okay
- User can delete their account and all data at any time
- Legal: wellness/educational disclaimer, not medical advice (already on waitlist page)

---

## Report Structure

### Section 1: Your Genetic Summary
- "X variants found that affect your health optimization"
- Risk tier breakdown: Priority 🔴 / Notable ⚡ / Informational 🔵
- System breakdown: Metabolism, Brain, Cardiovascular, Hormones, Longevity

### Section 2: Priority Findings
*3-5 highest-priority variants with clear action items*

**Format per finding:**
```
[VARIANT] MTHFR C677T — Folate Processing
Status: Heterozygous (one copy)
What this means: Your body processes folate ~40% less efficiently than average.
Why it matters: Folic acid from fortified foods won't convert to the usable form.
What to do: 
  Primary: Methylfolate (L-5-MTHF) 400-800mcg/day
  Food: Leafy greens, lentils, beans
  Avoid: Synthetic folic acid (masks deficiency, may cause issues)
Confidence: High (replicated in >50 studies, GWAS catalog: rs1801133)
```

### Section 3: Full Protocol
- Complete list of all flagged SNPs
- Sorted by priority score
- Dosage guidance, timing, cycling recommendations

### Section 4: Your Stack Summary
- Combined daily protocol (morning / with food / evening)
- Estimated monthly cost at mainstream retail
- Potential interactions to watch

### Section 5: What To Track
- Suggested biomarkers to test after 90 days
- Expected changes per intervention

---

## Tech Stack

### Frontend
- **React + TypeScript** (or Next.js if we want SSR for SEO)
- Tailwind CSS (consistent with waitlist page aesthetic)
- **DNA Parser:** JavaScript port of existing Python parser (or WASM for perf)

### Backend
- **Next.js API routes** or **Cloudflare Workers** (existing infra)
- Ephemeral file processing (Cloudflare R2 with 24h TTL, or in-memory)
- **Report generation:** Python FastAPI endpoint (reuse existing parse_genome.py)
- **PDF generation:** Puppeteer or @react-pdf/renderer

### Data
- **GWAS Catalog subset:** Pre-compiled SQLite (ship as static asset, ~5MB)
  - 66 curated SNPs at launch, expandable to full catalog in v1.1
- **No user DNA storage** (processed report results only)
- **User accounts:** Supabase (reuse existing infra from Companion)

### Payments
- **Stripe** ($49 one-time, $149 post-launch, $29/month subscription)
- Webhook → Supabase → email delivery

### Email
- **Loops.so** or **Resend** (preferred over SendGrid for simplicity)
- Transactional: waitlist confirm, report delivery, account creation
- Marketing: waitlist activation sequence (5 emails over 14 days)

---

## Pricing Strategy

| Tier | Price | What You Get |
|------|-------|-------------|
| Early Access | $49 | Full report, 66 SNPs, PDF, email delivery |
| Launch Price | $149 | Same + priority queue |
| Subscription | $29/mo | Monthly re-analysis as we expand SNP database, GWAS updates |
| Pro (future) | $99/mo | API access, practitioners, bulk uploads |

**Reasoning:**
- $49 = impulse buy for someone already spending $300/mo on supplements
- $149 = still cheap vs a functional medicine consult ($300-500)
- $29/mo subscription = the real LTV driver (expanding database is the product moat)

---

## Go-To-Market

### Phase 1: Waitlist Activation
- Email sequence to waitlist (5 emails, 14 days):
  1. Welcome + sample report preview
  2. "The MTHFR problem" (educational)
  3. "Your genome has been silently shaping you" (story)
  4. "Here's what 3 people found in their DNA" (social proof)
  5. Early access offer ($49, 48h window)

### Phase 2: Organic + Viral
- **Twitter/X:** "The 4 genes most people have that change which supplements work"
  - MTHFR (40% of population), CYP1A2, APOE, FOXO3 — each is inherently shareable
- **Reddit:** r/Supplements, r/Nootropics, r/23andMe (community provides use cases)
- **YouTube:** Partner with biohacking/longevity creators (review fee or rev share)

### Phase 3: SEO (Month 2-3)
- Target keywords: "23andMe supplement recommendations", "MTHFR supplements", "DNA personalized vitamins"
- Content engine: one blog post per SNP (66 SNPs = 66 SEO articles)
- Medium competition, high buyer intent

### Phase 4: B2B (Month 4+)
- Functional medicine doctors / naturopaths
- "White-label patient report" or API access
- Higher LTV, less viral but more defensible

---

## Revenue Projection

### Conservative (3 months post-launch)
- Waitlist: 500 signups
- Conversion: 15% → 75 customers
- Mix: 60% $49 / 30% $149 / 10% $29/mo
- **Month 1:** ~$6,100 one-time + $220/mo recurring
- **Month 3:** ~$2,800/mo assuming modest growth

### Target (with X + organic traction)
- Waitlist: 2,000 signups (one viral tweet can do this)
- Conversion: 20% → 400 customers
- **Month 1:** ~$26,000 one-time + $1,200/mo
- **Month 3:** $8,000/mo with subscription growth

### Why This Can Spike:
- MTHFR alone affects 40% of the population
- One tweet by a micro-influencer (100K+ follows) in biohacking space = 5K+ signups
- Consumer DNA testing is growing — new users regularly looking for "what to do with this data"

---

## What Makes Trait Defensible

1. **Curated SNP database** — our 66 (→ 200 → full catalog) with natural-first recommendations is manually curated. Hard to auto-generate from GWAS alone.

2. **Natural compounds first** — this is a values and positioning choice. The supplement industry defaults to synthetics. We don't. Resonates with biohacking audience.

3. **GWAS integration** — real scientific citations per finding, not bro-science. Different from most DNA wellness products.

4. **Expanding database** — every month we add SNPs, every subscriber gets updates. Subscription model is the moat.

5. **Privacy story** — if we ship client-side parsing, we have "the only DNA wellness app where your DNA never leaves your device."

---

## Open Questions

1. **Brand domain:** `trait.io`, `traitdna.com`, `getyourtrait.com`? Availability TBD.
2. **Privacy model:** Client-side vs server-side processing — needs Josh decision
3. **Email platform:** Formspree (free, dumb) vs Loops.so ($free tier) vs Resend
4. **Compound database expansion:** Do we build a full compound library, or source from an API (Examine.com API, iHerb affiliate)?
5. **Series 6 legal:** Does selling a wellness report create any securities/RIA issues? (Unlikely — we're selling information, not investment/medical advice)
6. **Affiliate revenue:** Add Amazon/iHerb affiliate links to recommended compounds? Could 2x LTV.

---

## Connection to Companion + Pulse

The stack:
```
Trait (genetics layer)
  ↓ feeds
Companion (acts on genetic + behavioral data)
  ↓ runs on
Pulse (autonomous nervous system)
  ↓ embodied in
3D Internet (spatial interface)
```

**Phase 2 (60 days post-launch):** Trait user's genetic profile + Apple Watch biometrics → Companion that knows your biology. "Your cortisol looks elevated today — you have the COMT Val variant that makes stress harder to clear. Here's your protocol adjustment."

This is the real product vision. Trait is the first layer.

---

## First Milestone: $1K MRR in 30 Days

**Definition of done:**
- Working upload → report → payment → delivery flow
- 20+ customers at any mix of pricing
- No customer service fires (privacy, legal, accuracy)

**Then:**
- Iterate based on what customers actually ask about
- Expand SNP database based on most-asked questions
- Build subscription feature (monthly updates)

---

*Next doc: TECH_ARCHITECTURE.md (database schema, API design, deployment)*  
*Blocks cleared by: Josh approving design direction + wiring Formspree/email platform*
