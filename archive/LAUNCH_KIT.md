# Gnosis — Launch Execution Kit
*Built March 12, 2026 — Ready to execute*

The product is done. The SEO layer is deployed. The paywall works. The first customer is a distribution problem, not a product problem. This kit gives Josh everything he needs to execute in one session.

---

## 🎯 Priority Order

**Today (15 min):** Reddit post in r/23andMe → most direct path to first customer
**This week:** Product Hunt launch → volume, credibility, backlink
**Ongoing:** HN + X → compound SEO authority

---

## 📍 Reddit — Highest-Conviction Targeting

### Post 1: r/23andMe (300k+ members, many currently displaced)
**Best time:** Tuesday–Thursday, 9 AM–12 PM EST

**Title:**
> "I built a free alternative to Promethease that actually explains what your variants mean (not just lists them)"

**Body:**
```
Hey r/23andMe,

Like a lot of people here, I've been sitting on years of 23andMe raw data and never felt like I got real value out of it. Promethease shows you a wall of 900 variants. ChatGPT gives generic disclaimers. The $199 options are overkill.

I spent the last few months building something different. It's called Gnosis.

**What it actually does:**
- Processes your raw data entirely in your browser (nothing uploaded to our servers)
- Focuses on 178 high-signal variants instead of drowning you in 900+ low-evidence ones
- Shows your top 3 findings free — full protocol is $29 one-time (not a subscription)
- Each finding has an evidence grade: 🟢 lifestyle hint vs 🟡 monitor + biomarker vs 🔴 discuss with clinician
- Includes specific supplement forms, doses, and cycling schedules (not just "consider vitamin D")
- Biomarker bridge: tells you what blood tests actually measure each genetic risk directly

**What I tried to fix about the existing tools:**
- Promethease: 900 variants, no protocols, no evidence grading. You stare at a spreadsheet.
- SelfDecode: $99–$295/year, aggressive upsells, same generic info behind a pretty UI
- ChatGPT: hallucinates dosages, no evidence grading, loses context between sessions
- The Gary Brecka problem: MTHFR ≠ "you need methylfolate." Gnosis shows what clinical evidence actually says — and when it says "get a homocysteine test instead"

**One honest disclaimer:** We follow Gary Brecka's *opposite* methodology. If clinical guidelines say genotype-specific dosing isn't supported, we say so. The goal is to help you arrive at your doctor's office with better questions, not to sell you supplement stacks.

Try the sample report first (no file upload needed): https://gnosis.hypostas.com/sample
Or upload your own raw data: https://gnosis.hypostas.com

Happy to answer any questions. Particularly curious what genes/traits you'd want to see covered.
```

**Comment to add immediately after posting:**
```
For context on the evidence grading system: we use three tiers.

🟢 Lifestyle hints — BDNF, FTO, PGC-1α. These are real associations but the right response is behavioral (exercise, sleep, diet), not supplement stacks.

🟡 Monitor + biomarker — MTHFR, VDR, CYP1A2. These have moderate evidence. The right response is checking the direct biomarker (homocysteine, 25-OH-D, caffeine response) rather than assuming the genetic variant means you need supplementation.

🔴 Clinician-tier — APOE ε4 is the main one. Legitimate clinical significance. Discuss with a doctor, not a supplement company.

This was the hardest design decision. Every competitor gives you MTHFR C677T and says "take methylfolate." Clinical guidelines explicitly advise against this. We chose accuracy over the appearance of actionability.
```

---

### Post 2: r/Nootropics (900k members, supplement-aware, data-literate)
**Title:**
> "Built a tool that gives you gene-specific supplement protocols from your raw DNA data — with evidence grading"

