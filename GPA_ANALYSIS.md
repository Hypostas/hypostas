# GPA_ANALYSIS.md — the Tier-3 anonymity analysis

**Status:** DESIGN v3, pre-gate, 2026-08-05, for **HYP-526**. This is the *conditional* statement the
two prior full-leg reviews converged on: v1 reversed the conclusions, v2 over-asserted them, v3 states
each with its condition. **Sound core stable across all three** (§3 metric, §4.1 formula, §7 model↔runtime
gap, §5 RR-bound form). v1/v2 and the six review verdicts are in git history
(`scripts/factory/verdicts/hypostas-{d8a681e9,1833782a}*`).

> ⚠️ **PRE-GATE. Two claims are flagged FOR-THE-GATE and must not be relied on until confirmed:**
> the affirmative local-DP→identity-advantage bridge (§5, the one *positive* security claim — writing
> it is harder than refuting one, and v1/v2 show this author can miss in either direction), and the
> `q^E` independence model underlying the de-anonymisation numbers (§4.1). The **document is honest
> about its own conditions**; it is not a settled guarantee.
>
> Code lives in the **`dyados` sibling repo @ `013b4d8a`** — a reader of `hypostas` alone cannot audit
> the `file:line` citations; open `dyados` at that SHA to verify. Section numbers are contracts fixed by
> the ~15 code citations pointing at them.

---

## §1 The adversary

**Tier 3 — Global Passive Adversary (GPA)** (`THREAT_MODEL.md` §4.3): sees *all* links, cannot decrypt,
correlates timing/volume across the whole network, with **records that persist indefinitely** (50-year
store-now-analyse-later; §4.3 lines 84-85). **The adversary is computationally bounded** — the threat
model grants indefinite *storage* and a 50-year *capability-growth window*, **not** unbounded
*computation* (a corrected reading; v2 conflated the two). Every Phase-1 guarantee, this one included,
is computational — the AEAD, the ratchet, and the dither all rest on standard hardness.

**What Phase 1 claims** (`THREAT_MODEL.md` §5 matrix, line 209): *"Tier 1 fully + Tier 2 partial +
**chassis for Tier 3/4**."* It does **not** claim durable Tier-3 relationship anonymity — that needs a
mixing vantage point, Phase 2+ (`COVER_TRAFFIC.md` §7.1 *"anonymity set effectively 1"*;
`CIRCUIT_LIFECYCLE.md` §3 single-hop N=1). This document bounds **what a GPA learns from the
cover-traffic schedule**.

## §2 The observable

When cover is **on**, a GPA sees per dyad, per carrier, per slot: a fixed-size ciphertext cell on a
constant-rate grid. Hidden: content, destination, real-vs-cover. Three residual observables:

1. **The grid rate = `EnergyClass`** (`cover_traffic.rs rate_ms`: A 5 s / S 1 s / E 500 ms / C 200 ms).
   `THREAT_MODEL.md` §6.3 line 296: *"the streams reveal… what energy class it's in."* This is the
   analysis's main subject.
2. **The size-class of each cell** — but *matched by design*: cover samples weights (`generate.rs:22`)
   chosen *"so cover matches the real size distribution"* (S/M/L/XL = 0.70/0.20/0.08/0.02). The residual
   leak is only the extent to which a real conversation's size mix *deviates* from those weights (e.g.
   a photo-heavy chat vs the 0.02 XL weight), not the raw presence of size classes.
3. **Class *transitions*** — an onset localizable to the 30 s debounce reveals *when* a conversation
   began, orthogonal to *who* the partner is. The harness models it (`sim.rs onset_localization`,
   `adversary.rs burst_observable`). Not bounded here; named as open surface.

**Where the observable does not exist — and where it composes adversarially.** `THREAT_MODEL.md` §12.5
(line 633): cellular at 20–50 % battery → *"Cover suspended, real messages only"*; < 20 % → queued. On
those links every emitted packet is real. A real phone **interleaves** WiFi (full cover) and mid-battery
cellular (no cover) minute-to-minute, and the §4.1 intersection attack **accumulates across both** — the
cover-OFF epochs inject exact-class (`γ_eff=0`) observations into the *same* attack the dither cannot
touch. So the all-cover-on analysis of §3–§7 is not a clean bound for a mixed-connectivity dyad; it
*understates* the leak. (Prevalence of the cover-OFF band is unmeasured — no "dominant regime" claim.)

