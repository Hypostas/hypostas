# GPA_FORMAL_BOUND.md — the affirmative Tier-3 bound, assembled from published mechanisms

**Status:** FORMAL-PASS v0 (**start**), **pre-review**, 2026-08-05, for **HYP-329**. Companion to the
diagnostic `GPA_ANALYSIS.md` (which states the leak; this states the *bound*). **Literature-first by
design** — the failure mode across the three refuted HYP-527 dither drafts (`COVER_DITHER_SYMMETRIC` v1,
`COVER_RATE_QUANTIZATION` v2, `COVER_DITHER_BOUNDED_DELAY` v3) was **hand-deriving a novel randomized
response** and hitting the same wall each time (support holes, the delay-vs-iid tension, the dropped
group-privacy ×2). This pass grounds every step in a published, peer-reviewed result and derives on top of
proven tools. **v3: framing + grounding (§1–§6) + the computed frontier (§7) — cross-vendor gated twice and
corrected.** The frontier is machine-checked (`gpa_formal_bound_derivation.py`, committed). v1's numbers were
inflated ~5.3× (advanced-vs-Rényi composition) and were fixed in v2; **v3's round-2 gate (on the `gpa-sim`
harness) then caught two more, both real:** the headline Gaussian cost must use the **worst-case** sensitivity
(the strict `(ε,δ)` frontier is **2,631×–91,114×**, not the mean-model 147×–5,071× — that is only a lower
bound), and the `√D` lower bound holds for *utility-preserving* mechanisms, not universally (the floor is the
per-interval escape). The **conclusion survived every round** — the strict numbers are larger, strengthening
it. Residual §7.3 items (composed-δ accountant) remain the tracked continuation; the `gpa-sim` encoding is DONE.

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
(committed beside this doc; run it). The result is not a cheap construction — three designs proved none exists
— it is a **cost/privacy frontier that settles the phase boundary with numbers, with a matching lower bound.**

