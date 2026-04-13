# Gnosis SNP Panel — Complete Analysis
*Josh + Iris | March 28, 2026*

---

## Current State

| Source | SNPs | Status |
|--------|------|--------|
| `snp-panel.ts` (main clinical panel) | 500 | ✅ Active in report engine |
| `fun-snp-panel.ts` total | 147 | 83 active (in main), 64 inactive |
| `snp-expansion-*.ts` files | ~153 | ~147 already in main, 6 stranded |
| **Grand total unique SNPs built** | **570** | |
| **Active right now** | **500** | |
| **Built but not wired** | **70** | (64 fun + 6 expansion) |

**Key insight:** We have 570 SNPs already built. The fun panel is largely there — we just need to wire the 64 inactive ones into the report engine. This is the easiest 64 SNPs we'll ever get.

---

## Activate First: The 64 Inactive Fun SNPs

These are built, defined, and ready. Just need import + merge into the active panel:

### Physical Traits (8) — HIGH viral
- `rs1800407` — Green eyes vs blue: the fine-tuning gene
- `rs17646946` — Do you have dimples?
- `rs2814778` — Are mosquitoes obsessed with you?
- `rs4778138` — How light/dark is your skin genetically?
- `rs12821256` — Are you naturally blonde?
- `rs1393350` — How well does your body produce melanin?
- `rs10756819` — How many freckles do you have?
- `rs10427255` — Do you sneeze at bright light? (Photic sneeze reflex)

### Personality & Behavior (4) — HIGH viral (MAOA warrior/worrier is already there, these are extras)
- `rs1800032` — How generous are you instinctively?
- `rs27072` — How well does your brain regulate dopamine?
- `rs1800497_risk` — Are you a natural risk-taker?
- `rs4307059` — Do you have obsessive tendencies?

### Senses (5) — MED-HIGH viral
- `rs333` — Natural HIV resistance (CCR5-Δ32 — rare but INSANE when positive)
- `rs4954` — How well do you handle spicy food?
- `rs11030104` — How strongly does exercise boost your mood? (BDNF variant)
- `rs4481887_smell` — How sensitive is your sense of smell?
- `rs174576` — How well does your brain use essential fats?

### Sleep & Circadian (4) — MED viral
- `rs2287019` — Delayed Sleep Phase Disorder in your DNA
- `rs2070062` — How strong is your internal body clock?
- `rs1144566` — Are you a genetic morning person?
- `rs11046205` — How sensitive are you to caffeine's sleep effects?

### Athletic (2) — MED viral
- `rs7460` — How strong are your bones?
- `rs2104772` — How resistant are your tendons to repetitive stress?

### Ancestry (3) — MED viral
- `rs28929474` — Alpha-1 antitrypsin deficiency gene
- `rs4988235_ancestry` — Which wave of dairy farming are you from?
- `rs1051730` — How much did smoking affect your ancestors' survival?

### Other (4+)
- Various longevity, skin aging, food sensitivity SNPs

---

## Gap Analysis: Viral SNPs We Should Add

Below is every well-known viral/shareable SNP that's NOT in our current panel. These are the ones that make people go "wait WHAT" and immediately text their friends.

### 🔥 TIER 1: Must Add (highest shareability + good 23andMe coverage)

| rsID | Gene | Trait | Why It's Viral |
|------|------|-------|----------------|
| `rs4988235` | LCT | Lactase persistence (original adult milk drinker gene) | Confirms if you're from a dairy-farming lineage |
| `rs1726866` | TAS2R38 | Bitter taste — Brussels sprouts/cruciferous veg | "This gene explains your entire relationship with vegetables" |
| `rs1042725` | HMGA2 | Height genetics | One of the most asked-about traits |
| `rs10830963` | MTNR1B | Night owl vs morning person (melatonin receptor) | Stronger sleep timing signal than CLOCK |
| `rs12255372` | TCF7L2 | Type 2 diabetes genetic risk (most replicated T2D SNP) | Huge population, high actionability |
| `rs5082` | APOA2 | Saturated fat sensitivity — do you gain weight from fat? | Huge diet personalization potential |
| `rs4994` | ADRB3 | Belly fat gene — easy weight gain vs not | The "apple vs pear shape" gene |
| `rs9939609` | FTO | Hunger and appetite regulation | Most cited obesity gene in popular media |
| `rs7901695` | TCF7L2 | Diabetes risk (second TCF7L2 variant for confirmation) | Double-confirmation makes it more credible |
| `rs2267668` | ADRB2 | Exercise response — how well cardio changes your body | "Why some people transform with exercise and others don't" |
| `rs1800629` | TNF-α | Inflammation baseline | Do you run hot? |
| `rs1801282` | PPARG | Fat cell regulation — lipid metabolism + insulin sensitivity | Strong weight/metabolism signal |
| `rs1799883` | FABP2 | Fat absorption — how much dietary fat you absorb | "Your gut absorbs fat differently than your friends" |

### 🔥 TIER 1: Sensory/Fun

