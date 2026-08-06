# CIRCUIT_BUILD_UNLINKABILITY_DESIGN.md — HYP-522

**Status:** DESIGN **v4**, pre-review, 2026-08-06. Supersedes v3 (review REFUTED the *bound* — the mechanism was credited sound; the truncation atom was analyzed only in the spectrum but is a detectable point mass in the per-circuit LIFETIME histogram, and the "info-theoretic / memoryless" claim was false). Grounded in `CIRCUIT_BUILD_UNLINKABILITY_RESEARCH.md` + Josh's decisions. Companion derivation: `circuit_spectral_bound_derivation.py`. Prereq: **HYP-331**. **The affirmative bound cannot be CERTIFIED until Codex-on-hypostas (HYP-533) is fixed** — this doc iterates via the Claude adversarial (MC-backed) leg; the Codex cross-vendor leg is owed, tracked.

## v3→v4 changelog (the bound-P1 + reframe)
- **Atom removal — DITHER the hard-cap teardown (§2b).** v3's `min(Exp(μ), MAX)` puts a point mass at exactly `MAX` (circuits reaching the deadline), detectable in the lifetime histogram (92% at r=8) and not whitened by superposition. **v4: teardown at `min(Exp(μ), MAX − U)`, `U ~ Uniform[0, D]`** — no point mass survives (the deadline-hitters smear over `[MAX−D, MAX]`); `circuit_spectral_bound_derivation.py` confirms the atom vanishes at any `r` with a modest dither. This closes both the lifetime-atom and the spectral-comb.
- **Bound REFRAME (§5) — the honest correction.** v3 over-claimed "info-theoretic Loopix indistinguishability / no composition budget." **v4: the *activity*-unlinkability guarantee is STRUCTURAL, not info-theoretic** — every circuit (cover or real) is built + torn down on the *identical* code path (same dithered law), so `concurrent-count = N_target`, per-turnover transient, and lifetime distribution are all **role-independent by construction (⊥ activity)**. The process's residual *deviation from ideal Poisson* (the smooth dithered tail) is a **bounded MEMBERSHIP residual** (R-process, already conceded — no system hides that you run the process), NOT an activity leak, precisely because it is role-independent. Retract "memoryless / no composition budget."
- **Destination migration chain = the RELATIONSHIP channel = Phase-2 (§6).** v3-review P2: a real conversation's successive carriers re-address the same peer (a per-conversation destination chain) while cover draws independently. This is the **destination/relationship** channel — which the GPA settlement (HYP-329) already places in **Phase-2 mixing**, out of 522's scope (522 owns *build/lifecycle* observability, not *who-talks-to-whom*). Stated, not a new hole.

## v2→v3 changelog (the 2 P1s)
- **1(b) (P1) — carried-circuit liveness → opposite count transients.** v2 tore over cover circuits destroy-first (count −1) but a live carrier needs make-before-break (count +1): a per-turnover real/cover classifier. **v3: make-before-break on ALL turnovers** (cover included) — build successor, fixed overlap, destroy predecessor at a **fixed offset regardless of drainage** — so every turnover is +1-then-−1, symmetric; lifetime ⊥ role (§2).
- **#2 (P1) — bounded-jitter is spectrally separable.** v2's `Uniform[MAX−W,MAX]` (CV≪1) put a periodogram line at 1/MAX; my "can't anchor" argument defended the wrong attack (aggregate reconstruction needs no anchor). **v3: memoryless (exponential) refresh truncated at the hard deadline** — Poisson is spectrally white; only the truncation atom (prob `e^{−r}`, `r=MAX/E[T]`) is non-white, and it is **exponentially suppressed by the refresh rate**. `circuit_spectral_bound_derivation.py` computes the 1/MAX line below the 24h periodogram floor at **r ≳ 4**, negligible by **r ≈ 8** (`p_trunc ≈ 3·10⁻⁴`) — a **machine-checked spectral bound** (pending review), the setup-channel analog of the GPA frontier (§2b, §5).
- **P2/P3 folded:** headline downgraded to "a **host-originated** real send…" (R-mobile is load-bearing, §3c); saturation wait is conversation-end-bounded → `N_target` sized so saturation is rare (§2, R-cap); §3b restart framing corrected + rebuild-at-λ age-re-randomization credited (§3b); teardown identity resolved by fixed-offset destroy (§2/§7).