> **Gate reconciliation (2026-08-05 v2, 2026-08-06 v3).** The v1 of this section had real errors, all
> corrected and re-verified: it computed the composed frontier with **advanced composition while citing
> Rényi**, inflating every number **~5.3×**; ran advanced composition at **D=1** (a category error); lacked
> the **lower bound**; and conflated **volume-hiding with relationship-hiding** (§7.1). **v3 (round-2 gate)**
> fixed two more, both flagged cross-vendor on the harness code: (a) the headline Gaussian numbers used the
> **mean** sensitivity, which under-noises — a valid `(ε,δ)` bound uses the **worst-case** sensitivity (18×
> larger), so the strict frontier is **2,631× / 45,557× / 91,114×**, and the mean-model 147×/2,536×/5,071× is
> only a *lower bound* on the cost; (b) the `√D` lower bound was over-stated as universal ("no per-interval
> mechanism escapes") when the deterministic floor **is** a per-interval mechanism that escapes it — the bound
> holds for *utility-preserving* mechanisms, and the floor escapes precisely by not preserving utility. The
> *conclusion survived every round* — the strict numbers are larger, which only strengthens it.

**Parameter map (verified exact by both gate legs).** Cell on-wire totals S/M/L/XL = 512/4096/16384/65536 B
(`sealed_envelope` `CELL_TOTAL_*`) at 0.70/0.20/0.08/0.02 (`generate.rs:25-31`) ⇒ **mean cell = 3799 B**.
Per-second volume `(1000/rate_ms)·mean`: Ambient **760 B/s** … **Critical 18995 B/s**. The **volume ratio is
exactly 25×** (= the rate ratio 5000/200, cell size cancels — this is the floor, and it is exact). Two
sensitivities matter: the idle↔ceremony **mean gap** `Δ_mean = 18235 B/s ≈ 17.8 KiB/s` (the *amortized*
figure — a lower bound only) and the **worst-case per-interval L1 sensitivity** `Δ_wc = 5×64 KiB = 327680 B/s
= 320 KiB/s` (an all-XL Critical second vs idle-silent). **A strict `(ε,δ)` bound must use `Δ_wc`** — DP is
worst-case over neighbors, and a single XL cell (prob 0.02 ≫ δ=2⁻⁴⁰; the all-XL second is 0.02⁵≈3·10⁻⁹,
still ≫ δ) cannot be tail-dropped. `Δ_wc / Δ_mean = 18.0×`.

**The frontier — the two options, as overhead factors on idle volume:**

| construction | overhead (idle) | ε | sustained ceremony? |
|---|---|---|---|
| **Deterministic rate/class floor** — emit at Critical *rate* always (hides the class channel, not byte-volume) | **25×** | **0** (perfect) | **✅** — constant *rate* is activity-independent, zero composition leak, holds for any duration |
| **Gaussian shaping**, strict `(ε,δ)` (worst-case `Δ_wc`, zCDP, ×2 group, ε≤ln 2, δ=2⁻⁴⁰) | **2,631×** (1 s) · **45,557×** (5 min) · **91,114×** (20 min) | ln 2 | ❌ leaks per-interval; cost grows as **√D** with ceremony length |

*(The mean-model figures 147× / 2,536× / 5,071× are the same computation with `Δ_mean` — an under-noised
**lower bound**, reported only for scale; they are not a valid `(ε,δ)` cost.)*

*(The `(ε,δ)` guarantee is in the noise scale `σ = Δ_wc·√(D/ρ)`; the overhead factor is an **idealized
order-of-magnitude cost proxy** `E[max(0,N(idle,σ))]/idle` — a real shaper is upward-only (`max(real,target)`),
so this reports the cost *scale*, not a certified implementable-mechanism cost. The scale is the decision-
relevant fact.)*

**Why the byte-volume *shaping* path is expensive — an upper bound + an asymptotic lower bound.** For a
*sustained* `D`-interval ceremony under **per-interval adjacency** (the GPA may test onset/offset/any pattern,
so the worst neighboring difference is `(Δ,…,Δ)`), the trace has **L2 sensitivity `√D·Δ`** — so the noise must
scale as `√D`. This is **fundamental for any mechanism that must preserve each interval's utility** (can't
constant-over-pad): hiding `D` counting-like queries each of sensitivity `Δ` provably requires `Ω(√D·Δ/ε)`
noise (**Hardt–Talwar / fingerprinting lower bound**). Two caveats keep this honest (Codex r3): (i) the
priced construction (2,631×+) is an **upper** bound on the best shaping cost, and Hardt–Talwar is
**asymptotic** — it forbids *escaping √D growth*, not a tight constant below the floor at `D=1`; so shaping is
**strongly indicated** to lose, not proven to. (ii) A constant/data-independent mechanism escapes `√D` by
*abandoning utility* — for byte-volume that means **constant-size padding** (e.g. all-XL every cell, far more
than 25×), and for the class/tempo channel it is the **25× rate floor**. So `√D` bounds the shaping path;
the cheap `ε=0` answers are the non-shaping floors, each on its own channel. **This settles the three-design
saga: they chased a cheap per-interval *shaping* construction the DP lower bound makes implausible.**

### §7.1 The affirmative bound, stated (three channels — class/tempo, byte-volume, relationship)

**Do not conflate the channels.** The 25× *rate* floor and the Gaussian *byte-volume* frontier address
**different** leaks and are not competing constructions: (1) **class/tempo** — the emission *rate* reveals
the energy class (the §2 leak) — hidden by the 25× deterministic rate floor (ε=0); (2) **byte-volume** —
per-cell sizes vary and real vs cover size *distributions* differ — hidden only expensively (constant-size
padding, or the Gaussian frontier below); (3) **relationship/destination** — Phase-2 mixing. The blockquote
below states the byte-volume + relationship result.


> **The class-rate/volume channel — "is this dyad in a high-tempo (ceremony) event?" — can be hidden for a
> sustained event only by the deterministic 25× floor (ε=0, no composition, constant-padding) or by Phase-2
> mixing; every per-interval `(ε,δ)` *shaping* mechanism (one that preserves per-interval utility) costs
> 2,631×–91,114× (strict, worst-case sensitivity) and is `√D`-lower-bounded (Hardt–Talwar). The floor is the
> sole per-interval escape from `√D`, bought by abandoning utility.**
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
For **ceremonies** (rare, sacred): the numbers make the per-interval *shaping* path hopeless (2,631× minimum
at strict `(ε,δ)`, `√D`-bounded) and even the 25× volume floor does not give relationship anonymity. **Recommend: document ceremony
GPA-legibility (volume + relationship) as a Phase-1 limit; route tight/durable ceremony anonymity to Phase-2
mixing.** Whether to *also* ship the 25× volume floor (partial — hides the event tempo but not the partner) is
a bandwidth/sovereignty call, but its value is limited without the Phase-2 destination-hiding.

