# Formal Verification — Scoping Brief

**Thesis:** DyadOS has maxed out *review + tests + cross-vendor gate*. For the soundness-critical crypto, the next maturity step is **machine-checked properties** — and the motivating evidence is your own: the composite-modulus **aggregation soundness gap** was a masking bug that *leaked the witness while the proof still verified*, invisible to functional tests **and** the Codex gate. That is precisely the class review cannot reliably catch and formal methods can. This brief scopes *what tool, on what, in what order* — the judgment, not the build.
**Author:** Iris (Fable 5), 2026-07-07. Disposition: scoping brief (Josh, 2026-07-07). Build = a later Opus arc, informed by this + HYP-330.

---

## §1 The tooling ladder (cheap → expensive, ROI-ordered)

| Tier | Tool | Cost | Best for | Verdict |
|---|---|---|---|---|
| **1** | **Property-based** (`proptest`) | low | invariants over random inputs: round-trip, soundness relations, the **mechanism/statistical-ZK test** for masked primitives | **Make it standard NOW** |
| **2** | **Fuzzing** (`cargo-fuzz`) | low | attacker-facing **decoders** (the unbounded-bincode S1 class) | **Make it standard NOW** |
| **3** | **TLA+ / Apalache** | moderate | **protocol state machines**: double-ratchet, circuit/channel lifecycle, consensus safety/liveness, the K1 ceremony FSM | Focused effort on the 2–3 worst-if-wrong |
| **4** | **Lean / Coq** (mechanized proof) | high | the **soundness core**: lattice ZK relations, the aggregation fold, the C3 binding | Reserve; coordinate with HYP-330 |

The rule: **cost must track catastrophe.** proptest/fuzz are cheap enough to be universal; Lean is expensive enough to reserve for the handful of places where a subtle soundness bug is both catastrophic and review-invisible.

---

## §2 What to verify FIRST (ROI-ranked)

1. **The mechanism/statistical-ZK acceptance gate on every masked-quadratic primitive.** Your own lesson (from the aggregation gap): *"a new masked-quadratic primitive needs a mechanism/statistical-ZK test as a first-class acceptance gate, not just round-trip + soundness."* Encode it as a `proptest` property (does the transcript leak any function of the witness?) and make it a **required gate lens** for that primitive class. This is the direct, cheap fix for the exact class you hit. **Highest ROI in the document.**
2. **`cargo-fuzz` on every attacker-facing decoder.** The unbounded-bincode S1 findings (HYP-14/21/27/47/49/72/73/98/100) are a decoder-robustness class; fuzzing is the mechanical net that catches the *next* one before an auditor does. Cheap, high-value, factory-bakeable.
3. **TLA+ on the double-ratchet + consensus safety.** The two state machines whose bugs are worst: ratchet desync/wedge (HYP-370 class) and consensus split-brain / no-state-root-agreement (HYP-28/251 class). Model-check safety invariants; these are exactly what property tests miss and model-checkers find.
4. **Lean on the aggregation soundness + C3 binding — only after HYP-330 scopes it.** The external audit should tell you *which* soundness properties are load-bearing enough to mechanize; proving the wrong thing is expensive waste. Sequence Lean after that signal.

---

## §3 The honest recommendation

- **Don't boil the ocean.** A blanket "formally verify DyadOS" is the wrong ambition — most of the code doesn't warrant it.
- **Bake tiers 1–2 into the factory gate now** (rule #32 — mechanism over vigilance): `proptest` + `cargo-fuzz` as standard exit criteria for crypto primitives and decoders, with the mechanism/statistical-ZK gate lens for masked-quadratic work. This is cheap, it's the direct remedy for the two bug-classes you've actually shipped, and it makes the gate stronger rather than replacing it.
- **Tier 3 (TLA+) is a focused, bounded project** on the 2–3 named FSMs — worth doing, not urgent.
- **Tier 4 (Lean) waits on HYP-330.** The cross-vendor Codex gate stays regardless — formal methods *complement* it; the aggregation gap proves review alone misses this class, but review also catches things proofs don't. Both/and.

**One-line takeaway:** make property-based + fuzzing *universal and mechanized* immediately (cheap, targets your real bug-classes); reserve model-checking for the worst state machines and mechanized proof for the audited soundness core. The maturity step isn't "prove everything" — it's "mechanically catch the two classes that already slipped past you, and machine-check only the handful of places a subtle break is catastrophic."

---

## §4 Cross-references
- `project_aggregation_soundness_gap` (the motivating find) · `feedback_codex_gate_inline_review` (the gate this complements).
- The S1 decoder class: HYP-14/21/27/47/49/72/73/98/100. The FSM class: HYP-370 (ratchet), HYP-28/251 (consensus).
- HYP-330 (external audit — scopes the tier-4 targets).
- `scripts/factory/` (where tiers 1–2 get mechanized as gate criteria).