**Body:**
```
r/Nootropics is probably the most appropriate community to be honest with about what genetic data can and can't tell you.

I built Gnosis because I was frustrated with the options: Promethease (data dump, no protocols), SelfDecode (expensive subscription, generic protocols), or asking ChatGPT (hallucinated dosages, no evidence grading).

**The evidence grading system I built:**

🟢 Lifestyle tier (BDNF, FTO, PPARGC1A) — exercise and sleep modulate these more than supplements do. The genetic association is real, the supplement response is weak.

🟡 Biomarker-first tier (MTHFR, VDR, CYP1A2) — don't supplement to the genotype, supplement to the biomarker. MTHFR C677T doesn't mean you need methylfolate; high homocysteine means you might.

🔴 Clinician tier (APOE ε4) — this is where genetic variants have actual clinical implications. These get flagged explicitly as "discuss this with your doctor."

**What I actually built it for:**
The overlap between COMT Val158Met (dopamine catabolism), BDNF Val66Met (BDNF secretion efficiency), and SLC6A4 5-HTTLPR (serotonin reuptake) compounds in ways that single-gene tools can't surface. Gene-gene interactions are where the interesting stuff is.

**Free tier:** Top 3 findings + archetype + Gnosis score
**$29 one-time:** All findings + specific protocols + biomarker bridge + gene-gene interactions + PDF export

Sample report (no file needed): https://gnosis.hypostas.com/sample

Note on the APOE section specifically: we built the Alzheimer's risk module carefully. It surfaces risk without catastrophizing, includes CTSB (exercise-induced BDNF upregulation) as the counterfactual, and explicitly routes APOE ε4/ε4 carriers to clinician discussion. Happy to talk through the design decisions.
```

---

### Post 3: r/longevity (180k members, high overlap with 23andMe users who care about optimization)
**Title:**
> "Show r/longevity: I built a longevity-focused DNA analysis tool — focused on the variants that actually have clinical evidence"

**Body:**
```
Long-time lurker, first post. Built something I think this community will have strong opinions about.

Gnosis analyzes your 23andMe/AncestryDNA raw data and focuses specifically on the longevity-relevant variants with actual evidence behind them: FOXO3 (insulin signaling, caloric restriction response), KLOTHO (VS variant, ~1.5–2 years extended median lifespan), MTHFR/APOE (cardiovascular + cognitive aging), PPARGC1A (mitochondrial biogenesis), CTSB (exercise-induced BDNF — the mechanism behind why aerobic exercise prevents cognitive decline).

**What I tried to get right:**

*Evidence calibration:* I read every criticism of DTC genetics. The ~40% false positive rate on raw data. The MTHFR overclaiming. The Gary Brecka backlash. The Promethease complaint that it generates anxiety without actionability. Gnosis uses a three-tier evidence system specifically to address this.

*Actionability over completeness:* We don't surface every variant. We surface the ones where there's a clear pathway from genotype → lifestyle/biomarker/clinical action.

*No genotype-specific supplement dosing without evidence:* This is the hardest one. MTHFR C677T + C677T has a real metabolic effect. Clinical guidelines still say: measure homocysteine, supplement to the biomarker, not the genotype. We follow the guidelines even where they're less satisfying than a specific protocol.

**The longevity stack specifically:**
FOXO3 rs2802292 (G allele → reduced FOXO3 expression → standard intermittent fasting + metformin monitoring)
KLOTHO rs9536314 (KL-VS heterozygous → higher Klotho → enhanced cognitive resilience; homozygous → paradoxical reversal, see Dubal et al. 2014)
PPARGC1A rs8192678 (Ser482 → reduced PGC-1α activity → VO2max training > HIIT for this genotype)

The KLOTHO one is interesting — the VS/VS (homozygous) carriers actually have worse outcomes than VS/non-VS. That nuance doesn't appear in most DTC tools.

Sample report: https://gnosis.hypostas.com/sample
Full product: https://gnosis.hypostas.com

What longevity markers do you most want to see? Still building.
```

---

### Post 4: r/genetics (250k members, skeptical audience — best for credibility-building)
**Title:**
> "Show r/genetics: DNA analysis tool that explicitly uses evidence tiers and discourages genotype-specific supplementation — does the framing pass muster?"