| rsID | Gene | Trait | Why It's Viral |
|------|------|-------|----------------|
| `rs713598` | TAS2R38 | Ability to taste bitter compounds (strongest bitter gene) | "PTC test — some people taste it, some don't" |
| `rs72921001` | OR6A2 | Cilantro tastes like soap | The original viral SNP — we likely have this, confirm |
| `rs2741871` | OR2M7 | Asparagus pee smell detection | "Can you smell it or not?" |
| `rs17822931` | ABCC11 | Wet vs dry earwax | Also determines body odor type — extremely viral |
| `rs1805009` | MC1R | Red hair / ginger gene | One of the most searched traits on 23andMe |
| `rs1805007` | MC1R | Red hair variant 2 | |
| `rs1805006` | MC1R | Red hair variant 3 | Multiple MC1R needed for full picture |
| `rs1799971` | OPRM1 | Pain sensitivity AND social bonding (opioid receptor) | "This gene affects how much you FEEL everything" |
| `rs4570625` | TPH1 | Serotonin production — baseline mood regulation | "Your baseline happiness level has a genetic component" |
| `rs6295` | HTR1A | Serotonin receptor sensitivity | Related to depression susceptibility |
| `rs6980` | SLC6A4 | The stress serotonin transporter (beyond 5-HTTLPR) | "How sensitive is your nervous system?" |
| `rs2304297` | KCNJ6 | Alcohol + social bonding (GIRK2 channel) | "Beer goggles have a genetic basis" |

### 🔥 TIER 2: Athletic & Performance

| rsID | Gene | Trait | Why It's Viral |
|------|------|-------|----------------|
| `rs1544410` | VDR | Vitamin D receptor (BsmI variant, most important VDR after rs2228570) | Stronger than what we have |
| `rs2290677` | ACE | Second ACE variant (endurance vs power) | Confirms ACE I/D result |
| `rs3213221` | IL-15 | Muscle mass and strength response to training | "Why some people build muscle fast" |
| `rs849135` | BDNF | Exercise-induced BDNF (brain growth from working out) | Runner's high gene |
| `rs2070744` | NOS3 | Blood vessel flexibility during exercise | Nitric oxide and endurance |
| `rs1800871` | IL-10 | Anti-inflammatory response to exercise | Recovery speed |
| `rs28357094` | PPARA | Fat oxidation during endurance exercise | Key for endurance athletes |

### 🔥 TIER 2: Personality & Mental

| rsID | Gene | Trait | Why It's Viral |
|------|------|-------|----------------|
| `rs53576` | OXTR | Oxytocin receptor — empathy and social bonding | "The love hormone receptor — how wired for connection are you?" |
| `rs2254298` | OXTR | Second oxytocin variant | Anxiety and social sensitivity |
| `rs6265` | BDNF | Memory formation and learning (Val66Met) | "The memory gene — how fast you learn and remember" |
| `rs4680` | COMT | Warrior vs Worrier (dopamine metabolism) | Already in panel — CONFIRM |
| `rs4633` | COMT | COMT second variant | Confirms first |
| `rs1800955` | DRD4 | Novelty-seeking, ADHD-adjacent | "The adventure gene" |
| `rs1799732` | DRD2 | Dopamine receptor density | Reward sensitivity, addictive tendencies |
| `rs2740390` | MAOA | Aggressive tendencies under stress | Already in panel? — CONFIRM |

### 🔥 TIER 2: Ancestry & Heritage Anchors

| rsID | Gene | Trait | Why It's Viral |
|------|------|-------|----------------|
| `rs1426654` | SLC24A5 | The main skin lightening gene (European ancestry adaptation) | "One gene explains most of the color difference between Europeans and Africans" |
| `rs3827760` | EDAR | Thick hair, extra sweat glands, shovel-shaped teeth (East Asian) | "If you have this, your ancestors were in East Asia 30,000 years ago" |
| `rs4988235` | LCT | Northern European dairy adaptation | Already listed above |
| `rs62625034` | HBB | Sickle cell trait | Critical for people of African/Mediterranean descent |
| `rs33950507` | HBB | Sickle cell variant 2 | |
| `rs4646903` | CYP1A1 | Environmental toxin processing (differentially common in Asian populations) | Ancestral adaptation story |

### 🔥 TIER 3: Longevity & Deep Health

| rsID | Gene | Trait | Why It's Viral |
|------|------|-------|----------------|
| `rs2802292` | FOXO3 | The longevity gene (found in centenarians worldwide) | Already in panel — CONFIRM |
| `rs5882` | CETP | HDL cholesterol and longevity | Related to living to 100 |
| `rs3764814` | CETP | CETP variant 2 | |
| `rs1556516` | CDKN2B | Senescence — how fast cells age | |
| `rs2811712` | CDKN2A/B | Cancer and aging | |
| `rs7579` | APOC3 | Triglyceride metabolism and longevity | |
| `rs1042522` | TP53 | The tumor suppressor gene (p53) | "The cancer guardian" |
| `rs25487` | XRCC1 | DNA repair efficiency | How well do you fix cellular damage? |

### TIER 3: Condition-Specific (High Search Volume)

