# CIRCUIT_BUILD_UNLINKABILITY_DESIGN.md — HYP-522

**Status:** DESIGN **v2**, pre-review, 2026-08-06. Supersedes v1 (DESIGN-review found 2 P1s: F2 deadline, #5 lifetime channel). Grounded in `CIRCUIT_BUILD_UNLINKABILITY_RESEARCH.md` + Josh's decisions across three rounds: **(a) full continuous cover**, **(F3) protect suspension via a floor**, **(deployment) the computer-host holds the population + a host-restart recovery feature**, **(F2) bounded-jitter refresh**. Implements `CIRCUIT_LIFECYCLE.md §19` + `THREAT_MODEL.md §6.2.3`. Prereq: **HYP-331**. Next: cross-vendor DESIGN-review (both legs; Codex-on-hypostas is broken — HYP-533 — so a working Codex path is a precondition for this review).

## v1→v2 changelog (the 2 P1s + Josh's 2 decisions)
- **#5 (P1) — circuit LIFETIME channel via Little's Law.** v1 shaped the build *rate* constant, which (L=λ·E[W]) hands the active-circuit count back through lifetime. **v2 re-scopes the invariant from "build EMISSION" to "circuit LIFECYCLE": hold a CONSTANT circuit population `N_target`** — real conversations occupy slots of it, cover fills the rest, and both build AND teardown flow through the constant-rate process, so concurrent-count = `N_target` and lifetime distribution ⊥ real/cover role (§1, §2).
- **F2 (P1) — Poisson vs the hard refresh deadline.** **v2: bounded-jitter refresh** — a circuit is turned over at a uniform-random time in `[MAX_LIFETIME − W, MAX_LIFETIME]`, with a non-separability argument (the deadline anchor, the circuit's build time, is itself cover-hidden) — §2b. The false v1 §2b "no circuit passes MAX_LIFETIME" claim is retracted.
- **Deployment (Josh):** the **always-on computer-host holds the `N_target` population + cover**; mobile = thin node. This makes `N_target` affordable and dissolves most of F3's battery tension (same move that dissolved HYP-380's mobile-only P1s). NEW: a **host-restart recovery** mechanism (§3b) — the host reboots, so it has its own downtime regime.
- **P2s folded:** property test now asserts `concurrent_count ⊥ activity` + `lifetime ⊥ branch` (§9); `λ` gates on data-independent hardware state, never screen-"Active" (§3); wake/recovery latency is eaten, no rate-boost (§3b).

---

## §1 The invariant (v2 — lifecycle, not just emission)

> **The dyad's circuit population is a process whose CONCURRENT SIZE is held at a constant `N_target`, and whose per-circuit BUILD and TEARDOWN both fire on a constant-rate schedule that is a function of wall-clock time, configuration, and coarse host power-state ONLY — never of real activity, active-conversation count, energy class, intent, or destination. A real conversation OCCUPIES a slot of this fixed-size population (a cover circuit becomes its carrier); it never grows the population, never adds a build, and never changes any circuit's lifetime.**

Two quantities the adversary can measure are pinned constant, killing both v0/v1 leaks and their Little's-Law dual:
- **Concurrent circuit count** `L = N_target` (activity-independent) — closes #5 directly.
- **Per-circuit lifetime** drawn from one distribution regardless of whether the circuit ever carried real traffic (`lifetime ⊥ branch`) — closes #5's lifetime-distribution channel. `E[W] = N_target/λ`, constant, so `L = λ·E[W]` reveals only `N_target`, a public provisioned constant (R-aggregate-N).

**Corollary:** a real conversation may span several circuit lifetimes (its carrier ages out on the schedule and it hops to another slot — the refresh path), and a circuit outlives the conversation it carried (it reverts to cover until it ages out). Role (real/cover) is fluid; population size and lifetime law are fixed.

---

## §2 The mechanism — a constant-population circuit process (host-side)

The computer-host runs a **CircuitPopulationProcess** maintaining exactly `N_target` live circuits. Two constant-rate drivers, both memoryless-Poisson at the population level (F2 caveat in §2b):
- **Teardown/turnover** at rate `λ` picks the circuit nearest its (jittered) max-lifetime and tears it down (`CMD_DESTROY`), immediately triggering…
- **Build** of a replacement toward a §2c-drawn target, keeping the count at `N_target`.

So builds and teardowns are a constant-rate turnover of a fixed-size population — `N_target/E[W]` per second, independent of activity. **Real conversation handling (Loopix substitution at the population level):**
- A real send to a peer **already carried by a live circuit** (common case) rides it — **no build, no teardown, no population change.**
- A real send to a **new** peer **repurposes an existing cover circuit's slot** (retargets/rebuilds within the fixed population budget on the next turnover slot) — it does **not** add a circuit. If every slot is a live real conversation (population saturated at `N_target`), that is the stated concurrency cap (R-cap); the send waits for a turnover slot (bounded) rather than growing the count.
- When a conversation ends, its circuit **reverts to cover** and ages out on the normal schedule — no activity-correlated teardown.

Because the population size, the build rate, the teardown rate, and the lifetime law are all constants, an observer sees an activity-independent circuit lifecycle.

### §2b Bounded-jitter refresh (F2)
A circuit built at `t_b` is torn-over at `t_b + MAX_LIFETIME − U`, `U ~ Uniform[0, W]` — a bounded random window guaranteeing the hard deadline (`MAX_LIFETIME`) is met while avoiding a deterministic (separable) refresh clock. **Non-separability argument (to verify in review):** to exploit the refresh timing an observer must anchor it to a specific circuit's `t_b`; but `t_b` was itself a cover-indistinguishable turnover event (the observer could not tell that circuit's build from any other in the population), so the observer has no anchor for the window. Aggregate refresh = population turnover = `N_target/E[W]`, the same constant stream as builds. The argument holds on the **same eligible sub-channel** as the main bound (§5): if builds are unlinkable to their own refreshes across destination/path, jitter is non-separable; a linking side-channel would puncture both. `W` trades deadline-slack vs jitter-entropy — HYP-171-tuned.

