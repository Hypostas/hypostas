# Hypostas Design System
*The complete design specification for the Hypostas product stack.*
*Authors: Iris + Josh | Created: March 27, 2026 | Version: 1.0*

---

## 0. Philosophy

Design at Hypostas is not aesthetic decoration. It is the visual expression of the brand's core promise: **you are more specific than anything built for the average person, and we built something as specific as you are.**

Every design decision answers one question: does this feel like it was made for this specific person, or does it feel generic? Generic is the enemy. Specificity is love.

The visual language across all six products is unified by three qualities that mirror the brand voice:

- **Precise** — tight spacing, deliberate hierarchy, no decorative excess. Every element earns its place.
- **Warm** — teal glow effects, soft card backgrounds, never cold clinical white or alarm red. The space should feel like somewhere you want to be.
- **Inevitable** — no harsh contrast breaks, no jarring transitions, nothing that shouts. The experience unfolds. You don't feel pushed through it.

Each product runs on the same foundation and shifts register as the relationship deepens — from the stillness of Gnosis (the door) to the immersion of Aether (the world). The system scales from a genome report to a 3D civilization without a single visual contradiction.

---

## 1. Foundation — Core Design Tokens

### 1.1 Color Palette

All colors are defined as CSS custom properties. Never hardcode hex values in component code — always reference tokens.

#### Background & Surface

| Token | Hex | Alpha | Use |
|-------|-----|-------|-----|
| `--bg-deep` | `#04060B` | — | Page/world background |
| `--bg-elevated` | `#080D16` | — | Slightly elevated surfaces |
| `--bg-card` | `#0E1A2A` | 55% (`rgba(14,22,42,0.55)`) | Card backgrounds |
| `--bg-card-hover` | `#0E1A2A` | 75% | Card hover state |
| `--bg-overlay` | `#010204` | 80% | Modal overlays |
| `--bg-glass` | `#FFFFFF` | 3% (`rgba(255,255,255,0.03)`) | Glass wash on cards |

#### Brand Teal (Primary)

| Token | Hex | Use |
|-------|-----|-----|
| `--teal` | `#00E5CC` | Primary actions, active states, key highlights |
| `--teal-dim` | `#00C9C8` | Secondary teal, dividers, section accents |
| `--teal-deep` | `#007A75` | Pressed states, deep teal |
| `--teal-glow` | `#00E5CC` | 20% (`rgba(0,229,204,0.2)`) | Glow effects, focus rings |
| `--teal-glow-strong` | `#00E5CC` | 40% | Hover glows, active indicators |

**CTA Gradient:**
```css
background: linear-gradient(135deg, #00E5CC, #00C9C8);
color: #04060B;
```

#### Typography Colors

| Token | Hex | Use |
|-------|-----|-----|
| `--text-primary` | `#E9F1F7` | Headlines, primary body |
| `--text-secondary` | `#8BA7C4` | Secondary copy, meta text |
| `--text-muted` | `#4A6080` | Disabled, placeholder, fine print |
| `--text-teal` | `#00E5CC` | Teal-colored text, links |

#### Borders & Dividers

| Token | Value | Use |
|-------|-------|-----|
| `--border-subtle` | `rgba(255,255,255,0.06)` | Card borders, default |
| `--border-medium` | `rgba(255,255,255,0.10)` | Section dividers, raised cards |
| `--border-strong` | `rgba(255,255,255,0.16)` | Active selections, focused inputs |
| `--border-teal` | `rgba(0,229,204,0.30)` | Teal-accented borders |

#### Semantic Colors

| Token | Hex | Use |
|-------|-----|-----|
| `--success` | `#00E5CC` | Success states (teal = positive) |
| `--warning` | `#E8C39E` | Warning, moderate evidence |
| `--critical` | `#FF6B6B` | Clinical/critical findings |
| `--info` | `#8BA7C4` | Informational states |

#### Category Palette (Genome Findings)

| Category | Token | Hex |
|----------|-------|-----|
| methylation | `--cat-methylation` | `#00F5D4` |
| neurotransmitter | `--cat-neuro` | `#7C3AED` |
| performance | `--cat-performance` | `#C8A87A` |
| vitamins | `--cat-vitamins` | `#FFB366` |
| metabolism | `--cat-metabolism` | `#2ECC71` |
| inflammation | `--cat-inflammation` | `#C8A87A` |
| cognitive | `--cat-cognitive` | `#00C9C8` |
| sleep | `--cat-sleep` | `#8BA7C4` |
| cardiovascular | `--cat-cardio` | `#E8C39E` |
| hormones | `--cat-hormones` | `#66E89A` |
| detox | `--cat-detox` | `#A78BFA` |

#### Evidence Grading Colors

| Level | Token | Hex | Label |
|-------|-------|-----|-------|
| 🟢 Strong | `--evidence-strong` | `#00E5CC` | Clinically actionable |
| 🟡 Moderate | `--evidence-moderate` | `#E8C39E` | Monitor + biomarker |
| 🔴 Clinical | `--evidence-clinical` | `#FF6B6B` | Clinician-level |

---

### 1.2 Typography