The per-epoch observation is an idle-vs-active bit `b_d ∈ {0,1}`, re-decided **once per 30 s dither
epoch** (`cover_content.rs:211`; class constant within an epoch).

## §3 The anonymity metric (Serjantov–Danezis)

Anonymity = **effective set size `2^H`**, `H` = Shannon entropy of the GPA's posterior over *who the
target's partner is* (Serjantov–Danezis, PET 2002). `adversary.rs posterior_partner_entropy`: over the
`E` epochs the target is active, candidate *d* scores

```
score(d) = k_d·ln(a/q′) + (E−k_d)·ln((1−a)/(1−q′))
```

`k_d` = *d*'s observed-active count, `a = 1−γ`, `q′ = q(1−γ)+(1−q)γ`, `q` = background co-activity;
`H` = entropy of the softmax. Limits (in code): **γ=0** → `H = log₂|S_∩|` (intersection); **γ→½** →
`H → log₂(N−1)`. This is the currency for relationship anonymity, and §5 shows the DP budget is a
*bounded-window companion* to it, not a replacement.

## §4 The leaks

### §4.1 The intersection attack — conditional on the activity model

No noise ⇒ exact class ⇒ the GPA intersects the target's `E` active epochs. A non-partner survives all
`E` with probability `q^E` **under an i.i.d. per-epoch activity model**; the **expected** surviving set
is

```
E[|S_∩|] = 1 + (N−2)·q^E             (measure.rs analytical_partner_count)
```

This is an **upper bound** on anonymity (Jensen: `log₂ E[|S|] ≥ E[log₂|S|]`), which is exactly why
`measure.rs` gates on `measured_partner_entropy_bits` = `E[log₂|S|]`, not on `log₂` of the mean (test
`measure.rs:304-342`). And even `E[log₂|S|]` is an *average* — a material fraction of relationships can
realize `|S|=1` (certainty) while the mean is comfortable; a true safety floor needs a lower-quantile
guarantee.

**⚠️ The `q^E` model is not a proven bound, and the conclusion inherits that.** Real activity is
diurnally/weekly correlated (evenings), which makes joint survival `> q^E` — so the *true* set is
**larger** and the attack **weaker** than the table. `q` is unmeasured (HYP-171). The numbers are
therefore a **model, conditional on low, roughly-independent `q`**:

| N | E | q=0.25 | q=0.9 |
|---|---|---|---|
| 5 | 3 | 1.05 (near-identified) | **3.19 (anonymous)** |
| 50 | 8 | 1.001 | **21.7 (anonymous)** |

**Assumption-robust qualitative claim** (what survives any `q`): *the cover schedule does not close the
class-activity leak; a sufficiently long, sufficiently exclusive co-activity pattern shrinks the partner
set toward 1.* Whether a real founding pair is at risk depends on the measured `q` (HYP-171) — it is not
settled by this document. (Note "worst at small N" holds only *ceteris paribus* — `E[|S|]` is increasing
in N at fixed E; the table above varies both axes and does not by itself demonstrate a monotone
small-N danger.)

### §4.2 Volume and onset

Size (§2.2, matched-by-design residual) and onset (§2.3) are separate Tier-3 surfaces the harness
models; not bounded here.

## §5 The differential-privacy treatment — a bounded-window budget

Model one epoch's defence as a **randomized response** on the active bit: emit truth w.p. `1−γ`, flip
w.p. `γ ≤ ½`. Per epoch this is **`ε_epoch`-local-DP** in the class bit, `ε_epoch = ln((1−γ)/γ)`
(`measure.rs epsilon_epoch`; Warner 1965 / Dwork–Roth). γ→0 ⇒ ε→∞; γ=½ ⇒ ε=0.