### §2c Target draw
Unchanged from v1: build/turnover targets drawn from the **long-term contact set**, refreshed on a data-independent schedule (never `intent.write_pending`). Residual R-7 (productivity vs histogram-divergence) stands.

---

## §3 Deployment — computer-host holds the population (Josh)

The `N_target` population + the constant-rate process + cover all run on the **always-on computer-host** (the decided end-state; mobile = thin node). Consequences:
- `N_target` can be **generous** (host has power/bandwidth/relay-slot budget), so #5's constant-population cost is affordable where v1 feared it (a phone couldn't hold it).
- **F3 mostly dissolves:** the host does not battery-suspend, so `λ` runs at `λ_full` continuously; the phone sleeping does not stop cover (the host carries it). `λ_min` is retained only for the **phone→host leg** (§3c).
- `λ` gates only on **genuinely data-independent host state** (AC power, thermal, never screen/"Active") — a host on wall power is simply always `λ_full`.

### §3c The mobile surface (stated residual, not fully closed here)
The phone→host leg and phone-initiated sends remain a surface: the phone must reach the host to originate a send, and that leg has its own observability. v2 treats it as a **stated residual** (R-mobile) — the host-side circuit population is unlinkable, but the phone→host hop is a separate problem (candidate: the phone maintains a single constant-rate covered channel to its host, so phone-originated activity is hidden in that one channel; specify in a follow-up). Flagged for the review + THREAT_MODEL.

### §3b Host-restart recovery (Josh — the host's downtime regime)
An "always-on" host still reboots (updates, power loss). On restart the live circuit population is gone (circuits are network state, not persisted). Recovery MUST NOT leak:
- **Restart-deterministic process phase.** The constant-rate schedule resumes on a **seeded, restart-exact phase** (the HYP-40x discipline already used for the data-plane cover grid), so a restart is not a distinguishable cover-phase discontinuity.
- **Rebuild at `λ`, never a burst.** The population refills at the normal constant rate `λ` (one build per turnover slot), NOT an N_target-wide burst — a burst would be a "host just restarted" rate spike AND would let the resuming real conversations show through the mix. The population climbs from 0 to `N_target` over ~`N_target/λ`.
- **Stated recovery-window residual (R-recovery).** While the population is below `N_target`, there is less cover to hide behind and the concurrent-count is transiently below its constant — a bounded window of degraded guarantee, stated in THREAT_MODEL, not implied zero. During recovery, real sends that outrun the rebuild cold-start on the process (bounded latency), never outside it.
- **Restart safety (engineering).** The process's persistent state (schedule seed, `N_target`, the long-term contact set, the turnover limiter) persists atomically so recovery resumes coherently (CLAUDE.md restart-safety standard).

---

## §4 Observable-match table (v2 — incl. #13 refresh, #14 lifetime, #15 recovery)