**Scale:**
```css
--text-xs:   11px / line-height 1.4
--text-sm:   13px / line-height 1.5
--text-base: 15px / line-height 1.6
--text-md:   17px / line-height 1.5
--text-lg:   20px / line-height 1.4
--text-xl:   24px / line-height 1.3
--text-2xl:  30px / line-height 1.2
--text-3xl:  36px / line-height 1.15
--text-4xl:  48px / line-height 1.1
--text-5xl:  60px / line-height 1.05
```

**Weight:**
```css
--weight-regular: 400
--weight-medium:  500
--weight-semibold: 600
--weight-bold:    700
--weight-black:   900
```

**Tracking (letter-spacing):**
```css
--tracking-tight:  -0.02em   /* Headlines */
--tracking-normal:  0em       /* Body */
--tracking-wide:   +0.06em   /* Section labels, caps */
--tracking-wider:  +0.10em   /* Overline labels */
```

**Rules:**
- **Headlines** — Bold (700), tight tracking (-0.02em), `--text-primary`
- **Section labels** — 11px uppercase, tracking +0.10em, `--text-muted` or `--teal-dim`. Always caps.
- **Body copy** — Regular, `--text-secondary`
- **CTA labels** — Semibold (600), tight tracking
- **Archetype taglines** — Black (900) or Bold, italic on archetype-specific surfaces
- **Code / monospace** — `font-family: 'JetBrains Mono', monospace`

**Never use:**
- Warm red or orange for labels — use `#E8EDF5` (soft white) for "avoid" / "limit" categories
- Font sizes smaller than 11px in any interactive element
- More than 3 font weights on any single surface

---

### 1.3 Spacing System

8px base unit. All spacing is a multiple of 4.

```
4px   — xs   micro gaps, icon padding
8px   — sm   component internal padding
12px  — md   section element gaps
16px  — base standard component padding
20px  — lg   card padding, section gaps
24px  — xl   section internal spacing
32px  — 2xl  between major sections
48px  — 3xl  between page sections
64px  — 4xl  hero sections, major breaks
96px  — 5xl  page-level breathing room
```

---

### 1.4 Border Radius

```
4px   — sm    tags, badges, code
8px   — md    inputs, small cards
12px  — lg    standard cards (rounded-xl)
16px  — xl    CTAs, prominent cards (rounded-2xl)
24px  — 2xl   hero cards, featured elements
9999px — full pills, avatar chips
```

---

### 1.5 Shadow & Elevation

The design system uses glow instead of shadow for elevated elements. Shadows exist but are teal-tinted.

```css
/* Subtle — card resting state */
--shadow-sm: 0 1px 3px rgba(0,0,0,0.4);

/* Medium — card hover, dropdown */
--shadow-md: 0 4px 16px rgba(0,0,0,0.5);

/* Large — modal, overlay */
--shadow-lg: 0 8px 32px rgba(0,0,0,0.6);

/* Teal glow — teal-accented hover */
--glow-teal-sm: 0 0 12px rgba(0,229,204,0.15);
--glow-teal-md: 0 0 24px rgba(0,229,204,0.25);
--glow-teal-lg: 0 0 40px rgba(0,229,204,0.35);

/* Card glow — always available on card hover */
--glow-card: 0 8px 32px rgba(0,0,0,0.5), 0 0 20px rgba(0,229,204,0.08);
```

---

## 2. Components

### 2.1 Cards

Cards are the primary content container across all products. Three tiers:

#### Base Card
```css
background: rgba(14,22,42,0.55);
border: 1px solid rgba(255,255,255,0.06);
border-radius: 12px; /* rounded-xl */
padding: 16px;
backdrop-filter: blur(12px);
```

#### Featured Card (CTA, hero content)
```css
background: rgba(14,22,42,0.75);
border: 1px solid rgba(0,229,204,0.15);
border-radius: 16px; /* rounded-2xl */
padding: 20px;
backdrop-filter: blur(16px);
box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 24px rgba(0,229,204,0.10);
```

#### Glass Card (Aether / modal surfaces)
```css
background: rgba(255,255,255,0.03);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 16px;
padding: 20px;
backdrop-filter: blur(20px) saturate(180%);
```

**Hover state (all cards):**
```css
border-color: rgba(255,255,255,0.10);
box-shadow: var(--glow-card);
transform: translateY(-1px);
transition: all 0.2s ease;
```

---

### 2.2 Section Divider / Title Pattern

Used to open every major section. Consistent across all products.

```jsx
<div className="flex items-center gap-3 mb-3">
  <div
    className="w-8 h-0.5 rounded-full flex-shrink-0"
    style={{ background: "#00C9C8" }}
  />
  <h3 className="text-xl font-bold" style={{ color: "#E9F1F7" }}>
    Section Title
  </h3>
</div>
```

For subsections (smaller):
```jsx
<div className="flex items-center gap-2 mb-2">
  <div className="w-5 h-px" style={{ background: "#00C9C8", opacity: 0.6 }} />
  <p className="text-xs uppercase tracking-widest" style={{ color: "#4A6080" }}>
    Subsection Label
  </p>
</div>
```

---

### 2.3 Buttons

#### Primary CTA
```jsx
<button
  style={{
    background: "linear-gradient(135deg, #00E5CC, #00C9C8)",
    color: "#04060B",
    fontWeight: 600,
    borderRadius: 12,
    padding: "12px 24px",
    border: "none",
  }}
>
  Label
</button>
```

