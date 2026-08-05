# COVER_DITHER_SYMMETRIC_DESIGN.md — the 4-class cover dither that closes the ε=∞ ceremony leak

**Status:** DESIGN v1, **pre-review**, 2026-08-05, for **HYP-527** (closes **HYP-526**). Decision on record
(Josh, 2026-08-05): **full cover for all classes** — ceremonies/dissolutions get real cover, the sovereignty
cost is accepted. This document proposes the construction, states the one tension that decision runs into,
and routes the formal bound to HYP-329. **Not yet gated.** Next step per FACTORY.md: cross-vendor
DESIGN-review (Claude lenses + Codex, `gate-plan.sh` lean) before any build.

**Code grounded in `dyados@<pin-at-build>`** — every `file:line` below resolved on the `main` read of
2026-08-05; re-verify at build. Companion: `GPA_ANALYSIS.md` (diagnostic; the budget provenance).

---

## §1 The defect (what we are fixing)

The shipped class-dither manufactures cover **only between Ambient↔Standard**. Read directly from
`vita-carriers/src/cover_traffic.rs:435-451` (`emitted_class`):

```
fires=false            → current                       (no noise)
Ambient   , fires      → Standard.min(ceiling)         (up-flip)
Critical  , fires      → Critical                      (exempt — never delay a ceremony)
_ , fires, pending_vol → current                       (down-flip SUPPRESSED on the secret)
_ , fires              → Ambient                        (down-flip)
```

**Three ways this is ε=∞** (each a real, currently-shipped leak; HYP-527 body has the full derivation):

1. **High classes are certain tells.** Nothing ever flips *to* Elevated or Critical. So
   `P(observe Critical | true≠Critical)=0` while `P(observe Critical | true=Critical)=1` — an unbounded
   likelihood ratio. **A GPA identifies every bond ceremony / dissolution / succession (200 ms) and every
   Klinos consult / live bio-stream (500 ms) by grid rate alone.** These are the events THREAT_MODEL §6.2.4
   marks most sensitive.
2. **The down-flip is secret-conditioned.** `:449 _ if has_pending_real_volume => self.current` zeroes the
   down-flip *iff real traffic is queued* — so the emitted rate is a function of the secret. Data-dependent,
   unbounded LR.
3. **Mid-epoch mutation.** `scheduler.rs:248` feeds a live per-slot `ceiling` (`effective_cover_ceiling()`,
   pinned to `current()` under `cover_suspended()`/`escalation_locked()`) into `emitted_class` while the RR
   bit stays latched for the 30 s epoch — so the *observed* class is not constant within an epoch, and a
   neighbouring true-trajectory can have disjoint observed support.

Plus **γ mistuned** (`DITHER_GAMMA_NUM/DEN = 1/5`, `cover_traffic.rs:66-68` ⇒ `ε_epoch=ln4=2·ln2`, twice the
stated per-window budget at E=1), and the **availability gap** (`generate.rs:92` `candidates.choose(rng)?`
returns `None` with no cover candidates ⇒ an observable grid gap; GPA_ANALYSIS §2).

---

## §2 The tension the "full symmetric cover" decision runs into (READ THIS FIRST)

"Symmetric cover" in the strict DP sense means a **full-support** randomized response: for the emitted class
`o` and true class `c`, `P(o|c) > 0` for **every** pair, so no observation ever has an infinite likelihood
ratio. Full support has an unavoidable consequence:

> a full-support RR requires a **true-Critical dyad to sometimes emit *below* Critical** (else
> `P(observe Ambient | true=Critical)=0`, and observing Ambient is again an ∞ tell in the other direction).

But the emitted grid rate is the rate at which **real** cells are carried. A true-Critical dyad in a ceremony
has real 200 ms-cadence traffic; emitting below Critical that epoch means **real ceremony packets wait for the
next cell** — up to one dither epoch (30 s) of added latency on a dissolution/succession. So:

**Latency ⟂ symmetric-ε ⟂ no-secret-conditioning — you may have any two.**

