# COVER_DITHER_BOUNDED_DELAY_DESIGN.md — bounded-delay symmetric RR on the ceremony bit

**Status:** ⛔ **REFUTED by the cross-vendor DESIGN-review, 2026-08-05** (Codex generic 3/2 P1, reasoning-hygiene
3/1 P1, Claude depth 3 P1). **Do not build. This is the terminal of the design iteration — three drafts, three
refutations, and v3 re-entered v1's exact trilemma.** The sensitive-event construction is routed to formal work
(HYP-329); Phase-1 ships only the correctness fixes that survived every review. For **HYP-527** (closes **HYP-526**).
Supersedes the two

> ## ⛔ Why v3 is REFUTED — and why the design iteration STOPS here (route, don't redraft)
>
> **The decisive observation (Claude):** P1 #1 and P1 #3 both trace to **the same trilemma v1 named** — a mechanism
> cannot be secret-independent ∧ bounded-delay ∧ symmetric at once. v3 picked the unbounded-latency corner and
> *mislabeled* it bounded. The falling finding count (7→7→3) was not convergence; it was the same wall from three
> angles. A v4 would re-enter it again.
>
> **P1 — the "bounded delay" is geometric and unbounded, and deleting `has_pending_real_volume` (`:449`) is WHAT
> unbounds it.** That secret-conditioned suppression *was* the current delay bound; removing it to be
> "secret-independent" is exactly what makes the delay a Geometric(1−γ) with P(≥2 epochs)=γ=0.41 — a
> **high-probability** violation of Josh's ≤30 s, not a tail. Bounding it back (cap consecutive down-flips) makes
> "two non-Critical in a row" impossible for a ceremony but possible while idle ⇒ ε=∞. Both horns are bad.
>
> **P1 — the binary {Critical, not-Critical} RR is ASSUMED, not derived.** The down-flip *target rate* is left
> unspecified; for the natural "one rung down," an idle dyad never emits that rate ⇒ ε=∞ in that direction. This is
> precisely **GPA_ANALYSIS §5(b) OPEN item 2 — "a specified four-class RR construction (output matrix + recomputed
> ε)" — which was already routed to HYP-527/HYP-329, and which every design I wrote SKIPPED and replaced with a
> binary formula I cannot derive.** That skip is the tell: the artifact HYP-527 actually needs is the formal
> construction, not a dither draft.
>
> **P1 — the capped guarantee is unsound against the code.** The budget cap clamps the **committed class**
> (`cover_traffic.rs:525,768`), not just cover, so a capped ceremony emits at ≤Elevated and `P(Critical|capped
> ceremony)=0` — the Critical down-flip **never engages** and protects by exactly zero. §3's "graceful for capped"
> rests on a mechanism state that never occurs; the real capped leak (Elevated ε=∞) is v2's T2, intact.
>
> **Plus:** the 9.9× up-cover drives dyads into the ≥50 % cap that disables up-cover (v2's self-defeat, recurring);
> the budget is double-spent (ceremony bit + activity bit each claim the full ln2); the §5 guard encodes the
> *binary* ε so it cannot catch the ε=∞ hole; the win holds only for D≤W (~4 min at W=8) against an unmeasured
> ceremony duration (v2's base-rate failure class).
>
> **What SURVIVED (bank it — it is the SPEC for HYP-329, produced by a design process that produced no design):**
> the **axiom inversion** (ceremonies are cryptographic commitments, more delay-tolerant than live consults — a
> sound premise); the two **impossibility theorems** (T1 symmetric ⟹ the 24× floor; T2 rate-manipulation cannot
> hide a capped dyad); the **factor-2 machine-check** discipline (finally correct: γ=√2−1 at W=1); the
> **hard-vs-soft ceiling split** and the **no-held/no-self destination** availability handling (real correctness
> fixes); and the **exhaustive support-hole list** any construction must avoid (down-flip target, cover-OFF,
> committed-class cap, cross-channel composition, duration). Every citation resolved (rule #33 clean).
>
> **THE TERMINAL:** the affirmative Phase-1 sensitive-event dither (the 4-class output matrix + a proven ε + a
> delay rule compatible with that ε) is **HYP-329** formal work — proven un-self-producible across v1/v2/v3 + the
> factor-2 slipping four times. **Phase-1 ships the correctness fixes only** (hard-vs-soft ceiling, availability,
> mid-epoch latch, factor-2-restored activity dither) + THREAT_MODEL honesty that sensitive-event rate-hiding is
> substantially Phase-2. That is the "implement before closing" Josh asked for, minus the broken privacy claim.
refuted designs — v1 (`COVER_DITHER_SYMMETRIC_DESIGN.md`, 4-class RR, infeasible budget) and v2
(`COVER_RATE_QUANTIZATION_DESIGN.md`, coarsening, buys ~0 for the sensitive events). This is the construction
the v2 review itself named. **Decision on record (Josh, 2026-08-05):** a **bounded delay ≤ 1 dither epoch
(~30 s) on ceremony / dissolution / succession traffic is acceptable** — the commitment completes normally;
only its cover packets settle over the window.

**The ε is machine-checked, not hand-derived** (the `python3` block in the HYP-527 trail, 2026-08-05) — with
the **group-privacy factor of 2 inside it**, because that factor is my documented blind spot (dropped 3× this
session). The §5 guard encodes `2·W·ε_epoch(γ) ≤ budget` as a test; γ=1/3 is *rejected*, γ=0.414 accepted.

**Code grounded in `dyados@<pin-at-build>`**, `main`-read 2026-08-05. Companions: `GPA_ANALYSIS.md`
(diagnostic), the two refuted designs (kept for the record + their reviews).

---

## §1 The construction — invert the axiom, then it is a plain symmetric RR

**The axiom the first two designs got backwards:** ceremonies (bond / dissolution / succession) are
*cryptographic state commitments* — the **least** latency-sensitive high events; the **live** Elevated traffic
(consult, bio-stream) is the latency-sensitive one. So the class that can absorb a delay is exactly the one we
most need to hide. Josh's decision makes the delay legal; that dissolves the trilemma that killed v1/v2.

**The ceremony bit** — the observable "is this dyad emitting the 200 ms ceremony rate?" — gets a **symmetric
randomized response**, both directions now affordable:

- **Up-cover (idle → Critical), COSTS bandwidth:** an idle dyad emits a 200 ms cover epoch with prob γ, so
  `P(observe Critical | true idle) = γ > 0`.
- **Bounded-delay down-flip (Critical → lower), FREE:** a true-ceremony dyad emits a *slower* rate for a γ
  fraction of epochs — its real 200 ms traffic waits ≤ one dither epoch (the delay Josh approved) — so
  `P(observe not-Critical | true ceremony) = γ > 0`. Emitting slower *saves* bandwidth, so this direction
  costs nothing and **a capped dyad can do it** (§3).

With `γ_up = γ_down = γ`, the ceremony-bit observable is a binary RR: `P(Critical|idle)=γ`,
`P(Critical|ceremony)=1−γ` — **symmetric** `ε_epoch = ln((1−γ)/γ)`. This is the standard Warner RR
(`measure.rs:145`), now actually realizable because both flip directions exist under the bounded delay.

The down-flip is **secret-independent** (a keyed per-epoch draw, not a function of queue occupancy), so the
v1/v2 secret-conditioning leak is gone by construction, and the ceremony's real traffic is delayed only within
the approved bound — never starved (the queue drains at the next non-down-flipped epoch, ≤ 1 epoch later).

---

## §2 The ε — machine-checked, factor-2 included (this is where v1/v2 died)

A partner-identity hypothesis change moves **two** dyads' trajectories, so the relationship-level budget is
`2·W·ε_epoch`, **not** `W·ε_epoch` (GPA_ANALYSIS §5(2)/§9 — the correction HYP-527 owes; `measure.rs:192`
omits it). Setting `2·W·ε_epoch(γ) ≤ TIER3_EPSILON_BUDGET = ln 2` gives (computed):

| W (protection window, epochs) | γ | `2·W·ε_epoch` | idle up-cover cost |
|---|---|---|---|
| 1 | 0.4142 | ln 2 (exact) | 9.9× |
| 2 | 0.4568 | ln 2 | 11.0× |
| 4 | 0.4784 | ln 2 | 11.5× |
| 8 | 0.4892 | ln 2 | 11.7× |

The guard **rejects** the tempting γ=1/3: `2·1·ln((2/3)/(1/3)) = 2·ln2 = ln4 > ln2`. It **accepts** γ=0.414.
This table is the spec; §5 encodes it as a `#[test]`. **No number in this doc is asserted without the
computation behind it** — the discipline v1/v2 lacked.

**Composition over a ceremony's duration is the real limit, honestly.** The down-flip is a *probabilistic*
cover (unlike v2's deterministic coarsening), so a D-epoch ceremony's per-window bound holds only for D ≤ W;
a longer ceremony spends `2·D·ε_epoch`. Tune `W` to the ceremony-duration distribution (HYP-171-adjacent
measurement), and state the achievable W in THREAT_MODEL. Durable hiding of an arbitrarily long ceremony is
Phase-2 (the odometer, GPA_ANALYSIS §5(3)/§8) — v3 does not claim otherwise.

---

## §3 The guarantee, per population — symmetric for uncapped, graceful one-sided for capped

**T2 (v2) softens but does not vanish, and the softening is the point.** The two flip directions have
opposite cost signs:

- **Uncapped dyad:** affords both directions ⇒ **symmetric ε** on the ceremony bit. `P(Critical|idle)=γ` and
  `P(not-Critical|ceremony)=γ`. Full protection — the crown-jewel win.
- **Capped dyad** (`effective_cover_ceiling < Critical`, `scheduler.rs:417`; cap-out-of-Critical at ≥50 %
  budget, `cover_traffic.rs:196-205`; LoRa/DHT device-capped): cannot afford the up-cover (`P(Critical|idle)=0`)
  **but the down-flip is free** — emitting a ceremony slower costs nothing — so `P(not-Critical|ceremony)=γ`
  still holds. Result: **one-sided** protection. Observing not-Critical is ambiguous (a real ceremony often
  looks lower); only observing Critical still leaks "not idle." **This is strictly better than v2, where a
  capped dyad's ceremony was a certain (ε=∞) tell in both directions** — the down-flip gives capped dyads real
  partial cover they could never get from any up-cover-only scheme.

State this split in THREAT_MODEL: symmetric for uncapped, one-sided-but-nonzero for capped; **and** the
product mitigation the v2 review noted — a dyad may **defer a ceremony to an uncapped window** (wall-power /
WiFi) to get the full symmetric guarantee, which sidesteps T2 entirely for the events that most need it.

---

## §4 The other two channels — one-sided, and NOT claimed symmetric (the v2 §4 fix)

v2 falsely claimed the activity channel was fixed. It is not delayable (Josh approved delaying *ceremonies*,
not normal messaging or live consults), so it stays **up-cover-only / one-sided** — and v3 says so plainly:

- **Activity bit (Ambient↔Standard):** up-cover only (idle → Standard, cheap), **down-flip deleted** (it was
  the secret-conditioned latency-breaker; deleting it is what removes leak #2). One-sided: observing Ambient ⇒
  idle. Retune its γ with the **same factor-2 budget** (§2). This is the honest guarantee the shipped dither
  always had, correctly labeled.
- **Elevated bit (live consult / bio-stream):** latency-sensitive, not delayable ⇒ up-cover only, one-sided.
  Its frequency still helps populate the high-rate observable, but v3 makes **no** symmetric claim for it.

Only the **ceremony (Critical) bit** is symmetric, because it is the only class Josh approved delaying. That is
the correct, minimal scope — and it is the class that matters most.

---

## §5 Correctness fixes the review confirmed (carry, done right this time)

- **rule #32 cross-crate guard:** `#[test]` in `vita-carriers` importing the budget: assert
  `2·W·epsilon_epoch_binary(γ) ≤ TIER3_EPSILON_BUDGET` **and** `0 < γ ≤ ½` **and** `W ≥ 1` (review P2 on
  unbounded γ). The `2·` is the whole point — encode it, do not re-derive it.
- **Hard vs soft ceilings (v2 P2):** the mid-epoch latch applies **only to the privacy-soft rate** (the RR
  draw). **Hard controls — `cover_suspended`, budget-hard-exhausted, carrier-policy, battery-emergency — take
  effect immediately**, pre-empting the latch. Two distinct code paths; a battery emergency is never delayed
  30 s for a privacy invariant.
- **Availability gap (v2 P2):** do **not** hold a last destination (a recurring-endpoint tell, §2.4) and do
  **not** self-address. If no cover destination exists, the slot is honestly idle → the cover-OFF regime
  (GPA_ANALYSIS §2), and closing it is **Phase-2** (a shared rendezvous set with its own anonymity-set
  argument, not a per-dyad hold). Route it, don't paper it.
- **Mid-epoch mutation:** latch the RR draw + soft ceiling per dither epoch (survived v2 review, matches
  GPA_ANALYSIS §7#2).

---

## §6 gpa-sim + cost (rule #8/#27)

- Model the **symmetric** ceremony-bit RR (both directions) + the **capped cohort** (down-flip only). Assert
  the **likelihood ratio** ≤ `e^{ε_epoch}` directly — **not** TV distance and **not** "advantage ≤ e^{ε}"
  (both v-review P2s: TV passes a support hole; advantage ≤ 1 always passes). The LR is the quantity with the
  support-hole sensitivity the guard needs.
- Publish cost in THREAT_MODEL: **up-cover ≈ 9.9× idle for W=1 (uncapped); down-flip FREE** (saves bandwidth);
  capped dyads pay **nothing** (down-flip only). This is far under v2's mischief and the 24× symmetric floor.

---

## §7 Residuals → Phase-2 (stated upfront, not as an afterthought)

The ceremony **rate** bit is hidden (symmetric, uncapped). NOT hidden by v3, and not claimed:
**duration/onset/periodicity** within the high observable; the **§2.2 size/volume** channel (a bursty
ceremony vs a steady bio-stream at the same rate); the **destination-frequency** channel (§2.4, which partner);
**durable** hiding of a ceremony longer than W; and the **capped up-cover** direction. All Phase-2 (multi-hop
mixing) or their own tracked follow-ups (file the duration/size leaks as issues per rule #4). The affirmative
per-window bound is **HYP-329**.

---

## §8 Build chunks (after this design review passes)

- **C1** `ceremony_bit_rr(true_class, draw, γ, ceiling)` — symmetric up-cover/down-flip pure fn; the down-flip
  emits a bounded-delay lower rate; capped ⇒ down-flip-only. Unit tests incl. the symmetric/one-sided split
  and the `P(Critical|idle)=γ`, `P(not-Critical|ceremony)=γ` histograms.
- **C2** wire into `emitted_class`/`dithered_rate_ms`; the bounded-delay queue semantics (drain ≤ 1 epoch);
  activity bit up-cover-only + delete its down-flip; factor-2 γ retune.
- **C3** hard-vs-soft ceiling split (immediate hard-control path).
- **C4** `gpa-sim` symmetric + capped model; LR assertions.
- **C5** rule #32 guard (`2·W·ε ≤ budget`, `0<γ≤½`, `W≥1`) + γ/W/cost in THREAT_MODEL.
- **C6** restart-exactness (HYP-40x — the draw stays `f(seed‖epoch)`); integration + smoke (rule #27); the
  bounded-delay latency test (real ceremony traffic drains ≤ 1 epoch); crypto-class gate; land; close 526+527.

---

## §9 Open questions for the cross-vendor DESIGN-review

1. **Is the ceremony bit the right (only) symmetric target,** or should Elevated also get a bounded delay
   (Josh scoped the delay to ceremonies — confirm consults are genuinely not delayable)?
2. **W vs the ceremony-duration distribution** — the per-window bound needs D ≤ W; is the measurement owner
   correct (this is NOT HYP-171's `q` — file the right measurement, do not repeat v2's mis-attribution)?
3. **The bounded-delay queue semantics** — does draining a down-flipped ceremony at the next epoch actually
   bound the delay at 1 epoch, or can consecutive down-flips stack (draw independence per epoch says no, but
   verify the worst case)?
4. **Capped one-sided** — is nonzero-but-one-sided honestly enough for capped dyads, or does the residual
   Critical-observation leak plus §2.4 destination still identify (as it did in v2)? Quantify.

## §10 Provenance

Arithmetic: the `python3` verification in the HYP-527 trail, 2026-08-05 — the (W, γ, 2Wε, cost) table;
γ=1/3 rejected `2ln2=ln4`; capped one-sided. Code: `emitted_class` (`cover_traffic.rs:435-451`),
`effective_cover_ceiling` (`scheduler.rs:417`), cap-out-of-Critical (`cover_traffic.rs:196-205`), binary RR +
budget (`measure.rs:137-198`), rates (`cover_traffic.rs:44-53`). Standard results: randomized response (Warner
1965), group privacy + sequential composition / odometer (Dwork–Roth; Rogers et al.). Affirmative bound →
**HYP-329**. This is a **design for review**, not a proof; every ε is machine-checked but the *tight* composed
identity bound is HYP-329's.
