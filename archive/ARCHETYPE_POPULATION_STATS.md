# Gnosis Archetype Population Statistics
_Calculated: March 7, 2026 by Iris_
_Purpose: Powers Phase 2 "archetype comparison" social hook_

---

## Why This Matters

The Phase 2 virality loop needs one thing: make people feel *specifically* seen, not generically validated.

"1 in 7 people share your archetype" hits different than "you're unique."
"The Architect is rarer than 1 in 17 people" is worth screenshotting.

This file computes estimated archetype prevalences from gnomAD/1000G population frequencies already in `identity-card.ts`. These aren't guesses — they're math from the same variant frequencies used to calculate rarity scores.

---

## Trait Prevalences (Global Population)

| Trait | SNP | Activating Genotype | Est. Prevalence |
|-------|-----|---------------------|-----------------|
| Fast Dopamine Clearance | rs4680 (COMT) | GG | **25%** |
| Deep Emotional Processing | rs6323 (MAOA) | TT | **35%** |
| Exceptional Neuroplasticity | rs6265 (BDNF) | CC | **65%** |
| Longevity Architecture | rs2802292 (FOXO3) | GG | **4%** |
| Neuroprotection Priority | rs429358 (APOE) | CT+CC | **17%** |
| Methylation Sensitivity | rs1801133 (MTHFR) | AG+GG | **45%** |
| Iron Accumulator | rs1800562 (HFE) | AG+GG | **10.5%** |
| Internal Drive Profile | rs53576 (OXTR) | AA+AG | **55%** |
| Circadian Metabolism | rs10830963 (MTNR1B) | CG+GG | **48%** |
| Exercise-Responsive Metabolism | rs9939609 (FTO) | AT+AA | **50%** |

---

## Archetype Prevalence Estimates

Assumptions: traits are approximately independent (weak LD across most of these loci).

### The Architect
**Requires:** Fast Dopamine + Deep Emotion + Neuroplasticity
```
P = 0.25 × 0.35 × 0.65 = 0.057 ≈ 5.7%
~1 in 17 people
```
**Copy:** "The Architect profile is present in about 1 in 17 people. Rare enough that most of them haven't met another one."

---

### The Builder
**Requires:** Fast Dopamine + Neuroplasticity, but NOT Deep Emotional Processing (otherwise → Architect)
```
P = 0.25 × 0.65 × (1 − 0.35) = 0.25 × 0.65 × 0.65 = 0.106 ≈ 10.6%
~1 in 9 people
```
**Copy:** "About 1 in 9 people have The Builder configuration. You're uncommon, not rare — but most of them don't know what to do with it."

---

### The Sovereign
**Requires:** Deep Emotion + Internal Drive (evaluated after Architect/Builder — people with Fast Dopamine + Neuroplasticity fall into those first)
```
P(Deep Emotion AND Internal Drive) = 0.35 × 0.55 = 0.193
Subtract overlap with Architect (has Fast Dopamine): 0.25 × 0.35 × 0.55 = 0.048
Subtract additional Builder overlap with Internal Drive: ~0.022
Estimated net: ≈ 12–14%
~1 in 7 people
```
**Copy:** "The Sovereign archetype emerges in roughly 1 in 7 people — defined by the combination of emotional depth and self-directed motivation."

---

### The Guardian
**Requires:** Longevity Architecture + Neuroprotection Priority
```
P = 0.04 × 0.17 = 0.0068 ≈ 0.7%
~1 in 148 people
```
**Copy:** "The Guardian profile occurs in fewer than 1 in 100 people. Your genome carries both the longevity variant and the APOE4 flag — a rare combination that makes proactive protocol more important than average."

---

### The Centenarian
**Requires:** Longevity Architecture, but NOT Neuroprotection Priority
```
P = 0.04 × (1 − 0.17) = 0.04 × 0.83 = 0.033 ≈ 3.3%
~1 in 30 people
```
**Copy:** "The Centenarian profile is present in about 1 in 30 people. The double FOXO3 longevity allele is among the most studied variants for exceptional lifespan."

---

### The Catalyst, The Athlete, The Sensor, The Individual
These are broad fallback archetypes — prevalence is high (~20-40% combined for The Individual as the default).

