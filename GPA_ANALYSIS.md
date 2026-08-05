# GPA_ANALYSIS.md — the Tier-3 anonymity analysis

**Status:** ⛔ **v2 OVER-CORRECTED — refined by the full-leg review, 2026-08-05.** v1 reversed the
conclusions (reassuring-false); v2 fixed the direction but over-asserted them (alarming-absolute); the
review (Codex 6 + Codex 4 + Claude 8) converged on the precise, conditional truth below. The **sound
core survives all three drafts** (§3 metric, §4.1 formula, §7#2 ladder gap, §7#3 epoch fix, §5 TYPE
correction). v3 is a **surgical "condition, don't assert" pass**, specified here.

> ## ⛔ v2's over-reaches, and the v3 statement each becomes (all verified against code)
>
> 1. **§5 "the ε≤ln2 budget is the WRONG TARGET" is itself an over-correction.** The target is
>    **mis-scoped (needs a *window*), not ill-posed.** Local-DP on the class bit *does* bound the
>    identity advantage (standard LDP→hypothesis-test composition), and the harness proves it:
>    `measure.rs:366` `dithering_drops_epsilon_and_raises_anonymity` asserts ε↓ and posterior-entropy↑
>    **in lockstep** — the exact bridge v2 said "must not be [made]." **v3:** state a **bounded-window
>    `(ε_W, δ)`-LDP budget**, γ tuned to `W`; keep §3 entropy as the average-case companion; reconcile
>    with §9 (which already said "per-window"). **This makes HYP-527 a bounded, tunable fix, not a
>    mechanism-philosophy rethink.**
> 2. **The de-anonymisation headline is conditional on the unmeasured `q`.** Re-derived: N=5/E=3 → 1.05
>    at q=0.25 but **3.19 at q=0.9**, and N=50/E=8 → 21.7 at q=0.9 (anonymous). `q` is unmeasured
>    (HYP-171). **v3:** condition §6/§8 on the low-q regime; the assumption-robust claim is *"cover does
>    not close the class-trajectory leak; long conversations shrink the set."*
> 3. **§8 "no working Tier-3 defense" over-claims vs the body.** The dither *raises* H (harness:
>    **>2 bits at γ=0.4** over baseline) — a **bounded-window** defense that **decays** over a
>    relationship lifetime, not "none." **v3:** *"no **durable** Tier-3 defense; the dither buys
>    bounded-window anonymity that decays toward identification; durable anonymity needs the Phase-2
>    mixing vantage point."*
> 4. **§5's "enumerable 256-bit seed ⇒ ε→∞" is a category error.** `THREAT_MODEL` grants 50-year
>    *records*, not unbounded *computation*; that adversary breaks the AEAD too, so the dither is not
>    distinctively broken. **v3:** keep the plain TYPE correction (computational DP, Mironov CDP);
>    delete the unbounded-adversary flourish and the non-sequitur rotation "reassurance."
> 5. **"HYP-522 is the only mechanism" over-claims.** A GPA sees every hop; multi-hop alone does not
>    stop end-to-end timing correlation. Tier-3 needs **multi-hop + relay padding + cover-relayed
>    cover** (`NETWORK_WIDE_COVER_DESIGN.md`, `PRIVACY_DEPENDENCY_TREE.md`). **v3:** HYP-522 is the
>    *necessary foundation*, not the whole defense.
> 6. **§7#2 sub-clause miscites the lock.** `emitted_class` reads `(fires, has_pending_real_volume,
>    ceiling)` only — **not** `escalation_locked`/`cover_suspended`; the lock acts *via* `ceiling`, and
>    no scheduler call site was cited (rule #33 check-1). **v3:** cite the scheduler `ceiling` site or
>    soften. The rest of §7#2 (Critical exempt, nothing to Elevated, secret-suppressed down-flip) is
>    **fully supported** and is the document's strongest result.
> 7. **Lesser:** size-class weights are matched-by-design (`generate.rs:22-23`) so partly mitigated;
>    cover-OFF regimes *compose adversarially* with cover-ON (worse, not "does not apply"), and
>    "dominant mobile regime" is unsupported prevalence; `E[log₂|S|]` is still a mean not a worst-case
>    floor; "verified against code" is unauditable from `hypostas` (code is in the `dyados` sibling —
>    v3 must pin its SHA); the `verdicts/` path citation and a few ±2-line code cites need a tightening
>    pass.
>
> **The forward path this produced (the reason it is progress, not circling):** the missing root is
> now understood well enough to **fix HYP-527** — (a) state the window `W` and tune γ to it,
> (b) symmetrize the class ladder so the per-epoch bound holds on all classes. Phase 1's Tier-3 story
> is a **decaying bounded-window defense that is currently mistuned (HYP-527: γ too small for the
> window) and mis-implemented (ladder asymmetry ⇒ ε=∞ on the sensitive classes)** — both fixable —
> while **durable** lifetime anonymity remains Phase-2 (HYP-522 + relay padding + cover-relayed cover).

---

**Superseded v2 header:** DESIGN v2, pre-gate, 2026-08-05, for **HYP-526**. v1 was written and **refuted at the
conclusions by a full-leg cross-vendor review** (Codex generic 6 · reasoning-hygiene 4 · Claude depth
8); its sound core (§3 metric, §4.1 formula, §5 RR-bound form, §7 model↔runtime gap) is carried
forward, its four wrong conclusions are fixed here. v1 is in git history; the review verdicts are in
`scripts/factory/verdicts/hypostas-d8a681e9*`.

> ⚠️ **STILL PRE-GATE.** A security bound is canon only after v2 passes its own full-leg review and
> every citation resolves. Until then the numbers are claims. The **honest headline is not
> reassuring** and is the point of the document: *Phase 1 has no working Tier-3 relationship-anonymity
> defense* (§8).
>
> **The document was cited ~15× and did not exist** until v1 (verified: never in any repo, branch,
> stash, or on disk — a from-scratch derivation, not a recovery). Section numbers are fixed by the
> citations that point at them (`gpa-sim/src/{measure,adversary,sim}.rs`, `cover_content.rs`,
> `cover_traffic.rs`): §3 = Serjantov–Danezis entropy, §4.1 = class-rate leak + intersection, §5 = the
> DP treatment, §7 = findings. They are contracts, not choices.

---

## §1 The adversary

**Tier 3 — Global Passive Adversary (GPA)** (`THREAT_MODEL.md` §4.3): sees *all* links, cannot decrypt,
correlates timing/volume across the whole network, **records persist indefinitely** — an *unbounded,
50-year, store-now-analyse-later* adversary (§4.3 lines 84-85). That "unbounded compute" clause is
load-bearing and is why §5 must be careful about *computational* vs *information-theoretic* guarantees.

**What Phase 1 claims** (`THREAT_MODEL.md` §5 matrix, line 209): *"Tier 1 fully + Tier 2 partial +
**chassis for Tier 3/4**."* It does **not** claim Tier-3 relationship anonymity — that needs a mixing
vantage point (multi-hop + relay padding), which is Phase 2+ (`COVER_TRAFFIC.md` §7.1 *"anonymity set
effectively 1"*; `CIRCUIT_LIFECYCLE.md` §3 single-hop N=1). This document bounds **what a GPA learns
from the cover-traffic schedule**, and states plainly where that leaves relationship anonymity.

## §2 The observable — and where it does not exist

When cover is **on**, a GPA sees per dyad, per carrier, per slot: a fixed-size ciphertext cell on a
constant-rate grid. Hidden: content, destination, real-vs-cover. **Not hidden, and the subject of this
analysis:**

1. **The grid rate = `EnergyClass`** (`cover_traffic.rs rate_ms`: A 5 s / S 1 s / E 500 ms / C 200 ms).
   `THREAT_MODEL.md` §6.3 line 296 admits it: *"the streams reveal… what energy class it's in."*
2. **The size-class of each cell.** Cells are one of four sizes; cover samples a *fixed* distribution
   (`generate.rs` `COVER_SIZE_{S,M,L,XL}_WEIGHT` = 0.70/0.20/0.08/0.02) while a real cell's size
   follows its payload. So the **size distribution** is a second observable — v1 wrongly dismissed it.
3. **Class *transitions*.** An Ambient→Standard onset, localizable to the 30 s debounce, reveals *when*
   a conversation began — orthogonal to *who* the partner is. The harness measures it directly
   (`sim.rs onset_localization`, `adversary.rs burst_observable`). v1 wrongly called it subsumed.

**⚠️ The dominant mobile regime has NO cover.** `THREAT_MODEL.md` §12.5 (line 633): cellular at
**20–50 % battery → "Cover suspended, real messages only"**; < 20 % → queued. On those links the entire
apparatus of §3–§7 **does not apply** — every emitted packet is real, and the GPA reads conversation
timing and volume directly (this is `COVER_TRAFFIC.md` §4.5a row 11, the *default cellular regime*).
**Any Tier-3 claim below is conditioned on cover being on; a mid-battery phone on cellular is outside
it, and strictly worse off.** This regime is the largest single gap and is not closed by any parameter.

The per-epoch observation of an idle-vs-active bit `b_d ∈ {0,1}` is re-decided **once per 30 s dither
epoch** (`cover_content.rs:211`, `cover_traffic.rs:70`; class constant within an epoch).

## §3 The anonymity metric (Serjantov–Danezis)

Anonymity = **effective anonymity-set size `2^H`**, `H` = Shannon entropy of the GPA's posterior over
*who the target's partner is* (Serjantov–Danezis, PET 2002). This is what `adversary.rs`
`posterior_partner_entropy` computes: over the `E` epochs the **target** is active, candidate *d* scores

```
score(d) = k_d·ln(a/q′) + (E−k_d)·ln((1−a)/(1−q′))
```

with `k_d` = *d*'s observed-active count among those `E` epochs, `a = 1−γ`, `q′ = q(1−γ)+(1−q)γ`, `q` =
background co-activity; `H` = entropy of the softmax. Limits (both in code): **γ=0** → all mass on the
all-`E` intersection, `H = log₂|S_∩|`; **γ→½** → `H → log₂(N−1)` (the bit is uninformative).

**This is the right currency for relationship anonymity**, and §5 explains why the DP budget is *not*.

## §4 The leaks

### §4.1 The intersection attack (finding #1's consequence)

With no noise the class is emitted exactly, so the GPA intersects the target's `E` active epochs. A
non-partner survives all `E` by coincidence with probability `q^E` **(assuming per-epoch activity is
i.i.d.; real human activity is bursty/session-correlated, so the true joint may differ and `q^E` is a
model, not a proven bound — a v2 caveat).** The **expected** surviving set is

```
E[|S_∩|] = 1 + (N−2)·q^E             (measure.rs analytical_partner_count)
```

**This is an *upper bound* on anonymity, not the anonymity.** By Jensen `log₂ E[|S|] ≥ E[log₂|S|]`, and
a safety floor needs `E[log₂|S|]` — which is exactly why `measure.rs` gates on
`measured_partner_entropy_bits` (`E[log₂|S|]`), not on `log₂` of the mean (regression test
`measure.rs:304-342`). v1 quoted the upper bound as the anonymity; v2 does not.

**The attack de-anonymises at every realistic scale**, and is *worst* at small `N` (re-derived,
`q=0.25`):

| N | E | E[\|S_∩\|] | reading |
|---|---|---|---|
| 2 | any | **1** | one candidate exists; the relationship is structurally determined (set = 1, **not 2**) |
| 5 | 3 | **1.05** | near-identified — and N=5 is founding scale |
| 50 | 8 | **1.001** | identified |
| 1000 | 8 | **1.02** | identified |

The set is bounded **below by 1**, and a realized set of **exactly 1 is certainty** (only the
*expectation* stays above 1). So "the GPA can never be certain" (a v1 claim) is false. **Small
populations give *less* relationship anonymity, not immunity** — the exact reversal of v1's §6, and it
lands hardest on the Klinos founding pair.

### §4.2 Volume and onset

The size-class distribution (§2.2) and the conversation-onset timing (§2.3) are **separate** Tier-3
leaks, each modelled by the harness. Constant *cadence* does not flatten *size distribution* or hide a
*transition*. They are not bounded here; they are named as open Tier-3 surface (v1 wrongly declared no
bound needed).

## §5 The differential-privacy treatment — and why it is the wrong target

Model one epoch's defence as a **randomized response** on the active bit: emit truth w.p. `1−γ`, flip
w.p. `γ ≤ ½`. The per-epoch guarantee is

```
ε_epoch = ln((1−γ)/γ)                (measure.rs epsilon_epoch)
```

— the log of the max output-likelihood-ratio between the two input bits; standard RR (Warner 1965 /
Dwork–Roth). γ→0 ⇒ ε→∞ (finding #1); γ=½ ⇒ ε=0.

**This is a *computational*, not information-theoretic, guarantee (v2 correction).** The flip is
`dither_fires = HKDF-Expand(seed_key, "dither"‖epoch)` (`cover_content.rs:217-238`): **one** per-dyad
`seed_key`, with the epoch in the HKDF *info*, not a fresh independent draw per epoch. The bits are a
deterministic PRF of `(seed, epoch)`. So:

- The RR bound and composition hold **only computationally**, under the HKDF-PRF assumption. v1's
  *"verified independent"* was false — nothing verifies independence, and there is no such test.
- Against the **unbounded** GPA of §1, a 256-bit seed is enumerable in the limit ⇒ every flip
  de-noised ⇒ `ε` information-theoretically **→ ∞**. Practically infeasible (2²⁵⁶), and the seed
  **rotates every 24 h** (`cover_content.rs:47-51,94`), bounding seed-compromise blast radius to one
  day — but a security document invoking a 50-year adversary must state the assumption, not assume it.

**The "lifetime ε_total ≤ ln 2" budget is the wrong target, and unachievable as stated (v2's central
correction).** Two independent reasons:

1. **Unbounded composition.** Basic composition is `ε_total = E·ε_epoch`, linear in `E`; "active epochs
   over a lifetime" is unbounded, so for any fixed `γ<½`, `ε_total → ∞`. No `γ<½` meets a *lifetime*
   `ln 2`. The seed's daily rotation does **not** rescue this: rotation re-keys the *noise*, but the
   *secret* — the partner identity — is the **same person every day**, so the identity leak
   accumulates across the whole relationship regardless of how often the seed rotates. DP-composition
   of a per-epoch class-bit mechanism simply is not the same quantity as lifetime relationship
   anonymity.
2. **Wrong currency.** ε bounds a per-epoch *likelihood ratio* on the *class bit*. Relationship
   anonymity is the entropy §3 of the *identity* posterior. Collapsing `ln 2 = "one bit of advantage"`
   treats a likelihood-ratio bound as an entropy/set-size claim; they are different measures and the
   document must not bridge them silently (v1 did).

**The honest role of the dither:** it converts §4.1's hard intersection into §3's soft posterior —
*raising* `H`, i.e. *slowing* the de-anonymisation — but it does **not** hold anonymity at any fixed
level as `E` grows, and it carries **no** lifetime `(ε,0)`-DP guarantee. The right way to state its
value is the §3 entropy it buys per relationship-lifetime at a given `γ`, measured by `gpa-sim`, not a
`ln 2` budget. **HYP-527's "shipped γ blows the ln 2 budget" is therefore a symptom of a mis-posed
target as much as a mistuned parameter; the target itself needs restating (a v2 finding beyond
HYP-527).**

## §6 Concrete scale

Founding scale (Klinos + early adopters, `THREAT_MODEL.md` §10 / HYP-171): `N` small, `q ≈ 0.25`
(`gpa-sim` default — *provisional, HYP-171 still tracks empirical validation; not a measured constant*).
§4.1's table shows the intersection attack **already near-identifies at N=5, E=3**. So the correct
statement is the opposite of v1's: **the attack is most dangerous at founding scale**, precisely where
the network launches. There is no scale at which Phase 1's cover schedule alone provides relationship
anonymity against a persistent GPA.

## §7 Findings

**#1 — the exact-class leak.** γ=0 ⇒ ε=∞; the GPA reads every class every epoch and mounts §4.1. Why
HYP-357/359 shipped the dither. ✔.

**#2 — the shipped dither does not achieve even the per-epoch RR bound (HYP-527).** `emitted_class`
(`cover_traffic.rs:435-451`) is a 4-state asymmetric ladder, verified by its own tests
(`cover_traffic/tests.rs:606-631`): `Critical` is exempt and nothing up-flips to `Elevated`
(γ_eff=0 ⇒ **ε=∞** on the most sensitive classes); the down-flip is **suppressed by the secret**
(`has_pending_real_volume`); the up-flip is locked for 120 epochs under `escalation_locked` /
`cover_suspended`. So the RR bound holds only on `Ambient↔Standard`, with no queued real and no lock;
on the reachable complement ε=∞. `gpa-sim`'s symmetric-binary model is an **upper bound on protection**,
not a model of the runtime. **Fixing this is a mechanism redesign** (symmetric, secret-independent flip
across the ladder — or a different, honest guarantee), not a γ retune.

**#3 — the epoch-unit note, corrected (v1 had it backwards).** The RR is drawn once per 30 s dither
epoch (`cover_content.rs:210`). `gpa-sim`'s `coactivity_trace` also flips **once per abstract epoch**
and does **not** read `epoch_ms` (verified `sim.rs:45-87`) — v1's "flips every 1 s slot, over-credits
30×" was wrong about the code. And the *safety direction* is the reverse of v1's claim: denominating a
lifetime in finer units inflates `E`, which *lowers* modelled anonymity and *raises* the γ that
`min_gamma_for_tier3` demands — **conservative**, not an over-credit. Holding one flip constant across a
30 s epoch also *defeats* adversary averaging that a per-slot flip would permit, so reality is if
anything stronger than a per-slot model. This is a calibration/interpretation note, not a leak.

## §8 What Phase 1 can honestly claim

- **Tier 1 (same-link observer): defended *when cover is on*.** Constant-rate fixed-size cover makes a
  single link activity-invariant (§6.3 line 296). **Caveat:** in the cover-OFF cellular regime (§2) even
  this does not hold — every packet is real.
- **Tier 3 (GPA) relationship anonymity: NOT defended.** The intersection attack (§4.1) de-anonymises a
  co-active pair at any scale; the dither only *slows* it and carries no lifetime guarantee (§5); the
  most sensitive classes get no dither protection at all (§7#2); and volume/onset (§4.2) are unmodelled
  surface. The real Tier-3 defense is a **mixing vantage point** — multi-hop routing so the GPA cannot
  read a per-dyad activity bit at all — which is **Phase 2+ (HYP-522)**.
- **The network-wide "1-in-N" set** of `COVER_TRAFFIC.md` §6.2.2 is Phase 2+ and, as stated, wrong
  (partitioned by class before the count — `NETWORK_WIDE_COVER_DESIGN.md`).

**Arc-level consequence:** HYP-522 (a real send emits no observable circuit build → the idle-circuit
pool → multi-hop mixing) is not a Phase-2 nicety. **It is the only mechanism that provides Tier-3
relationship anonymity at all.** The cover-traffic schedule is a Tier-1 defense with a Tier-3 chassis,
exactly as `THREAT_MODEL.md` §5 line 209 says — this document is the quantitative proof of that line,
and a correction to anywhere the arc assumed more.

## §9 Consequences for the citing code (HYP-526 ACs)

Every `§N` in `measure.rs`, `adversary.rs`, `sim.rs`, `cover_content.rs`, `cover_traffic.rs` now points
at a real section. **Two doc-comment corrections are owed** (tracked, not silently resolved): the code
implies the shipped γ *achieves* the budget (false, §7#2 / HYP-527), and `measure.rs`'s "lifetime DP
budget" framing is the mis-posed target of §5 — those comments should cite §5/§7, and the "budget"
should be restated as a per-window, computational, class-bit-local statement. `spec-guard` stops
reporting `GPA_ANALYSIS.md` once v2 lands, but **HYP-526 closes only after v2 passes its full-leg
review** — this line does not itself resolve the citations.

## §10 Provenance

**Derived, not recovered.** **Verified against code this session:** §3 vs `adversary.rs`, §4.1 vs
`measure.rs`, §7#2 vs `emitted_class` + its tests, §7#3 vs `sim.rs coactivity_trace`, §5 seed handling
vs `cover_content.rs dither_fires`, §2 size-class vs `generate.rs`, §2 onset vs `sim.rs onset_localization`,
the cover-OFF table vs `THREAT_MODEL.md:633`. **Standard results, not novel:** Serjantov–Danezis (PET
2002), randomized-response DP (Warner 1965), sequential composition (Dwork–Roth). **NOT independently
verified, for the gate:** the `q^E` i.i.d. model vs bursty human activity (§4.1); the exact
computational-DP reduction and the enumerable-seed limit (§5); whether "restate the target" or "redesign
the mechanism" is the right resolution of §5+§7#2. This is a design draft; canon only after cross-vendor
review.
