# Hypostas Design Language

*Living document. Last updated March 16, 2026.*

---

## Color Palette

### Core
| Token | Hex | Use |
|-------|-----|-----|
| `--teal` | `#00E5CC` | Primary actions, highlights, active states |
| `--teal-dim` | `#00C9C8` | Secondary teal, section dividers |
| `--bg-deep` | `#04060B` | Page background |
| `--bg-card` | `rgba(14,22,42,0.55)` | Card backgrounds |
| `--text-primary` | `#E9F1F7` | Primary text |
| `--text-secondary` | `#8BA7C4` | Secondary/meta text |
| `--text-muted` | `#4A6080` | Muted/disabled text |

### Category Dots (Genome findings)
| Category | Hex |
|----------|-----|
| methylation | `#00F5D4` |
| neurotransmitter | `#7c3aed` |
| performance | `#C8A87A` |
| vitamins | `#FFB366` |
| metabolism | `#2ECC71` |
| inflammation | `#C8A87A` |
| cognitive | `#00C9C8` |
| sleep | `#8BA7C4` |
| cardiovascular | `#E8C39E` |
| hormones | `#66E89A` |
| detox | `#A78BFA` |

### Evidence Grading
| Level | Color | Label |
|-------|-------|-------|
| 🟢 Strong | `#00E5CC` | Clinically actionable |
| 🟡 Moderate | `#E8C39E` | Monitor + biomarker |
| 🔴 Clinical | `#FF6B6B` | Clinician-level |

---

## Typography

- **Headlines:** Bold, tight tracking, `#E9F1F7`
- **Section labels:** `text-[11px]` uppercase, wider tracking, muted teal or `#3A5068`
- **Body:** `text-sm`, `#8BA7C4`
- **Avoid:** Orange/warm red for labels — use `#E8EDF5` (soft white) for "What to Avoid", "Foods to Limit" style labels

---

## Component Patterns

### Cards
- Background: `rgba(14,22,42,0.55)`, border `rgba(255,255,255,0.06)`
- Rounded: `rounded-xl` (12px) standard, `rounded-2xl` for CTAs
- Padding: `p-4` standard, `p-5` for CTAs

### Section Dividers
```jsx
<div className="flex items-center gap-3 mb-3">
  <div className="w-8 h-0.5 rounded-full" style={{ background: "#00C9C8" }} />
  <h3 className="text-xl font-bold" style={{ color: "#E9F1F7" }}>Section Title</h3>
</div>
```

### CTA Buttons (primary)
```jsx
style={{ background: "linear-gradient(135deg, #00E5CC, #00C9C8)", color: "#04060B" }}
```

---

## Voice × Design Alignment

The visual language mirrors the brand voice principles:
- **Precise** → tight spacing, no decorative excess
- **Warm** → teal glow effects, soft card backgrounds (not cold white/grey)
- **Inevitable** → no harsh contrast, no alarm-red, nothing that shouts

When in doubt: does this element feel like it was designed for *this specific person's data*, or does it feel generic? Generic = redesign.