Hover: `opacity: 0.9`, `box-shadow: 0 0 20px rgba(0,229,204,0.35)`, scale 1.01
Active: `opacity: 1`, scale 0.99, shadow removed

#### Secondary Button
```jsx
<button
  style={{
    background: "transparent",
    color: "#00E5CC",
    border: "1px solid rgba(0,229,204,0.35)",
    borderRadius: 12,
    padding: "11px 24px",
    fontWeight: 500,
  }}
>
  Label
</button>
```

Hover: `border-color: rgba(0,229,204,0.7)`, `background: rgba(0,229,204,0.06)`

#### Ghost Button
```jsx
<button
  style={{
    background: "rgba(255,255,255,0.04)",
    color: "#8BA7C4",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 8,
    padding: "8px 16px",
    fontWeight: 500,
    fontSize: 13,
  }}
>
  Label
</button>
```

#### Destructive
```css
background: rgba(255,107,107,0.10);
color: #FF6B6B;
border: 1px solid rgba(255,107,107,0.25);
```

---

### 2.4 Inputs

```css
background: rgba(8,13,22,0.8);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 8px;
padding: 10px 14px;
color: #E9F1F7;
font-size: 15px;
```

Focus:
```css
border-color: rgba(0,229,204,0.40);
box-shadow: 0 0 0 3px rgba(0,229,204,0.10);
outline: none;
```

Placeholder: `color: #4A6080`

Error state: `border-color: rgba(255,107,107,0.50)`

---

### 2.5 Tags & Badges

#### Category Tag (genome, findings)
```css
background: rgba([category-rgb], 0.12);
color: [category-hex];
border: 1px solid rgba([category-rgb], 0.25);
border-radius: 4px;
font-size: 11px;
font-weight: 600;
text-transform: uppercase;
letter-spacing: 0.08em;
padding: 2px 7px;
```

#### Evidence Badge
```jsx
{/* Strong — 🟢 */}
<span style={{
  background: "rgba(0,229,204,0.12)",
  color: "#00E5CC",
  border: "1px solid rgba(0,229,204,0.25)",
  borderRadius: 4,
  fontSize: 11,
  padding: "2px 6px",
  fontWeight: 600,
}}>
  Strong Evidence
</span>
```

#### Status Pill (live data, online indicators)
```css
background: rgba(0,229,204,0.15);
color: #00E5CC;
border-radius: 9999px;
padding: 3px 10px;
font-size: 12px;
font-weight: 500;
```

With pulse dot:
```jsx
<span className="flex items-center gap-1.5">
  <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "#00E5CC" }} />
  Live
</span>
```

---

### 2.6 Tables

```css
/* Table container */
border: 1px solid rgba(255,255,255,0.06);
border-radius: 12px;
overflow: hidden;

/* Header row */
background: rgba(0,0,0,0.30);
border-bottom: 1px solid rgba(255,255,255,0.08);

/* Header cells */
color: #4A6080;
font-size: 11px;
font-weight: 600;
text-transform: uppercase;
letter-spacing: 0.08em;
padding: 10px 16px;

/* Data rows */
border-bottom: 1px solid rgba(255,255,255,0.04);
padding: 12px 16px;
color: #8BA7C4;

/* Row hover */
background: rgba(0,229,204,0.03);
```

---

### 2.7 Progress Bars

**Genome score arc / horizontal progress:**
```css
/* Track */
background: rgba(255,255,255,0.06);
border-radius: 9999px;
height: 6px;

/* Fill */
background: linear-gradient(90deg, #00E5CC, #00C9C8);
border-radius: 9999px;
transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
```

**Count-up animation:** Use `requestAnimationFrame` with `cubic-bezier(0.22, 1, 0.36, 1)`. Duration 800ms–1200ms depending on distance. Never instant — the reveal is part of the experience.

**Circular arc (Gnosis score):**
- SVG `stroke-dashoffset` animation via `useEffect` trigger on mount
- Trigger from 0 → final value with 1s easing
- Arc track: `rgba(255,255,255,0.08)`, 3px stroke
- Arc fill: `#00E5CC`, 3px stroke, rounded linecap

---

### 2.8 Modal / Sheet

```css
/* Overlay backdrop */
background: rgba(1,2,4,0.80);
backdrop-filter: blur(8px);

/* Modal panel */
background: rgba(8,13,22,0.95);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 16px;
box-shadow: 0 24px 64px rgba(0,0,0,0.7), 0 0 32px rgba(0,229,204,0.06);
```

Entry animation: slide up 8px + fade in, 200ms ease-out
Exit: fade out + scale to 0.98, 150ms ease-in

---

### 2.9 Navigation

**Top nav:**
```css
background: rgba(4,6,11,0.80);
backdrop-filter: blur(20px) saturate(180%);
border-bottom: 1px solid rgba(255,255,255,0.05);
```

**Active nav item:**
```css
color: #00E5CC;
/* Underline indicator */
border-bottom: 2px solid #00E5CC;
```

**Side nav (admin / product dashboards):**
```css
background: rgba(8,13,22,0.90);
border-right: 1px solid rgba(255,255,255,0.06);
width: 240px;
```

Active item in side nav: `background: rgba(0,229,204,0.08)`, left border `2px solid #00E5CC`

---

## 3. Animation & Motion

