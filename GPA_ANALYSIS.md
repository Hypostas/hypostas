# GPA_ANALYSIS.md — the Tier-3 anonymity analysis

**Status:** DESIGN v4 — **DIAGNOSTIC-scoped; the affirmative Tier-3 bound is DEFERRED to formal work
(HYP-329/HYP-330), not stated here.** 2026-08-05, for **HYP-526**.

> ## ⛔ Why the affirmative bound is deferred, not drafted again
>
> Four drafts, ten cross-vendor review legs. v1 reversed the conclusions, v2 over-asserted, v3
> over-credited, v4's confirmation leg then found a **P1 observable channel this analysis omitted in all
> four drafts** (destination frequency — §2, below) and **self-inconsistent arithmetic in the affirmative
> §5** (the group-privacy factor of 2 was introduced but not propagated: γ=1/5 spends **4·ε_target** in
> one epoch, not the 2· the text stated), plus known precision gaps (`ε` vs advantage: group privacy
> bounds the *likelihood ratio* by `e^{2ε_W}`, not an "advantage by ≈2ε_W"; the "decays" claim is false
> at the degenerate γ=½ where ε=0). **This is the evidence that the affirmative Tier-3 security bound is
> beyond what this author can soundly self-certify** — precisely the escalation the OPERATING_MANUAL
> names ("method narrows the gap with a stronger model, it does not close it"). The **diagnostic** value
> below is sound and captured; the **affirmative bound** — the composed identity guarantee, its exact
> constant, and the full channel set — is routed to a formal/cryptographer pass (**HYP-329** formal
> analysis / **HYP-330** audit). §5 states the *mechanism and the formal requirements*, not a bound.
>
> The four-draft history and the ten verdicts are in git (`scripts/factory/verdicts/hypostas-*`).

> **What this document is.** A **diagnostic** analysis (what a GPA observes, and how the shipped
> mechanism departs from its model) plus an **in-model** statement of the dither's guarantee and its
> limits. It is **not** a formal proof: two residual items are genuine formal/empirical work, precisely
> specified in §10 and routed to HYP-329 (formal analysis) / HYP-330 (audit) / HYP-171 (measure `q`).
> **Code lives in `dyados` @ `013b4d8a`** — verify citations there.

---

## §1 The adversary

**Tier 3 — GPA** (`THREAT_MODEL.md` §4.3): sees all links, cannot decrypt, correlates timing/volume
network-wide, **records persist indefinitely**. **Computationally bounded** — the model grants indefinite
*storage* and a 50-year *capability-growth window* (the harvest-now/decrypt-later horizon), not unbounded
*computation*; every Phase-1 guarantee (AEAD, ratchet, dither) is computational.

**Phase 1 claims** (`THREAT_MODEL.md` §5 line 209) *"Tier 1 fully + Tier 2 partial + chassis for Tier
3/4"* — not durable Tier-3 relationship anonymity (that needs a mixing vantage point, Phase 2+;
`CIRCUIT_LIFECYCLE.md` §3 single-hop N=1).

## §2 The observable