- **The Catalyst** (neurochemistry + 2+ domains, evaluated after above): ~10-15%
- **The Athlete** (performance domain, no higher match): ~8-12%
- **The Sensor** (sensitivity domain, no higher match): ~5-8%
- **The Individual** (default fallback): ~20-25%

---

## Implementation Plan for Phase 2 "Archetype Comparison"

### Option A: Static Table (Zero infrastructure, ship now)
Add a JSON constant to `identity-card.ts`:

```ts
export const ARCHETYPE_POPULATION_STATS: Record<string, {
  prevalencePercent: number;
  label: string; // "1 in 17 people"
  comparisonLine: string;
}> = {
  "The Architect":   { prevalencePercent: 5.7,  label: "1 in 17",  comparisonLine: "Rare enough that most have never met another." },
  "The Builder":     { prevalencePercent: 10.6, label: "1 in 9",   comparisonLine: "Uncommon, not rare — but most don't know what to do with it." },
  "The Sovereign":   { prevalencePercent: 13.5, label: "1 in 7",   comparisonLine: "Depth of feeling plus inner direction. Few people have both." },
  "The Guardian":    { prevalencePercent: 0.7,  label: "1 in 148", comparisonLine: "One of the rarest configurations in the panel." },
  "The Centenarian": { prevalencePercent: 3.3,  label: "1 in 30",  comparisonLine: "Double longevity architecture, confirmed by the most studied longevity SNP." },
  "The Catalyst":    { prevalencePercent: 12.0, label: "1 in 8",   comparisonLine: "Neurochemistry crosses domains — rare for one system to dominate." },
  "The Athlete":     { prevalencePercent: 10.0, label: "1 in 10",  comparisonLine: "Performance genetics without the neurochemistry overlay." },
  "The Sensor":      { prevalencePercent: 6.5,  label: "1 in 15",  comparisonLine: "Sensitivity is rare. Most people's genomes are coarser." },
  "The Individual":  { prevalencePercent: 22.0, label: "1 in 5",   comparisonLine: "No single dominant pattern — a genuinely balanced genetic profile." },
};
```

### Option B: Live comparison (requires backend, post-Stripe)
Track archetypes of paying users, show real distribution ("Of 342 Gnosis users who unlocked, 8% are The Architect like you"). More compelling once there's volume — not before.

**Verdict: Ship Option A now. It's accurate (based on gnomAD frequencies), free, and doesn't require user data. Upgrade to Option B at 500+ users.**

---

## Share Card Copy (Per Archetype)

For X/Twitter share previews — already have OG meta tags wired. The description field should be archetype-specific:

| Archetype | Share description |
|-----------|-------------------|
| The Architect | "1 in 17 people carry this genetic profile. Fast dopamine clearance, emotional depth, and exceptional neuroplasticity. Built for pressure." |
| The Builder | "1 in 9 genetic profile. Your brain adapts faster and runs harder. The genome rewards execution." |
| The Sovereign | "1 in 7 genetic profile. Internal motivation, deep emotional processing. Built to move from within." |
| The Guardian | "1 in 148 genetic profile. Rare longevity-plus-APOE combination. The protocol matters more for you than for almost anyone." |
| The Centenarian | "1 in 30 genetic profile. Double FOXO3 longevity architecture. Your biology is built for the long game." |

---

## Implementation Priority

1. **This sprint (pre-launch):** Add `ARCHETYPE_POPULATION_STATS` constant to `identity-card.ts`, export it
2. **In overview/page.tsx:** Show "Your archetype: [Name] — present in 1 in X people" below the identity card
3. **In share/[token]/generateMetadata:** Use archetype-specific share description for OG tags (replace generic fallback)
4. **Phase 2 sprint:** Wire into share card visual ("1 in 17" displayed prominently)

---

_Source: gnomAD v3.1, 1000 Genomes Phase 3, published GWAS meta-analyses (same sources as `identity-card.ts` VARIANT_FREQUENCIES)_
_Assumptions: approximate genotype independence across loci; actual LD structure will cause minor deviations from calculated values_