| If you want… | you pay… |
|---|---|
| **Symmetric ε** (bounded both directions) + no ceremony delay | the rate must down-flip *only cover, not real* ⇒ **secret-conditioned** (leak #2 returns) |
| **Symmetric ε** + no secret-conditioning | true-Critical sometimes emits low ⇒ **ceremony latency** degraded up to 30 s |
| **No delay + no secret-conditioning** | **one-sided** ε: bound the sensitive direction only (below) |

This is not an implementation detail to be resolved in code — it is the shape of the achievable guarantee, and
the cross-vendor review must confirm which corner we take. **This design proposes the third row** (one-sided,
below) as the construction that best honours "never delay a ceremony" while giving ceremonies real cover, and
flags the choice explicitly for the review and for Josh.

---

## §3 The construction — an upward-biased 4-class keyed RR with a one-sided guarantee

### §3.1 The mechanism

Replace the binary `emitted_class` with a **keyed categorical draw** over the four classes. Per dyad, per
30 s dither epoch, from the same secret cover seed:

- Generalize `CoverKeyMaterial::dither_fires(epoch,num,den)` (`cover_content.rs:217`, a keyed
  `Bernoulli(γ)` over an HKDF draw) to **`dither_class(epoch) → u64`**: one uniform 64-bit HKDF draw under a
  new domain-separator `HKDF_INFO_COVER_DITHER_CLASS` (keep the existing `dither_fires` for nothing — this
  replaces it; do not run both off the same info or the draws correlate). Deterministic in `epoch`, keyed by
  the secret ⇒ **restart-exact** (HYP-40x) and **unpredictable to the GPA** are both preserved for free,
  because a categorical draw off one keyed uniform is still a pure function of `seed‖epoch`.
- Map the uniform draw to an **observed class** via a fixed **upward-biased RR row** selected by the true
  class `c`:

```
observed(c, u) = the class o such that u falls in o's sub-interval of [0,1) under row P(·|c)
```

with the row family (γ_up the per-step up-cover rate, the single tunable knob):

```
P(o | Ambient ) : Ambient 1−3γ_up , Standard γ_up , Elevated γ_up , Critical γ_up
P(o | Standard) : Standard 1−2γ_up , Elevated γ_up , Critical γ_up          (never below Standard*)
P(o | Elevated) : Elevated 1−γ_up  , Critical γ_up                          (never below Elevated*)
P(o | Critical) : Critical 1                                               (always ≥ Critical — no delay)
```

`*`the **"never below true class"** rule is the no-delay invariant: `observed ≥ true` always, so real traffic
is never starved and **no ceremony is ever slowed**. (The old down-flip — active *looks* idle — is dropped;
§4.1 explains why its intersection-attack value is superseded and its cost here is the secret-conditioning we
are removing.)

### §3.2 The guarantee this actually gives (one-sided, per-epoch, composing)

For the **sensitive direction** — "is this dyad in a high-class event this epoch?" — the per-epoch likelihood
ratio for any high class `h` is bounded:

```
P(observe h | true = h)        1
───────────────────────── = ───── = e^{ε_up},   ε_up = ln(1/γ_up)
P(observe h | true = idle)     γ_up
```

so a single epoch of Critical cover gives the GPA at most `ε_up` nats of advantage at calling a ceremony real.
This is **not** classical symmetric (ε,0)-DP: the reverse ("observe Ambient ⇒ not-Critical-this-epoch") is
unbounded, but it reveals only the **non-sensitive** fact that the dyad is *not* mid-ceremony. The design
claim is a **one-sided DP bound on detection of the sensitive high-class event**, which is the property we
actually want and the honest thing to state.

**It composes over the event's duration, not just one epoch.** A real 20-minute ceremony is ~40 consecutive
Critical epochs; cover Critical is per-epoch independent at rate γ_up, so sustained Critical still accrues
`≈ D·ε_up` over a D-epoch event — the **odometer** of GPA_ANALYSIS §5(3). Therefore the dither bounds the
**per-window** advantage and **tunes γ_up to a named window W** (§5); **durable** hiding of a long ceremony is
Phase-2 mixing, exactly as GPA_ANALYSIS §8 concludes. The design does not over-claim lifetime unlinkability.

### §3.3 Per-epoch ε and the knob

The **worst-case per-epoch ε** across the whole matrix (max log-LR over all `(o,c,c′)`) is
`ε_epoch = ln(1/γ_up)` (the Critical/Elevated one-sided ratios dominate; the Ambient row's internal ratios are
smaller). Note this is **not** the binary `ln((1−γ)/γ)` that `measure.rs:145 epsilon_epoch` computes — a new
`epsilon_epoch_categorical(γ_up, k)` is owed (§7), and `TIER3_EPSILON_BUDGET` must be interpreted against it.

---

## §4 The three residual leaks — stated, not hidden

Design-first honesty (rule #1, and the §2.4 lesson from GPA_ANALYSIS): the construction does not close
everything. Each residual is either fixed here, bounded, or routed.

1. **Secret-conditioning — REMOVED by construction.** Because `observed(c,·)` is a pure function of
   `(true class, epoch, seed)` and the "never below true class" floor depends only on the *true* class (which
   the dyad is in regardless of queued volume), the emitted rate no longer depends on `has_pending_real_volume`.
   Leak #2 is designed out. **Caveat the review must check:** the true class itself is set by
   `note_activity` from real activity, so "true class" is already secret — the claim is only that we add **no
   new** dependence on queue occupancy beyond the class the system already commits to and already dithers.
2. **Affordability conditioning — BOUNDED, partially residual.** A budget/battery/carrier-capped dyad has
   `effective_cover_ceiling() < Critical` (`scheduler.rs:255`), so it *cannot* emit Critical cover:
   `P(observe Critical | capped)=0`. Observing Critical therefore still rules out capped dyads — a partition
   on carrier/budget, not on identity, but real. **Options for the review:** (a) document it as a Phase-1
   residual (capped dyads are a distinguishable cohort, but not *identified*); (b) require a minimum cover
   affordability to participate in the high-class anonymity set; (c) let a capped dyad emit a *bounded* count
   of high-class cover cells from a reserve. Recommend (a) for Phase 1 + track (b)/(c) — but this is the crux
   the gate will probe, so it is a decision, not a default.
3. **Duration composition — PER-WINDOW by design, durable = Phase-2.** §3.2. Tracked to HYP-329 (the formal
   per-window bound) and the Phase-2 mixing stack (GPA_ANALYSIS §8), not solved here.

Also fixed here: the **mid-epoch mutation** (leak #3) — the observed class must be latched for the whole
dither epoch. The ceiling clamp stays (an up-flip must never exceed policy), but the ceiling is **sampled once
per epoch** with the RR draw, not re-read per slot (§6). The **availability gap** — `generate`→`None` — is
closed by a self-addressed fallback cover cell so a scheduled slot never emits nothing (§6).

---

## §5 γ_up retune to a window, and the cross-crate budget check (rule #32)

- **Name the window `W`** (active epochs the per-window bound must hold over) in THREAT_MODEL, and set
  `γ_up` so `W·ln(1/γ_up) ≤ TIER3_EPSILON_BUDGET` (interpreted for the categorical mechanism, §3.3). State the
  achievable `W` for the chosen γ_up — "lifetime" is not a usable framing at any γ (GPA_ANALYSIS §5(3)).
- **The mechanism (rule #32):** the ε=∞ shipped for months because `γ` lives in `vita-carriers` and the
  budget in `gpa-sim` (a non-default workspace member) and **nothing compares them**. Fix: a
  build/gate/test check that fails when the shipped `γ_up` violates the stated per-window budget at `E=1`.
  Force the two constants into the same room — a `#[test]` in `vita-carriers` that imports the budget (or a
  shared `const` both cite) and asserts `epsilon_epoch_categorical(γ_up,4) ≤ TIER3_EPSILON_BUDGET/W`. This is
  the actual durable fix; retuning γ without it re-opens the same hole for the next constant.

---

## §6 Mechanism changes (the build surface)

1. `cover_content.rs`: add `dither_class(epoch) → u64` (keyed uniform, new domain-sep) and a pure
   `fn observed_class(true_class, draw, gamma_up, ceiling) -> EnergyClass` implementing §3.1 with the
   `observed ≥ true` floor and the ceiling clamp. Keep it a pure function of its inputs (restart-exact, testable).
2. `cover_traffic.rs`: replace `emitted_class`'s binary ladder with a call to `observed_class`. Delete the
   `has_pending_real_volume` down-flip suppression (no longer any down-flip). **Latch the ceiling** for the
   epoch: the ceiling passed in is sampled at the same epoch boundary as the RR draw, not per-slot.
3. `scheduler.rs:242 dithered_rate_ms`: drop `has_pending_real_volume`; pass the once-per-epoch ceiling.
4. `generate.rs`: on `candidates.choose → None`, emit a **self-addressed** fixed-size cover cell (never a gap).
5. **Restart:** unchanged in shape — the draw stays `f(seed‖epoch)`, so `persist`/recovery (`persist/tests.rs`)
   needs only the new draw wired; no new persisted state. Re-verify the HYP-40x restart-exact tests.

---

## §7 gpa-sim model + the ε test (rule #8, rule #27)

- Extend `gpa-sim` from a **binary** class bit to the **4-class** observation (`sim.rs` currently flips one
  bit; `measure.rs:145` is the binary RR bound). Add `epsilon_epoch_categorical(γ_up, k)` and re-derive
  `min_gamma`. Model the **affordability conditioning** (a capped-dyad population that cannot emit Critical) so
  the measured advantage is not optimistic — the same discipline that caught the binary model over-crediting.
- **Measure, don't co-monotone:** GPA_ANALYSIS §5(4) — the existing harness shows ε↓/entropy↑ move together,
  which is not a bound. Add a test that *measures* the one-sided detection advantage against the modelled
  adversary and asserts it ≤ `e^{ε_up}` per epoch and ≤ budget over `W` (rule #8 — encode the spec value).

---

## §8 Cost — what "full cover" spends

Per `measure.rs:173 dither_bandwidth_overhead`, an idle dyad up-flipping to class `o` at rate γ_up costs
`γ_up·(idle_ms/rate_o − 1)` extra cells. Full 4-class cover has the idle dyad reaching **Critical** (200 ms)
at rate γ_up: overhead `≈ γ_up·(5000/200 − 1) = 24·γ_up` on the Critical component alone (plus the Elevated
and Standard terms). At γ_up=0.05 that is ~1.2× idle bandwidth from the Critical term — **the sovereignty cost
Josh accepted.** The design must (a) publish this number for the chosen γ_up, and (b) respect the existing
budget ceilings (`fraction_consumed` caps, `cover_traffic.rs:174-204`): a dyad past its budget floor stops
buying others' cover (that is the affordability residual §4.2), which bounds the worst-case spend.

---

## §9 Test plan (merge gate — rule #27)

- **Unit:** `observed_class` — the matrix rows sum to 1; `observed ≥ true` always; ceiling clamp; γ_up=0 ⇒
  identity; every high class reachable from idle (the ε=∞ regression test — asserts `P(Critical|idle)>0`).
- **Integration:** wire `dither_class` through the real `CoverTrafficScheduler` + driver; advance real epochs;
  assert the emitted-rate histogram over a capped and an uncapped dyad matches the matrix (the seam, not a mock).
- **Smoke:** a real driver tick at an epoch where the draw selects Critical cover for an idle dyad emits a
  Critical-rate cell without panicking.
- **ε regression:** the §5 cross-crate budget assertion; the §7 measured-advantage bound.
- **Restart:** the HYP-40x exact-cadence tests still pass with the categorical draw.

---

## §10 Build chunks (after the design review passes)

- **C1** `dither_class` + `observed_class` pure functions + unit tests (incl. the ε=∞ regression).
- **C2** wire into `emitted_class`/`dithered_rate_ms`/scheduler; drop the secret-conditioned down-flip; latch
  the ceiling per epoch.
- **C3** availability-gap fallback in `generate`.
- **C4** `gpa-sim` 4-class model + `epsilon_epoch_categorical` + measured-advantage test.
- **C5** the rule #32 cross-crate budget check + γ_up calibration constant + THREAT_MODEL `W` + cost number.
- **C6** restart-exactness re-verification; integration + smoke (rule #27); crypto-class gate; land; close 526+527.

---

## §11 Open questions for the cross-vendor DESIGN-review

1. **§2's corner:** is the one-sided (below) guarantee the right one, or does Josh want strict symmetric ε at
   the cost of bounded ceremony delay? (Design recommends one-sided; flagged as a decision.)
2. **§4.2 affordability:** document the capped-cohort partition (recommend), or enforce a participation floor,
   or a reserve? The gate should pressure-test whether "capped ⇒ never Critical cover" leaks more than a cohort.
3. **§3.3 ε form:** confirm `ε_epoch = ln(1/γ_up)` is the true matrix worst-case, and that
   `epsilon_epoch_categorical` is derived, not assumed (route the tight statement to HYP-329).
4. **Down-flip removal:** does dropping the "active looks idle" down-flip weaken the intersection-attack floor
   the up-flip alone must now carry? (GPA_ANALYSIS §4.1 — the up-flip manufactures the false co-active floor;
   confirm it suffices without the down-flip.)
5. **Composition:** basic vs advanced composition for `W` (`measure.rs:156` uses basic/conservative).

## §12 Provenance

Every code claim cites a `file:line` read on `dyados@main`, 2026-08-05: `emitted_class`
(`cover_traffic.rs:435-451`), `dither_fires` (`cover_content.rs:217-238`), `dithered_rate_ms` + ceiling
(`scheduler.rs:242-259`), the budget + RR math (`measure.rs:137-198`), rate constants
(`cover_traffic.rs:44-53`), `generate`→`None` (`generate.rs:92`). Standard results: randomized response
(Warner 1965), categorical/`k`-ary RR ε (Kairouz–Oh–Viswanath), sequential composition / odometer
(Dwork–Roth; Rogers et al.). The affirmative per-window bound (§3.2/§3.3) is stated in-model here and routed
to **HYP-329** for the formal statement — this document is a **design for review**, not a proof.