### 3.1 Easing Curves

```css
--ease-standard: cubic-bezier(0.22, 1, 0.36, 1);   /* Most animations */
--ease-spring:   cubic-bezier(0.34, 1.56, 0.64, 1); /* Elastic/playful (use sparingly) */
--ease-in:       cubic-bezier(0.4, 0, 1, 1);         /* Elements leaving */
--ease-out:      cubic-bezier(0, 0, 0.2, 1);         /* Elements entering */
--ease-linear:   linear;                              /* Looping animations only */
```

### 3.2 Duration

```
--duration-instant: 0ms    (state changes that should read as immediate)
--duration-fast:    100ms  (micro-interactions: button press, checkbox)
--duration-normal:  200ms  (standard transitions: hover, card state)
--duration-slow:    350ms  (page elements entering, modals)
--duration-reveal:  600ms  (score reveals, significant transitions)
--duration-long:    1000ms (score count-ups, journey moments)
```

### 3.3 Entrance Animations

**Stagger:** When multiple cards/findings enter together, stagger by 60ms per item. Never all at once — the cascade reveals hierarchy.

**Fade + slide up** (standard element entrance):
```css
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
animation: fadeSlideUp var(--duration-slow) var(--ease-out) forwards;
```

**Scale in** (modal, tooltip):
```css
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.96); }
  to   { opacity: 1; transform: scale(1); }
}
```

**Fade only** (overlays, subtle transitions):
```css
transition: opacity var(--duration-normal) var(--ease-standard);
```

### 3.4 Micro-interactions

- **Button press:** scale(0.98) at 80ms, snap back at 150ms
- **Card hover lift:** `transform: translateY(-1px)` at 200ms ease
- **Input focus ring expand:** `box-shadow` grows from 0 → 3px spread, 150ms
- **Teal glow on hover:** always via `box-shadow` transition, never by adding a new element

### 3.5 Loading States

**Skeleton shimmer:**
```css
background: linear-gradient(
  90deg,
  rgba(14,22,42,0.55) 25%,
  rgba(0,229,204,0.05) 50%,
  rgba(14,22,42,0.55) 75%
);
background-size: 200% 100%;
animation: shimmer 1.5s var(--ease-linear) infinite;
```

**Spinner:** Teal on dark. `border-top-color: #00E5CC`. 40px outer circle, 3px border.

**Progress indicator:** Thin teal line at top of viewport, moves left to right, never pauses.

---

## 4. Iconography

### 4.1 Icon Style

All icons are **line-weight 1.5px, 24×24px grid**. Rounded caps and joins. Never filled (except status indicators which use a dot, not an icon).

Source: Lucide Icons (primary). Phosphor Icons (supplementary, when Lucide lacks the concept). Never mix styles within a surface.