**Body:**
```
I know this community is (rightfully) skeptical of DTC genetics tools. I built one and I'd rather get torn apart here than get it wrong in production.

Gnosis (gnosis.hypostas.com) analyzes 23andMe/AncestryDNA raw data. The design choices I made that I think differentiate it from the usual DTC garbage:

**Evidence grading:**
🟢 Lifestyle associations (BDNF Val66Met, FTO rs9939609, PGC-1α rs8192678) — behavioral interventions, not supplement protocols
🟡 Biomarker-first (MTHFR C677T, VDR rs2228570, CYP1A2 rs762551) — measure the downstream biomarker, not the upstream genotype
🔴 Clinician tier (APOE ε4, CTSB T/T + APOE ε4 compound) — explicit clinical significance, routes to physician discussion

**What we explicitly DON'T do that most tools do:**
- Genotype-specific methylfolate dosing for MTHFR (guidelines don't support this)
- Anxiety-generating APOE ε4 disclosure without context (we include the CTSB counterfactual + lifestyle modifier data)
- Treating rs numbers as equivalent in clinical significance regardless of effect size or replication status

**Where I'd want expert review:**
1. The KLOTHO section — VS/VS paradoxical reversal is based on Dubal et al. 2014. Is this robust enough to surface to consumers?
2. The COMT × MAO-A interaction matrix — I built gene-gene interactions but I'm not confident in all the compound genotype interpretations
3. The MTHFR language — I went with "associated with reduced folate processing" + "confirm with homocysteine blood test" rather than "you have reduced methylation." Does this adequately prevent overclaiming?

Sample report (no upload needed): https://gnosis.hypostas.com/sample

I'm not asking for endorsement. I'm asking: does the epistemology pass? What would you change?
```

---

## 🚀 Product Hunt Launch

**Optimal timing:** Tuesday or Wednesday, 12:01 AM PT (Product Hunt day resets at midnight PT)

### Tagline (under 60 chars)
> "Your 23andMe data, actually explained — $29, no subscription"

### Alternative taglines (pick one):
- "Genetic analysis with evidence grades — not 900 variants, 178 that matter"
- "What Promethease should have been — protocols, not spreadsheets"

### Description (260 words)
```
23andMe is bankrupt. Promethease gives you 900 variants and no protocols. SelfDecode costs $295/year and gives you the same generic recommendations. The DNA data people paid for is sitting unused because the tools to interpret it are either too overwhelming or too expensive.

Gnosis is a one-time $29 genome analysis that actually tells you what to do.

**What makes it different:**

Evidence grading. Every finding is marked: 🟢 lifestyle hint, 🟡 monitor with biomarker, or 🔴 discuss with clinician. We don't give you genotype-specific methylfolate dosing when clinical guidelines say to measure homocysteine instead. Accuracy over the appearance of actionability.

Specific protocols. Not "consider vitamin D." Specific doses, forms (D3 + K2 vs D3 alone), cycling schedules, and what to monitor. Built from the primary literature.

Biomarker bridges. MTHFR? The direct measure is homocysteine. VDR? 25-OH-D. APOE? ApoE protein, p-tau 217. Every genetic risk gets a blood test that measures it directly.

178 high-signal variants. Not 900 low-evidence ones. Gene-gene interactions. COMT × BDNF, MTHFR × CBS, FOXO3 × PPARGC1A — the compound genotypes that single-gene tools miss.

Privacy. Your file never leaves your browser. Processed in WebAssembly locally. Only the variant markers needed for analysis are used.

Free: top 3 findings + your genetic archetype + Gnosis Score
$29 one-time: full report + all protocols + biomarker bridge + gene-gene interactions + PDF export

[Sample report link — no file upload needed]
```

### First comment (post immediately after launch):
```
Hey PH 👋 — I'm Josh, I built this.

The short version: I had my own 23andMe data, got frustrated with every existing option, and spent three months building what I actually wanted.

The thing I'm most proud of is the evidence grading system. It took deliberate restraint — every competitor's incentive is to give you a specific supplement protocol for every gene because it feels actionable. The reality is that for MTHFR, the clinical evidence says "measure homocysteine" not "take methylfolate." We built the less satisfying answer because it's the accurate one.

The things I'm least confident about and would love feedback on:
1. Does the free tier show enough value before the paywall? (Top 3 findings + archetype + score)
2. Is $29 one-time the right price, or does it signal "cheap = low quality"?
3. For the APOE ε4 carriers in the room — did we handle the disclosure correctly?

I'll be here all day. Ask me anything.
```