**A computational guarantee.** `dither_fires = HKDF-Expand(seed_key, "dither"‖epoch)`
(`cover_content.rs:217-238`) — one per-dyad seed, epoch in the HKDF *info*, so the flips are a PRF of
`(seed, epoch)`, not information-theoretically independent draws. The DP therefore holds **computationally**
under the HKDF-PRF assumption (Mironov et al., *computational DP*). This is the honest type of the
guarantee; it is not distinctively weaker than the rest of the Phase-1 stack, which is all computational.

**A bounded-*window* budget, not a lifetime one — the corrected target (v2 said "wrong target"; the
review corrected it to "mis-scoped").** Over a window of `W` active epochs, basic sequential composition
gives `ε_W = W·ε_epoch(γ)` (`measure.rs epsilon_total`). Because `W` is finite and chosen, `γ` can be
tuned to hold `ε_W ≤ ε_target` for that window. This is a *privacy odometer* (DP under continual
observation): the budget is spent per window and the window must be **named** — a *lifetime* `ε ≤ ln 2`
is unachievable because the identity secret is queried across the whole relationship (and the seed's
daily rotation, `cover_content.rs:94`, re-keys the *noise* but not the *identity*, so it does not help).

**The DP budget bounds identity advantage (FOR-THE-GATE — the one positive claim).** By the
hypothesis-testing interpretation of local DP (Kairouz–Oh–Viswanath; Wasserman–Zhou), an `ε_W`-LDP
observation window bounds any adversary's advantage at distinguishing "d is the partner" from "d is not"
over that window — i.e. the §3 posterior cannot move by more than the budget allows. The `gpa-sim`
harness **demonstrates the bridge empirically**: `measure.rs:366`
`dithering_drops_epsilon_and_raises_anonymity` asserts `ε_total ↓` and posterior entropy `↑` *in
lockstep* as `γ` grows (>2 bits of entropy gained at γ=0.4 over the exact-class baseline). **This is why
the DP budget and the §3 entropy are companions, not rivals** — v2 wrongly said they *"must not be
bridged."* **The exact constant in the LDP→identity reduction is the step the gate must confirm; this
document asserts the *form*, not a proven tight bound.**

**Consequence for HYP-527.** The shipped `γ=1/5` gives `ε_epoch = ln 4`, so it holds `ε_W ≤ ln 2` for a
window of **less than one epoch** — mistuned for any useful `W`. The fix is therefore **bounded and
tunable**: (a) name the protection window `W`; (b) set `γ` so `W·ln((1−γ)/γ) ≤ ε_target`; (c) fix §7#2's
ladder asymmetry so the per-epoch bound actually holds on every class. Not a mechanism-philosophy
rethink — a window declaration plus a parameter plus a symmetrization.

## §6 Concrete scale

Founding scale (`THREAT_MODEL.md` §10 / HYP-171): `N` small, `q ≈ 0.25` (`gpa-sim lib.rs:92` default —
**provisional, unmeasured, HYP-171 tracks it**). Under that provisional low-`q`, §4.1's model
near-identifies a founding pair; under high `q` it does not (§4.1 table). **The operative unknown is
`q`, and Phase-1's Tier-3 exposure is a measurement question (HYP-171), not a settled fact.**

## §7 Findings

**#1 — the exact-class leak.** γ=0 ⇒ ε=∞; without the dither the GPA reads every class and mounts §4.1.
Why HYP-357/359 shipped. ✔.

**#2 — the shipped dither does not hold the per-epoch LDP bound on every class (HYP-527), the document's
strongest concrete result.** `emitted_class` (`cover_traffic.rs:435-451`) is a 4-state **asymmetric**
ladder (verified by its own tests, `cover_traffic/tests.rs:606-631`): `Critical` is exempt and nothing
up-flips to `Elevated` (γ_eff=0 ⇒ **ε=∞** on the most sensitive classes); the down-flip is **suppressed
by the secret** (`_ if has_pending_real_volume ⇒ current`). Separately, the scheduler pins the up-flip
`ceiling` to the committed class under `cover_suspended()` / `escalation_locked()`
(`scheduler.rs:248`), so the up-flip is a no-op for `ENERGY_CLASS_STEP_DOWN_LOCK_MS / DITHER_EPOCH_MS =
120` epochs. So the LDP bound holds only on `Ambient↔Standard`, with no queued real and no lock; on the
reachable complement ε=∞. `gpa-sim`'s symmetric-binary model is an **upper bound on protection**, not a
model of the runtime. **Fix: symmetrize the flip across the ladder (or state a per-class guarantee),
not a γ retune.**