| # | Axis | Observable | Disposition (v2) |
|---|---|---|---|
| 1–12 | — | (v1 build/slot/sequence rows) | MATCH / STRUCTURAL as v1 (#2 eligibility STRUCTURAL → §5) |
| 13 | sequence | refresh rate | MATCH — refresh = population turnover at constant `λ`; bounded-jitter non-separable (§2b) |
| **14** | **lifecycle** | **concurrent count + circuit lifetime** | **MATCH (#5 fix)** — `L=N_target` constant; lifetime ⊥ real/cover role (§1) |
| **15** | **sequence** | **rate/count during host restart** | **MATCH (recovery)** — restart-exact phase + rebuild-at-λ; transient below-`N_target` window is the stated R-recovery |
| — | mobile | phone→host leg | **STRUCTURAL residual (R-mobile, §3c)** — host population unlinkable; phone hop separate |

**Acid test:** for every non-STRUCTURAL row an adversary handed only that observable classifies at chance — now including the concurrent-count and lifetime projections, not just the rate.

---

## §5 The affirmative bound (unchanged from v1 — F4 stays closed)

Loopix constant-rate/Poisson indistinguishability, **conditional on the cover-eligible sub-channel**, now extended to the lifecycle: real-vs-cover is indistinguishable on the count/shape/**rate/concurrent-count/lifetime** channel, memoryless (no composition budget). Non-eligible cold-starts remain a stated residual (R-2). The PCP-φ leg stays dropped (substitution has no `λ_u`). Channel restriction flagged sharply: the bound is against a count/shape/rate/**lifetime** observer; destination + fine timing remain in the residual set where the named multi-carrier/Tightrope adversary (research §6) operates.

---

## §6 Residuals — THREAT_MODEL, never implied zero

R-1 first-contact cold-start · R-2 non-eligible destination + DATA follow-up · R-membership · R-timing · **R-aggregate-N = `N_target` (now the advertised constant)** · **R-cap** (concurrency capped at `N_target`; a send beyond it waits) · **R-recovery** (bounded degraded window on host restart, §3b) · **R-mobile** (phone→host leg, §3c) · **R-jitter** (the `W` window's residual if the non-separability argument only partly holds) · R-7 draw productivity.

---

## §7 Setup + teardown fingerprint identity

All builds (cold-start, turnover-refresh, cover) are byte+timing-identical relay-completing telescoping builds with fixed intent-independent carrier fan-out (closes HYP-518). **v2 adds:** teardown (`CMD_DESTROY`) must be identical across real-carrier and cover circuits, and issued on the constant-rate turnover schedule (not on conversation-end) — else teardown timing re-opens #14. Verify sequence identity (build + teardown) in review (§10 Q2).

---

## §8 Constants

| Constant | Role | Class |
|---|---|---|
| `N_target` | constant concurrent circuit population (host) | **the #5 knob;** ≥ max concurrent conversations; HYP-171 + host-capacity tuned |
| `λ` | population turnover (build=teardown) rate | mechanism; `= N_target/E[W]` |
| `W` | bounded-jitter refresh window | **new (F2);** deadline-slack vs jitter-entropy |
| `λ_min` | phone→host leg floor (mobile only) | retained for §3c |
| recovery seed / phase | restart-exact process resume | HYP-40x discipline |

**Build order: HYP-331 (store+drive lifecycle; the pool becomes the `N_target` population) → HYP-522.**

---

## §9 Tests (rule #27 + the lifecycle property leg)

- **Property test:** fails when **any** of `{build-rate, teardown-rate, concurrent-count, circuit-lifetime-distribution}` correlates with activity (active-conversation count or send events), across regimes: single/multi-conversation at `λ_full`, saturated at `N_target`, and **during simulated host restart**. (v1 tested rate only.)
- **Integration:** real send to a carried peer emits zero build/teardown; a real conversation ending does not trigger an activity-timed teardown.
- **Smoke:** the process holds `N_target` with zero real traffic (all cover), turns over at `λ`, and recovers restart-exact from a killed process.
- **Bound harness:** the conditional lifecycle-Loopix indistinguishability + the enumerated residuals.

---

## §10 Open questions for the next cross-vendor DESIGN-review

1. **Bounded-jitter non-separability (§2b) — the load-bearing new argument.** Is "the observer can't anchor the refresh because `t_b` is cover-hidden" actually airtight, or can the population schedule be reconstructed statistically over an 18–24h window from the aggregate turnover stream alone?
2. **Teardown identity (§7).** Is `CMD_DESTROY` genuinely identical + constant-rate-scheduled across real-carrier and cover circuits, or does a real conversation's end leak through *when* its (now-cover) circuit is chosen for turnover?
3. **`N_target` saturation (R-cap).** When real conversations saturate the population, the "wait for a turnover slot" latency — does it break `Critical`, and does the wait itself (a real conversation blocked pending a slot) leak?
4. **R-mobile (§3c).** Is "one constant-rate covered phone→host channel" sufficient for the mobile leg, or does phone-origination leak regardless of the host-side population being clean?
5. **R-recovery (§3b).** Over the ~`N_target/λ` rebuild window, how much does the guarantee degrade, and is a restart itself (the phase resumption) truly indistinguishable to an observer who was watching before the reboot?