Cover **on**: per dyad/carrier/slot a fixed-size cell on a constant-rate grid; content and real-vs-cover
hidden — **destination is NOT hidden at single-hop** (see #4). Four residual observables:

1. **Grid rate = `EnergyClass`** (`cover_traffic.rs rate_ms`: 5 s/1 s/500 ms/200 ms). `THREAT_MODEL.md`
   §6.3 line 296 admits it. The main subject of §3–§5.
2. **Size-class, matched by design** (`generate.rs:22`, weights chosen *"so cover matches the real size
   distribution"*): residual leak = only real traffic's *deviation* from the fixed mix.
3. **Class transitions** (onset localizable to the 30 s debounce): *when* a conversation began. Modelled
   by the harness (`sim.rs onset_localization`); not bounded here.
4. **Destination frequency — the direct relationship channel at N=1** (surfaced by v4's confirmation leg,
   omitted in v1–v4; then **verified at the call site**, rule #33). At single-hop (`CIRCUIT_LIFECYCLE.md`
   §3) the next-hop endpoint *is* the destination, and a GPA sees it. Cover **establishes a circuit to a
   randomly-sampled destination** (`generate.rs:92` `candidates.choose(rng)`; `driver.rs:582-599`
   `spawn_establish → establish_with_intent(&dest,…)`), while real traffic keeps the actual partner
   (`driver.rs:456` `seal_data_ready(&pkt.destination,…)`). So the GPA sees a dyad's circuits fan out to
   {real partner — **recurring**} ∪ {cover peers — **scattered, freshly random per slot**}: destination-
   frequency links the pair **independently of `EnergyClass`**, and §3–§5's activity-channel bound does
   **not** cover it. This is a Tier-3 surface **multi-hop closes** (the GPA then sees only the first hop),
   reinforcing §8's Phase-2 conclusion. Its exact bound — and whether routing-identity rotation (HYP-166)
   raises the cover baseline enough to blunt it — is formal work (§10).

**Availability caveat — the grid is constant-rate only while a cover cell is *available*.**
`CoverPacketSource::generate` returns `None` when it has **no cover candidates** (`generate.rs:92`, the
`?` on `choose`), emitting nothing and leaving an **observable gap**. "A cell per slot" is a Tier-1
invariant only when candidates exist; candidate-starvation gaps — and the cover-OFF regime below — are
themselves observable and break the constant-rate claim exactly where it is load-bearing.

**Cover OFF, and adversarial composition.** `THREAT_MODEL.md` §12.5 line 633: cellular 20–50 % battery →
*"Cover suspended, real messages only."* A phone interleaves WiFi (cover) and mid-battery cellular (no
cover); the §4.1 attack **accumulates across both**, cover-OFF epochs injecting exact-class (`γ_eff=0`)
observations. §3–§7 assume cover-on and thus *understate* a mixed dyad's leak. (Prevalence unmeasured.)

Per-epoch observable: the active bit `b_d`, re-decided once per 30 s dither epoch — **but see §7#2: the
runtime lets the *observed* class change within the epoch, so this is the model, not the runtime.**

## §3 The anonymity metric (Serjantov–Danezis)

Effective set size `2^H`, `H` = entropy of the GPA's posterior over the partner (PET 2002).
`adversary.rs posterior_partner_entropy`: `score(d) = k_d·ln(a/q′)+(E−k_d)·ln((1−a)/(1−q′))`,
`a=1−γ`, `q′=q(1−γ)+(1−q)γ`. Limits (in code): γ=0 → `log₂|S_∩|`; γ→½ → `log₂(N−1)`. This is the
relationship-anonymity currency; §5's DP budget is its **per-window companion**, not a replacement.

## §4 The leaks

### §4.1 Intersection attack — a model, conditional on `q` and on independence

No noise ⇒ exact class ⇒ intersect the target's `E` active epochs. `E[|S_∩|] = 1+(N−2)·q^E`
(`measure.rs:38`) **under an i.i.d. activity model**. This is a Jensen **upper bound** on anonymity
(code gates on `E[log₂|S|]`, test `measure.rs:304`); even that is a mean — a fraction of relationships
realize `|S|=1` while the mean is comfortable.

**Two independence caveats, both load-bearing:**
- `q` (background co-activity) is **unmeasured** (`gpa-sim lib.rs:92` default 0.25; HYP-171 tracks it).
  At q=0.25 a founding pair near-identifies (set 1.05); at q=0.9 it stays anonymous (set 3.2–21.7).
- The `q^E` step assumes per-epoch independence. **Correlation moves the true joint in *either*
  direction** — positive (diurnal) correlation enlarges the surviving set (weaker attack);
  *anti*-correlation (candidates active in disjoint epochs) shrinks it below `q^E` (stronger). So the
  table is a **model, neither an upper nor a lower security bound** without a measured joint.

**The one assumption-robust claim:** *the cover schedule does not close the class-activity leak; a
sufficiently long, sufficiently exclusive co-activity pattern shrinks the partner set toward 1.* Whether
a real pair is at risk is HYP-171's measurement.

### §4.2 Volume and onset — separate, unbounded

Size-deviation (§2.2) and onset (§2.3) are distinct Tier-3 surfaces the harness models; not bounded here.

## §5 The dither's guarantee — an in-model, per-window, activity-channel bound

Per epoch, the dither is a **randomized response** on the active bit: `ε_epoch = ln((1−γ)/γ)`-local-DP
(`measure.rs epsilon_epoch`; Warner 1965). **Computational** DP under the HKDF-PRF assumption:
`dither_fires = HKDF(seed, "dither"‖epoch)` (`cover_content.rs:217`) is a PRF of `(seed, epoch)`, not
information-theoretic independence — not distinctively weaker than the rest of the computational stack.

**The in-model claim, with its exact limits** (this is what the reviews converged on; each limit is a
finding a prior draft got wrong):

1. **Channel, not identity, directly.** LDP composes over a window of `W` active epochs to `ε_W = W·ε_epoch`
   on the activity *trajectory* (`measure.rs epsilon_total`; privacy odometer, Rogers et al.).
2. **Identity via group privacy — the *form*, exact constant deferred.** Changing the hypothesis "partner
   is `d`" → "partner is `e`" changes **two** dyads' trajectories, so group privacy bounds the **likelihood
   ratio** between the two partner-hypotheses over the window by `e^{2·ε_W}` (the factor 2 is the group
   size — exact, not "≥2"). This bounds the *likelihood ratio*, **not** a "distinguishing advantage
   ≈2·ε_W": the advantage-as-statistical-distance is a different quantity (at equal priors the
   total-variation advantage is `tanh(ε_W)`), and stating it precisely is the **HYP-329** formal item
   (§10). The bound covers **only the activity-count channel** §3's posterior uses; size (§2.2), onset
   (§2.3) and **destination (§2.4)** are outside it.
3. **Per-window, NOT lifetime.** The partner identity is **time-invariant** (daily seed rotation,
   `cover_content.rs:94`, re-keys the *noise* but not the *secret*), so an unrestricted adversary
   accumulates advantage on the *same* hypothesis across every window — the odometer **never resets** for
   a fixed secret. `ε_W` therefore bounds **per-conversation linkage**, and the §3 relationship anonymity
   **decays toward identification as windows accumulate** — *for any operating `γ<½`* (`ε_epoch>0`). At the
   degenerate `γ=½` the class bit carries no activity information, `ε_epoch=0`, and there is no decay — but
   the ladder's latency/energy tiering it exists to serve is also destroyed, so `γ=½` is not an operating
   point. *This is the rigorous reason durable Tier-3 anonymity needs a Phase-2 mixing vantage point, not a
   better dither.*
4. **The harness shows help, not the bound.** `measure.rs:366` asserts ε_total↓ and posterior entropy↑
   are each monotone in the shared knob γ — evidence the dither *helps*, **not** a proof of the form
   `advantage ≤ 2ε_W` (co-monotonicity through a common cause). The ">2 bits at γ=0.4" figure is in the
   idealized **symmetric** model (`sim.rs:70`) at a **non-shipped** γ — an upper bound on protection
   (§7#2), not the shipped mechanism's gain.

**Consequence for HYP-527 — a bounded but non-trivial fix, not a mechanism-philosophy rethink:**
(a) name the protection window `W` and set γ so `2·W·ε_epoch(γ) ≤ ε_target` for per-conversation linkage;
(b) **specify a real class-noising matrix** — "symmetrize the ladder" is under-defined: a full-support RR
over four observable classes has `ε = ln(3(1−γ)/γ)`, and adjacent-only flipping keeps zero-probability
outputs (ε=∞), so the fix needs an explicit output distribution and recomputed bound; (c) **make the
observed class actually constant within a dither epoch** (§7#2), or model the mutable channel. Durable
lifetime anonymity is out of scope for any dither and needs Phase-2 (§8).

## §6 Concrete scale

Founding scale, `q ≈ 0.25` **provisional/unmeasured** (HYP-171). Under that low `q`, §4.1's model
near-identifies a founding pair; under high `q` it does not. **Phase-1 Tier-3 exposure is a measurement
question, not a settled fact.**

## §7 Findings

**#1 — exact-class leak.** γ=0 ⇒ ε=∞; without the dither, §4.1 runs at zero error. Why HYP-357/359 shipped.

**#2 — the runtime departs from the RR model on a reachable subset (HYP-527), the strongest concrete
result.** `emitted_class` (`cover_traffic.rs:435-451`, read directly — the cited test `tests.rs:606-631`
builds only Ambient/Standard/Critical, so the Elevated case is verified by *code*, not that test) is an
**asymmetric ladder**: `Critical` exempt and nothing up-flips to `Elevated` (γ_eff=0 ⇒ **ε=∞** on the two
most sensitive classes); down-flip suppressed by the secret (`has_pending_real_volume`). Separately, the
observed class is **not constant within a dither epoch**: the scheduler feeds a live per-slot `ceiling`
(`scheduler.rs:248`, pinned to the committed class under `cover_suspended()`/`escalation_locked()` — a
lock of `3_600_000/30_000 = 120` epochs) into `emitted_class` while the RR bit stays latched, so a
neighbouring true-trajectory can have disjoint observed support ⇒ ε=∞ there too. The symmetric
`gpa-sim` model is an **upper bound on protection**, not the runtime. Fix per §5(b)/(c).

**#3 — epoch-unit note.** `gpa-sim coactivity_trace` (`sim.rs:45`) flips once per abstract epoch, does
not read `epoch_ms`; denominating a window in finer units inflates `W`, *lowering* modelled anonymity and
*raising* demanded γ — **conservative**. A calibration note, not a leak.

## §8 What Phase 1 can honestly claim

- **Tier 1 (same-link): volume and content, yes; activity, no.** Constant-rate fixed-size cover hides
  raw per-slot volume and content, but the **grid rate is the `EnergyClass`, which tracks activity** — so
  a same-link observer still reads the class-rate activity signal (and the §2.2/§2.3 residuals). "Fully
  activity-invariant" is false even with cover on; it is false outright in the cover-OFF regime (§2).
- **Tier 3 (GPA): a per-window, activity-channel, computational bound that *decays* across windows,
  currently below spec.** In-model the dither buys real per-conversation linkage protection (§5); it is
  **mistuned** (HYP-527: γ=1/5 ⇒ ε_epoch=ln 4, so with the §5(2) group-privacy factor `2·ε_epoch=ln 16=
  4·ε_target` after ≈one epoch) and **mis-implemented**
  (§7#2 ⇒ ε=∞ on sensitive classes and under mid-epoch mutation). Both fixable per §5.
- **Durable / lifetime Tier-3 relationship anonymity: Phase 2+.** The odometer argument (§5(3)) is the
  rigorous reason: no per-epoch class-noise can hold a *lifetime* bound on a *fixed* identity. It needs a
  **mixing vantage point** so the GPA cannot read a per-dyad activity bit at all — a GPA sees every hop,
  so **multi-hop routing AND relay padding AND cover-relayed cover**, with **HYP-522** (idle-circuit pool
  ⇒ real sends emit no observable build) the **necessary foundation**, not the whole.

**Arc-level:** the cover schedule is a Tier-1 defense (volume/content) with a decaying per-window Tier-3
*chassis* — exactly `THREAT_MODEL.md` §5 line 209. The Phase-1 dither is fixable (HYP-527); durable
Tier-3 is the Phase-2 mixing stack.

## §9 Consequences for the citing code (HYP-526 ACs)

Every `§N` resolves. **Owed corrections (tracked in HYP-527):** `measure.rs TIER3_EPSILON_BUDGET` should
read as a **per-window `(ε_W)` activity-channel** budget with `W` named, not "lifetime"; and the implicit
"shipped γ achieves the budget" is false (§7#2). `spec-guard` stops reporting once v4 lands; **HYP-526
closes only after v4's review + the §10 formal items**.

## §10 Provenance and the residual open items

**Derived, not recovered.** **Verified against `dyados@013b4d8a`** (all `file:line` resolve; the §4.1
table, the §7#2 ladder + `scheduler.rs:248` lock + the 120-epoch arithmetic, the §5 seed handling, the
§3 formula — all confirmed by the cross-vendor review). **Standard results:** Serjantov–Danezis (PET
2002), RR-DP (Warner 1965), sequential composition / privacy odometer (Dwork–Roth; Rogers et al.), LDP
hypothesis testing (Kairouz–Oh–Viswanath), group privacy + computational DP (Dwork–Roth; Mironov et al.).

**Residual OPEN items — genuine formal/empirical work, not another draft. This is the whole affirmative
bound; the diagnostic above stands, the *proof* is routed:**
1. **The affirmative identity bound itself** — §5's composed guarantee stated as a *distinguishing
   advantage* (not just the `e^{2ε_W}` likelihood-ratio form), with the worst-case-`q` value and the
   channel set it covers. The reviews established the in-model *form*; four drafts also showed this author
   accrues precision errors in it (the factor-2 propagation, the ε-vs-advantage conflation, the γ=½ edge) —
   which is the signal to route it, not draft it. → **HYP-329** (formal GPA analysis) / **HYP-330** (audit).
2. **A specified four-class RR construction** for the §5(b) / §7#2 fix (output matrix + recomputed ε),
   replacing "symmetrize the ladder." → part of **HYP-527**.
3. **Measure `q`** (and the joint activity correlation §4.1) → **HYP-171**.
4. **Bound the destination-frequency channel (§2.4)** — the per-slot random-destination cover vs. the
   recurring real endpoint at N=1; quantify the frequency leak and whether HYP-166 routing-identity
   rotation blunts it, or confirm it is a Phase-2 (multi-hop) item. → **HYP-329**, new sub-item.

This document is **diagnostic and canon** once v4's review is reconciled; the **affirmative bound is
explicitly not in it** — it is items 1 and 4, owned by HYP-329/HYP-330. A design analysis with its open
questions named, not a self-certified proof.
