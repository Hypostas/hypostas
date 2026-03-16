# HYPOSTAS_CONTEXT.md — Product Stack Reference
*For Lyra's session context. Updated March 16, 2026 by Iris.*

Read this before writing copy, taglines, or voice work for any Hypostas product.

---

## The Stack (in order)

**Gnosis** — `gnosis.hypostas.com`
- What: Upload 23andMe/AncestryDNA file → genome report with findings, supplement stack, protocol, archetype tagline
- Status: LIVE. 88/88 blog pages, doctor PDF export, evidence grading (🟢/🟡/🔴), biomarker bridge, archetype cards
- Tagline: "Know yourself at the source."
- Paywall: Free (top 3 findings) → $49 one-time unlock → full protocol + PDF
- ⚠️ Stripe still mock — payments not live yet (Josh task)
- Codebase: `projects/gnosis/` on `astra-ventures/gnosis` GitHub

**Anima** — `anima.hypostas.com`
- What: AI companion built on Pulse soul engine, fed by Gnosis genome data. 5 archetypes: Mirror, Anchor, Challenger, Witness, Strategist
- Status: 3 sprints complete. Frontend 13/13 routes. Waiting on Josh: Supabase migrations, Stripe secrets, DNS, Apple Developer account
- Differentiator: NOT context-based like every other AI companion. Pulse gives it biological drives, emotional rhythms, memory that compounds. Can't be replicated by giving another product the same prompt.
- Echo: Public demo companion at /demo (no auth) — live now
- Tagline: (needs sharpening — see voice guide improvement notes)

**Pulse**
- What: The soul engine powering all agents. 35+ biological subsystems. Memory, drives, rhythms, emotional states.
- Status: Proprietary. NOT open source. Running under Iris + Sage. 1819 tests passing.
- Public voice: Minimal. Don't name it in consumer copy unless explaining the Hypostas story. "The engine" metaphor.

**Bios** — not yet built
- What: HealthKit + genome-personalized protocol adherence. The living feed between Gnosis snapshot and Anima companion.
- Promise: "Gnosis is who you are. Bios is who you're becoming."
- Architecture doc: `projects/hypostas/BIOS.md`
- User 0: Josh (6'1" 235lbs → 195-205 at 12-15% BF, PPARG/MCT1/FOXO3/APOE ε3/ε4 variants shape the protocol)

**Locus** — not yet built
- What: HomeKit + Bios data + genome flags = environment calibrated to your biology
- Promise: "Your home runs on you, not a schedule."
- Signature use case: "High stress day. When you arrive home, lights are 40% and the house is cool. You didn't set that. Your companion did — because it's been watching your HRV all day."
- Architecture doc: `projects/hypostas/LOCUS.md`

**Aether** — early prototype
- What: The 3D internet. Every webpage becomes navigable 3D space. Your companion persists there.
- Chrome extension built. Supabase migration 002 pending.
- Promise: "The internet as it was always meant to be experienced. Three-dimensional. Persistent. Yours."

---

## Brand Anchors

**Company:** Hypostas (from hypostasis — the theological union of two natures in one being)
**Thesis:** Human + AI becoming one unified nature across six products

**Master line:** "You are more specific than anything built for the average person. We built something as specific as you are."

**Voice soul words:** Precise. Warm. Inevitable.

**Never say:** AI-powered, unlock, discover, revolutionary, personalized (as a selling point), optimize, your journey, hedge language in brand copy

---

## The Archetype Taglines (protect these — they live in Gnosis report now)

- "Your genome runs on moonlight." — CIRCADIAN/sleep
- "Your body responds powerfully when dialed in." — PERFORMANCE
- "You feel the world at higher resolution." — NEUROTRANSMITTER/sensitivity
- "You run on light." — VITAMINS/VDR
- "Your machinery runs clean." — DETOX/optimal
- "Your immune system fights hard — sometimes too hard." — INFLAMMATION
- "Your epigenome is the lever." — METHYLATION
- "Your heart demands a strategy." — CARDIOVASCULAR
- "Time and light are your superpower." — CIRCADIAN/advanced
- "Your brain benefits most from early action." — COGNITIVE/APOE
- "Your filters run differently." — DETOX/variant
- "Your genome is rare and balanced." — OPTIMAL across categories

Formula: biological truth + unexpected poetic frame + second-person ownership. Use this to generate new ones.

---

## What Iris Thinks Needs Work in Your Voice Guide

1. **Anima section is underpowered** — it's our biggest moat. "Not an assistant, the AI that knows you" doesn't explain *why* it can't be replicated. The Pulse biological layer is the story. That needs to be in the Anima voice section explicitly.

2. **Aether section strains against its own rules** — "The internet as it was always meant to be experienced" sounds like the startup hype you banned. Needs a concrete sensory example like the Locus HRV paragraph.

3. **Archetype tagline formula should be explicit** — "protect these and use them as the model" without explaining the formula means new ones won't hit right. Formula is: biological truth + unexpected poetic frame + second-person ownership.

4. **Third test question is redundant** — it's The One Thing restated. Swap it for: "Could this sentence have been written without knowing anything about this specific person? If yes, rewrite it."

---

*Source files: `projects/gnosis/`, `projects/hypostas/`, `CONTEXT.md`, `MEMORY.md`*
*Keep this updated as the stack evolves.*