---

## §1 The invariant (v3 — lifecycle, symmetric turnover)

> **The dyad's circuit population is held at a constant concurrent size `N_target`, and every circuit — cover or real-carrier — is built and torn down on ONE identical, make-before-break, memoryless-scheduled turnover process whose rate is a function of wall-clock time, configuration, and coarse host power-state ONLY. A real conversation OCCUPIES a slot (migrating across successive carriers as they turn over); it never changes the population size, the turnover schedule, the per-turnover count transient, or any circuit's lifetime law.**

Pinned constant, closing #5, 1(b), and #2 together — all **structurally** (the same code path builds/tears every circuit, so none of these can branch on activity): **concurrent count** `L=N_target`; **per-turnover count transient** = +1→−1 for every circuit regardless of role (1(b)); **lifetime law** dithered-truncated (§2b), identical for cover and real (lifetime ⊥ role, no point mass — #2). The residual deviation from ideal Poisson is a bounded *membership* residual, not activity (§5).

---

## §2 The mechanism — constant-population, make-before-break, memoryless turnover

The always-on host maintains `N_target` live circuits. Each circuit's turnover fires on a **memoryless (exponential, rate μ) clock truncated at `CIRCUIT_MAX_LIFETIME` (MAX)**. On a turnover — **identical for cover and real-carrier (1(b) fix):**
1. **Build** the successor circuit to a §2c target (count `N_target → N_target+1`).
2. **Fixed overlap** `OVERLAP` (a constant, not drainage-gated): if the predecessor carries a live conversation, the conversation migrates to the successor at overlap-start; in-flight predecessor cells drain during `OVERLAP`.
3. **Destroy** the predecessor at exactly overlap-start `+ OVERLAP`, **regardless of whether cells are still draining** (count `→ N_target`). A rare boundary cell still in flight is dropped and **retransmitted on the successor** (rides the constant data-plane cover — not observable). This makes the teardown instant a **fixed offset**, not an activity-timed one (closes 1(b)'s drain-tail + §7 teardown identity).

Every turnover is thus a **symmetric +1-then-−1** count blip of identical shape and timing for cover and real. Real conversations are handled by **occupation**: a send to a peer already carried rides its circuit (no turnover); a send to a new peer occupies the next turnover's successor build (target = that peer, within the fixed `N_target` budget — no extra circuit). **Saturation (R-cap):** if all `N_target` slots carry live conversations, a new peer waits for a slot to free — which happens on **conversation-end (unbounded)**, not turnover. So `N_target` MUST be provisioned above the realistic max concurrent conversation count; a genuinely saturated `Critical` send is a stated latency residual, and `N_target` sizing is the mitigation (host-affordable).

### §2b Dithered-truncated refresh (#2 / v3-review fix)
Turnover inter-times are **`T = min(Exp(μ), MAX − U)`, `U ~ Uniform[0, D]`** — a memoryless exponential refresh, with a **dithered** hard cap: a circuit that would reach the deadline is instead torn over at a random point in `[MAX − D, MAX]`. Consequence: **there is no point mass at any single lifetime** (the v3 truncation atom at exactly `MAX` is smeared over the dither window `D`), so the lifetime histogram carries no detectable spike and the spectral comb is broadened out. `circuit_spectral_bound_derivation.py` confirms the at-`MAX` pile-up vanishes (`P(detect) → 0`) for a modest dither at any refresh rate. `D` is the knob (a fraction of `MAX`, e.g. 10%); the refresh rate `r = MAX/E[T]` is a separate cost/latency knob (HYP-171-tuned) that no longer has to carry spectral flatness. **The bound this enables is stated structurally in §5, not as an info-theoretic Poisson claim** (the v3 over-claim).

### §2c Target draw
Long-term contact set, data-independent refresh schedule (never `intent.write_pending`); R-7 productivity/divergence residual stands (v2).

---

## §3 Deployment — computer-host (Josh), honestly scoped

`N_target` + turnover + cover run on the **always-on computer-host** (end-state; mobile = thin node): `N_target` generous, `λ` continuous at full rate (host on AC power → no energy-class gating; `λ` may gate only on genuinely data-independent host state — AC/thermal — never screen).

### §3c Headline scope + the mobile leg (R-mobile — load-bearing)
The bound is: **"a HOST-ORIGINATED real send emits no observable circuit build."** For a phone-primary user the origination is the phone, so the phone→host leg is load-bearing, not a minor residual. **v3 specifies:** the phone maintains **one constant-rate covered channel to its host** (Loopix substitution on that single channel) — hiding phone-origination *timing*. The conversation's *destination* still surfaces at the host as the occupied-slot's target (composes with R-2). So phone-origination is covered for *timing/which-slot*, **not destination** — stated, matching the overall residual position, not implied closed.

### §3b Host-restart recovery (Josh)
On host reboot the population is gone (network state, not persisted). Recovery:
- **Rebuild at `λ`, not a burst** — the population climbs 0→`N_target` over ~`N_target·E[T]`. **Credited property (v2 review):** rebuild-at-`λ` makes circuit ages **uniform on [0, MAX]**, the stationary distribution — no bunched-cohort echo.
- **The count collapse IS observable (R-recovery).** Honest correction to v2: "restart-exact phase" (HYP-40x) aligns the *schedule* but does nothing for the *count*, which visibly drains to 0 and refills over ~`N_target·E[T]` — a stated degraded window, not implied zero. (The schedule-phase seed still avoids a turnover discontinuity; it just doesn't hide the count.)
- **Restart safety:** schedule seed, `N_target`, contact set persist atomically (CLAUDE.md restart-safety).

---

## §4 Observable-match table (v3)

| # | Axis | Observable | Disposition (v3) |
|---|---|---|---|
| 1–12 | — | v1/v2 build/slot/sequence rows | MATCH / STRUCTURAL (#2 eligibility → §5) |
| 13 | sequence | refresh rate + spectrum + **lifetime histogram** | MATCH (activity) — dithered ⇒ no point mass, no comb (§2b); residual process-vs-Poisson deviation is role-independent → R-process (membership, §5.2) |
| 14 | lifecycle | concurrent count + **per-turnover transient** + lifetime | **MATCH — STRUCTURAL (§5.1)** — `L=N_target`; every turnover +1→−1 symmetric; lifetime ⊥ role by identical code path |
| 15 | sequence | host-restart count | STATED R-recovery — count collapse observable (§3b) |
| — | mobile | phone→host origination | timing MATCH via §3c covered channel; destination STRUCTURAL (R-2/R-mobile) |

---

## §5 The bound (v4 — STRUCTURAL activity-unlinkability + a bounded membership residual)

The v3 "info-theoretic Loopix / memoryless / no composition budget" claim was refuted and is **retracted**. The honest bound has two clearly-separated legs:

**(1) Activity-unlinkability — STRUCTURAL (the guarantee 522 owns).** Every circuit — cover or real-carrier — is built and torn down on the **identical code path** (same dithered-truncated law §2b, same make-before-break turnover §2, same fixed-offset teardown). Therefore `concurrent-count = N_target`, the per-turnover ±1 transient, and the lifetime distribution are **role-independent by construction** — they cannot depend on activity because the code that produces them does not branch on it. This is not a statistical bound to be tuned; it is an invariant of the mechanism, checkable by the §9 property test (`{count, transient, lifetime} ⊥ activity`). It is **conditional on the cover-eligible sub-channel** (a real cold-start to a non-eligible peer is destination-distinguishable — R-2).

**(2) Membership residual — the process's deviation from ideal Poisson — BOUNDED, not zero, and NOT an activity leak.** A patient adversary can still detect that the dyad *runs the circuit-cover process* (the dithered-truncated lifetime law is not exactly exponential). This is **role-independent** (identical for a purely-idle and a maximally-active dyad), so it leaks **membership**, not activity — and membership is a residual **every surveyed system concedes** (Loopix/Herd/Karaoke: "we do not hide that you run the system", research §5). The dither (§2b) *shrinks* this deviation (removes the sharp atom); the residual is a smooth tail difference, quantified by `circuit_spectral_bound_derivation.py`'s lifetime-histogram ROC and encoded as a `gpa-sim` test — a bounded MEMBERSHIP figure, not an activity claim.

**The crux for the review:** leg (1) rests entirely on "cover and real circuits are the identical code path." If any observable (destination §6, migration handoff §10 Q3) branches on role, leg (1) leaks there — those are the enumerated residuals. PCP-φ stays dropped.

---

## §6 Residuals — THREAT_MODEL, never implied zero

R-1 first-contact · R-2 non-eligible destination + follow-up · R-membership · **R-process** (§5.2 — the dithered-truncated lifetime law's smooth deviation from ideal Poisson; role-independent ⇒ membership not activity; dither-bounded) · **R-dest-chain** (§ v4 changelog — a real conversation's successive carriers re-address the same peer: the **destination/relationship channel**, which per the GPA settlement is **Phase-2 mixing**, out of 522's scope — NOT a new hole) · R-timing (per-cell) · R-aggregate-N (`=N_target`) · **R-cap** (saturation → conversation-end wait; size `N_target`) · **R-recovery** (host-restart count collapse ~`N_target·E[T]`) · **R-mobile** (phone→host destination) · **R-drain** (boundary cell-drop → retransmit; conditional on data-plane cover) · R-7 draw productivity.

---

## §7 Fingerprint identity
Builds AND teardowns byte+timing-identical across cover/real, fixed intent-independent fan-out (HYP-518). Teardown identity is now **structural, not aspirational** (v2's flaw): the fixed-offset destroy (§2 step 3) makes every teardown a constant-offset event independent of in-flight data. Verify multi-cell build+teardown sequence identity in review (§10 Q2).

---

## §8 Constants

| Constant | Role | Class |
|---|---|---|
| `N_target` | constant host circuit population | ≥ max concurrent conversations (R-cap); HYP-171 + host-capacity |
| `D` | dither width of the hard-cap teardown (`MAX−U`, `U∈[0,D]`) | **the #2 knob (removes the lifetime atom); ~10% of MAX** |
| `r = MAX/E[T]` | refresh-rate multiple | cost/latency knob only (no longer carries spectral flatness); host-tuned |
| `E[T]` | refresh mean = MAX/r | HYP-171-tuned |
| `OVERLAP` | fixed make-before-break overlap | constant (drainage-independent); 1(b) |
| mobile channel rate | phone→host covered-channel λ | §3c |
| restart seed | restart-exact schedule phase | HYP-40x |

**Build order: HYP-331 → HYP-522.**

---

## §9 Tests (rule #27 + lifecycle)
- **Property test (activity — §5.1):** fails when any of `{build-rate, teardown-rate, concurrent-count, per-turnover count-transient sign, lifetime distribution}` correlates with activity, across regimes (single/multi-conversation, saturated, host-restart). This checks the STRUCTURAL invariant directly.
- **Membership-residual harness (§5.2):** the `circuit_spectral_bound_derivation.py` lifetime-histogram ROC (dithered-truncated vs ideal Poisson) encoded as a `gpa-sim` test — a bounded MEMBERSHIP figure at the chosen `D`, not an activity claim.
- **Integration/Smoke:** real send to a carried peer emits zero build/teardown; conversation-end triggers no activity-timed teardown; the process holds `N_target` at all-cover and recovers restart-exact.

---

## §10 Open questions for the next cross-vendor DESIGN-review
1. **Is leg (1) truly STRUCTURAL / role-independent (§5.1) — the whole bound rests on it.** Does the "identical code path" claim actually hold for EVERY observable, or does some path (the migration handoff §10 Q3, the successor-destination draw, the retransmit) branch on whether a circuit carries real traffic? And is the R-process membership residual (§5.2) genuinely activity-INdependent, or can an active dyad's process deviate from an idle dyad's? (The v3 lesson: I mislabeled an activity leak; verify the activity/membership split.)
2. **Fixed-offset teardown drainage (§2 step 3, R-drain).** Does dropping a boundary cell + retransmit actually stay unobservable, or does the retransmit's timing (or the migration handoff) leak the conversation across the carrier hop?
3. **Migration handoff (§1 corollary).** Is a conversation hopping carriers at each turnover truly seamless+unobservable, or is the `Warming→Active` handoff of live traffic a distinguishable event?
4. **R-mobile destination (§3c).** Does the single covered phone→host channel + host-side occupation actually bound phone-origination, or does the destination leak swallow the guarantee for phone-primary users?
5. **`N_target` sizing vs R-cap/R-recovery.** What `N_target` makes saturation rare AND keeps the restart-recovery window (~`N_target·E[T]`) tolerable — do these pull against each other?
