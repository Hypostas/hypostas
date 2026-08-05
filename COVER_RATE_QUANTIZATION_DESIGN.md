# COVER_RATE_QUANTIZATION_DESIGN.md — the observable-rate policy that hides *which* sensitive event

**Status:** DESIGN v2, **pre-review**, 2026-08-05, for **HYP-527** (closes **HYP-526**). Supersedes the
**refuted** v1 (`COVER_DITHER_SYMMETRIC_DESIGN.md`, `hypostas@792c3fc` — a 4-class upward RR that could not
meet its own budget at any valid parameter and reopened ε=∞ for capped dyads). This v2 is a *different
construction* built from what the review's arithmetic actually permits. **Every number here is computed
against its constraint** (the `python3` block in the HYP-527 trail, 2026-08-05) — the discipline v1 lacked.

**Decision on record (Josh, 2026-08-05):** full cover for all classes / bandwidth cost accepted — that
stands; v2 spends the accepted bandwidth where it *buys* something and refuses to spend it where it cannot.

**Code grounded in `dyados@<pin-at-build>`**, `main`-read 2026-08-05. Companion: `GPA_ANALYSIS.md`
(diagnostic), `COVER_DITHER_SYMMETRIC_DESIGN.md` (refuted v1, kept for the record).

---

## §1 The two leaks HYP-527 actually contains — separate them (v1's first mistake)

v1 tried to hide two *different* channels with one 4-class randomized response and satisfied neither. They
have different structure and want different mechanisms:

- **The ACTIVITY channel** (Ambient↔Standard): idle-vs-active — the intersection attack (GPA_ANALYSIS §4).
  This is what the shipped HYP-357/359 **binary** dither exists for. It is *feasible* (see §4).
- **The SENSITIVE-EVENT channel** (Elevated/Critical): *which* high-tempo event — consult vs bio-stream vs
  bond ceremony vs dissolution vs succession. This is HYP-527's ε=∞ finding, and its right mechanism is
  **not a dither at all** (§3).

v2 keeps them separate: **§3 coarsening** for the sensitive-event channel, **§4 the retuned binary dither**
for the activity channel.

---

## §2 The impossibility theorem — what Phase-1 fundamentally CANNOT do (state it, don't fight it)

Two hard facts bound every Phase-1 rate mechanism. Both are consequences of one constraint: **latency —
a true class never emits *slower* than its rate** (real 200 ms ceremony traffic needs 200 ms cells).