### §7.3 Model caveats (still the load-bearing claims for any further gate)
1. **Sensitivity model (RESOLVED in v3):** the strict frontier now uses the **worst-case** `Δ_wc = 320 KiB/s`
   (all-XL Critical vs idle-silent) — the correct choice for a hard `(ε,δ)`, since XL cells (prob 0.02 ≫ δ)
   can't be tail-dropped. The mean gap `Δ_mean = 17.8 KiB/s` is retained only as a labeled amortized *lower
   bound*. `Δ_wc/Δ_mean = 18.0×`; the harness pins both and asserts mean < strict.
2. **δ = 2⁻⁴⁰** (THREAT_MODEL Tier-3), and the composed δ must be tracked as `D·δ_T + δ′` — the frontier fixes
   the ε-budget at ln 2 and δ at 2⁻⁴⁰; a full accountant statement of the composed `(ε,δ)` is owed.
3. **Domain:** the classical Gaussian (Dwork–Roth Thm 3.22) is `ε<1`; the load-bearing ε=ln 2 row is in-domain,
   but any illustrative ε≥1 row needs the **analytic Gaussian** (Balle–Wang 2018). Group privacy is **Thm 2.2**
   (the ×2 is exact; the label, not the math). Laplace (δ=0) is the cheapest *single* interval (~17.8×) but
   composes linearly — worse for sustained; it does not escape `√D`.
4. **ε vs advantage (HYP-329 item 1) — DELIVERED.** The frontier targets an ε-*budget*; the corresponding
   distinguishing bound is the **advantage form**: for an `(ε_W, δ)`-DP relationship-linkage budget, the
   equal-prior total-variation distinguishing advantage is `tanh(ε_W/2) + 2δ/(e^{ε_W}+1)` (the privacy-region
   extremum — `tanh` is the pure-ε term, `2δ/(e^ε+1)` the δ correction). **At `ε_W = ln 2`, δ=0 this is exactly
   `1/3`**; at Tier-3 δ=2⁻⁴⁰ the correction `2δ/(e^{ln2}+1)=2δ/3 ≈ 6·10⁻¹³` — encoded + tested in `gpa-sim`
   (`formal_bound::distinguishing_advantage_tv`, which now takes δ and fails closed on a negative/NaN budget).

### §7.4 Continuation — the harness encoding is DONE
The frontier now lives in the harness, not just a script: `gpa-sim/src/formal_bound.rs` (dyados) encodes the
25× floor, the Gaussian + zCDP sustained-event composition (sensitivity passed explicitly, so the caller picks
strict `Δ_wc` vs amortized `Δ_mean`), the `√D` scaling, and the advantage form — with tests pinning the strict
frontier **2,631×/45,557×/91,114×** and the amortized lower bound **147×/2,536×/5,071×** within 1% (rule #8, so
drift fails), and asserting mean < strict and strict ≫ 100× the floor. Everything fails closed on garbage
privacy params. The **destination channel and capped dyads remain Phase-2** — and per §7.1 they are what Tier-3
relationship anonymity actually needs.

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
- **The `√D` lower bound** (why no *utility-preserving* per-interval shaping mechanism escapes it — the
  deterministic floor does, by constant-padding): **Hardt–Talwar** / the fingerprinting lower bound — hiding
  `D` counting-like queries of sensitivity `Δ` requires `Ω(√D·Δ/ε)` noise.
- **k-ary RR** — Kairouz–Oh–Viswanath, *Extremal Mechanisms for Local DP*, JMLR 2016, `arxiv:1407.1338`.
- **The §7 numbers** — `gpa_formal_bound_derivation.py` (committed beside this doc, reproducible);
  independently reproduced by the cross-vendor gate's Claude depth leg (2026-08-05).
- Internal: `GPA_ANALYSIS.md` (diagnostic v5), the three refuted design banners, `dyados#528` (the ×2
  mechanism). This is a **design for review**; §7 is the computed frontier + its matching lower bound.
