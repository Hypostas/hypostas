# GPA_FORMAL_BOUND.md — the affirmative Tier-3 bound, assembled from published mechanisms

**Status:** FORMAL-PASS v0 (**start**), **pre-review**, 2026-08-05, for **HYP-329**. Companion to the
diagnostic `GPA_ANALYSIS.md` (which states the leak; this states the *bound*). **Literature-first by
design** — the failure mode across the three refuted HYP-527 dither drafts (`COVER_DITHER_SYMMETRIC` v1,
`COVER_RATE_QUANTIZATION` v2, `COVER_DITHER_BOUNDED_DELAY` v3) was **hand-deriving a novel randomized
response** and hitting the same wall each time (support holes, the delay-vs-iid tension, the dropped
group-privacy ×2). This pass grounds every step in a published, peer-reviewed result and derives on top of
proven tools. **v2: framing + grounding (§1–§6) + the computed frontier (§7) — cross-vendor gated and
corrected.** The frontier is machine-checked (`gpa_formal_bound_derivation.py`, committed) and was
**independently reproduced by the gate's Claude depth leg**; v1's numbers were inflated ~5.3× (advanced-vs-
Rényi composition) and are fixed. Gated 2026-08-05: the **conclusion survived** both Codex and the independent
re-derivation; the residual §7.3/§7.4 items (worst-case sensitivity, composed-δ accountant, advantage-form
bound, `gpa-sim` encoding) are the tracked continuation.

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
   is `e`" moves **two** dyads' traces, so by **group privacy** (Dwork–Roth **Thm 2.2**, group size 2) the
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

**Machine-checked and reproducible** — every number below is emitted by `gpa_formal_bound_derivation.py`
(committed beside this doc; run it), and the composed frontier was **independently reproduced by the
cross-vendor gate's Claude depth leg** (147×/2536×/5072×, matching to rounding). The result is not a cheap
construction — three designs proved none exists — it is a **cost/privacy frontier that settles the phase
boundary with numbers, with a matching lower bound.**

> **Gate reconciliation (2026-08-05).** The v1 of this section had real errors, all corrected here and
> re-verified: it computed the composed frontier with **advanced composition while citing Rényi**, inflating
> every number **~5.3×** (780×→**147×**, 26,980×→**5,072×**); it ran advanced composition at **D=1** (a single
> interval — a category error); it lacked the **lower bound** that makes the impossibility rigorous; and it
> conflated **volume-hiding with relationship-hiding** (§7.1). The *conclusion survived both Codex and the
> independent Claude re-derivation* — only the numbers and the scope statement needed fixing.

**Parameter map (verified exact by both gate legs).** Cell on-wire totals S/M/L/XL = 512/4096/16384/65536 B
(`sealed_envelope` `CELL_TOTAL_*`) at 0.70/0.20/0.08/0.02 (`generate.rs:25-31`) ⇒ **mean cell = 3799 B**.
Per-second volume `(1000/rate_ms)·mean`: Ambient **760 B/s** … **Critical 18995 B/s**. The idle↔ceremony
**mean-model** sensitivity is `Δ = 18235 B/s ≈ 17.8 KiB/s`; the **volume ratio is exactly 25×** (= the rate
ratio 5000/200, cell size cancels). *(Caveat, §7.3: `Δ` here is the mean/amortized sensitivity; a strict
worst-case per-interval L1 sensitivity is larger — up to 5×64 KiB ≈ 320 KiB/s from an all-XL Critical second —
which makes the numbers **worse**, never better.)*

**The frontier — the two options, as overhead factors on idle volume:**

| construction | overhead (idle) | ε | sustained ceremony? |
|---|---|---|---|
| **Deterministic floor** — transmit ceremony volume always | **25×** | **0** (perfect) | **✅** — a constant output has *zero* composition leak, so it holds for any duration |
| **Gaussian shaping** (zCDP composition, ×2 group, ε≤ln 2, δ=2⁻⁴⁰) | **147×** (1 s) · **2,536×** (5 min) · **5,072×** (20 min) | ln 2 | ❌ leaks per-interval; cost grows as **√D** with ceremony length |

**Why the Gaussian path cannot win, with a *lower* bound (not just our upper bound).** For a *sustained*
`D`-interval ceremony, the two hypotheses (idle-throughout vs Critical-throughout) differ by the vector
`(Δ,…,Δ)` over `D` intervals, whose **L2 sensitivity is `√D·Δ`** — so the noise must scale as `√D`, not stay
constant. And this is **fundamental**: hiding `D` counting-like queries each of sensitivity `Δ` provably
requires `Ω(√D·Δ/ε)` noise (**Hardt–Talwar / fingerprinting lower bound**), so **no per-interval mechanism —
Gaussian, Laplace, discrete, or otherwise — escapes the `√D` growth.** The deterministic floor is cheap
*precisely because a constant output composes to zero*, which the `√D` bound does not touch. **This settles the
three-design saga: they were chasing a cheap per-interval construction that a DP lower bound forbids.**

### §7.1 The affirmative bound, stated (corrected: this hides VOLUME, not the relationship)

> **The class-rate/volume channel — "is this dyad in a high-tempo (ceremony) event?" — can be hidden for a
> sustained event only by the deterministic 25× floor (ε=0, no composition) or by Phase-2 mixing; every
> per-interval `(ε,δ≥0)` memoryless mechanism costs 147×–5,072× and is `√D`-lower-bounded (Hardt–Talwar).**
>
> **This is NOT, by itself, Tier-3 *relationship* anonymity.** Relationship anonymity (AnoA §3) is *who-talks-
> to-whom* — the **destination** channel (GPA_ANALYSIS §2.4), which volume shaping does **not** touch: if the
> two partner hypotheses expose different endpoints, their observable supports are disjoint regardless of any
> volume floor. **So Tier-3 relationship anonymity is a Phase-2 (multi-hop mixing) property, full stop** — the
> per-interval mechanisms only ever addressed the *volume sub-channel*, and even perfecting it (the 25× floor)
> leaves the relationship graph in the clear.