**#3 — epoch-unit note.** The RR is drawn once per 30 s dither epoch. `gpa-sim`'s `coactivity_trace`
(`sim.rs:45-87`) also flips **once per abstract epoch** and does **not** read `epoch_ms`. Denominating a
window in finer units inflates `W`, which *lowers* modelled anonymity and *raises* the demanded `γ` —
**conservative**, not an over-credit (v1 had this backwards). Holding one flip constant across 30 s also
defeats per-slot averaging, so reality is if anything stronger than a per-slot model. A calibration note,
not a leak.

## §8 What Phase 1 can honestly claim

- **Tier 1 (same-link): defended when cover is on.** Constant-rate fixed-size cover makes a single link
  activity-invariant (§6.3 line 296). Not in the cover-OFF regime (§2).
- **Tier 3 (GPA): a decaying, bounded-window defense, currently below spec.** The dither buys real
  per-window anonymity (§3/§5, harness: >2 bits at γ=0.4) that **decays toward identification as the
  window grows** — a *time-limited* defense, not "none" (v2 over-claimed "none") and not durable. Today
  it is **mistuned** (HYP-527: γ too small for any useful window) and **mis-implemented** (§7#2 ladder
  asymmetry ⇒ ε=∞ on sensitive classes). Both are bounded fixes.
- **Durable / lifetime Tier-3 relationship anonymity: Phase 2+.** It needs a **mixing vantage point** so
  the GPA cannot read a per-dyad activity bit at all — and a GPA sees every hop, so this is **multi-hop
  routing AND relay padding AND cover-relayed cover**, not any single mechanism. HYP-522 (idle-circuit
  pool → real sends emit no observable build) is the **necessary foundation** of that stack, not the
  whole of it.
- **The network-wide "1-in-N" set** (`COVER_TRAFFIC.md` §6.2.2) is Phase 2+ and mis-stated as written
  (`NETWORK_WIDE_COVER_DESIGN.md`).

**Arc-level:** the cover-traffic schedule is a Tier-1 defense with a Tier-3 *chassis* — exactly
`THREAT_MODEL.md` §5 line 209 — and this document is that line's quantitative backing. The Phase-1
Tier-3 dither is fixable (HYP-527: window + γ + symmetrize); durable Tier-3 is the Phase-2 mixing stack.

## §9 Consequences for the citing code (HYP-526 ACs)

Every `§N` resolves. **Two doc-comments are owed corrections** (tracked in HYP-527, not silently closed):
`measure.rs`'s `TIER3_EPSILON_BUDGET` should read as a **per-window** `(ε_W)`-LDP budget with `W` named,
not a "lifetime" one; and the code's implicit "shipped γ achieves the budget" is false (§7#2). `spec-guard`
stops reporting `GPA_ANALYSIS.md` once v3 lands, but **HYP-526 closes only after v3 passes its full-leg
review** — this line does not resolve the citations.

## §10 Provenance

**Derived, not recovered** (the document never existed). **Verified against `dyados@013b4d8a`:** §3 vs
`adversary.rs`, §4.1 vs `measure.rs` (incl. the Jensen `E[log₂|S|]` gate), §5 seed vs `cover_content.rs
dither_fires` + the lockstep test `measure.rs:366`, §7#2 vs `emitted_class` + `scheduler.rs:248` +
`tests.rs:606-631`, §7#3 vs `sim.rs coactivity_trace`, §2 size vs `generate.rs:22`, §2 cover-OFF vs
`THREAT_MODEL.md:633`. **Standard results:** Serjantov–Danezis (PET 2002), randomized-response DP (Warner
1965), sequential composition / privacy odometer (Dwork–Roth; Rogers et al.), LDP hypothesis testing
(Kairouz–Oh–Viswanath; Wasserman–Zhou), computational DP (Mironov et al.). **FOR-THE-GATE, not asserted
as proven:** the exact constant in the LDP→identity-advantage reduction (§5); the `q^E` independence model
(§4.1). Canon only after cross-vendor review confirms both.
