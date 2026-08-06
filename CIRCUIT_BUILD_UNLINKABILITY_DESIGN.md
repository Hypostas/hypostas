# CIRCUIT_BUILD_UNLINKABILITY_DESIGN.md — HYP-522

**Status:** DESIGN **v3**, pre-review, 2026-08-06. Supersedes v2 (review found 2 P1s: 1(b) carried-circuit liveness, #2 bounded-jitter spectral separability). Grounded in `CIRCUIT_BUILD_UNLINKABILITY_RESEARCH.md` + Josh's decisions: **(a) full continuous cover · computer-host holds the population + restart recovery · make-before-break + machine-checked spectral bound**. Companion derivation: `circuit_spectral_bound_derivation.py`. Prereq: **HYP-331**. Next: cross-vendor DESIGN-review (both legs; Codex-on-hypostas broken — HYP-533 — is a precondition).

## v2→v3 changelog (the 2 P1s)
- **1(b) (P1) — carried-circuit liveness → opposite count transients.** v2 tore over cover circuits destroy-first (count −1) but a live carrier needs make-before-break (count +1): a per-turnover real/cover classifier. **v3: make-before-break on ALL turnovers** (cover included) — build successor, fixed overlap, destroy predecessor at a **fixed offset regardless of drainage** — so every turnover is +1-then-−1, symmetric; lifetime ⊥ role (§2).
- **#2 (P1) — bounded-jitter is spectrally separable.** v2's `Uniform[MAX−W,MAX]` (CV≪1) put a periodogram line at 1/MAX; my "can't anchor" argument defended the wrong attack (aggregate reconstruction needs no anchor). **v3: memoryless (exponential) refresh truncated at the hard deadline** — Poisson is spectrally white; only the truncation atom (prob `e^{−r}`, `r=MAX/E[T]`) is non-white, and it is **exponentially suppressed by the refresh rate**. `circuit_spectral_bound_derivation.py` computes the 1/MAX line below the 24h periodogram floor at **r ≳ 4**, negligible by **r ≈ 8** (`p_trunc ≈ 3·10⁻⁴`) — a **machine-checked spectral bound** (pending review), the setup-channel analog of the GPA frontier (§2b, §5).
- **P2/P3 folded:** headline downgraded to "a **host-originated** real send…" (R-mobile is load-bearing, §3c); saturation wait is conversation-end-bounded → `N_target` sized so saturation is rare (§2, R-cap); §3b restart framing corrected + rebuild-at-λ age-re-randomization credited (§3b); teardown identity resolved by fixed-offset destroy (§2/§7).

---

## §1 The invariant (v3 — lifecycle, symmetric turnover)

> **The dyad's circuit population is held at a constant concurrent size `N_target`, and every circuit — cover or real-carrier — is built and torn down on ONE identical, make-before-break, memoryless-scheduled turnover process whose rate is a function of wall-clock time, configuration, and coarse host power-state ONLY. A real conversation OCCUPIES a slot (migrating across successive carriers as they turn over); it never changes the population size, the turnover schedule, the per-turnover count transient, or any circuit's lifetime law.**

Pinned constant, closing #5, 1(b), and #2 together: **concurrent count** `L=N_target`; **per-turnover count transient** = +1→−1 for every circuit regardless of role (1(b)); **lifetime law** memoryless-truncated, identical for cover and real (lifetime ⊥ role); **turnover spectrum** white to a machine-checked bound (#2).

---

## §2 The mechanism — constant-population, make-before-break, memoryless turnover

The always-on host maintains `N_target` live circuits. Each circuit's turnover fires on a **memoryless (exponential, rate μ) clock truncated at `CIRCUIT_MAX_LIFETIME` (MAX)**. On a turnover — **identical for cover and real-carrier (1(b) fix):**
1. **Build** the successor circuit to a §2c target (count `N_target → N_target+1`).
2. **Fixed overlap** `OVERLAP` (a constant, not drainage-gated): if the predecessor carries a live conversation, the conversation migrates to the successor at overlap-start; in-flight predecessor cells drain during `OVERLAP`.
3. **Destroy** the predecessor at exactly overlap-start `+ OVERLAP`, **regardless of whether cells are still draining** (count `→ N_target`). A rare boundary cell still in flight is dropped and **retransmitted on the successor** (rides the constant data-plane cover — not observable). This makes the teardown instant a **fixed offset**, not an activity-timed one (closes 1(b)'s drain-tail + §7 teardown identity).

Every turnover is thus a **symmetric +1-then-−1** count blip of identical shape and timing for cover and real. Real conversations are handled by **occupation**: a send to a peer already carried rides its circuit (no turnover); a send to a new peer occupies the next turnover's successor build (target = that peer, within the fixed `N_target` budget — no extra circuit). **Saturation (R-cap):** if all `N_target` slots carry live conversations, a new peer waits for a slot to free — which happens on **conversation-end (unbounded)**, not turnover. So `N_target` MUST be provisioned above the realistic max concurrent conversation count; a genuinely saturated `Critical` send is a stated latency residual, and `N_target` sizing is the mitigation (host-affordable).

### §2b Memoryless-truncated refresh + the spectral bound (#2)
Turnover inter-times are `T = min(Exp(μ), MAX)`, mean `E[T] = MAX/r`. Poisson (`Exp`) renewal is spectrally **white** — no line for the periodogram attack. The only non-white component is the truncation atom at `MAX` (a circuit reaching the deadline un-refreshed), probability `p_trunc = e^{−r}`, whose 1/MAX line power scales `~p_trunc²`. Per `circuit_spectral_bound_derivation.py` (renewal Bartlett spectrum + a 24h coherent-line-vs-white-floor detection model): the line is **below the 24h periodogram floor at `r ≳ 4`** and negligible by **`r ≈ 8`** (`p_trunc ≈ 3·10⁻⁴`). **Recommend `r ≈ 8`** (refresh mean `E[T] ≈ 4 min`) for margin; cost = `r×` the naive one-refresh-per-lifetime rate (host-affordable; HYP-171-tuned). **This bound is computed, PENDING cross-vendor review** — the detection-SNR model is the load-bearing assumption the gate must check (the GPA lesson: never self-certify an affirmative bound).

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
| 13 | sequence | refresh rate + **spectrum** | MATCH — memoryless-white; 1/MAX line below the 24h floor at r≳4 (§2b, machine-checked pending review) |
| 14 | lifecycle | concurrent count + **per-turnover transient** + lifetime | **MATCH (1(b) fix)** — `L=N_target`; every turnover +1→−1 symmetric; lifetime ⊥ role |
| 15 | sequence | host-restart count | STATED R-recovery — count collapse observable (§3b) |
| — | mobile | phone→host origination | timing MATCH via §3c covered channel; destination STRUCTURAL (R-2/R-mobile) |

---

## §5 The affirmative bound (v3)

Loopix constant-rate/Poisson indistinguishability, **conditional on the cover-eligible sub-channel**, over the full lifecycle: real-vs-cover indistinguishable on count/shape/rate/**concurrent-count/lifetime/spectrum**, memoryless (no composition budget). **The spectrum leg is the new machine-checked piece** (`circuit_spectral_bound_derivation.py`, §2b) — encode as a `gpa-sim`-style periodogram harness (rule #8). Non-eligible cold-starts + destination remain stated residuals; PCP-φ stays dropped. Channel restriction stated: the bound is against a count/shape/rate/lifetime/**spectrum** observer; fine per-cell timing + destination are the residual set where the Tightrope multi-carrier adversary operates.

---

## §6 Residuals — THREAT_MODEL, never implied zero

R-1 first-contact · R-2 non-eligible destination + follow-up · R-membership · R-timing (per-cell) · R-aggregate-N (`=N_target`) · **R-cap** (saturation → conversation-end wait; `N_target` sized to make it rare) · **R-recovery** (host-restart count collapse ~`N_target·E[T]`) · **R-mobile** (phone→host destination) · **R-drain** (rare boundary cell-drop → retransmit) · **R-spectral** (the `p_trunc=e^{−r}` residual line at the chosen `r`) · R-7 draw productivity.

---

## §7 Fingerprint identity
Builds AND teardowns byte+timing-identical across cover/real, fixed intent-independent fan-out (HYP-518). Teardown identity is now **structural, not aspirational** (v2's flaw): the fixed-offset destroy (§2 step 3) makes every teardown a constant-offset event independent of in-flight data. Verify multi-cell build+teardown sequence identity in review (§10 Q2).

---

## §8 Constants

| Constant | Role | Class |
|---|---|---|
| `N_target` | constant host circuit population | ≥ max concurrent conversations (R-cap); HYP-171 + host-capacity |
| `r = MAX/E[T]` | refresh-rate multiple → spectral flatness | **#2 knob; recommend ≈8** (derivation); cost `r×`, host-tuned |
| `E[T]` | memoryless refresh mean = MAX/r | ≈4 min at r=8 |
| `OVERLAP` | fixed make-before-break overlap | constant (drainage-independent); 1(b) |
| mobile channel rate | phone→host covered-channel λ | §3c |
| restart seed | restart-exact schedule phase | HYP-40x |

**Build order: HYP-331 → HYP-522.**

---

## §9 Tests (rule #27 + lifecycle + spectrum)
- **Property test:** fails when any of `{build-rate, teardown-rate, concurrent-count, per-turnover count-transient sign, lifetime distribution, turnover PERIODOGRAM}` correlates with activity, across regimes (single/multi-conversation, saturated, host-restart).
- **Spectral harness:** the `circuit_spectral_bound_derivation.py` periodogram bound encoded as a `gpa-sim` test (the 1/MAX line vs the white floor at the chosen `r`).
- **Integration/Smoke:** real send to a carried peer emits zero build/teardown; conversation-end triggers no activity-timed teardown; the process holds `N_target` at all-cover and recovers restart-exact.

---

## §10 Open questions for the next cross-vendor DESIGN-review
1. **The spectral bound's detection model (§2b).** Is "coherent line integration vs white floor over 24h" the right adversary model, or does a matched-filter / Neyman-Pearson detector lower the safe `r`? Re-derive against the actual test (the GPA lesson — the bound is only as good as the assumed adversary).
2. **Fixed-offset teardown drainage (§2 step 3, R-drain).** Does dropping a boundary cell + retransmit actually stay unobservable, or does the retransmit's timing (or the migration handoff) leak the conversation across the carrier hop?
3. **Migration handoff (§1 corollary).** Is a conversation hopping carriers at each turnover truly seamless+unobservable, or is the `Warming→Active` handoff of live traffic a distinguishable event?
4. **R-mobile destination (§3c).** Does the single covered phone→host channel + host-side occupation actually bound phone-origination, or does the destination leak swallow the guarantee for phone-primary users?
5. **`N_target` sizing vs R-cap/R-recovery.** What `N_target` makes saturation rare AND keeps the restart-recovery window (~`N_target·E[T]`) tolerable — do these pull against each other?
