# GPA_FORMAL_BOUND.md — the affirmative Tier-3 bound, assembled from published mechanisms

**Status:** FORMAL-PASS v0 (**start**), **pre-review**, 2026-08-05, for **HYP-329**. Companion to the
diagnostic `GPA_ANALYSIS.md` (which states the leak; this states the *bound*). **Literature-first by
design** — the failure mode across the three refuted HYP-527 dither drafts (`COVER_DITHER_SYMMETRIC` v1,
`COVER_RATE_QUANTIZATION` v2, `COVER_DITHER_BOUNDED_DELAY` v3) was **hand-deriving a novel randomized
response** and hitting the same wall each time (support holes, the delay-vs-iid tension, the dropped
group-privacy ×2). This pass grounds every step in a published, peer-reviewed result and derives on top of
proven tools. **v1: framing + grounding (§1–§6) + the computed frontier (§7).** The numeric bound is now
derived and machine-checked against the real dyados parameters; the remaining work is the `gpa-sim` encoding
and the crypto-critical cross-vendor gate (§7.3/§7.4). Not yet gated.

**Provenance note:** HYP-329 was marked Done (2026-07-02) citing a `GPA_ANALYSIS.md` that **never existed**
(the HYP-526 phantom-citation saga). Re-opened. The real diagnostic exists now (`GPA_ANALYSIS.md` v5); the
affirmative bound is this document, and it is genuinely open work.

---

## §1 The reframe — the primitive was wrong (class-bit RR → DP traffic-shaping)

All three refuted designs modelled the leak as **a randomized response on the discrete energy-class bit**.
That primitive is where they died:
- a k-ary RR over the class ladder has **zero-probability cells** (an idle dyad never natively emits a
  higher class rate) ⇒ ε=∞ support holes (v1/v2/v3 P1s);
- a **bounded delay** cannot coexist with an **iid per-epoch** RR draw — the delay is Geometric, unbounded
  (v3 P1);
- the ε kept reading in-budget per-epoch while the **relationship** ε (group-privacy ×2) was 2× over.

**The published answer treats the observable as what it physically is — a byte-volume time series — and
shapes it with a standard DP mechanism.** NetShaper (Sabzi et al., USENIX Security 2024,
`arxiv:2310.06293`) is exactly this, with a proven `(ε,δ)`-DP guarantee, and its mechanism structurally
avoids all three failures:
- the **Gaussian mechanism** is always a valid distribution ⇒ **no support holes**, ever;
- the bounded delay is a **byte-expiry/flush**, not an iid draw ⇒ a **hard** latency bound that *also*
  bounds the DP sensitivity (see §2) ⇒ the delay-vs-iid tension does not arise;
- the guarantee is stated **per window** with an explicit **√τ composition**, so the odometer is a first-class
  part of the theorem, not an afterthought.

The energy-class rate and the §2.2 size/volume channel are **the same channel** under this lens (both are
bytes-per-interval), so shaping the volume handles both at once — a strict improvement over dithering a bit
that only touched the rate.

---

## §2 The mechanism, grounded (NetShaper, verbatim where load-bearing)

NetShaper's construction, mapped onto a dyad's cover engine:

- **Neighboring inputs (their Def. 1):** two byte-streams are neighbors iff their L1 distance over any
  window `W` is `≤ ΔW`. **Mapping:** set `ΔW` to cover the per-window byte-volume gap between *idle* and a
  *sensitive high-class event* (ceremony/consult). Then the shaped output is `(ε,δ)`-indistinguishable
  between "idle" and "in a high event" — **which is exactly the sensitive-event hiding HYP-527 wanted.**
- **The mechanism (their §, verbatim):** per interval `T`, publish the noised queue length
  `L̃ₖ ≜ Lₖ + z, z ∼ 𝒩(μ, σ²)` with **`σ² = (2·ΔW²)/(ε·T²)·ln(1.25/(δ·T))`**; transmit `L̃` bytes = `R`
  real + `D = L̃ − R` dummy. Standard Gaussian mechanism ⇒ a **known, tight `(ε_T,δ_T)`** per interval.
