# CIRCUIT_BUILD_UNLINKABILITY_DESIGN.md — HYP-522

**Status:** DESIGN v0, pre-review, 2026-08-06. Grounded in `CIRCUIT_BUILD_UNLINKABILITY_RESEARCH.md` (four-leg literature survey) and Josh's decision **(a) full continuous setup-cover** — HYP-522 is an affirmative-bound deliverable (HYP-329 class). Implements `CIRCUIT_LIFECYCLE.md §19` + `THREAT_MODEL.md §6.2.3` as ONE mechanism. Prerequisite: **HYP-331** (pool + driven 6-state lifecycle). Next step after this doc: cross-vendor DESIGN-review (Codex + Claude legs — the 493 process lesson), then build 331 → 522.

---

## §1 The invariant (stated precisely)

> **The circuit-warming-handshake emission process is a fixed-rate clock whose rate is a deterministic function of time and configuration alone — never of real activity, queue state, energy class, intent, or destination. A real circuit-open CONSUMES a scheduled warming slot (or a pre-built idle circuit); it never ADDS a handshake, and it never suppresses one.**

This is Loopix's substitution discipline lifted to the circuit-setup channel (research §4). Activity changes only a slot's *contents* — real cold-start vs cover pre-warm — never the *rate*. It is the exact inverse of HYP-493's fatal property (cover-rate ∝ 1 − activity).

**Corollary (the 493 killer, negated):** the warming hook is evaluated **once per slot on the fixed clock, unconditionally** — not inside any `SlotOutcome` branch, not gated on an empty real queue, not gated on cover-suspended. If cover is battery-suspended, warming is suspended *for real and cover identically* (see §6 R-open).

---

## §2 The mechanism — the warming clock

A per-dyad **WarmingScheduler** ticks at a fixed interval `WARM_TICK_MS` (a low rate — see §8; circuits live 600 s, so setup is inherently a trickle vs the 200 ms–5 s data plane). Each tick emits **exactly one** warming handshake, whose target is chosen by this priority, all producing a **byte- and timing-identical** setup (§7):

1. **Real cold-start pending** — a destination the dyad needs a circuit to and has none warm → emit the real establish into this slot.
2. **Pool below target** — the idle pool (§3) has < `IDLE_CIRCUIT_POOL_SIZE` warm circuits → emit a cover pre-warm toward a cover-eligible likely destination, refilling the pool.
3. **Pool full** — emit a **loop/drop warming** handshake (a self-addressed or discard establish that produces the identical on-wire setup but no usable circuit), so the slot is never empty.

Because every tick emits one handshake regardless of which branch fires, the **setup-event rate is constant** and the branch taken is not observable (§4). A real send to an *already-warm* destination (the common case, via the pool) emits **no handshake at all** — the strongest form of the property, and pure Loopix substitution: the real send rode a warming slot that already happened.

---

## §3 The idle pool (HYP-331) — latency layer, zero security credit

The pool is the buffer that makes warming *productive* (so real sends usually find a ready circuit). **It carries no security credit** (research §1, Leg B): the bound comes from the constant warming rate, not from the pool being non-empty. Design consequences:

- The pool is filled **only** by the warming clock (§2 branch 2), **never** off the Stroma `intent.write_pending` signal (§6.2.3 trap — warming off an intent signal reintroduces conversation-correlation).
- Interface to HYP-331: the pool holds circuits in the driven `ChannelState::Warming` resting state (currently unreachable — HYP-331 must store+drive the 6-state `ChannelLifecycle`). A real send transitions a pooled circuit `Warming → Active` with **no wire event**.
- `IDLE_CIRCUIT_POOL_SIZE` is a latency/hit-rate knob (HYP-171-tuned), **not** a security parameter. A larger pool lowers the cold-start fraction (R-1) but does not change the bound.

---

## §4 Observable-match table (the load-bearing section — 493 lesson: all three axes)

Every observable from `COVER_TRAFFIC.md §4.5a` #1–#12, and how this design makes it **MATCH** across the real-cold-start and cover-warming paths (or declares it a stated STRUCTURAL residual). *The invariant §1 makes most of these dissolve because both paths are the same clock emitting the same-shaped handshake.*