**T1 — Symmetric ε on the top (Critical) class requires everyone-always-Critical (the 24× floor).**
A true-Critical dyad with real traffic must emit ≤ 200 ms, and Critical *is* the fastest rate, so its
observable is **deterministically Critical**: `P(observe not-Critical | true-Critical) = 0`. Therefore *any*
construction in which a "not-Critical" observation can occur makes that observation a **certain** not-Critical
tell — the reverse likelihood ratio is ∞. Symmetric ε (bounded *both* directions) is possible only if no
"not-Critical" observation ever occurs — i.e. **every dyad emits Critical always**. Cost: `5000/200 = 25×`
the idle packet rate (24× overhead), **always, for every dyad** (computed). This is the *only* symmetric
point; there is no cheaper one. (v1's one-sided RR was an attempt to dodge T1 and still failed T3 below.)

**T2 — No rate manipulation can hide a capped dyad's class.** Hiding a class means emitting *faster* than
its true rate (up-cover); a budget/battery/carrier-capped dyad (`effective_cover_ceiling < Critical`,
`cover_traffic.rs:196-205`; LoRa/DHT capped to Ambient) *cannot* emit faster — that is what "capped" means.
So for capped dyads the observable rate **equals** the true class, fully distinguishing. This is not a
residual to patch; it is inherent. **Hiding the class-rate channel for capped dyads is Phase-2 (mixing hides
the rate regardless of what the dyad emits).** This is exactly the review's P1 #2, restated as a boundary
rather than a bug.

**Consequence:** Phase-1 cannot deliver symmetric ceremony-hiding, and cannot hide capped dyads at all. What
it *can* do cheaply is narrower and still worth doing — §3.

---

## §3 Mechanism 1 — deterministic coarsening: hide *which* high event

**Collapse the two sensitive classes into one observable rate.** Emit both Elevated (real 500 ms) and
Critical (real 200 ms) traffic on the **same 200 ms observable grid**. Deterministic — no randomness, no
per-epoch draw, no budget.

- **What it hides:** at the rate level, a GPA sees "high" (200 ms) and **cannot tell a bond ceremony /
  dissolution / succession (Critical) from a routine Klinos consult or bio-stream (Elevated)**. The sensitive
  *semantic* distinction dies. And because Elevated events (consults, streams) are far more frequent than
  Critical events (rare ceremonies), **the routine Elevated traffic is itself the cover for ceremonies** — no
  synthetic cover cells required.
- **Cost:** a true-Elevated dyad emits 200 ms instead of 500 ms = **2.5× during Elevated events only**
  (computed). **Idle and Standard dyads pay nothing** (their rates are unchanged). Contrast the 24× symmetric
  floor (T1): coarsening is ~10× cheaper because it hides *which* high event, not *whether* in one.
- **Composition-safe:** deterministic, so there is **no odometer** (GPA_ANALYSIS §5(3)) — a 40-epoch ceremony
  is exactly as hidden as a 1-epoch one; sustained duration does not erode it (unlike any probabilistic cover).

**The honest boundary (T2):** the collapse requires emitting Elevated *up* at 200 ms, which a **capped**
dyad cannot afford — so a capped dyad emits Elevated at 500 ms and Critical at 200 ms, and the two stay
distinguishable. **Coarsening hides which-high-event for dyads that can afford the 2.5× Elevated premium
(uncapped: WiFi / wall-power); for capped dyads it is Phase-2.** State this in THREAT_MODEL; do not claim
universality (v1's fatal claim).

**Residuals coarsening does NOT close (routed, not hidden):**
1. **"In a high bucket at all"** — `P(high | idle) = 0` without added cover, so a GPA still sees *that* the
   dyad is in some high event. Hiding this needs idle→high cover, which by T1/composition costs → the 24×
   floor for a sustained event (computed: D=40 ⇒ p≥0.98 ⇒ ~24×). **Not worth it in Phase-1; → Phase-2.**
2. **Duration / pattern within the high bucket** — a 20-min "high" vs a 5-min "high" can still separate a
   ceremony from a consult temporally. Coarsening hides the *rate* tell, not the *duration* tell. → Phase-2
   (traffic-shaping / padding-duration), or a separate follow-up.
3. **Which partner** — the destination-frequency channel (GPA_ANALYSIS §2.4). → Phase-2 (multi-hop).

---

## §4 Mechanism 2 — the activity dither, retuned (feasible, unlike v1)

The Ambient↔Standard **binary** dither (HYP-357/359) is the right tool for the activity channel and — unlike
v1's 4-class RR — it is **arithmetically feasible**. The binary RR ε is `ln((1−γ)/γ)` (`measure.rs:145`); at
**γ = 1/3** that is `ln 2` exactly, meeting `TIER3_EPSILON_BUDGET` at W=1 (`min_gamma_for_tier3(1) ≈ 0.333`,
`measure.rs:189`, computed). The 4-class RR was infeasible only because 3 equal up-targets from Ambient forced
γ ≤ 1/3 ⇒ ε ≥ ln 3 > ln 2; the binary dither has **one** flip target and no such constraint.

- **Retune γ to a named window `W`** (per GPA_ANALYSIS §5): pick `W`, set γ so `W·ln((1−γ)/γ) ≤ ln 2`, and
  **publish the achievable `W`** in THREAT_MODEL. (γ=1/3 ⇒ W=1; larger W needs γ→1/2, at which the activity
  bit is nearly uninformative — state the honest ceiling.)
- **Fix the three forkless correctness bugs** the review confirmed (these are real regardless of construction):
  - **Secret-conditioned down-flip** (`cover_traffic.rs:449` `has_pending_real_volume`) — removed: the
    coarsening makes the observable ≥ true class, so a real packet is never slowed and the queue-gate is
    unnecessary. (Claude leg confirmed this half is sound.)
  - **Mid-epoch mutation** (`scheduler.rs:248` live per-slot ceiling into a latched RR bit) — latch the
    ceiling *and* the emitted rate for the whole dither epoch; a mid-epoch policy *lowering* takes effect at
    the next epoch boundary (bounded 30 s exposure, documented — not "never exceed policy" overclaimed).
  - **Availability gap** (`generate.rs:92` `→ None`) — **not** the v1 self-addressed cell (the review showed
    that is a distinguishable destination, contradicting §2.4). Instead: hold the last valid cover destination
    or a fixed rendezvous set so a scheduled slot always emits a cell to a *plausible* destination; if truly
    no destination exists, the slot is genuinely idle and the gap is honest (documented as the cover-OFF
    regime, GPA_ANALYSIS §2), not papered over.

---

## §5 The rule #32 mechanism (carries over) + what to encode

The ε=∞ shipped for months because γ lived in `vita-carriers` and the budget in `gpa-sim` and nothing
compared them. v2 keeps the fix, now targeting the **feasible binary** ε: a `#[test]` in `vita-carriers`
that imports the budget (or a shared `const`) and asserts `epsilon_epoch_binary(γ) ≤ TIER3_EPSILON_BUDGET/W`
— and, critically, **also asserts the coarsening invariant** (`observed rate of Elevated == observed rate of
Critical` for an uncapped dyad) so a future edit cannot silently re-split the sensitive classes. Encode the
*spec value*, not existence (rule #8).

---

## §6 gpa-sim (rule #8/#27) + cost publication

- Model the **3 observable buckets** {Ambient, Standard, high} and the **capped cohort** (T2 — capped dyads
  do not collapse). Measure that an uncapped dyad's Elevated and Critical observations are identical, and that
  a capped dyad's are not (the honest boundary, asserted, not hidden).
- Do **not** re-add the vacuous `advantage ≤ e^{ε}` test (review P2 #6: advantage ≤1 always passes). For the
  activity dither, assert the *likelihood ratio* ≤ `e^{ε}` directly, or the TV advantage ≤ `tanh(ε/2)`.
- Publish the true cost in THREAT_MODEL: **coarsening = 2.5× during Elevated events, 0 idle**; the activity
  dither overhead `γ·(idle/active − 1)` at the chosen γ. No headline that hides the Elevated/Standard terms
  (review P3 #6).

---

## §7 Build chunks (after this design review passes)

- **C1** `observed_rate(true_class, ceiling)` — deterministic coarsening: Elevated→200 ms **iff** `ceiling ≥
  Critical` (uncapped), else true rate; Critical→200 ms; Ambient/Standard unchanged. Pure fn + unit tests
  (the capped-vs-uncapped split asserted; the Elevated≡Critical collapse for uncapped).
- **C2** retune the binary activity dither γ to `W`; latch rate+ceiling per epoch; delete the secret-
  conditioned down-flip.
- **C3** availability gap: last-valid-destination hold (not self-addressed); honest idle when none.
- **C4** `gpa-sim` 3-bucket + capped-cohort model; LR/TV assertions (not the vacuous advantage test).
- **C5** rule #32 cross-crate check (binary ε ≤ budget/W **and** the coarsening invariant) + γ + `W` +
  cost numbers in THREAT_MODEL.
- **C6** restart-exactness (HYP-40x); integration + smoke (rule #27); crypto-class gate; land; close 526+527.

---

## §8 Open questions for the cross-vendor DESIGN-review

1. **Bucket count.** 3-bucket (collapse Elevated+Critical only — recommended, 0 idle cost) vs 2-bucket
   (also collapse Ambient→Standard, hiding idle-vs-active at the rate level, but **5× idle cost always**,
   computed). Recommend 3-bucket; 2-bucket is a Josh cost decision if the activity-rate tell matters beyond
   what §4's dither already covers.
2. **T2 acceptance.** Is "capped dyads' sensitive events are Phase-2" an acceptable Phase-1 boundary, or does
   Josh want a capped-dyad reserve (spend a bounded Critical-cover budget even when capped)? Recommend accept
   the boundary — a reserve just moves the cost, and T1's odometer means it can't hide a sustained ceremony
   anyway.
3. **Residual #2 (duration).** File the within-bucket duration/pattern leak as its own follow-up now, or fold
   into Phase-2 mixing? (rule #4 — track it, don't let it vanish.)
4. **Is coarsening's value real given base rates?** It hinges on Elevated events being frequent enough to
   cover rare Critical ones (§3). That is a measurement (HYP-171) — state the dependency, don't assume it.

## §9 Provenance

Arithmetic: the `python3` verification in the HYP-527 activity trail, 2026-08-05 — T1 floor `5000/200=25×`;
coarsening `500/200=2.5×`, idle 0; binary feasibility `ε(1/3)=ln2`; sustained-cover `D=40 ⇒ p≥0.983 ⇒ 23.6×`;
v1 infeasibility `ε(γ≤1/3)≥ln3=1.58×` budget. Code: `emitted_class` (`cover_traffic.rs:435-451`),
`effective_cover_ceiling` (`scheduler.rs:417`, cap-out-of-Critical `cover_traffic.rs:196-205`), binary RR +
budget (`measure.rs:137-198`), rates (`cover_traffic.rs:44-53`). Standard results: randomized response
(Warner 1965), sequential composition / odometer (Dwork–Roth; Rogers et al.). The affirmative per-window
bound for the activity dither is routed to **HYP-329**. This is a **design for review**, not a proof; T1/T2
are stated as arguments to be refuted, not self-certified theorems.