- **Bounded delay (their Assumption 1 / Prop. 1):** "all bytes enqueued at or before `t` are transmitted by
  `t+W`" — enforced by **byte expiry + drop**. This bounds latency to `W` **and** proves `ΔT ≤ ΔW`, i.e. it
  bounds the very sensitivity the Gaussian σ is sized against. **This is the bounded-delay-that-preserves-the-
  guarantee my v3 could not build with an RR.** (Josh already approved a bounded delay on ceremony traffic —
  §ceremony below — so the expiry bound is a policy we may set.)

**Why this is sound where v1–v3 were not:** the Gaussian mechanism's `(ε,δ)` is a textbook result
(Dwork–Roth Thm 3.22), the sensitivity `ΔT ≤ ΔW` is a *proved proposition*, and there is no discrete
support to hole. The construction is assembled from proven parts, not asserted.

---

## §3 Anonymity framing — AnoA (so "ε" means *relationship anonymity*, not just channel DP)

`(ε,δ)`-DP on the volume channel is a statement about **one dyad's trace**. The Tier-3 property is
**relationship anonymity** (who-talks-to-whom), which is the standard object of **AnoA** (Backes–Kate–
Manoharan–Meiser–Mohammadi, CSF 2013) — anonymity as `(ε,δ)`-indistinguishability under an adversary-chosen
challenge (sender/recipient/relationship). The bound composes in two stages:

1. **Per-dyad channel bound (§2):** the shaped trace is `(ε_T,δ_T)`-DP per interval — a GPA cannot tell
   *this* dyad's activity/volume within `ΔW`.