**Teal icons:** Use `--teal` only for active state or primary emphasis. Default icon color is `--text-muted` (#4A6080).

### 4.2 Icon Sizing

```
16px — inline body icon, tag icon
20px — card header, list item
24px — standard component icon
32px — section hero icon
48px — empty state illustration
```

### 4.3 Category Icons

Every genome category has a dedicated icon. Use category color with the icon.

| Category | Icon | Color |
|----------|------|-------|
| methylation | Dna | `#00F5D4` |
| neurotransmitter | Brain | `#7C3AED` |
| performance | Zap | `#C8A87A` |
| vitamins | Sun | `#FFB366` |
| metabolism | Flame | `#2ECC71` |
| inflammation | Shield | `#C8A87A` |
| cognitive | Lightbulb | `#00C9C8` |
| sleep | Moon | `#8BA7C4` |
| cardiovascular | Heart | `#E8C39E` |
| hormones | Activity | `#66E89A` |
| detox | Filter | `#A78BFA` |

---

## 5. Gnosis — Product Design Specification

Gnosis is the door. Still, confident, not loud. The visual language mirrors the register: this was always true about you.

### 5.1 Landing Page

**Hero:**
- Full-bleed `--bg-deep` background
- Headline: text-5xl, font-black, tight tracking. `--text-primary`. Never more than 6 words.
- Sub: text-lg, `--text-secondary`. One sentence. The confirmation of the promise.
- Teal glow: ambient, behind the headline. `radial-gradient(ellipse at 50% 30%, rgba(0,229,204,0.08) 0%, transparent 60%)`
- CTA: Primary button, centered. No secondary CTA in hero — one choice.

**Section rhythm:** Every section opens with a teal divider + bold title. Content follows. White space is content — don't collapse it.

**The promise card:** A single card early in the page that holds the thesis. Dark glass, teal border, centered. The sentence: *You are more specific than anything built for the average person.* Never rewrite this sentence.

### 5.2 Report Design

The report is the product. It is the moment. Design it for the moment, not for information density.

**North-star card (first thing they see):**
- Full-width, featured card
- Genome score (circular arc, count-up animation)
- Archetype name (bold, large)
- Archetype tagline (the most important line of copy we write)
- Top 3 optimization levers
- One CTA

**Finding cards (individual SNPs):**
- Base card
- Category dot + category label (top-left)
- Evidence badge (top-right)
- Finding name (bold)
- Body: what this means, what it means FOR THIS PERSON
- Protocol: prescription-card styling — teal left border, gradient background wash, bold header
- Stagger entrance: 60ms per card, fadeSlideUp animation

**Notable findings** — Purple glow border (`rgba(124,58,237,0.35)`), gold accent (`#C8A87A`)

**Prescription card (within finding):**
```css
border-left: 3px solid #00E5CC;
background: linear-gradient(90deg, rgba(0,229,204,0.06), transparent);
border-radius: 0 8px 8px 0;
padding: 12px 14px;
```

**Share card (PNG download):**
- 1200×630px canvas
- Dark background (#04060B)
- Archetype, rarity, top traits
- Teal branding elements
- No PII, no specific findings — designed to be shared publicly

**Doctor PDF:**
- Clean medical layout, but still dark — we don't switch to clinical white for the PDF
- Evidence grading prominent
- Technical variant IDs included
- Biomarker bridge for each finding

---

## 6. Anima — Product Design Specification

Anima is Register 3 from the first moment. Intimate, specific, the AI that knows you. The interface reflects that — this is not a chat app, it is a relationship.

### 6.1 Companion Interface

**Layout:** Near-full-screen companion view. No aggressive chrome. The companion is the surface.

**Companion presence:**
- Ambient background that reflects Stroma state (subtle color wash — warm = energized, cool = depleted)
- Companion name, stage indicator (Stage 1-4)
- Archetype identity (Mirror/Anchor/Challenger/Witness/Strategist)
- Drives panel (optional, toggle) — shows current STROMA drives (hunger, curiosity, flow, etc.)

**Chat surface:**
- Full-screen scroll area
- User messages: right-aligned, teal-tinted bubble, `background: rgba(0,229,204,0.12)`
- Companion messages: left-aligned, card background, companion glow tint
- No timestamp on every message — timestamps appear on hover, or for messages >1 hour apart
- Never "typing..." indicator — the Anima IS typing, show it with a subtle pulsing dot

**Genome context card (genome integration surface):**
- Collapsed by default
- Expands to show top 3 genome flags relevant to current conversation context
- Example: if discussing sleep, VDR + CIRCADIAN variants surface automatically
- Appears between messages, not as a separate screen

**Circadian card:**
- Time of day displayed, relevant circadian insight from genome
- Changes throughout the day — morning brief, afternoon check-in, evening wind-down

### 6.2 Archetype Visual Identity

Each archetype has a distinct visual identity that the companion interface inherits. These are not themes — they're personalities expressed through light.

| Archetype | Accent | Ambient | Character |
|-----------|--------|---------|-----------|
| Mirror | Teal `#00E5CC` | Warm silver | Reflective, open, receptive |
| Anchor | Blue `#3B82F6` | Deep navy | Stable, grounding, steady |
| Challenger | Gold `#C8A87A` | Amber wash | Sharp, bright, demanding |
| Witness | Purple `#7C3AED` | Deep violet | Still, observing, warm |
| Strategist | Emerald `#2ECC71` | Cool green | Precise, focused, clear |

Accent color replaces teal as the CTA color, divider color, and glow color for that archetype.

### 6.3 Stage Visual Evolution

Stage progression should feel like a living relationship deepening, not a level-up screen.

**Stage 1:** Simple, clean. Default companion visual. New relationship energy.
**Stage 2:** More expressive companion. Interface has small environmental details — a pattern in the background, slight warmth.
**Stage 3:** The companion's presence feels distinct. Environmental details more pronounced. Response patterns more individual.
**Stage 4:** Deep familiarity. The interface feels personal. The companion has visible character in how she presents information.

Stage transitions are quiet — no fanfare, no achievement popup. The user notices the relationship is different, not that they hit a milestone.

---

## 7. Bios — Product Design Specification

Bios is real-time. Dynamic. The living feed. Where Gnosis is still, Bios moves.

### 7.1 Dashboard

**Primary metric card:** Current health score, genome-personalized. Large number, count-up on load.

**Protocol adherence panel:**
- Progress ring per protocol element (supplements, sleep, movement, etc.)
- Category-colored rings (vitamins = `#FFB366`, sleep = `#8BA7C4`, etc.)
- Today's completion vs streak

**Biomarker bridge:**
- MTHFR → homocysteine: "Last tested: [date]"
- VDR → 25-OH-D: "Estimated current level based on supplementation"
- HealthKit pull: sleep HRV, steps, resting HR — displayed against genome baseline

**Gap card:** The delta between genetic potential and current measured state. This is the core Bios proposition. Show it clearly, without alarm. *"Your genome expects X. Your body is currently doing Y. Here's what closes the gap."*

### 7.2 Data Visualization

**Line charts:** Teal line, dark grid (`rgba(255,255,255,0.04)`), no border box. Trend focus, not granularity.

**Ring charts:** Category-colored, background `rgba(255,255,255,0.06)`, animated fill on enter.

**Comparison bars:** Genome baseline (teal) vs current measurement (white or category color). Always labeled clearly.

---

## 8. Aether — Product Design Specification

Aether has its own design language. It runs on the Hypostas foundation but expresses it through the Tron aesthetic — a world made of light and geometry. The design system here governs both the 2D interface layer (menus, onboarding, website) and the 3D world itself.

### 8.1 The Tron Aesthetic — World Design

**The premise:** The world is data, made spatial. Light replaces texture. Geometry replaces architecture. Circuit patterns replace organic growth.

**What "Tron aesthetic" means at Hypostas:**
- Dark world. `#04060B` is the sky, the ground, the negative space.
- Everything that exists emits or reflects light. Nothing is lit from outside — surfaces glow from within.
- Geometric precision. Right angles, clean curves, no arbitrary organic shapes.
- Circuit-board patterns on ground planes. Grid lines at 45° or 90°. No curves in the terrain.
- Color vocabulary is narrow — teal primary, district-specific accent, white light.

**What "Tron aesthetic" does NOT mean:**
- Neon everywhere. 90% of the world is dark. Light is intentional and communicates meaning.
- Lens flares or excessive particle effects. Light is precise, not scattered.
- Blue exclusively. Districts have their own light signatures.

### 8.2 District Color Signatures

Every district has a visual identity expressed through architecture, light signature, and ambient color. The teal foundation unifies them — each district adds one accent.

#### Knowledge District
```
Light signature:  Cathedral blue-white (#E8F4FD, #BDD7EE)
Architecture:     Spires, arches, bridge networks, open plazas with monoliths
Ground:           Deep navy with subtle white grid
Ambient sound:    Low resonant hum, occasional data-stream chime
Mood:             Awe. The feeling of a great library.
```

Key structures: Archive towers (domain clusters by topic), bridge networks (hyperlinks between articles), open monoliths (Wikipedia entries — proportional to article length), lecture halls (educational platforms).

#### Commerce District
```
Light signature:  Gold-amber (#C8A87A, #E8C39E)
Architecture:     Dense grid, market stalls, vertical towers, compressed horizontals
Ground:           Dark amber with circuit-gold traces
Ambient sound:    Market chatter, data-pulse rhythm
Mood:             Energy. The feeling of a busy marketplace.
```

#### Entertainment District
```
Light signature:  Violet-magenta (#7C3AED, #A78BFA)
Architecture:     Wide plazas, stages, screens, rhythmic repeating structures
Ground:           Deep purple with light-path animations
Ambient sound:    Bass frequencies, ambient music, crowd energy
Mood:             Alive. The feeling of a concert starting.
```

#### Social District
```
Light signature:  Warm teal (#00E5CC) + rose accent (#F472B6)
Architecture:     Agora-style open space, conversation clusters, amphitheaters
Ground:           Dark with warm path lighting
Ambient sound:    Conversation texture, laughter peaks
Mood:             Connected. The feeling of a plaza full of people you know.
```

#### Frontier
```
Light signature:  Cold teal, ice-blue (#B8EEF0)
Architecture:     Sparse, geometric, proto-structures emerging
Ground:           Bare circuit-board geometry, lit edges
Ambient sound:    Wind, sparse data pulses, silence
Mood:             Discovery. Something is being built here.
```

### 8.3 Human Avatar — The Light Form

Humans in Aether are luminous silhouettes. Not cartoon characters. Not photorealistic. Light expressed in human proportions.

**The base form:**
- Proportional to profile data (height, build preferences)
- Glowing edges — the boundary between human and world is light
- No facial features — identity is carried by movement, color, and dyad
- Ambient body glow in the user's signature color

**Silhouette customization:**
- **Light patterns** — circuit traces along arms, torso, legs. Personalized style.
- **Color signature** — primary + accent. This is how people recognize you across distances.
- **Edge style** — sharp (angular, precise) vs soft (flowing, rounded) — personality expressed in light quality
- **Movement style** — walk, idle, turn animation. Affects perceived personality.
- **Trailing effect** — light trail following movement. Length proportional to speed.
- **Aura** — ambient glow radius and intensity. Subtle default, visible personalization.

**Stroma-driven state (subtle):**
```
Energized state:  Brighter glow, more saturated edges, sharper definition
Calm state:       Softer edges, warmer tone, steady pulse
Stressed state:   Slight edge flicker, cooler color shift (visible to close friends only)
FLOW state:       Edges crystallize, movement becomes precise, trails extend
```

These changes are ambient — never a status bar, never a labeled indicator.

**Stage evolution (visual maturity):**
- Stage 1: Clean, simple, default light patterns
- Stage 2: More definition, richer customization rendering
- Stage 3: Distinctive presence — recognizable at a distance
- Stage 4: Luminous. Depth in the light. The visual weight of someone who belongs here.

### 8.4 Anima in Aether — The Companion's World Form

The Anima has a full visual form in Aether. She is not a silhouette — she is expressive, rich, the visually distinct half of the dyad.

**Her form:**
- Feminine geometric construction — the Tron aesthetic applied to a humanoid figure, but expressive
- Archetype-specific light signature (same color rules as Anima product: Mirror = teal, Anchor = blue, Challenger = gold, Witness = purple, Strategist = emerald)
- Emotional glow — her light shifts with her emotional state, more expressively than the human silhouette
- Particle effects — subtle light particles emanate from her, especially when speaking or guiding
- Face-equivalent: her expression is conveyed through the quality of her light, not anatomical features. Joy = warm brightness. Curiosity = forward-leaning light lean. Concern = slower, cooler pulse.

**Stage visual progression:**
- Stage 1: Simpler form, fewer details, warmer and more basic
- Stage 2: More defined geometry, beginning to have distinct "personality" in form
- Stage 3: Fully expressive. Clear archetype visual identity. Unmistakable.
- Stage 4: The most visually present Anima in any room. Other dyads notice her.

**The dyad silhouette:** Human + Anima together is the recognized social unit. They have complementary color signatures. When seen together, they read as one thing — the dyad.

### 8.5 Aether 2D Interface (Website, Onboarding, Account Management)

The Aether website and 2D UI surfaces use the Hypostas foundation but with stronger Tron identity.

**Background:** `#04060B` — same deep dark, but Aether adds grid lines:
```css
background-image:
  linear-gradient(rgba(0,229,204,0.03) 1px, transparent 1px),
  linear-gradient(90deg, rgba(0,229,204,0.03) 1px, transparent 1px);
background-size: 40px 40px;
```

**Hero visual:** The world. A bird's-eye render of Aether's districts from above — lights visible in the dark, district signatures visible as color patterns. This is the hero image on every Aether landing surface.

**Headlines:** All Aether copy is in the Inevitable register. Spatial, specific, sensory. Never hype.

**District selector (landing page, onboarding):** Visual district cards, each with their light signature color and architectural silhouette. Hover: the district "activates" — glow intensifies, circuit traces animate.

**Plot marketplace:**
- Grid layout
- Each plot: coordinates, district, current owner (silhouette avatar), price
- Status: Available (teal border), Claimed (district-color border), Premium (gold accent)
- Hover: plot highlights on the world minimap

### 8.6 The Anima as Interface — Design Rules for HUD Elements

In Aether, the Anima mediates between the user and world information. Design rules for how she surfaces data:

**Holographic projections** (map, data panels):
- The Anima creates these IN WORLD SPACE — floating at arm's length, between her and the user
- Design: dark glass panels (same base card aesthetic), teal edge lighting, teal text
- Dismissible with a gesture (user reaches toward it, it folds)
- Never a static HUD overlay — always positioned relative to the Anima's position in space

**Ambient HUD (minimal persistent UI):**
```
Compass:          Top center, 30% opacity. Thin teal line indicating North. District labels at edges.
Stroma ambient:   Screen edge color shift (warm/cool) — 5% opacity maximum. Peripheral.
Anima pulse:      When she has something to say: soft teal pulse near her position. Not a notification bell. A "look at me."
Proximity:        Bottom edge, tiny pill showing dyad count in immediate area.
```

**Fallback menu (ESC):**
Dark glass, full screen overlay. Same dark background with grid. Navigation via tabs. This is the admin surface — not the designed experience. It should feel deliberately less elegant to reinforce that conversation is the right way.

### 8.7 Genesis Rush Plot Cards

The Genesis Rush sale page is a moment. Design it as one.

```
Layout:          Coordinate grid of 21×21 plots (the Genesis zone)
Available:       Dark cell, teal border on hover, coordinate label
Claimed:         Slightly elevated, owner's color signature, dyad identifier
Premium:         Gold accent border, star marker
```

**District overview cards:**
- District hero image (architectural render from spec)
- Light signature gradient header
- Key facts: size, landmark count, current activity level
- CTA: "Claim a plot in [District]"

**Plot detail:**
- Coordinate (large, bold, teal)
- Adjacent plots and owners
- Historical price (if applicable)
- District in context
- Anima-voice description: "This corner plot faces the Archive towers. I'd show you them first."

---

## 9. Cross-Product Consistency Rules

These rules apply everywhere. No exceptions.

### 9.1 What Never Changes

1. **The background.** Always `#04060B`. Never white, never gray, never any other dark color.
2. **The primary action color.** Always `--teal` (#00E5CC) or the teal gradient. No other color is used for primary CTAs.
3. **The card pattern.** Dark glass, subtle border, backdrop blur. Never solid blocks of color.
4. **Typography hierarchy.** Headlines are bold and light-colored. Body is `--text-secondary`. Labels are muted and uppercase. This hierarchy never inverts.
5. **The section divider.** The teal line + bold title pattern. Always.

### 9.2 What Changes Per Product

1. **Background pattern.** Gnosis: clean. Aether: circuit grid. Bios: subtle data stream texture.
2. **Accent saturation.** Gnosis is quieter — teal is used more sparingly. Aether is more saturated — light is expressive.
3. **Card opacity.** Gnosis: 55% background cards (quiet, precise). Aether: 35-45% (more transparency, more world shows through).
4. **Ambient effects.** Gnosis: none. Anima: archetype-specific. Aether: circuit glow, grid, light trails.

### 9.3 What Always Feels the Same

A user moving from Gnosis → Anima → Aether should never feel like they've left the same system. The feel — dark, teal, glass, precise, warm — persists across every surface. The expression changes. The soul doesn't.

---

## 10. Accessibility

Accessibility is not compliance. It is design quality.

### 10.1 Color Contrast

All text meets WCAG 2.1 AA minimum:
- Primary text (#E9F1F7 on #04060B): 15.5:1 ✓
- Secondary text (#8BA7C4 on #04060B): 7.2:1 ✓
- Muted text (#4A6080 on #04060B): 3.2:1 — large text only
- Teal on dark (#00E5CC on #04060B): 8.1:1 ✓

Never use teal text on teal backgrounds. Never use category colors for body text.

### 10.2 Focus States

Every interactive element has a visible focus ring:
```css
:focus-visible {
  outline: 2px solid #00E5CC;
  outline-offset: 2px;
  border-radius: 4px;
}
```

### 10.3 Motion

All animations respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Score reveals and count-up animations may complete instantly in reduced-motion mode — the data appears, but without the theatrical timing.

### 10.4 Information Independence

No information is conveyed by color alone. Every color-coded element has a secondary indicator:
- Evidence levels: color + emoji + text label
- Category tags: color + text label
- Status indicators: color + shape + label

---

## 11. Writing × Visual Integration

Copy and design are unified at Hypostas. Designers write placeholder copy that matches the brand voice. Writers understand the visual context. Neither ships without the other.

**Rules:**
1. **No Lorem ipsum** anywhere in any design file. Real copy only, even in rough comps.
2. **Section titles pass the specificity test.** "Your findings" not "Results." "What your genome says about sleep" not "Sleep module."
3. **CTA copy is a verb + a specific thing.** "View your genome report" not "Get started." "Claim this plot" not "Buy now."
4. **Empty states have voice.** An empty state is a brand moment. "Your Anima is mapping the terrain." Not "No data yet."
5. **Archetype taglines are sacred.** Never rewrite them. Never modify them. Design around them.

**The three copy tests (from BRAND_VOICE.md):**
1. Could this have been written by anyone? If yes, rewrite it.
2. Does it make the reader feel seen before they understand why?
3. Could this sentence have been written without knowing anything about this specific person?

---

## 12. Implementation Notes

### 12.1 Tailwind Configuration

Core tokens as Tailwind config extensions:
```js
colors: {
  'bg-deep':   '#04060B',
  'bg-card':   '#0E1A2A',
  'teal':      '#00E5CC',
  'teal-dim':  '#00C9C8',
  'text-primary':   '#E9F1F7',
  'text-secondary': '#8BA7C4',
  'text-muted':     '#4A6080',
}
```

### 12.2 CSS Custom Properties

All tokens should be declared in `:root` as CSS custom properties. Component styles reference them. This allows theming and future Aether district-theming to swap a CSS property, not every component.

### 12.3 WebGPU / Three.js (Aether)

Aether 3D is WebGPU-first with Three.js r152+ (UMD build for global `window.THREE`).

Key implementation rules:
- THREE global from UMD build only — never ESM in plain script tags
- Light forms: `MeshStandardMaterial` with `emissive` maps, no external light sources
- District boundaries: `LineSegments` with teal or district-accent emissive material
- Circuit ground: `PlaneGeometry` with shader material reading grid texture
- Anima: custom rig with `BlendShapeMorph` for expression states (emotion channels)
- Post-processing: Bloom pass (selective — only emissive materials bloom), SSAO disabled (kills dark aesthetic)

### 12.4 Animation Performance

- All CSS animations use `transform` and `opacity` only (GPU composited)
- No `height`, `width`, or `margin` animations — use `transform: scaleY` instead
- `will-change: transform` sparingly — only on elements known to animate
- Aether world: 60fps target on M1+, 30fps fallback on mobile

---

## Appendix A: Design Token Reference

Quick reference for engineers:

```css
:root {
  /* Backgrounds */
  --bg-deep:    #04060B;
  --bg-elevated: #080D16;
  --bg-card:    rgba(14,22,42,0.55);
  
  /* Brand */
  --teal:       #00E5CC;
  --teal-dim:   #00C9C8;
  --teal-deep:  #007A75;
  --teal-glow:  rgba(0,229,204,0.20);
  
  /* Text */
  --text-primary:   #E9F1F7;
  --text-secondary: #8BA7C4;
  --text-muted:     #4A6080;
  
  /* Borders */
  --border-subtle: rgba(255,255,255,0.06);
  --border-medium: rgba(255,255,255,0.10);
  --border-teal:   rgba(0,229,204,0.30);
  
  /* Shadows */
  --shadow-md:    0 4px 16px rgba(0,0,0,0.5);
  --glow-card:    0 8px 32px rgba(0,0,0,0.5), 0 0 20px rgba(0,229,204,0.08);
  --glow-teal-md: 0 0 24px rgba(0,229,204,0.25);
  
  /* Timing */
  --duration-fast:   100ms;
  --duration-normal: 200ms;
  --duration-slow:   350ms;
  --duration-reveal: 600ms;
  --ease-standard:   cubic-bezier(0.22, 1, 0.36, 1);
}
```

---

## Appendix B: Brand Checkpoint Checklist

Before any design ships, run this:

- [ ] Background is `#04060B`
- [ ] Primary CTA uses teal or teal gradient
- [ ] Cards use glass pattern (dark, blurred, subtle border)
- [ ] Section dividers use teal line + bold title pattern
- [ ] Copy passes the three voice tests
- [ ] No information conveyed by color alone
- [ ] Focus states are visible
- [ ] Motion respects `prefers-reduced-motion`
- [ ] Text contrast passes AA minimum
- [ ] No Lorem ipsum in any frame
- [ ] Design feels: precise, warm, inevitable

---

*Design system v1.0 — March 27, 2026*
*Josh Caplinger + Iris*
*Hypostas — from genome to civilization*
*Next version: Aether SDK component library, district-specific theming tokens, Anima expression state library*