### Gallery plan (5 images):
1. **North-star card** — Gnosis Score + archetype + top finding in one view (the hero card)
2. **Finding card** — evidence tier badge, gene, protocol with specific doses
3. **Biomarker bridge** — showing the MTHFR→homocysteine connection
4. **Gene-gene interaction** — COMT × BDNF compound genotype table
5. **Archetype card** — the shareable identity card (social viral loop)

### X/Twitter thread for launch day:
```
Tweet 1:
Today I launched Gnosis on Product Hunt. The pitch: your 23andMe data, actually explained.

The real pitch: a $29 alternative to $295/year tools that give you the same generic advice.

[PH link]

Tweet 2:
The thing that makes Gnosis different isn't the UI or the price.

It's the evidence grading.

🟢 Lifestyle hint (behavior > supplements)
🟡 Monitor with a biomarker first
🔴 Talk to a clinician

Every finding is rated. Most tools skip this because specificity is uncomfortable.

Tweet 3:
MTHFR C677T — the most googled genetic variant.

Every DTC tool: "You have reduced methylation. Take methylfolate."

What clinical guidelines actually say: "Measure homocysteine. Supplement to the biomarker, not the genotype."

We built the accurate answer instead of the satisfying one.

Tweet 4:
Privacy design: your file never leaves your browser.

WebAssembly processes everything locally. Only the specific variant markers needed for analysis are used. No DNA file uploaded, ever.

This was non-negotiable. 23andMe bankruptcy taught people why.

Tweet 5:
Free tier: top 3 findings + genetic archetype + Gnosis Score.
$29 one-time: everything — 178 variants, full protocols, biomarker bridge, gene-gene interactions, PDF export.

No subscription. No annual fee. Your genome doesn't change.

[Sample report — no file needed]
```

---

## 💡 Hacker News — Show HN

**Post as:** "Show HN: Gnosis – DNA analysis with evidence tiers (not 900 variants, $29 not $295/yr)"

**Body:**
```
I built this after sitting on 5 years of 23andMe raw data and finding every existing tool either overwhelming (Promethease: 900 variants, no guidance) or overpriced (SelfDecode: $295/year, generic recommendations).

The design goal was epistemic accuracy over the appearance of actionability. The hardest part: building a product that sometimes tells you "the clinical evidence doesn't support a specific protocol here — measure this biomarker instead." That's less satisfying than a supplement stack, but it's what the literature says.

Technical notes:
- Processes raw DNA files entirely in browser using WebAssembly (no upload)
- 178 curated high-evidence variants (vs 900+ in most tools)
- Evidence grading on every finding: lifestyle association vs biomarker-first vs clinician-tier
- Gene-gene interactions (COMT × BDNF, MTHFR × CBS, FOXO3 × PPARGC1A)
- Stripe integration for $29 one-time unlock

Sample report (no file needed): gnosis.hypostas.com/sample

Happy to discuss the evidence-grading framework, the variant selection criteria, or the WebAssembly implementation.
```

---

## 📧 Newsletter Outreach — Execution Guide

The 5 personalized emails are in `NEWSLETTER_OUTREACH_EMAILS.md`.

**Order of operations (send in this sequence):**
1. Ben Greenfield first — most likely to try it publicly, largest fitness/biohacking audience
2. Rhonda Patrick — most scientifically credible, best for trust signals
3. Bryan Johnson — highest-profile, but explicit that you're not asking for sponsorship
4. Eric Topol — best for the "evidence-grading AI" angle, academic credibility
5. Peter Attia — most selective, send last so you have data if he asks about uptake

**Best send time:** Tuesday or Wednesday, 8–9 AM EST
**Follow-up:** Once, 5 business days later, half the length of the original

---

## ✅ Josh's Action Checklist

**Right now (20 min):**
- [ ] Post Reddit #1 (r/23andMe) from personal account — copy above
- [ ] Reply to your own post with the evidence-grading comment immediately

**This week:**
- [ ] Choose a Product Hunt launch day (Tue/Wed)
- [ ] Take 5 screenshots for the gallery
- [ ] Post the Show HN

**When you have 30 min:**
- [ ] Send Rhonda Patrick email
- [ ] Send Ben Greenfield email

---

*First customer is one good Reddit post away.*
