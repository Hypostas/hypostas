# CIRCUIT_BUILD_UNLINKABILITY_DESIGN.md — HYP-522

**Status:** DESIGN **v1**, pre-review, 2026-08-06. Supersedes v0, which a cross-vendor DESIGN-review refuted with 4 P1s (design-first working as intended — caught on paper, not in a build graveyard). Grounded in `CIRCUIT_BUILD_UNLINKABILITY_RESEARCH.md` + Josh's decisions: **(a) full continuous setup-cover** and **(F3) protect suspension via an always-cover floor**. Implements `CIRCUIT_LIFECYCLE.md §19` + `THREAT_MODEL.md §6.2.3` as ONE mechanism. Prerequisite: **HYP-331**. Next: cross-vendor DESIGN-review (both legs, working Codex) → build 331 → 522.

## v0→v1 changelog (the review's 4 P1s + 2 P2s)
- **F1 (P1) — the missed observable: circuit REFRESH.** v0 modeled only the initial build; refresh is also a handshake and its per-circuit-timer rate ∝ active-circuit count ∝ activity. **v1: refresh is process-driven** — it consumes a slot of the one setup-cover process, never fires its own timer (§2, §2b).
- **F2 (P1) — deterministic ≠ memoryless.** v0's fixed-interval clock is separable and doesn't inherit Loopix. **v1: a Poisson process at rate `λ`** (§2).
- **F3 (P1) — suspend corner.** v0 stopped cover on suspension ⇒ no slot to substitute into, in the default regime. **v1: `λ` has a positive floor `λ_min` that never stops** (§3b — Josh's always-cover choice).
- **F4 (P1) — bound over-claimed + category-mismatched.** **v1: Loopix indistinguishability is stated CONDITIONAL on the cover-eligible sub-channel; non-eligible cold-starts are a stated residual; the PCP-φ leg is DROPPED (wrong model for substitution)** (§5).
- **F5 (P2) — branch-3 self-contradiction.** **v1: the loop/drop warming is a genuine relay-completing build** (§7).
- **F6 (P2) — destination draw.** **v1: pre-warm targets drawn from the slowly-updated long-term contact set on a data-independent schedule** (§2c), with the productivity/divergence residual stated (§6 R-7).

---

## §1 The invariant (v1)

> **The circuit-setup-handshake EMISSION PROCESS is a Poisson process with rate `λ(t)`, where `λ(t)` is a function of wall-clock time, configuration, and coarse energy-state ONLY — never of real activity, queue state, active-circuit count, energy *class*, intent, or destination. Every setup event the dyad emits — cold-start, refresh, pool pre-warm, loop — is one firing of this single process and CONSUMES a slot; nothing outside it emits a handshake, and real demand never adds or suppresses a slot.**

- **Energy-state vs energy-class:** `λ(t)` may step between a full rate `λ_full` and a suspension floor `λ_min > 0` as a function of *coarse device power state* (§3b) — a slow, data-independent signal. It is NEVER a function of the *energy class* of any conversation (which encodes activity). This is the precise distinction v0 violated (F3).
- **Corollary (the 493 killer, negated on all axes):** the emission process is the sole handshake source. Refresh (F1), cold-start, pre-warm, and loop all draw from it; none has an independent timer. So the aggregate setup rate is `λ(t)`, provably independent of how many conversations the dyad holds.

---

## §2 The mechanism — one Poisson setup-cover process

A per-dyad **SetupCoverProcess** fires on a Poisson clock of rate `λ(t)` (memoryless — F2). On each firing it services **exactly one** setup action, chosen by a fixed priority over pending demand, all producing a **byte- and timing-identical** relay-completing build (§7):

1. **Refresh-due** — a live circuit within `REFRESH_HORIZON` of its max lifetime → rebuild it (the new circuit replaces the old under the existing 30 s overlap). *(This is F1's fix — see §2b.)*
2. **Cold-start pending** — a destination the dyad needs and has no fresh circuit to → build it.
3. **Pool below target** — < `IDLE_CIRCUIT_POOL_SIZE` warm circuits → pre-warm toward a §2c target.
4. **Loop** — none of the above → a self-directed relay-completing build that is torn down after completion (§7), so the slot is never empty and the process rate is exactly `λ`.

Because every firing emits exactly one identical build and the firing rate is `λ(t)` regardless of which branch is taken, the **setup-event rate is activity-independent**. A real send to an already-warm destination (common case, via the pool) emits **no handshake at all** — pure Loopix substitution.

### §2b Refresh is process-driven (F1)
Circuits do **not** each run a 600 s timer that emits a rebuild. Instead, branch 1 services the *most-imminent* refresh each firing. For every live circuit to be refreshed before its `CIRCUIT_MAX_LIFETIME_MS` (1 800 s), the process must offer refresh slots at least as fast as circuits age out:

> **`λ_full ≥ N_max / CIRCUIT_MAX_LIFETIME_MS`**, where `N_max` is the provisioned max concurrent circuits per dyad.

This is the cost F1 surfaced: `λ_full` is a **constant floor set by `N_max`, paid always (idle included)** — a real setup roughly every `1800/N_max` seconds. `N_max` is a cost↔functionality knob (more concurrent conversations ⇒ higher constant cover cost), HYP-171-calibrated; a dyad exceeding `N_max` live circuits is a stated cap, not a silent degrade. Refresh urgency is bounded: if refresh demand transiently exceeds `λ`, the *oldest* circuit is serviced first, so no circuit passes `CIRCUIT_MAX_LIFETIME_MS` as long as `λ_full` meets the bound above.

### §2c Pre-warm target draw (F6)
Pool pre-warm (branch 3) and loop (branch 4) targets are drawn from the dyad's **long-term contact set**, refreshed on a **data-independent schedule** (e.g. a slow epoch clock, NOT recent activity) — so the draw is not a function of `intent.write_pending` or recent sends (the §6.2.3 trap). **Residual (R-7):** an activity-independent draw is less productive than an activity-driven one, so it raises the cold-start fraction (R-1) and its aggregate histogram may diverge from the real-contact histogram under an adversary with partial graph knowledge. Stated, not closed; the long-term set narrows the divergence.

---

## §3 The idle pool (HYP-331) — latency only, zero security credit

Unchanged from v0 in principle: the pool buffers warm circuits so real sends usually emit nothing; it carries **no security credit** (the bound is in `λ`, not in pool occupancy). Filled only by the SetupCoverProcess (§2 branch 3), never off `intent.write_pending`. Interface: circuits rest in the driven `ChannelState::Warming` (HYP-331 must store+drive the 6-state `ChannelLifecycle`; a real send transitions `Warming → Active` with **no wire event** — verify in review, §10 Q4).

### §3b The always-cover floor `λ_min` (F3 — Josh's decision)
`λ(t)` steps as a function of **coarse device power state** only:
- **Active/charging/WiFi:** `λ = λ_full` (§2b).
- **Battery-gated / cellular-suspended (the default regime):** `λ = λ_min > 0`, delivered over whichever carrier is available (the "always-cover carrier" generalized to a positive rate floor — this is what makes it work for cellular-only users: it is not a second carrier, it is a floor on the one you have).

**The floor never reaches zero,** so there is always a slot for a suspension-era cold-start to substitute into; it waits ≤ ~`1/λ_min` (bounded, `WARM_LATENCY_BUDGET_MS`) and **never emits a lone handshake** (closes F3's #11 leak). `λ_min` trades suspension-era cold-start latency + a small always-on battery cost against coverage — HYP-171-calibrated. The power-state signal must be **coarse and data-independent** (it may not be modulated by conversation activity, or it re-introduces the F3/§1 leak). During the `λ_min` regime, refresh provisioning (§2b) is relaxed to `λ_min ≥ N_active/CIRCUIT_MAX_LIFETIME_MS` for the *reduced* set of circuits kept warm under suspension (excess circuits are allowed to expire and cold-start on wake — a stated latency, R-6).

---

## §4 Observable-match table (all axes, incl. the F1 refresh row)

| # | Axis | Observable | Disposition (v1) |
|---|---|---|---|
| 1 | handshake | trigger predicate | MATCH — every branch fires on the one Poisson clock |
| 2 | handshake | destination eligibility | **STRUCTURAL** (R-2) — real cold-start to a non-cover-eligible peer can't be pre-warmed; bounds only the eligible sub-channel (§5) |
| 3 | handshake | (handshake, DATA) pairing | MATCH — real DATA deferred to the constant data-plane cover, not slot-adjacent |
| 4 | handshake | intent / carrier fan-out | MATCH — fixed fan-out independent of intent; closes HYP-518 (§7) |
| 5 | handshake | build rate | MATCH — the invariant; `λ(t)` ⊥ activity |
| 6 | handshake | follow-up | partial (R-2 #6) — DATA follow-up deferred to data-plane cover |
| 7 | handshake | retry | MATCH — next firing re-draws by the same rule |
| 8 | handshake | CircuitPurpose | MATCH — `Standard` both |
| 9 | slot | handshakes per slot | MATCH — exactly one per firing |
| 10 | slot | cover-vs-real-queue occupancy | MATCH — the invariant; unconditional per-firing evaluation |
| 11 | sequence | rate while suspended | **MATCH (F3 fix)** — `λ_min > 0` persists; a suspended cold-start substitutes into a floor slot, never emits alone |
| 12 | sequence | budget-exhausted steady state | MATCH — no separate budget; `λ(t)` is the only rate |
| **13** | **sequence** | **REFRESH rate (F1)** | **MATCH (F1 fix)** — refresh is process-driven (§2b); aggregate setup rate is `λ(t)`, independent of active-circuit count |

**Acid test for review:** for every non-STRUCTURAL row, an adversary handed only that observable classifies at chance. #2 is the surviving structural residual → §6.

---

## §5 The affirmative bound (v1 — corrected per F4)

**Loopix constant-rate/Poisson indistinguishability**, stated **conditional on the cover-eligible sub-channel**: for a setup to a destination the cover process *can* target (cover-eligible), "real cold-start" and "cover pre-warm/loop" are firings of the same `Pois(λ)` process ⇒ information-theoretically indistinguishable on the count/shape/rate channel, memoryless (no composition budget). This is the setup-channel analog of the GPA result, **on that sub-channel only.**

**Non-eligible cold-starts are NOT bounded by this** — a handshake to a peer the cover process cannot address is `P(real)=1` on the destination dimension (R-2). This is a stated residual, not hidden inside the bound (v0's F4 error).

**The PCP-φ leg is dropped** — PCP's `φ=λ_d/λ_u` is an *additive* model (dummies alongside real builds that reach the wire); our substitution mechanism has no independent `λ_u` to form the ratio. Any quantified residual bound must be re-derived in the *substitution* model; until then the residual (R-1, R-2, R-7) is stated qualitatively, never with a transplanted φ.

**Deliverable parity with HYP-329:** the conditional bound + the residual set live in `THREAT_MODEL.md` + a `gpa-sim`-style harness (the property test §9), not prose.

---

## §6 Residuals — stated in THREAT_MODEL, never implied zero

- **R-1 first-contact cold-start** — `P=1` for a never-contacted peer; bounded only by `λ`, not pool size.
- **R-2 structural** — #2 non-eligible destination (the bound's sub-channel condition), #6 DATA follow-up.
- **R-membership** — no design hides that the dyad runs the system / that warming happens.
- **R-timing** — the real-send-vs-cover timing channel (PCP open); the Poisson process makes it *believed* small, not proven.
- **R-aggregate-N** — `λ_full` advertises an upper bound on provisioned circuits (`N_max`); resize only on a coarse data-independent schedule.
- **R-6 suspension latency** — under `λ_min`, a cold-start waits ≤ ~`1/λ_min`, and circuits beyond the suspended warm-set expire and cold-start on wake.
- **R-7 draw productivity** — the activity-independent pre-warm draw (§2c) is less productive (raises R-1) and may diverge from the real-contact histogram under partial graph knowledge.

---

## §7 Setup-fingerprint identity + branch-4 loop (F5)

All setup handshakes — cold-start, refresh, pre-warm, **and loop** — MUST be a **genuine, relay-completing multi-cell telescoping build** (HANDSHAKE→REPLY, EXTEND→EXTENDED per hop to `MAX_HOPS_PER_CIRCUIT`), byte- and timing-identical, with a **fixed carrier fan-out independent of intent** (closes HYP-518). The branch-4 **loop** builds a real circuit and **tears it down after completion** (rather than being a cheap self-short-circuit) — so it is on-wire identical to a real build (resolving v0's F5 "identical but unusable" contradiction). Torn-down loops must respect `MAX_CIRCUITS_PER_NODE` (build → complete → immediate teardown, never accumulating). **Verify in review (§10 Q3):** does `sealed_envelope`/Sphinx give *sequence* identity across the full multi-cell build, or only per-cell identity?

---

## §8 Constants

| Constant | Role | Class |
|---|---|---|
| `λ_full` | full-power setup-cover Poisson rate | **mechanism now; value HYP-171-tuned.** Floored by §2b: `≥ N_max/1800s` |
| `λ_min` | suspension-regime rate floor (>0) | **new (F3);** value HYP-171-tuned; trades suspend latency vs battery |
| `N_max` | provisioned max concurrent circuits/dyad | cost↔functionality knob; sets `λ_full` floor |
| `IDLE_CIRCUIT_POOL_SIZE` | latency buffer (v0 placeholder = 2) | latency knob, NOT security |
| `REFRESH_HORIZON` | how early branch-1 services a refresh before max-lifetime | mechanism; ≥ one `λ` inter-arrival |
| `WARM_LATENCY_BUDGET_MS` | max a cold-start waits for a slot | bounds the substitution wait; ~`1/λ` |

**Build order: HYP-331 (store+drive lifecycle; pool producing `Warming`) → HYP-522 (SetupCoverProcess + invariant + bound).**

---

## §9 Tests (rule #27 + the property leg — keyed correctly this time)

- **Property test (F1-aware):** fails when the setup-event rate correlates with **active-circuit count** OR with real-send events, evaluated in **all regimes** (`λ_full` single-conversation, `λ_full` multi-conversation, `λ_min` suspended). v0's test keyed only on send-time correlation and would have missed the refresh leak — v1 asserts `rate ⊥ active_circuits` directly.
- **Integration:** real send to a warm destination emits zero handshake cells (assert on the wire).
- **Smoke:** the process fires at `λ_full` with zero real traffic (all loops), and at `λ_min` under a simulated suspend.
- **Bound harness:** the conditional Loopix indistinguishability on the eligible sub-channel + the enumerated residuals (no transplanted φ).

---

## §10 Open questions for the next cross-vendor DESIGN-review

1. **`λ_min` battery reality:** is a positive always-on setup-cover floor over cellular actually tolerable on a battery-gated phone, or does `λ_min` have to be so low that `1/λ_min` cold-start latency breaks `Critical` sends during suspension? The core tension of Josh's (F3) choice.
2. **Refresh urgency vs Poisson:** can a memoryless `Pois(λ)` process guarantee every circuit refreshes before `CIRCUIT_MAX_LIFETIME_MS` (a hard deadline) without a deterministic escape hatch that reintroduces a separable tell (F2)? Or does deadline-driven refresh need a bounded-jitter window that must itself be proven non-separable?
3. **Sequence-identity (F5/F7):** does the multi-cell telescoping build have byte+timing sequence identity across cold-start / refresh / loop, or is there a tell (RTT, hop count, teardown timing) between them?
4. **331 interface (§3):** is `Warming → Active` truly wire-event-free, or is there a hidden establish on transition?
5. **Non-eligible sub-channel (F4/R-2):** how large is the non-eligible cold-start fraction in practice, and does it dominate the bound (making the "conditional" bound cover a minority of real sends)?
