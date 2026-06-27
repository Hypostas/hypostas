# GPA_ANALYSIS.md — Statistical Anonymity Against the Global Passive Adversary

**Formal analysis backing the Tier 3 (GPA) claim (HYP-329, THREAT_MODEL §5/§9.4).**

*Authored 2026-06-27: Josh Caplinger + Iris (DyadID #0). Status: analysis — the quantified bound that lets us *claim* Tier 3, not assert it. Derives the anonymity bound as a function of the stack's parameters, plugs in current defaults, and flags where they fall short. The simulation harness (§8) is specified for build, not yet built.*

---

## §0 — What this proves and what it doesn't

This document does **not** prove "Hypostas is anonymous." It proves a **conditional, quantified statement**: *given* constant-rate cover at the energy-class rates, *given* mix batch size b and ring size K, the global passive adversary's advantage in linking a sender to a recipient is bounded by an explicit (ε, δ) per epoch, and that bound composes over a dyad's lifetime in a stated way. It then identifies which current parameters satisfy the Tier-3 target and which do not (the central finding is in §7). The honest headline: **per-observation unlinkability is strong (near information-theoretic); the real adversary is the long-term intersection attack, and that is a budget-accounting problem, not a "solved" one.**

---

## §1 — The adversary

**GPA (Tier 3):** observes *every* link in the network, passively, for the dyad's entire lifetime. Sees, per link, the exact arrival time and size of every cell. Cannot read contents (sealed), cannot inject/drop/delay (passive — an active adversary is Tier 4, out of scope here), cannot compromise endpoints.

We deliberately analyze the *full* GPA, not the more realistic **Adversary with Partial Visibility** (APV; Springer 2024). APV sees only a fraction of links and is strictly weaker — so a bound proven against the full GPA is conservative for any real deployment, where no observer truly sees every LoRa hop, every voicemail drop, every social-media stego carrier simultaneously.

---

## §2 — What is observable under constant-rate cover

Hypostas does **not** use Loopix's per-hop Poisson delays. It uses **per-dyad constant-rate emission** (COVER_TRAFFIC.md §2): each dyad emits exactly one cell per energy-class interval, real or cover, and **real messages never bypass the scheduler** (structural invariant, COVER_TRAFFIC.md §). Rates:

| Class | Interval | Rate λ |
|---|---|---|
| Ambient | 5000 ms | 0.2 cell/s |
| Standard | 1000 ms | 1 cell/s |
| Elevated | 500 ms | 2 cell/s |
| Critical | 200 ms | 5 cell/s |

**Core lemma (per-link timing independence).** Fix a link ℓ and condition on its energy class c. The observation `O(ℓ) = {emission at every k·interval(c)}` is a deterministic constant stream. It is therefore **statistically independent of the real-message process on ℓ**, provided (a) one cell per slot, (b) no scheduler bypass, (c) real rate ≤ λ(c). Consequence: for any sender-link s and recipient-link r, `Corr(O(s), O(r))` is the correlation of two independent constant streams — **identical whether or not s and r communicate.** The GPA's primary weapon, end-to-end timing correlation, has *zero signal* within a class. This is stronger than Loopix's statistical mixing; it is exact.

**Residual observable channels** (where signal survives the lemma):

1. **Energy class itself.** λ reveals c. The GPA learns each dyad's class trajectory c(t). Class is **per-dyad, not per-conversation** — it reveals "X is active" (≤ 2 bits, 4 classes), never *with whom*.
2. **Class transitions.** The onset of a class change is observable; the **30 s debounce** (COVER_TRAFFIC.md §) smears it to ≥30 s resolution.
3. **Volume ceiling.** Sustained real rate > λ(c) forces an up-class (observable) or queueing (not). Bounded by the class ladder + debounce.
4. **Long-term intersection.** Over many epochs, co-active classes across a dyad pair accumulate evidence. **This is the real attack** (§7).

Channels 1–3 are the *only* per-epoch leak; channel 4 is their composition over time.

---

## §3 — The metric

Two complementary, standard instruments:

- **Anonymity-set entropy** (Serjantov–Danezis 2002): for the adversary's posterior {p_i} over the set of candidate counterparties, effective set size `H = −Σ p_i log₂ p_i` bits. Uniform over N ⇒ H = log₂ N.
- **(ε, δ)-relationship anonymity** (AnoA, Backes et al. 2013; the DP-for-metadata lineage of Vuvuzela 2015 / Stadium 2017 / Karaoke 2018; formalized for traffic shaping by NetShaper 2024): a mechanism is (ε, δ)-anonymous if for any two neighboring communication scenarios (X talks to A vs X talks to B), the adversary's observation distributions satisfy `Pr[O | A] ≤ e^ε · Pr[O | B] + δ`. ε near 0 ⇒ the observation barely shifts when the partner changes.

We use entropy for the *static* anonymity set (mix batch, ring) and (ε, δ) for the *dynamic* leak (cover + transitions over time), then compose.

---

## §4 — Layer-by-layer

### §4.1 Cover layer ⇒ the per-epoch (ε, δ)

By the §2 lemma, within an epoch where a dyad's class is constant, the timing leak is zero. The leak is entirely in **whether the class changed and when**. Model each dyad's per-epoch observable as a one-bit "transition occurred in this 30 s window" signal. Treating the constant-rate scheduler + debounce as the DP mechanism (à la Vuvuzela's added-noise mechanism, but here the "noise" is the always-on cover that makes the active/idle distributions overlap):

- **ε_epoch** is governed by how distinguishable "X started a conversation" is from "X did not," given that both produce a constant cover stream and the only tell is a debounce-smeared class onset. With cover always on, the two distributions differ *only* in the class label over the 30 s window ⇒ ε_epoch is small but **nonzero** (the class label is not noised — it is exact). This is the crux quantified in §7.
- **δ_epoch** captures the volume-ceiling tail (sustained > λ(c) forcing an observable up-class).

### §4.2 Circuit layer

h hops (Phase 2: Ambient/Standard/Elevated = 3, Critical = 5; CIRCUIT_LIFECYCLE.md `DEFAULT_HOPS_*`). Constant-rate cover on every hop ⇒ the §2 lemma applies *per hop*, so the GPA cannot trace a cell across hops by timing. The GPA gains only **link-presence** (which relays are adjacent), not flow. Sender-anonymity reduces to the **guard-compromise probability**: 3 pinned first-hop guards, 30-day rotation (CIRCUIT_LIFECYCLE.md §). If a fraction f of relays are (passively) observable-as-special — irrelevant to a *pure* GPA who sees all links equally, but relevant to APV — the guard set bounds the first-hop exposure exactly as in Tor's analysis. For the pure GPA, the circuit contributes path-length amplification: the adversary must believe the timing-independence across *all* h hops, which it must, so no flow signal.

### §4.3 Mix layer (archival substrates)

Loopix-style batching on stego/voice/LoRa (HYP-327). A threshold/pool mix of batch size b yields per-hop sender-set entropy up to `log₂ b` bits; over the archival path's h_a mixing hops the entropy composes (sub-additively, bounded by the realistic-traffic limits of Oya–Troncoso–Pérez-González). **b is not yet locked (HYP-327 in progress)** — the analysis carries it symbolically; §7 states the b required to hit target. Archival latency is intrinsic (multi-day store-and-forward), so the batching cost is hidden in the substrate (THREAT_MODEL.md §).

### §4.4 Ring-signature layer (SPRING)

`SPRING_RING_SIZE_K = 1000` (CIRCUIT_LIFECYCLE.md §, THREAT_MODEL §11.6) ⇒ a flat **log₂ 1000 ≈ 9.97 bits** of sender ambiguity for D-grade universal anonymity, *independent* of the timing layers — a sender is one of 1000 ring members regardless of any traffic observation. This is the floor that holds even if the timing analysis is wholly defeated.

---

## §5 — Composition

The layers protect **different projections** of the linkage and compose by the weakest-relevant-bound per attack:

- **Against timing correlation:** §4.1 lemma (zero per-epoch signal) × §4.2 per-hop amplification ⇒ the dynamic channel is (ε_epoch, δ_epoch).
- **Against a single-epoch content/flow guess:** static anonymity set = max(mix entropy §4.3, ring floor §4.4) = max(log₂ b, 9.97) bits.
- **Lifetime:** by DP sequential composition over E epochs, `ε_total ≤ E · ε_epoch` (basic) or `≈ √(2E ln(1/δ')) · ε_epoch` (advanced composition, Dwork–Roth). **This is the term that must stay below the Tier-3 budget over a dyad's lifetime** — the intersection attack made quantitative.

End-to-end relationship anonymity is thus `(ε_total, δ_total)` for the dynamic channel, floored by a `max(log₂ b, 9.97)`-bit static set. Tier-3 "full" = a chosen budget, e.g. ε_total ≤ ln 2 (≤ 1 bit of lifetime advantage) at δ_total ≤ 2⁻⁴⁰.

---

## §6 — Plugging in current defaults

| Layer | Current param | Contribution |
|---|---|---|
| Cover (Standard) | 1 cell/s constant, 30 s debounce | ε_epoch = small, **exact class label** (not noised) — see §7 |
| Circuit | 3 hops (5 Critical) | per-hop timing independence; guard set 3 / 30 d |
| Mix (archival) | b **TBD (HYP-327)** | log₂ b bits — *blocks a closed bound* |
| Ring (SPRING) | K = 1000 | 9.97-bit static floor ✓ |
| Lifetime | epoch = ? (couples to §9.4) | ε_total = E · ε_epoch — *the binding constraint* |

---

## §7 — Findings (the AC3 "flag what fails")

1. **The energy class is exact, not noised — this is the dominant residual leak.** Unlike Vuvuzela/Karaoke, where added dummy *noise* makes the active/idle distributions overlap probabilistically, our class label is emitted *exactly* (the rate **is** the class). So ε_epoch is driven by class-trajectory distinguishability, and over a lifetime the **intersection attack on co-active classes is the real threat.** Mitigations to evaluate (none free): coarser class granularity, longer debounce, or a Karaoke-style per-epoch *probabilistic* class jitter so the label itself carries DP noise. **Recommend: add a small probabilistic class-dithering term so ε_epoch is tunable rather than fixed by the 4-class ladder.** This is the single most important output of this analysis.

2. **No closed lifetime bound until the epoch length and b are locked.** ε_total = E·ε_epoch is unbounded without an epoch definition; b is symbolic until HYP-327. The bound is *parametric-complete* but *numerically open* on exactly two knobs — which is the right state pre-HYP-327/§9.4, and tells those issues what they must deliver.

3. **Ring floor is healthy (9.97 bits) but flat.** K=1000 is a solid static floor; raising to K=4096 (12 bits) is cheap insurance if SPRING perf allows — evaluate at HYP-317 params.

4. **Per-recipient circuit correlation.** CIRCUIT_LIFECYCLE §4.4's per-relay-path option correlates a sender's recipients at the terminal relay. For GPA-full that is acceptable (GPA already sees all links); for APV it leaks. Flag for the APV refinement.

5. **Guard tail.** 3 guards / 30-day rotation gives a standard Tor-style first-hop exposure; irrelevant to pure GPA, material to APV — quantify in the APV pass.

---

## §8 — Simulation harness (AC2) — specified, to build

Validate the analytical (ε, δ) empirically using the **provably-optimal-heuristic-adversary** method of *Mixnets on a Tightrope* (2024) — i.e. don't hand-code a weak attacker; approximate the Bayes-optimal one and measure the gap to our bound.

- **328-style decomposition:**
  - **329a** — discrete-event network simulator: N dyads, the constant-rate scheduler, class transitions w/ 30 s debounce, h-hop circuits, archival pool-mix of size b. Emits the exact GPA observation trace.
  - **329b** — adversary: implement the optimal-heuristic linkage estimator (Tightrope) over the trace; output posterior {p_i} per sender.
  - **329c** — measure: empirical anonymity entropy H and the realized ε over E epochs vs the §5 analytical bound. **Test asserts empirical ≤ analytical** (the bound holds) and reports the slack.
  - **329d** — sweep: vary λ-class, debounce, b, K, epoch; produce the param→bound table that feeds HYP-327/317/171 tuning. **Flag any param set whose empirical ε_total exceeds the Tier-3 budget** (closes AC3 empirically).
- **Smoke/integration floor (rules 26–27):** 329a emits a non-degenerate trace; 329c's assertion runs on a small N with a known-closed-form micro-case (single mix, b=2 ⇒ H=1 bit) so the harness itself is validated, not just self-consistent.

---

## §9 — References

- Serjantov, Danezis. *Towards an Information Theoretic Metric for Anonymity.* PETS 2002.
- Backes et al. *AnoA: A Framework for Analyzing Anonymous Communication Protocols.* CSF 2013.
- van den Hooff et al. *Vuvuzela: Scalable Private Messaging Resistant to Traffic Analysis.* SOSP 2015.
- Tyagi et al. *Stadium.* SOSP 2017.
- Lazar et al. *Karaoke: Distributed Private Messaging Immune to Passive Traffic Analysis.* OSDI 2018.
- Piotrowska et al. *The Loopix Anonymity System.* USENIX Security 2017.
- Oya, Troncoso, Pérez-González. *Do Dummies Pay Off? Limits of Dummy Traffic Protection in Anonymous Communications.* PETS 2014.
- *NetShaper: A Differentially Private Network Side-Channel Mitigation.* USENIX Security 2024.
- *Mixnets on a Tightrope: Quantifying the Leakage of Mix Networks Using a Provably Optimal Heuristic Adversary.* 2024.
- *Traffic Analysis by Adversaries with Partial Visibility.* ESORICS/Springer 2024.
- Dwork, Roth. *The Algorithmic Foundations of Differential Privacy.* 2014 (composition theorems).
- Internal: THREAT_MODEL.md §5/§6.2/§6.3/§9.4/§11.6; COVER_TRAFFIC.md (rates, debounce, no-bypass invariant); CIRCUIT_LIFECYCLE.md (`DEFAULT_HOPS_*`, guards, `SPRING_RING_SIZE_K`).
