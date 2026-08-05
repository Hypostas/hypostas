# GPA_ANALYSIS.md — the Tier-3 anonymity analysis

**Status:** DESIGN / pre-gate, written 2026-08-05 for **HYP-526**. This document was cited ~15× by
shipped code and `gpa-sim` and **did not exist** until now (verified: no copy anywhere in the
workspace, no git history in any repo). It is therefore a *from-scratch derivation*, not a recovery.

> ⚠️ **NOT YET GATED.** A security/anonymity bound written by one model on a long context is exactly
> what rule #1 and the cross-vendor sign-off rule forbid self-certifying. Every citation below is
> "resolved" only after this passes the full-leg cross-vendor DESIGN-review. Until then, treat the
> **numbers as claims, not guarantees**, and the model↔runtime gap in §7 as the load-bearing result.

This document's section numbers are fixed by the citations that already point at them
(`gpa-sim/src/measure.rs`, `protocol-core/src/cover_content.rs`, `vita-carriers/src/cover_traffic.rs`):
§3 = Serjantov–Danezis entropy, §4.1 = the per-epoch class-rate leak + intersection, §5 = the DP
budget + composition, §7 = findings (finding #1 = exact-class emission). They are contracts, not
choices.

---

## §1 The adversary

**Tier 3 — Global Passive Adversary (GPA)**, per `THREAT_MODEL.md` §4.3: sees *all* network links
simultaneously, cannot decrypt content, but correlates timing and volume across the entire visible
network, with records that persist indefinitely (store-now-analyse-later). `THREAT_MODEL.md` §6.3
line 296 already states the Phase-1 posture in prose; this document is its quantitative backing.

**What Phase 1 claims, and does not.** `THREAT_MODEL.md` §5 (matrix) line 209: Phase 1 ships *"Tier 1
fully + Tier 2 partial + **chassis for Tier 3/4**."* It does **not** claim full Tier-3 relationship
anonymity — that needs a mixing vantage point (multi-hop + relay padding), which is Phase 2+
(`COVER_TRAFFIC.md` §7.1: *"Phase 1 baseline… anonymity set effectively 1"*; `CIRCUIT_LIFECYCLE.md`
§3: single-hop, N=1). This analysis therefore bounds **what the GPA learns from the cover-traffic
schedule alone**, which is the one Tier-3-relevant surface Phase 1 actually exposes.

## §2 The observable

A GPA sees, per dyad per carrier per slot, a fixed-size ciphertext cell on a constant-rate grid.
Content, destination, and real-vs-cover are hidden (SEALED_ENVELOPE + constant-rate fill). **One thing
is not hidden: the grid rate itself**, which equals the dyad's `EnergyClass` (`cover_traffic.rs`
`rate_ms`: Ambient 5 s / Standard 1 s / Elevated 500 ms / Critical 200 ms). §6.3 admits this:
*"the streams reveal… what energy class it's in."*

The GPA's per-epoch observation of dyad *d* is therefore its **emitted class** `E_d ∈ {A,S,E,C}` — or,
in the binary model the simulator and the dither actually operate on, the **active bit** `b_d ∈ {0,1}`
(idle vs active), re-drawn once per **30 s dither epoch** (`cover_content.rs:211`,
`cover_traffic.rs:70`; the class is constant within an epoch).

## §3 The anonymity metric (Serjantov–Danezis)

Anonymity is measured by the **effective anonymity-set size** `2^H`, where `H` is the Shannon entropy
of the GPA's posterior over *who the target's partner is* (Serjantov–Danezis, PET 2002). This is what
`gpa-sim/src/adversary.rs` `posterior_partner_entropy` computes: over the `E` epochs in which the
**target** is active, each candidate *d* accrues a log-likelihood-ratio

```
score(d) = k_d · ln(a / q')  +  (E − k_d) · ln((1−a) / (1−q'))
```

where `k_d` = epochs *d* was observed active among the target's `E` active epochs, `a = 1−γ`
(P[observed active | true partner]), and `q' = q(1−γ) + (1−q)γ` (P[observed active | non-partner],
`q` = background co-activity). `H` is the entropy of the softmax of these scores. Two limits fix the
metric (both asserted in code):

- **γ = 0** (no dither): the idle-slot log-LR → −∞, all posterior mass collapses onto candidates
  active in *every* target-active epoch, and `H = log₂|intersection set|` — the pure intersection
  attack (§4.1).
- **γ → ½**: the LRs flatten, `H → log₂(N−1)` — full anonymity, the class bit carries no information.

The dither's job is to move `H` from the first limit toward the second. §5 bounds how far a given γ can
go; §7 states why the *shipped* mechanism does not achieve it.

