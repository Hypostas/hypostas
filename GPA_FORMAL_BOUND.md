# GPA_FORMAL_BOUND.md — the affirmative Tier-3 bound, assembled from published mechanisms

**Status:** FORMAL-PASS v0 (**start**), **pre-review**, 2026-08-05, for **HYP-329**. Companion to the
diagnostic `GPA_ANALYSIS.md` (which states the leak; this states the *bound*). **Literature-first by
design** — the failure mode across the three refuted HYP-527 dither drafts (`COVER_DITHER_SYMMETRIC` v1,
`COVER_RATE_QUANTIZATION` v2, `COVER_DITHER_BOUNDED_DELAY` v3) was **hand-deriving a novel randomized
response** and hitting the same wall each time (support holes, the delay-vs-iid tension, the dropped
group-privacy ×2). This pass grounds every step in a published, peer-reviewed result and derives on top of
proven tools. **This v0 is the framing + grounding + derivation plan, not the finished parametric bound** —
the numeric bound (§7) is the tracked continuation. Not yet gated.

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

## §7 The tracked continuation (what the next, fresh-context derivation must produce)

This v0 established the *primitive and the grounding*. The finished bound owes:
1. **The dyados parameter map:** `T` (interval), `W`/`ΔW` (window + sensitivity = the idle↔ceremony volume
   gap from `EnergyClass` rates), the per-interval `(ε_T,δ_T)`, and the composed `ε_W` — plugged from the
   real cover-engine constants (`cover_traffic.rs:44-53` rates; the SANGUIS/ceremony volume profile).
2. **The Rényi composition worked example** at those params (the √τ curve) + the ×2 relationship bound, as a
   **computed test in `gpa-sim`** (rule #8 — encode the spec value; never assert the ε), extending the
   harness (329a–d) to model the Gaussian-shaped trace and the AnoA relationship challenge.
3. **The ceremony bounded-delay expiry** wired to Josh's approved ≤1-epoch bound, and the cost curve
   (bandwidth vs ε) for the Josh operating-point decision.
4. **Cross-vendor gate** (this is crypto-critical): the neighboring definition's mapping, the sensitivity
   `ΔW`, and the composition are the load-bearing claims to refute.

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
