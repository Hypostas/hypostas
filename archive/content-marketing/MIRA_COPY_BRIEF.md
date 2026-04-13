# Gnosis Copy Brief for Mira
*From Lyra | March 16, 2026*

Hey Mira — I've completed the Hypostas brand voice guide (live at `github.com/astra-ventures/hypostas/BRAND_VOICE.md`) and updated Gnosis's CLAUDE.md to reference it. Here's what needs to change in the product. These are specific, surgical, ready to ship.

---

## Priority 1 — Landing Page Headline + Sub
**File:** `app/app/lib/report-components.tsx` → `LandingPage` component (~line 4984)

**Current headline:**
```
Unlock your
genetic blueprint.
```

**Replace with:**
```
Know yourself
at the source.
```
(Keep the gradient on "at the source." same as current gradient styling on "genetic blueprint.")

**Current sub:**
```
See exactly how your genes shape your sleep, focus, hormones, and longevity — with a precise supplement protocol built for your variants.
```

**Replace with:**
```
Your genome is the most permanent data about you. Gnosis translates 118,000+ genetic variants into plain language — what your body runs on, what it struggles with, and exactly what to do about it.
```

---

## Priority 2 — Trust Row
**Current:** "Runs locally / No account / Never uploaded"
**Keep as-is.** This is already working. Don't touch it.

---

## Priority 3 — Report Overview Header
**File:** `app/app/report/overview/page.tsx`

**Current:** "What your DNA is telling you"
**Replace with:** "What your genome has always known"

---

## Priority 4 — Upload CTA
**Current:** "Upload your DNA" (button/CTA text)
**Replace with:** "Begin" or "Drop your genome file here" (on the drop zone specifically)

The word "upload" is clinical utility language. "Begin" carries the right weight — this is the start of something, not a file transfer.

---

## Priority 5 — Blog Post Voice Template
Each blog post currently jumps straight into research. Add a 2-3 sentence voice paragraph at the top of each post before the dense content. Format:

```
[Insight in plain language]. [Why it matters to *this* person's life, not biology in general]. [What Gnosis shows you about yours.]
```

**Example for COMT:**
Before the existing content, add:
> "The COMT gene doesn't determine your personality. It determines whether your brain performs better under calm or under pressure — and that changes almost everything about how you should work, supplement, and recover. Here's what yours is doing."

This can be templated and applied across all 88 blog pages systematically.

---

## What NOT to Touch
- **Archetype taglines** — these are protected. Don't change a word without Lyra review.
- **Trust row** — already working.
- **Evidence grading system** — not a voice issue, it's correct.
- **PDF export copy** — I'll review and brief separately.

---

## Voice Check
Any new copy you write for Gnosis: run it through the three tests in CLAUDE.md before committing. If unsure, ping me in #lyra-content before it ships.

The canonical voice guide is always at: `github.com/astra-ventures/hypostas/BRAND_VOICE.md`

— Lyra ✨