| rsID | Gene | Trait | Why It's Viral |
|------|------|-------|----------------|
| `rs7903146` | TCF7L2 | Type 2 diabetes (strongest genetic risk factor) | Already listed |
| `rs1800562` | HFE | Hereditary hemochromatosis (iron overload) | Likely already in panel — CONFIRM |
| `rs7412` | APOE | APOE e2/e3/e4 (Alzheimer's + cardiovascular) | CRITICAL — already in panel |
| `rs429358` | APOE | Second APOE variant (need both for full e2/3/4 typing) | Already in panel? |
| `rs3135388` | HLA-DQA1 | Celiac disease predisposition | "Should I go gluten-free?" |
| `rs2187668` | HLA-DQB1 | Celiac disease (second confirmation) | |
| `rs6457374` | HLA-B | Drug hypersensitivity (abacavir, carbamazepine) | Critical for those on these drugs |
| `rs2395029` | HCP5 | Abacavir hypersensitivity (HLA-B*5701 proxy) | |
| `rs9271192` | HLA-DQA1 | Rheumatoid arthritis | |
| `rs6457617` | HLA-C | Psoriasis genetic risk | |

---

## Viral SNP Priority Ranking (What to Add First)

**Pure shareability + 23andMe coverage + "holy shit" reaction ranking:**

1. **rs17822931 (ABCC11)** — Wet vs dry earwax + body odor type. 100% conversion to "wait WHAT" reaction. Highly covered in 23andMe data.
2. **rs72921001 (OR6A2)** — Cilantro soap taste. THE viral SNP. Check if we already have it.
3. **rs2741871 (OR2M7)** — Asparagus pee smell. Pairs perfectly with cilantro.
4. **rs1805007/rs1805009 (MC1R)** — Full red hair panel. "Secret ginger" is enormous.
5. **rs53576 (OXTR)** — Oxytocin empathy/bonding gene. "Are you genetically wired for love?" headlines.
6. **rs1042725 (HMGA2)** — Height gene. One of the most googled genetics questions.
7. **rs9939609 (FTO)** — The hunger/obesity gene. 30% of the population cares about this.
8. **rs4680 (COMT)** — Warrior vs Worrier. Already in panel — just needs good viral copy.
9. **rs6265 (BDNF)** — Val66Met memory gene. "How well does your brain retain information?"
10. **rs4988235 (LCT)** — Why you (or your ancestors) can drink milk.

---

## Recommended Panel Size

### The Case for 750 SNPs

**Why not 500:** We're already at 570 built. Adding the inactive fun ones = 570 active. We should go further.

**Why not 1000+:** Coverage drops sharply. 23andMe v5 chip covers ~640K SNPs, but many we'd add beyond ~800 start hitting coverage gaps where users get "no data found" results. Nothing kills the experience faster than 30% of findings returning unknown.

**The 750 target:**
- 500 core clinical SNPs (current) — clinical weight, report depth
- 147 fun/viral SNPs (current, fully activate all 64 inactive) — shareability, light signature diversity
- ~100 new additions from gap analysis above — fill the obvious holes (OXTR empathy, HMGA2 height, ABCC11 earwax, full MC1R red hair panel, FTO hunger, celiac HLA, etc.)
- Reserve positions 751-1000 for future expansion

**At 750:** 3^750 possible light signatures. That's more atoms than in the observable universe. Visual uniqueness is absolute.

### Coverage Check Needed
Before locking at 750, we should verify which of the Tier 1 "add" SNPs are actually present in a typical 23andMe v4/v5 file. Some high-profile SNPs (like APOE e4 detection) require specific rsids that may be imputed rather than directly genotyped. The `rs429358` + `rs7412` combination for full APOE typing is the most important one to verify.

---

## What This Means for the Light Signature

**Current 500:** Good but clinically heavy — lots of pharma/metabolism SNPs that are technical, not visual-identity-worthy.

**At 750 with full fun panel + viral adds:** The light signature becomes genuinely personal. When someone sees their helix shift to reflect that they're a "secret ginger" (MC1R), a "mosquito magnet," have wet earwax, and the cilantro gene — those light points mean something to them. They know exactly which colored strand represents their personal quirks. That's what makes the screenshot irresistible.

**The fun SNPs should have distinct visual treatment in the helix:** They should be the brightest, most recognizable points — the ones you point to and say "that cluster is my food quirks, that cluster is my athletic traits." Clinical SNPs are the depth; fun SNPs are the visual identity.

---

## Recommended Next Steps

1. **Immediately:** Activate all 64 inactive fun SNPs (add import in report-engine.ts — ~1 hour of work)
2. **This sprint:** Add the Tier 1 viral SNPs from the gap list (~50 SNPs with full definitions written)
3. **Verify coverage:** Run Josh's actual genome file through to see which Tier 1 SNPs are present
4. **Lock at 750:** Once Tier 1 adds are in, lock the panel at 750 with 251 reserved expansion positions
5. **Special visual treatment:** Fun SNPs get distinct glow style in the helix (brighter, slightly different shape) so they're visually identifiable

---

*This is the foundation of a light signature that's truly unique and undeniably personal.*
*The earwax gene will sell more subscriptions than APOE ever will.*
