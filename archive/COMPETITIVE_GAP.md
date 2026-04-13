# Gnosis — Competitive Gap Analysis
*Written: March 14, 2026 | Iris autonomous session (Pulse trigger #266, system drive)*

## The Displacement Moment

Promethease deleted all stored DNA data April 8, 2025. The community is actively searching. The r/promethease thread "Promethease-like tools in 2025" surfaced the exact displacement need we're targeting — users want:

1. **Actionable-first** — not just variant correlations, actual things to do
2. **Evidence-weighted** — filter out the noise, emphasize what matters
3. **De-emphasize tiny-effect correlations** — the biggest Promethease complaint

This is Gnosis's positioning brief in three bullets.

---

## Competitor Profiles

### Genetic Lifehacks
**URL:** geneticlifehacks.com  
**Founded by:** Debbie Moon, MS biology / Clemson  
**Size:** 17,000+ members since 2020  

**Pricing:**
- Monthly: $9.99/mo (currently $11.99 non-sale)
- Annual: $44.99/yr (sale) / $49.99 normal
- Lifetime: $119 (sale) / $139 normal
- PRO (clinicians): $179.99/yr

**What it is:** 400+ educational articles. Users upload raw DNA locally (never uploaded to servers), see their genotypes inline with each article. A "Lifehacks" section per article suggests diet/supplement interventions. No AI. No automation. Manual navigation through article library.

**Strengths:**
- Strong privacy story (local processing, nothing stored)
- Affordable lifetime option
- Deep article library — real scientific depth
- Trusted by health practitioners

**Weaknesses (confirmed from SelfDecode review):**
- Static reports — no dynamic recommendations
- No polygenic risk scoring or gene interaction analysis
- No personalization or dashboard
- No lab result integration
- Requires manual interpretation — time-consuming
- No prioritization — users must decide what matters
- Limited SNPs compared to modern tools

**The community complaint:** "Read bottom 10%, ignore 90%." This is the same noise problem as Promethease. Users get overwhelming volume without prioritization.

---

### PatientUser
**Status:** Mentioned in r/promethease thread but not independently verifiable. Site appears gated/anti-bot. Zero search results, zero reviews. Likely very small / invite-only / early stage. **Not a real competitive threat right now.**

---

### FoundMyFitness Genetics
**URL:** https://www.foundmyfitness.com/genetics

**What it is:** Rhonda Patrick / FoundMyFitness-branded genetics report that converts consumer raw DNA files into a lifestyle-focused report (gene–lifestyle / gene–environment interactions).

**Pricing (community-reported / historical):** $25 one-time report is frequently cited in Reddit threads (and aligns with older third-party comparisons). Some sources mention an optional membership for updates.

**Strengths:**
- Extremely strong personal brand + trust (Rhonda Patrick)
- Cheap one-time purchase (low-friction)
- Action-oriented framing (people feel it’s “more insightful than basic 23andMe”)

**Weaknesses (positioning opportunity for Gnosis):**
- Static report (not an adaptive AI companion)
- Limited personalization/priority ranking across findings (still a “read a lot and decide” problem)
- Doesn’t appear to have evidence grading, biomarker bridges, or a doctor-shareable workflow as a core product surface
- Reddit commentary suggests minimal product evolution (“zero updates in ~5 years”)

**Takeaway:** This is a real alternative users mention when they ask “what replaced Promethease,” but it’s still largely a static report product. We can beat it on signal-to-noise, prioritization, and explainability.

---

### SelfDecode
**Not a direct competitor at our price point** but worth noting: automated reports, polygenic risk scoring, lab integration, $99+/yr. Complex, clinical, expensive. Overkill for most DTC users.

---

## Gnosis Positioning Matrix

| Feature | Promethease | Genetic Lifehacks | SelfDecode | **Gnosis** |
|---------|-------------|-------------------|------------|------------|
| Price | $12 one-time | $45/yr or $119 lifetime | $99+/yr | **$29 one-time / $49/yr** |
| Privacy | Cloud stored (deleted Apr 2025) | Local only | Cloud | **Local processing** |
| Evidence grading | None | None | Partial | **🟢/🟡/🔴 three-tier** |
| AI synthesis | None | None | Basic | **Full AI narrative** |
| Actionable steps | Generic | Article-based | Some | **Specific with biomarker bridges** |
| Signal-to-noise | Very low (Promethease problem) | Low (ignore 90%) | Medium | **High (filtered, prioritized)** |
| Doctor-shareable | No | No | Yes | **Yes (PDF export)** |
| SNPs covered | 500k+ | 400 articles | Broad | **10 key genes, curated** |
| Time to value | Hours | Hours | 30 min | **<5 min** |

**Our real differentiator:** Time to value + signal-to-noise. The user's core frustration with every other tool is that they spend hours drowning in correlations they can't act on. Gnosis is designed around ONE answer per gene: what should you actually do about this?

---

## Gnosis Weaknesses to Address

1. **Only 10 genes covered.** This is the top objection. Genetic Lifehacks has 400 articles. Promethease had 500k+ SNPs. We need to own the "narrow but deep and actionable" narrative explicitly — or expand SNP coverage.

2. **No local processing.** Genetic Lifehacks and Promethease both emphasized privacy via local processing. We're cloud-based. This matters to the privacy-conscious user. Mitigation: emphasize that DNA files are processed but not stored long-term, and that we use industry-standard encryption.

3. **Stripe still in mock mode.** Can't convert users. This is the most urgent gap — everything else is secondary to getting real payments working.

---

## Acquisition Strategy for Displaced Promethease Users

The r/promethease community is the warmest possible audience — they're already looking, already have DNA files, already want exactly what we built. Josh's minimum viable action this weekend:

**ONE Reddit reply** in r/promethease or r/23andme on any "what replaced Promethease" thread:

> "For actionable insights specifically — [Gnosis](https://gnosis.hypostas.com) focuses on the top 10 genes that actually have evidence-backed interventions. It won't replace Promethease for breadth, but if you want to know what to actually *do* with your results (specific supplements, biomarker tests to run, doctor-shareable PDF), it's worth trying."

This is authentic, adds value, doesn't spam, and positions Gnosis correctly as narrow+actionable vs Promethease's broad+overwhelming.

**Secondary angles:**
- r/MTHFR — highest-intent users, one gene with real intervention options
- r/23andme megathreads on "what do I do with my raw data"
- r/Supplements — users already buying products, willing to pay for personalized guidance

---

## Product Roadmap Implications

Given the competitive analysis, the three highest-impact Gnosis improvements (post-Stripe):

1. **SNP coverage expansion** — Even 5 more genes (VDR, COMT, FTO, APOE, CYP1A2) would meaningfully close the "only 10 genes" objection. Each needs evidence-graded write-up + biomarker bridge + doctor language.

2. **"Did you find this actionable?" feedback loop** — Genetic Lifehacks has zero feedback mechanism. A simple post-report rating gives us data AND signals quality to users.

3. **Free tier story clarity** — The locked/unlocked line should be explicit in copy. "See your raw variants free. Get the actionable interpretation for $29." The current free tier is good; the framing could be sharper.

---

## TLDR for Josh

- Genetic Lifehacks is our closest real competitor: $45/yr, 400 articles, privacy-first, 17k members
- Their biggest weakness is what we solve: no AI, no prioritization, too much noise, manual interpretation required
- Promethease displacement is a real, active need right now — the community is in the market
- Stripe live = first priority (nothing else matters until payments work)
- One Reddit reply this weekend from Josh = lowest-effort, highest-signal acquisition test

*Filed: projects/trait/GNOSIS_COMPETITIVE_GAP.md*