The 25× floor is also *blanket, always-on* (ceremonies are unpredictable, so it cannot be scoped to a window)
— impractical as a default. **Therefore the honest Phase-1 posture: ceremonies are GPA-legible at the
volume/rate level AND the relationship level; the volume floor is available at 25× but does not buy
relationship anonymity; tight/durable Tier-3 is Phase-2 mixing (which shrinks the volume gap *and* hides the
destination by re-routing).** Same conclusion as the diagnostic (GPA_ANALYSIS §8) and the three refuted
designs — now with the numbers *and* a matching lower bound.

### §7.2 The decision this surfaces (for Josh)
For **ceremonies** (rare, sacred): the numbers make the per-interval path hopeless (147× minimum, `√D`-bounded)
and even the 25× volume floor does not give relationship anonymity. **Recommend: document ceremony
GPA-legibility (volume + relationship) as a Phase-1 limit; route tight/durable ceremony anonymity to Phase-2
mixing.** Whether to *also* ship the 25× volume floor (partial — hides the event tempo but not the partner) is
a bandwidth/sovereignty call, but its value is limited without the Phase-2 destination-hiding.

### §7.3 Model caveats (still the load-bearing claims for any further gate)
1. **Sensitivity model:** `Δ` is the mean/amortized gap; the strict worst-case per-interval L1 sensitivity is
   larger (all-XL Critical second ≈ 320 KiB/s), which only worsens the frontier. State which the Tier-3 claim
   requires (worst-case for a hard `(ε,δ)`; mean for amortized cost).
2. **δ = 2⁻⁴⁰** (THREAT_MODEL Tier-3), and the composed δ must be tracked as `D·δ_T + δ′` — the frontier fixes
   the ε-budget at ln 2 and δ at 2⁻⁴⁰; a full accountant statement of the composed `(ε,δ)` is owed.
3. **Domain:** the classical Gaussian (Dwork–Roth Thm 3.22) is `ε<1`; the load-bearing ε=ln 2 row is in-domain,
   but any illustrative ε≥1 row needs the **analytic Gaussian** (Balle–Wang 2018). Group privacy is **Thm 2.2**
   (the ×2 is exact; the label, not the math). Laplace (δ=0) is the cheapest *single* interval (~17.8×) but
   composes linearly — worse for sustained; it does not escape `√D`.
4. **ε vs advantage (HYP-329 item 1, still owed):** the frontier targets an ε-*budget* (legitimate); it does
   **not** yet state the bound as a distinguishing *advantage* (equal-prior TV `= tanh(ε/2)`), which is the
   HYP-329 deliverable — route it to the continuation, do not narrate ε as "advantage."

### §7.4 Remaining continuation
Promote `gpa_formal_bound_derivation.py` into a **`gpa-sim` test** (rule #8 — the 25× floor, the `√D` composed
frontier, the fingerprinting lower bound as an assertion), extending 329a–d to the Gaussian-shaped trace + the
AnoA relationship challenge; state the advantage-form bound (§7.3(4)); then re-gate. The **destination channel
and capped dyads remain Phase-2** — and per §7.1 they are what Tier-3 relationship anonymity actually needs.

## §8 Provenance

- **NetShaper** — Sabzi, Vora, et al., *A Differentially Private Network Side-Channel Mitigation System*,
  USENIX Security 2024, `arxiv:2310.06293` (Def. 1 neighboring; the Gaussian queue-length mechanism +
  `σ²=2ΔW²/(εT²)·ln(1.25/δT)`; Assumption 1 / Prop. 1 `ΔT≤ΔW` bounded delay; Prop. 2 √τ composition; the
  "no renewal / monotonic loss" limitation). Fetched + quoted 2026-08-05.
- **AnoA** — Backes et al., *AnoA: A Framework for Analyzing Anonymous Communication Protocols*, CSF 2013
  (relationship anonymity as `(ε,δ)`-indistinguishability).
- **Gaussian mechanism (Thm 3.22, ε<1) / group privacy (Thm 2.2) / advanced composition (Thm 3.20)** —
  Dwork–Roth, *The Algorithmic Foundations of DP*. **Analytic Gaussian (ε≥1)** — Balle–Wang, ICML 2018.
  **zCDP / Rényi-DP** — Bun–Steinke 2016 / Mironov 2017 (the √D composition + the ×2 group scaling).
- **The `√D` lower bound** (why no per-interval mechanism escapes): **Hardt–Talwar** / the fingerprinting
  lower bound — hiding `D` counting-like queries of sensitivity `Δ` requires `Ω(√D·Δ/ε)` noise.
- **k-ary RR** — Kairouz–Oh–Viswanath, *Extremal Mechanisms for Local DP*, JMLR 2016, `arxiv:1407.1338`.
- **The §7 numbers** — `gpa_formal_bound_derivation.py` (committed beside this doc, reproducible);
  independently reproduced by the cross-vendor gate's Claude depth leg (2026-08-05).
- Internal: `GPA_ANALYSIS.md` (diagnostic v5), the three refuted design banners, `dyados#528` (the ×2
  mechanism). This is a **design for review**; §7 is the computed frontier + its matching lower bound.