## §4 The two leaks

### §4.1 The class-rate leak and the intersection attack

**Finding #1 (the leak the whole analysis is about):** with no dither the class is emitted *exactly*,
so the GPA reads `b_d` for every dyad every epoch with zero error. Over the target's `E` active epochs
it intersects: a non-partner survives (appears active in all `E`) only by background coincidence,
probability `q^E`. The expected surviving set is

```
|S_∩|  =  1 + (N−2)·q^E                    (measure.rs analytical_partner_count)
```

— the true partner (active in every shared epoch by definition) plus each of the other `N−2` dyads
with probability `q^E`. As `E` grows the set collapses toward 1: **the partner is de-anonymised by
repeated co-activity**, which is the canonical intersection/statistical-disclosure attack. This is the
concrete Phase-1 Tier-3 exposure, and it is *bounded below by 1* — it never reaches 0 (the GPA cannot
be *certain*), but it converges to near-certainty for a talkative pair.

### §4.2 The existence/volume leak (out of scope here, named for completeness)

Constant-rate fill (§6.3) already flattens per-epoch volume, so the residual is only the class-rate of
§4.1. Volume *within* a class is padded to fixed-size cells. No separate bound is needed; the leak is
subsumed by §4.1's class observable.

## §5 The differential-privacy budget

Model the per-epoch defence as a **randomized response (RR)** on the binary active bit: emit the true
bit with probability `1−γ`, flip it with probability `γ ≤ ½`. This is `(ε_epoch, 0)`-differentially
private in the bit, with

```
ε_epoch = ln((1−γ)/γ)                       (measure.rs epsilon_epoch; standard RR bound)
```