| # | Axis | Observable | Disposition under this design |
|---|---|---|---|
| 1 | handshake | trigger predicate | MATCH — both paths fire on the fixed clock tick, not on `seal_data_ready` vs `has_circuit` |
| 2 | handshake | destination eligibility | **STRUCTURAL residual** — a real cold-start to a non-cover-eligible peer cannot be pre-warmed by cover; stated (R-2). Mitigated: warming draws from the same directory as real where possible |
| 3 | handshake | (handshake, DATA) pairing | MATCH — DATA follows on a later independent slot in both paths (see #6) |
| 4 | handshake | intent / carrier fan-out | **MATCH by design (§7)** — all warming handshakes, real or cover, use a **fixed carrier fan-out** regardless of intent; closes HYP-518 |
| 5 | handshake | build rate | MATCH — the whole point: rate is the fixed clock, real does not exceed it (a real cold-start *waits for the next tick*, bounded by §8 latency budget) |
| 6 | handshake | follow-up traffic | **partial** — DATA follows a real establish with P≈1 vs cover P≈0. Mitigated: real DATA is deferred to ride the constant data-plane cover (already constant-rate), so the *follow-up timing* is not slot-adjacent. Residual stated (R-2 #6) |
| 7 | handshake | retry after failure | MATCH — both paths re-draw the next target by the same rule on the next tick; no same-dest run |
| 8 | handshake | CircuitPurpose | MATCH — `Standard` both |
| 9 | slot | handshakes per slot | MATCH — exactly one per tick, both paths (no real-build + cover-fill double) |
| 10 | slot | cover-build vs real-queue occupancy | **MATCH — the invariant** — warming fires once per tick regardless of queue state; real traffic does NOT suppress warming |
| 11 | sequence | rate while cover suspended | MATCH — warming suspends for real and cover **identically**; a real cold-start during suspension **waits** (bounded) rather than emitting a lone real handshake |
| 12 | sequence | budget-exhausted steady state | MATCH — no separate budget; the clock is the only rate, and it always emits |

**Acid test for the review:** for every row not marked STRUCTURAL, an adversary handed only that observable must classify real-vs-cover at chance. Rows #2 and #6 are the surviving residuals and go to THREAT_MODEL (§6), not hand-waved.

---

## §5 The affirmative bound (what we prove + encode)

**Primary — Loopix Poisson/constant-rate indistinguishability** (research §3): the warming emission is a fixed-rate process independent of queue state, so in any slot "real cold-start" is information-theoretically indistinguishable from "cover warming" *on the handshake-count/shape/rate channel*. No composition budget (memoryless clock). This is the setup-channel analog of the GPA data-plane result.

**Quantified fallback — PCP Thm 8.2** (research §3, `arXiv 2103.03831 §8`): for the residual real handshakes that *do* reach the wire (cold-starts, R-1), the optimal classifier's advantage over the base rate is bounded as a function of **φ = (cover-warming rate)/(real-cold-start rate)**. **To re-derive the exact form against the PDF before encoding** (GPA lesson — never assert a bound that merely sounds right). Encode as a `gpa-sim`-style harness (rule #8): a property test that fails when warming-emission events are statistically correlated with real-send events, + a computed φ→leakage curve pinned to the paper.

**Deliverable parity with HYP-329:** the bound + its residuals live in `THREAT_MODEL.md` + a `gpa-sim`/harness test, not in prose.

---

## §6 Residuals — stated in THREAT_MODEL, never implied zero (research §5)

- **R-1 first-contact cold-start** — `P(cold-start)=1` for a never-contacted peer (you cannot pre-warm a circuit to a peer you have never contacted); nonzero for any finite warming rate. Bounded by the continuous cover rate, not the pool size. Quantify the fraction at the chosen `WARM_TICK_MS` + pool size.
- **R-2 structural** — #2 (cover cannot address non-cover-eligible peers), #6 (real DATA follow-up), stated with their mitigations (§4).
- **R-membership** — no design hides that the dyad runs the system / that warming is happening at all (universal across the survey). Phase-boundary statement.
- **R-timing** — the timing channel between a real send and its surrounding cover is *not* proven closed by any surveyed system (PCP future work). Standing open residual; the constant clock makes it *believed* small but not proven.
- **R-aggregate-N** — the warming rate advertises an upper bound on concurrent warm circuits; resizing with demand is observable → resize only on a coarse, data-independent schedule.
- **R-open (cover-suspended)** — under battery suspension, warming stops; a real cold-start must **wait** for resumption (bounded by §8), or be **dropped/deferred**, never emitted alone. This is a utility↔privacy corner the review must pressure-test.

---

## §7 Fan-out / setup-fingerprint identity (closes HYP-518)

All warming handshakes — real and cover — MUST be byte- and timing-identical at the setup-packet level and use a **fixed carrier fan-out independent of intent**. Real `Critical` establishment must NOT fan out across both carriers when cover uses one (the HYP-518 leak). Our Sphinx-shaped `sealed_envelope` plausibly gives packet-level identity for free (as Sphinx does for Loopix) — **verify in the review**. Timing identity: the warming clock's inter-emission distribution is the same regardless of contents (Kadianakis: naive dummy handshakes still fingerprint unless timing-matched).

---

## §8 Constants (mechanism buildable now; values HYP-171-tuned)

| Constant | Role | Class |
|---|---|---|
| `WARM_TICK_MS` | the fixed warming-clock interval (the setup-cover rate) | **mechanism now; value HYP-171-tuned.** Set relative to circuit lifetime; low-rate |
| `IDLE_CIRCUIT_POOL_SIZE` | latency/hit-rate buffer (currently spec placeholder = 2) | latency knob, HYP-171-tuned; NOT a security parameter |
| `WARM_LATENCY_BUDGET_MS` | max a real cold-start waits for the next warming tick before a policy decision | **new — design must set**; bounds the R-open corner |
| `CIRCUIT_DEFAULT_LIFETIME_MS` | 600 000 (existing) | spec-fixed |
| φ target | cover:real warming ratio for the §5 bound | derive against PCP PDF |

**Build order:** HYP-331 (store+drive `ChannelLifecycle`; build the pool producing `Warming`) → HYP-522 (the WarmingScheduler + the invariant + the bound). 331 is the mechanical substrate; 522 is the property.

---

## §9 Tests (rule #27 + the property leg)

- **Property test (the 493-refuting one):** a statistical test that FAILS when warming-emission events correlate with real-send events, evaluated in **all three regimes** (continuous-real-traffic, cover-suspended, budget-N/A) — the axes 493 kept missing.
- **Integration:** a real send to a warm destination emits zero handshake cells (assert on the wire, not the API).
- **Smoke:** the WarmingScheduler ticks at the fixed rate with zero real traffic and emits loop/drop warming (branch 3).
- **Bound harness:** the φ→leakage curve pinned to PCP Thm 8.2 (once re-derived).

---

## §10 Open questions for the cross-vendor DESIGN-review

1. **R-open corner:** when cover is battery-suspended and a real cold-start is needed, is "wait up to `WARM_LATENCY_BUDGET_MS` then send anyway" a leak (a lone real handshake during suspension)? Or must the send be dropped/deferred? This is the sharpest utility↔privacy tension.
2. **#6 follow-up:** does deferring real DATA to the constant data-plane cover actually break the slot-adjacency, or does inter-arrival still link the establish to its DATA?
3. **φ and the bound:** re-derive PCP Thm 8.2's exact form; is the Loopix info-theoretic claim clean given our directory-scoped cover eligibility (#2), or does #2 puncture it?
4. **Sphinx packet-level identity:** does `sealed_envelope` truly give byte+timing-identical warming handshakes, or is there a length/format tell between a real establish and a loop/drop one?
5. **331 interface:** is the driven 6-state lifecycle sufficient to hold `Warming` as a resting state that a real send consumes with no wire event, or is there a hidden establish on `Warming → Active`?