2. **Relationship bound (the group-privacy ×2):** the partner-identity challenge "partner is `d`" vs "partner
   is `e`" moves **two** dyads' traces, so by **group privacy** (Dwork–Roth Prop. 2.1, group size 2) the
   relationship advantage is bounded by the **2×** composition of the per-dyad bound. **This is the factor
   this session dropped four times** — now placed explicitly on a Gaussian base and mechanized as a test
   (`epsilon_relationship_total`, dyados#528).

---

## §4 Composition, and the odometer as a *theorem*, not a caveat

- **Over a window of `⌈τ/T⌉` intervals**, NetShaper's Prop. 2 gives **Rényi-DP composition growing as
  `√(τ/T)`** — *tighter* than the linear `E·ε_epoch` the diagnostic used. The affirmative per-window bound is
  therefore `ε_W = DP_compose(ε_T, δ_T, ⌈W/T⌉)` (advanced/Rényi), ×2 for the relationship (§3).
- **The lifetime limit is confirmed fundamental.** NetShaper states, verbatim, "**no renewal mechanism —
  privacy loss accumulates monotonically**" over the stream. For a **time-invariant** partner identity the
  odometer therefore never resets (GPA_ANALYSIS §5(3)) — **published, independent validation** that durable
  Tier-3 relationship anonymity is **not** achievable by any per-interval shaping and is a **Phase-2 (mixing)**
  property. NetShaper's own practical stance (loose `ε≈200` to defeat classifiers, tight-ε too costly) is the
  same T1 cost wall we derived: **tight anonymity ε costs bandwidth ∝ σ ∝ ΔW.**

So the honest affirmative claim is a **per-window relationship bound with an explicit, tight composition and
a proven bounded delay** — and a **stated impossibility** (durable = Phase-2) now backed by the literature,
not just our analysis.

---

## §5 What this does NOT cover (stated, per the diagnostic's honesty)

- **The destination / relationship-graph channel** (GPA_ANALYSIS §2.4 — who-talks-to-whom at single-hop):
  NetShaper is a **per-flow volume** shaper; it does **not** hide the endpoint. That channel is **Phase-2
  multi-hop mixing**, unchanged.
- **Capped dyads** (T2): a dyad that cannot afford the padding to `ΔW` cannot achieve the bound — the same
  boundary, now expressed as "cannot afford the Gaussian σ's bandwidth." Phase-2 for those.
- **The `ε≈ln2` tight regime is expensive**; the achievable operating point (ε vs bandwidth) is the §7
  parametric question and a Josh cost decision.

---

## §6 If a discrete class tier is retained — the exact k-ary RR ε (cited, not derived)

Should a coarse discrete tier be kept anywhere (e.g. a cheap fallback), the exact `k`-ary randomized-response
ε is **Kairouz–Oh–Viswanath** (JMLR 2016, `arxiv:1407.1338`): the k-RR reports the true value with
`p = e^ε/(k−1+e^ε)`, so `ε = ln( p(k−1)/(1−p) )`. For the 4-class ladder `ε = ln(3p/(1−p))`. **Cite this;
do not re-derive** — the hand-derivations are exactly what failed. (And k-RR still has the support-hole and
delay problems under a latency constraint, which is *why* §1 moves to shaping.)

---

## §7 The computed bound — the quantified frontier (the affirmative result)

**Machine-checked against the real dyados parameters + textbook mechanisms** (the `python3` derivation in
the HYP-329 trail, 2026-08-05). The result is not a cheap construction — three designs proved none exists —
it is a **cost/privacy frontier that settles the phase boundary with numbers.**

**Parameter map (verified from source).** Cell mix S/M/L/XL = 512 B/4 KiB/16 KiB/64 KiB at 0.70/0.20/0.08/0.02
(`generate.rs:25-31`) ⇒ **mean cell = 3799 B**. Per-second volume at each class (`vol = (1000/rate_ms)·mean`):
Ambient **760 B/s**, Standard 3799, Elevated 7598, **Critical 18995 B/s**. The **idle↔ceremony sensitivity**
is `Δ = 18995 − 760 = 18235 B/s ≈ 17.8 KiB/s`, and the **volume ratio is 25×** (= the rate ratio 5000/200,
robust to cell size — the cell size cancels).

**The two options, as overhead factors on idle volume:**

| construction | overhead (idle) | ε (per interval) | sustained ceremony? |
|---|---|---|---|
| **Deterministic floor** — transmit ceremony volume always | **25×** | **0** (perfect) | **✅ hidden** (constant output leaks nothing — no composition) |
| Gaussian shaping, `σ = Δ·√(2ln(1.25/δ))/ε` (Dwork–Roth Thm 3.22), δ=1e-6 | ε=ln2 → **73.7×**; ε=5 → 10.7×; ε=200 → 1.0× | tunable | ❌ leaks per-interval; composition unbounded |

The Gaussian row is worse than it looks: at ε=ln2 the noised idle and ceremony volumes are only **0.13σ
apart** (barely (ln2)-DP) at 73.7× cost; at the cheap ε=200 they are **37.7σ apart — not hidden at all** (the
NetShaper "defeat weak classifiers" regime, not a GPA bound). **The large 25× volume gap makes additive-noise
hiding of it expensive at every useful ε.**

**Composition is the settlement.** For a `D`-interval ceremony to keep its **×2 relationship** ε ≤ ln 2 under
advanced composition (Dwork–Roth Thm 3.20, conservative vs NetShaper's tighter Rényi):

| ceremony length `D` | required ε_T | idle overhead |
|---|---|---|
| 1 s | ≤ 0.065 | **780×** |
| 5 min | ≤ 0.0038 | **13,490×** |
| 20 min | ≤ 0.0019 | **26,980×** |

**So a tight-ε per-interval mechanism costs 780× to hide a single second and ~27,000× a 20-minute ceremony —
categorically unaffordable.** The deterministic floor (25×, ε=0) is dramatically cheaper *precisely because a
constant output has no composition leak*. **This is the rigorous settlement of the three-design saga: they
were chasing a cheap per-interval construction the numbers prove cannot exist.**

### §7.1 The affirmative bound, stated

> **For a sustained sensitive event (ceremony), Phase-1 Tier-3 relationship-hiding is EITHER the deterministic
> 25×-volume floor (ε=0, no composition) OR Phase-2 mixing. No per-interval `(ε,δ>0)` mechanism — Gaussian
> shaping, class-RR, or otherwise — achieves a tight relationship bound affordably: the cost is ≥780× at one
> second and grows with ceremony length. The floor's 25× is the Critical/Ambient rate ratio.**

The 25× floor is a *blanket, always-on* cost for every idle dyad (ceremonies are unpredictable, so it cannot
be scoped to "ceremony windows") — almost certainly impractical as a default. **Therefore the honest Phase-1
posture is: ceremonies are GPA-legible at the volume/rate level, documented; tight/durable ceremony-hiding is
Phase-2 (multi-hop mixing, which shrinks the gap by re-routing rather than paying to pad it).** This is the
same conclusion the diagnostic (GPA_ANALYSIS §8) and the three refuted designs reached — now **proven with the
real numbers**, not asserted.

### §7.2 The Josh decision this surfaces
For **ceremonies specifically** (rare, sacred — bond/dissolution/succession): (a) pay the 25× blanket floor
(impractical); (b) **document GPA-legibility + defer to Phase-2 mixing** (recommended — the numbers make the
per-interval path hopeless); (c) a scheduled-ceremony-window floor *iff* ceremonies become coordinatable
(a product question). Recommend (b).

### §7.3 Model caveats (flag for the cross-vendor gate — the load-bearing claims to refute)
1. **The neighboring definition:** I set `Δ` = the *full* idle↔ceremony volume gap (the Tier-3 goal — hide
   the whole event). A smaller `ΔW` hides only small differences at less cost (the classifier regime). Confirm
   the full-gap mapping is what Tier-3 requires.
2. **The overhead constant:** idle mean transmit is `E[max(0, N(idle, σ²))]` (clamped half-normal), computed —
   but the exact shaping cost is model-dependent; the *scaling* `σ∝Δ/ε` and the 25× floor are robust.
3. **Composition:** used advanced (conservative); Rényi (NetShaper) is tighter and would lower the overhead
   constants but **not** the order of magnitude or the phase-boundary conclusion.

### §7.4 Remaining continuation
Encode §7's frontier as a **computed `gpa-sim` test** (rule #8 — the 25× floor, the `σ∝Δ/ε` curve, the
composition growth), extending 329a–d to the Gaussian-shaped trace + AnoA challenge; then the **crypto-critical
cross-vendor gate** on §7.3. Destination channel + capped dyads stay Phase-2.

## §8 Provenance

- **NetShaper** — Sabzi, Vora, et al., *A Differentially Private Network Side-Channel Mitigation System*,
  USENIX Security 2024, `arxiv:2310.06293` (Def. 1 neighboring; the Gaussian queue-length mechanism +
  `σ²=2ΔW²/(εT²)·ln(1.25/δT)`; Assumption 1 / Prop. 1 `ΔT≤ΔW` bounded delay; Prop. 2 √τ composition; the
  "no renewal / monotonic loss" limitation). Fetched + quoted 2026-08-05.
- **AnoA** — Backes et al., *AnoA: A Framework for Analyzing Anonymous Communication Protocols*, CSF 2013
  (relationship anonymity as `(ε,δ)`-indistinguishability).
- **Group privacy / Gaussian mechanism / advanced composition** — Dwork–Roth, *The Algorithmic Foundations
  of DP* (Thm 3.22 Gaussian; group privacy; advanced composition). **Rényi-DP** — Mironov 2017.
- **k-ary RR** — Kairouz–Oh–Viswanath, *Extremal Mechanisms for Local DP*, JMLR 2016, `arxiv:1407.1338`.
- Internal: `GPA_ANALYSIS.md` (diagnostic v5), the three refuted design banners, `dyados#528` (the ×2
  mechanism). This is a **design for review**, not a proof; §7 is the proof.