*(Derivation: the output-distribution likelihood ratio between the two input bits is at most
`(1−γ)/γ`; `ε` is its log. γ→0 ⇒ ε→∞ (exact class, finding #1); γ=½ ⇒ ε=0 (uninformative).)*

Over a dyad's active lifetime of `E` epochs, **basic sequential composition** gives

```
ε_total = E · ε_epoch(γ)                    (measure.rs epsilon_total)
```

(each epoch re-draws the RR from an independent seed — `dither_fires = HKDF(seed‖"dither"‖epoch)`,
verified independent across epochs, so basic composition applies; advanced composition
`≈ √(2E·ln(1/δ'))·ε_epoch` is tighter for large `E` but the budget is stated conservatively in basic
terms).

**The budget:** `TIER3_EPSILON_BUDGET = ln 2` — at most one bit of lifetime linkage advantage. *(An
`(ln 2, 0)`-DP channel bounds the partner-vs-non-partner likelihood ratio at 2, i.e. the GPA's
posterior odds move by at most one bit over the whole lifetime.)*

**⚠️ A structural problem with the budget itself, not the parameter (this is a §7 finding, stated
here because it lives in §5's math):** basic composition is *linear in E*, and `E` — "active epochs
over a lifetime" — is **unbounded**. For any fixed γ < ½, `ε_total = E·ln((1−γ)/γ) → ∞` as the dyad
keeps talking. **No γ < ½ satisfies a *lifetime* `ln 2` budget.** At a 30 s epoch, one hour of activity
is 120 epochs; the budget is already spent within the first epoch at any useful γ. So "ε_total ≤ ln 2
over a lifetime" is **not an achievable framing** as written — it is achievable only per bounded
window, and the window must be named. This is HYP-527's second finding, and it is a property of the
*budget statement*, independent of which γ ships.

## §6 Concrete parameters

The founding scale (Klinos founding practice + early adopters, `THREAT_MODEL.md` §10 / HYP-171):
`N` small (the pair, N=2, up to a few hundred early dyads), `q` = background co-activity ≈ 0.25
(`gpa-sim` `Config::default`), `E` = however many epochs the pair is co-active. At `N=2` the anonymity
set is **2 trivially** and the intersection attack is vacuous (there is no third candidate to exclude);
§4.1's collapse matters only once `N` is large enough for `(N−2)q^E` to be the operative term. This is
the arithmetic behind the dependency tree's "network-wide anonymity set is Phase 2+, gated on scale
(HYP-171/HYP-523)": **the intersection bound is real but only bites at a population that does not yet
exist.** Until then, Phase 1's honest Tier-3 claim is the §5 per-window DP statement, not a set size.

## §7 Findings

**Finding #1 — the exact-class leak.** Without dither, `γ_eff = 0 ⇒ ε_epoch = ∞`: the GPA reads every
dyad's class every epoch and mounts §4.1's intersection attack. This is why HYP-357/359 shipped the
dither at all. ✔ consistent with `gpa-sim`.

**Finding #2 — the shipped dither does NOT achieve the §5 bound (HYP-527).** §5's `ε_epoch = ln((1−γ)/γ)`
holds for a **symmetric binary RR**. The runtime is not one. `emitted_class`
(`vita-carriers/src/cover_traffic.rs:435-451`) is a 4-state ladder in which:

1. **`Critical` is exempt** (`Critical ⇒ Critical`), and nothing ever up-flips *to* `Elevated`. For the
   Critical/Elevated labels `γ_eff = 0 ⇒ ε = ∞`. The classes THREAT_MODEL calls most sensitive get
   **no DP protection at all**.
2. **The down-flip is suppressed when real traffic is queued** (`_ if has_pending_real_volume ⇒
   current`) — a flip vetoed *by the secret*, which makes the channel data-dependent and its ε
   unbounded, not `(ln 4, 0)`-DP.
3. **The up-flip is suppressed** under `cover_suspended` / `escalation_locked` for
   `ENERGY_CLASS_STEP_DOWN_LOCK_MS = 3.6e6` — 120 consecutive exact-class epochs.

(The suppression/lock/ceiling semantics here are the decided ones in canon `COVER_BUDGET_FORECAST_WIRE_DESIGN.md` — read for HYP-527; its ≥70%-consumed up-flip clamp is a fourth exact-class regime on top of these three.)

So the shipped mechanism realises the §5 bound **only on the `Ambient↔Standard` pair, only when no
real traffic is queued and no lock is engaged.** On the reachable complement, `ε = ∞`. The `gpa-sim`
model (a symmetric binary RR, `sim.rs`) is therefore an *upper bound on the protection*, not a model
of the runtime — it over-credits the dither. **Fixing HYP-527 is a mechanism redesign (make the flip
symmetric and secret-independent, or state a different guarantee), not a γ retune.**

**Finding #3 — the epoch-unit mismatch.** The RR is drawn once per 30 s dither epoch, but `gpa-sim`'s
`Config::epoch_ms` defaults to the 1 s Standard slot and flips every slot, over-crediting the dither's
noise by ~30×. Any calibration must denominate `E` in 30 s dither epochs. (HYP-527.)

## §8 What Phase 1 can honestly claim

- **Tier 1 (same-link observer): fully defended.** Constant-rate fixed-size cover makes a single link's
  stream activity-invariant. This is proven by construction and is the §6.3 line-296 guarantee.
- **Tier 3 (GPA): partially, and only as a per-window DP statement on the `Ambient↔Standard` bit** —
  and even that is not currently met (Finding #2). The intersection bound §4.1 is real but bites only
  at a population scale that does not yet exist (§6).
- **The network-wide anonymity set of `COVER_TRAFFIC` §6.2.2 is Phase 2+**, gated on a mixing vantage
  point (HYP-523) and on scale (HYP-171). Its stated "1-in-N" size is wrong for the reasons in
  `NETWORK_WIDE_COVER_DESIGN.md` (partitioned by class before the count).

## §9 Consequences for the citing code (the ACs of HYP-526)

- `measure.rs` `TIER3_EPSILON_BUDGET`/`epsilon_epoch`/`epsilon_total`, `cover_content.rs:211/232`,
  `cover_traffic.rs:70`, `sim.rs:3/58`, `adversary.rs:43`, `lib.rs` — every "§N" now resolves to a real
  section above. **But the code's implicit claim that the shipped γ *achieves* the budget is false
  (Finding #2); those doc-comments should be amended to cite §7, not just §5.** Tracked in HYP-527.
- `spec-guard` should stop reporting `GPA_ANALYSIS.md` as missing once this lands on `main`.

## §10 Provenance

**Derived, not recovered** — the document never existed. **Verified against code this session:** every
formula in §3/§4.1/§5 matches the cited `gpa-sim` function; the §7 runtime gap is read from
`emitted_class` and its own tests (`cover_traffic/tests.rs:606-631`). **Assembled from standard
results, not novel:** Serjantov–Danezis entropy (PET 2002), randomized-response DP (Warner 1965 /
Dwork–Roth), basic sequential composition; and `COVER_BUDGET_FORECAST_WIRE_DESIGN.md` (canon, read for HYP-527) for the escalation-lock / up-flip-clamp semantics cited in §7. **NOT independently verified:** the `ln 2 = "one bit"`
framing and the advanced-composition remark are stated as the code states them and are for the gate to
confirm or refute. This is a design draft; it is canon only after cross-vendor DESIGN-review.
